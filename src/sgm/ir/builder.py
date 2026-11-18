"""Constructor de operadores y aristas con su firma y su evidencia."""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

from sgm.frontend.libnames import InfoLibname
from sgm.ir.bibliotecas import resolver_biblioteca
from sgm.ir.formatos_usuario import FormatoUsuario
from sgm.ir.models import Edge, Evidence, Graph, Operator
from sgm.ir.signature import signature

INTERNAL = "(interno)"
_ID = re.compile(r"^op(\d+)$")


def qualify(name: str) -> str:
    """Nombre de dataset calificado: `WORK.x` si no tiene biblioteca, `LIB.tabla` si la tiene."""
    clean = name.strip()
    if "." in clean:
        lib, table = clean.split(".", 1)
        return f"{lib.upper()}.{table.lower()}"
    return f"WORK.{clean.lower()}"


class Builder:
    """Crea operadores con id secuencial dentro de un plan y los conecta en el grafo."""

    def __init__(
        self, graph: Graph, decisiones_libnames: Mapping[str, dict] | None = None
    ) -> None:
        self.graph = graph
        self.formatos: list[FormatoUsuario] = []
        self.sas_formats_by_dataset: dict[str, set[str]] = {}
        self.bibliotecas: dict[str, InfoLibname] = {}
        self.decisiones_libnames = {
            nombre.casefold(): dict(decision)
            for nombre, decision in (decisiones_libnames or {}).items()
        }
        self.created: list[Operator] = []  # en orden de creación; el lowering marca su origen
        self._count = max(
            (int(m.group(1)) for m in (_ID.match(o.id) for o in graph.operators()) if m), default=0
        )

    def next_id(self) -> str:
        self._count += 1
        return f"op{self._count:05d}"

    def registrar_libname(self, info: InfoLibname) -> None:
        """Aplica una declaración o un CLEAR al registro de librefs del programa."""
        if info.opciones == "clear":
            if info.nombre == "_all_":
                self.bibliotecas.clear()
            else:
                self.bibliotecas.pop(info.nombre, None)
            return
        if info.motor is not None or info.ruta is not None or info.ruta_dinamica:
            self.bibliotecas[info.nombre] = info

    def read_dataset(
        self,
        nombre: str,
        ev: Evidence,
        in_name: str | None = None,
        *,
        include_in: bool = False,
    ) -> Operator:
        """Crea un flujo de lectura normal o un lector SQL según el LIBNAME activo."""
        dataset = qualify(nombre)
        parametros: dict[str, Any] = {"dataset": dataset}
        if include_in:
            parametros["in"] = in_name
        libref = dataset.split(".", 1)[0].casefold()
        info = self.bibliotecas.get(libref)
        if info is not None and info.ruta_dinamica:
            parametros["pending_code"] = "P-LIBNAME-RUTA-DINAMICA"
            return self.op(
                "read",
                parametros,
                ev,
                status="hueco",
                notes=[f"Pendiente: la ruta de la biblioteca {libref} depende de una macro"],
            )
        if info is None or info.ruta is not None or info.motor is None:
            return self.op("read", parametros, ev)
        if info.motor not in {"impala", "postgres"}:
            parametros["pending_code"] = "P-LIBNAME-MOTOR-SIN-SOPORTE"
            return self.op(
                "read",
                parametros,
                ev,
                status="hueco",
                notes=[f"Pendiente: motor LIBNAME '{info.motor}' sin soporte"],
            )
        try:
            destino = resolver_biblioteca(dataset, self.bibliotecas, self.decisiones_libnames)
        except ValueError as error:
            parametros["pending_code"] = "P-LIBNAME-DECISION-INVALIDA"
            return self.op("read", parametros, ev, status="hueco", notes=[str(error)])
        if destino is None:
            parametros["pending_code"] = "P-LIBNAME-BASE"
            return self.op(
                "read",
                parametros,
                ev,
                status="hueco",
                notes=[
                    f"Pendiente: P-LIBNAME-BASE; falta la decisión de motor y base para el libref "
                    f"{libref} "
                    "en decisiones/<programa>.libnames.yaml"
                ],
            )
        motor, tabla_remota = destino
        parametros.update(
            {
                "engine": motor,
                "sql": f"SELECT * FROM {tabla_remota}",
                "outputs": [dataset],
                "connection_alias": libref,
            }
        )
        if info.opciones:
            parametros["connection_options"] = info.opciones
        return self.op("read", parametros, ev, placement=f"db:{motor}")

    def op(
        self,
        kind: str,
        params: dict[str, Any],
        ev: Evidence,
        *,
        status: str = "soportado",
        notes: list[str] | None = None,
        placement: str | None = None,
    ) -> Operator:
        operator = Operator(
            id=self.next_id(),
            kind=kind,
            params=params,
            placement=placement,
            evidence=[ev],
            status=status,
            signature=signature(kind, params),
            notes=list(notes or []),
        )
        self.graph.add_operator(operator)
        self.created.append(operator)
        return operator

    def link(self, src: Operator, dst: Operator, dataset: str = INTERNAL) -> None:
        self.graph.add_edge(Edge(src.id, dst.id, dataset))

    def refresh(self, operator: Operator) -> None:
        """Recalcula la firma tras cambiar los parámetros de un operador ya creado."""
        operator.signature = signature(operator.kind, operator.params)
