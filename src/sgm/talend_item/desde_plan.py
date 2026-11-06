"""Emisor de Jobs de Talend a partir del plan de la IR: lectura, `tMap` y escritura.

El plan ya trae el grafo con sus operadores, los esquemas de las tablas de entrada (MG-P1-02) y el
componente candidato de cada operador (pasada 10). Aquí no se decide nada de eso otra vez: se arma
el Job, se conecta en el orden del flujo y se anota lo que no se pudo demostrar.

Dos reglas gobiernan el archivo, y son las del pedido del usuario:

* **Nada se pierde.** Un operador que no se traduce no desaparece: queda en `pendientes` con su
  código y su línea del SAS. Y un operador que lanza una excepción tampoco tumba la migración: se
  captura, se anota como `P-FALLO-INTERNO` y los demás se traducen igual.
* **Nada se inventa.** Sin esquema, sin separador o sin llave demostrable, hay pendiente.

Un `read` o un `write` que solo nombran un conjunto ya producido por otro operador del mismo Job no
son un paso: son el nombre que el SAS le da a ese flujo. Se pliegan sobre el operador que lo produce
en vez de generar un nodo vacío o un pendiente que no existe.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace

from sgm.ir.models import Column, Operator, Plan
from sgm.migrar.esquemas import PendienteMigracion
from sgm.talend_item.conexiones import lookup
from sgm.talend_item.desde_plan_contextos import (
    contextos_de_plan,
    reemplazar_rutas,
    rutas_de_plan,
)
from sgm.talend_item.desde_plan_map import FALLO, Fuente, construir
from sgm.talend_item.desde_plan_nodos import nodo_escritura, nodo_lectura
from sgm.talend_item.modelo import Columna, Conexion, Job, Nodo

PASO = 192  # separación de la rejilla del lienzo, en píxeles
SIN_SOPORTE = "P-OPERADOR-SIN-SOPORTE"
# Operadores que el emisor sabe traducir a un componente del Job.
CON_NODO = frozenset({"read_file", "write_file", "map", "filter", "derive", "join"})


@dataclass
class ResultadoMigracion:
    """Lo que sale de migrar un plan: los Jobs, lo pendiente y la traza a las líneas del SAS."""

    jobs: list[Job] = field(default_factory=list)
    pendientes: list[PendienteMigracion] = field(default_factory=list)
    traza: dict[str, list[int]] = field(default_factory=dict)


def _linea(op: Operator) -> int | None:
    return op.evidence[0].line_start if op.evidence else None


def _tabla(dataset: str) -> str:
    """`WORK.ventas` a `ventas`: el `tMap` no conoce la librería."""
    return dataset.strip().lower().split(".")[-1]


def _produce(op: Operator) -> list[str]:
    if op.kind in ("read_file", "map", "filter", "derive", "join"):
        return [str(d).lower() for d in op.params.get("outputs", [])]
    return []


def _como_paso(op: Operator) -> Operator:
    """Un `filter`, `derive` o `join` suelto, visto como el único paso de un `map`.

    El `tMap` los trata igual que los pasos de dentro de un `map`; así hay un solo camino de código
    para las dos formas y no dos traducciones que se pueden separar con el tiempo.
    """
    if op.kind == "map":
        return op
    paso = {"kind": op.kind, "params": op.params, "signature": op.signature}
    return replace(op, kind="map", params={"steps": [paso], **op.params})


class _Job:
    """Armado de un Job: un recorrido hacia adelante sobre los operadores de sus subjobs."""

    def __init__(
        self, plan: Plan, esquemas: dict[str, list[Column]], ruta_java: str | None
    ) -> None:
        self.plan = plan
        self.esquemas = esquemas
        self.ruta_java = ruta_java
        self.nodos: list[Nodo] = []
        self.conexiones: list[Conexion] = []
        self.pendientes: list[PendienteMigracion] = []
        self.traza: dict[str, list[int]] = {}
        self._usados: dict[str, int] = {}
        self._nodo: dict[str, Nodo] = {}  # id de operador -> nodo del Job
        self._alias: dict[str, str] = {}  # id de operador plegado -> id que lo representa
        self._salida: dict[str, list[Columna]] = {}  # id de operador -> columnas que entrega
        self._tabla_de: dict[str, str] = {}  # UNIQUE_NAME del nodo -> tabla que entrega
        self._salidas_map: dict[str, str] = {}  # id de operador -> nombre de su salida
        self._entradas_map: dict[str, dict[str, str]] = {}  # id de operador -> origen -> fila
        self._productor = self._productores()
        self.rutas = rutas_de_plan(plan)

    # -- grafo -------------------------------------------------------------------------------
    def _productores(self) -> dict[str, str]:
        """Conjunto de datos -> operador que lo produce, dentro de este Job."""
        productores: dict[str, str] = {}
        for op in self.plan.graph.operators():
            for dataset in _produce(op):
                productores.setdefault(dataset, op.id)
        return productores

    def _resolver(self, op_id: str, visto: set[str] | None = None) -> str | None:
        """Operador que de verdad representa a este, siguiendo los plegados.

        Un `read` o un `write` que solo nombran un conjunto ya producido en el Job no son un paso:
        son el nombre que el SAS le da a ese flujo, y se pliegan sobre el operador que lo produce.
        """
        visto = set() if visto is None else visto
        if op_id in visto:
            return None
        visto.add(op_id)
        if op_id in self._nodo:
            return op_id
        if op_id in self._alias:
            return self._resolver(self._alias[op_id], visto)
        op = self.plan.graph.operator(op_id)
        if op.kind == "read":
            productor = self._productor.get(str(op.params.get("dataset", "")).lower())
            if productor and productor != op_id:
                self._alias[op_id] = productor
                return self._resolver(productor, visto)
        elif op.kind == "write":
            previos = self.plan.graph.predecessors(op_id)
            if previos:
                self._alias[op_id] = previos[0]
                return self._resolver(previos[0], visto)
        return None

    def _unico(self, componente: str) -> str:
        """UNIQUE_NAME con el ordinal del componente en el Job, como los escribe Studio."""
        self._usados[componente] = self._usados.get(componente, 0) + 1
        return f"{componente}_{self._usados[componente]}"

    # -- piezas ------------------------------------------------------------------------------
    def _sin_soporte(self, op: Operator) -> None:
        motivo = op.notes[0] if op.notes else f"el operador '{op.kind}' no tiene componente"
        self.pendientes.append(PendienteMigracion(SIN_SOPORTE, motivo, _linea(op)))

    def _lectura(self, op: Operator, x: int) -> None:
        tabla = str((op.params.get("outputs") or ["WORK.sin_nombre"])[0]).lower()
        esquema = self.esquemas.get(tabla, [])
        if not esquema:
            self.pendientes.append(
                PendienteMigracion(
                    "P-ESQUEMA-VACIO",
                    f"{tabla}: el SAS no demuestra ninguna columna para esta lectura",
                    _linea(op),
                )
            )
        unico = self._unico(str((op.component or {}).get("name") or "tFileInputDelimited"))
        resultado = nodo_lectura(op, esquema, unico, x, 0, self.ruta_java)
        self.pendientes += resultado.pendientes
        if resultado.nodo is None:
            return
        self._registrar(op, resultado.nodo, resultado.columnas, _tabla(tabla))

    def _escritura(self, op: Operator, x: int) -> None:
        consumido = str((op.params.get("inputs") or [""])[0]).lower()
        columnas: list[Columna] = []
        productor = self._productor.get(consumido)
        if productor:
            # El productor puede ser un nodo, un operador plegado o uno que falló: su esquema de
            # salida se conoce igual, y es lo que la escritura necesita.
            representante = self._resolver(productor)
            columnas = self._salida.get(representante or productor, [])
        if not columnas:
            self.pendientes.append(
                PendienteMigracion(
                    "P-ESCRITURA-SIN-COLUMNAS",
                    f"{consumido}: no hay columnas demostradas para escribir",
                    _linea(op),
                )
            )
            return
        unico = self._unico(str((op.component or {}).get("name") or "tFileOutputDelimited"))
        resultado = nodo_escritura(op, columnas, unico, x, 0, self.ruta_java)
        self.pendientes += resultado.pendientes
        if resultado.nodo is None:
            return
        self._registrar(op, resultado.nodo, columnas, _tabla(consumido))

    def _fuentes(self, op: Operator) -> list[Fuente]:
        fuentes: list[Fuente] = []
        vistos: set[str] = set()
        for previo in self.plan.graph.predecessors(op.id):
            representante = self._resolver(previo)
            if representante is None or representante in vistos:
                continue
            vistos.add(representante)
            fuentes.append(
                Fuente(
                    representante,
                    self._tabla_de.get(self._nodo[representante].unico, ""),
                    self._salida[representante],
                )
            )
        return fuentes

    def _mapa(self, op: Operator, x: int) -> None:
        fuentes = self._fuentes(op)
        unico = self._unico("tMap")
        armado = construir(_como_paso(op), fuentes, unico, x, 0, self.ruta_java)
        self.pendientes += armado.pendientes
        # El esquema de salida lo demuestra el SELECT, no el nodo: se guarda aunque el tMap falle,
        # para que la escritura de detrás sepa qué columnas tiene que escribir.
        self._salida[op.id] = list(armado.columnas)
        if armado.nodo is None:
            return
        tabla = _tabla(str((op.params.get("outputs") or ["WORK.sin_nombre"])[0]))
        self._registrar(op, armado.nodo, armado.columnas, tabla)
        self._entradas_map[op.id] = armado.entradas
        self._salidas_map[op.id] = (
            armado.nodo.metadatas[0].nombre if armado.nodo.metadatas else "out1"
        )

    def _registrar(self, op: Operator, nodo: Nodo, salida: list[Columna], tabla: str) -> None:
        self.nodos.append(nodo)
        self._nodo[op.id] = nodo
        self._salida[op.id] = list(salida)
        self._tabla_de[nodo.unico] = tabla
        evidencia = op.evidence[0] if op.evidence else None
        if evidencia is not None:
            self.traza[nodo.unico] = list(range(evidencia.line_start, evidencia.line_end + 1))

    # -- conexiones --------------------------------------------------------------------------
    def _conectar(self) -> None:
        vistas: set[tuple[str, str, str]] = set()
        for arista in self.plan.graph.edges():
            desde, hasta = self._resolver(arista.src), self._resolver(arista.dst)
            if desde is None or hasta is None or desde == hasta:
                continue
            nombre = self._nombre(desde, hasta)
            if nombre is None:
                continue
            origen, destino = self._nodo[desde].unico, self._nodo[hasta].unico
            clave = (origen, destino, nombre)
            if clave in vistas:
                continue
            vistas.add(clave)
            if hasta in self._entradas_map and nombre != "row1":
                # Las entradas de búsqueda de un tMap van por LOOKUP (`lineStyle` 8), no por FLOW.
                self.conexiones.append(lookup(origen, destino, nombre))
            else:
                self.conexiones.append(Conexion(origen, destino, nombre))

    def _nombre(self, desde: str, hasta: str) -> str | None:
        """Nombre de la conexión: la entrada que el `tMap` espera, o la salida que produce.

        `None` cuando el `tMap` de destino no tiene esa entrada: la arista existe en el plan pero no
        hay a qué fila del mapa corresponde, y una conexión con el nombre equivocado es peor que no
        tenerla.
        """
        if hasta in self._entradas_map:
            return self._entradas_map[hasta].get(desde)
        if desde in self._salidas_map:
            return self._salidas_map[desde]
        return "row1"

    # -- recorrido ---------------------------------------------------------------------------
    def armar(self, job) -> Job:
        orden = [
            op_id for subjob in job.subjobs for op_id in subjob
        ] or self.plan.graph.topological()
        for posicion, op_id in enumerate(orden):
            op = self.plan.graph.operator(op_id)
            x = PASO * posicion
            try:
                self._traducir(op, x)
            except Exception as error:  # noqa: BLE001 — un operador roto no tumba la migración
                self.pendientes.append(
                    PendienteMigracion(
                        FALLO,
                        f"{op.kind}: {type(error).__name__}: {error}",
                        _linea(op),
                    )
                )
        self._conectar()
        reemplazar_rutas(self.nodos, self.rutas)
        return Job(
            job.name,
            nodos=self.nodos,
            conexiones=self.conexiones,
            contextos=contextos_de_plan(self.plan),
        )

    def _traducir(self, op: Operator, x: int) -> None:
        if op.status == "hueco" or op.kind == "unsupported":
            self._sin_soporte(op)
            return
        if op.kind in ("read", "write"):
            # Si se pliega sobre otro nodo, el conjunto ya está en el flujo y no hay nada que hacer.
            if self._resolver(op.id) is None:
                self._sin_soporte(op)
            return
        componente = str((op.component or {}).get("name") or "none")
        if op.kind == "read_file":
            self._lectura(op, x)
        elif op.kind == "write_file":
            self._escritura(op, x)
        elif op.kind == "map":
            self._mapa(op, x)
        elif op.kind in CON_NODO:
            # `filter`, `derive` y `join` sueltos son un `tMap` de una sola entrada.
            self._mapa(op, x)
        elif componente == "none":
            self._sin_soporte(op)
        else:
            self.pendientes.append(
                PendienteMigracion(
                    SIN_SOPORTE,
                    f"el operador '{op.kind}' todavía no tiene emisor para {componente}",
                    _linea(op),
                )
            )


def plan_a_jobs(
    plan: Plan,
    esquemas: dict[str, list[Column]],
    ruta_java: str | None = None,
) -> ResultadoMigracion:
    """Un Job de Talend por cada Job del plan, con sus nodos, conexiones y pendientes."""
    resultado = ResultadoMigracion()
    for job in plan.jobs:
        armado = _Job(plan, esquemas, ruta_java)
        resultado.jobs.append(armado.armar(job))
        resultado.pendientes += armado.pendientes
        resultado.traza.update(armado.traza)
    return resultado


__all__ = ["ResultadoMigracion", "plan_a_jobs"]
