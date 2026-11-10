"""Arquitectura de Jobs declarada por el equipo: nombres de los Jobs, entornos y proyecto.

Vive en `decisiones/<programa>.jobs.yaml`. El SAS no dice cuántos Jobs hay ni cómo se llaman: es una
decisión de diseño, igual que las etapas. Los productos no se declaran aquí: salen de la agrupación.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from sgm.java_identificadores import require_context_identifier

JOBS_REQUERIDOS = ("padre", "producto", "totales", "conciliacion")


@dataclass(frozen=True)
class PeriodoDecl:
    """El Excel de la fecha del proceso: el padre lo lee una vez y deja su valor en el contexto."""

    fuente: str  # clave de la tabla 1.1 del diseño
    variables: tuple[tuple[str, str], ...]  # (columna del Excel, variable de contexto)


@dataclass(frozen=True)
class ValidacionProducto:
    """Validación de fila por lookup declarada por el equipo (sección 3.3 del diseño).

    `fuente` es la clave de la tabla 1.1 cuyo Excel sirve de homologación; un producto puede usar
    otro archivo (Nequi tiene su propia homologación), y eso va en `excepciones`.
    """

    nombre: str  # tipo_documento
    columna: str  # TIPO_DOC: columna de la sábana que se valida
    columna_lookup: str  # CNAME: columna del Excel contra la que se une
    motivo: str  # TIPO_DOC_INVALIDO: valor de la columna `motivo` del rechazo
    fuente: str  # clave de la tabla 1.1 para los productos sin excepción
    excepciones: tuple[tuple[str, str], ...] = ()  # producto -> otra clave

    def fuente_de(self, producto: str) -> str:
        """Clave de la fuente para un producto: su excepción si la tiene, la común si no."""
        return dict(self.excepciones).get(producto.upper(), self.fuente)


@dataclass(frozen=True)
class Arquitectura:
    proyecto: str
    entornos: tuple[str, ...]
    padre: str
    producto: str
    totales: str
    conciliacion: str
    mensaje_fin: str
    periodo: PeriodoDecl | None = None
    lookups: tuple[str, ...] = ()  # fuentes Excel que job_producto usa como lookup
    columna_saldo: str = ""  # columna cuya suma son los totales de origen (el SAS la suma)
    validaciones: tuple[ValidacionProducto, ...] = ()
    # Nombre del archivo final de totales, sin fecha ni extensión (la decisión del programa).
    archivo_totales: str = ""


def _validaciones(path: Path, items: list | None) -> tuple[ValidacionProducto, ...]:
    """Lee `validaciones_producto`. Una declaración incompleta falla con el nombre que falta."""
    resultado: list[ValidacionProducto] = []
    for item in items or []:
        faltan = [
            clave
            for clave in ("nombre", "columna", "columna_lookup", "motivo", "fuente")
            if not str(item.get(clave) or "").strip()
        ]
        if faltan:
            raise ValueError(f"{path}: validaciones_producto necesita {faltan} en {item}")
        excepciones = tuple(
            (str(producto).upper(), str(fuente).strip())
            for producto, fuente in (item.get("excepciones") or {}).items()
        )
        resultado.append(
            ValidacionProducto(
                str(item["nombre"]).strip(),
                str(item["columna"]).strip(),
                str(item["columna_lookup"]).strip(),
                str(item["motivo"]).strip(),
                str(item["fuente"]).strip(),
                excepciones,
            )
        )
    return tuple(resultado)


def _periodo(path: Path, item: dict | None) -> PeriodoDecl | None:
    if not item:
        return None
    fuente = str(item.get("fuente") or "").strip()
    variables = tuple((str(c), str(v)) for c, v in (item.get("variables") or {}).items())
    if not fuente or not variables:
        raise ValueError(f"{path}: `periodo` necesita fuente y variables")
    for _, variable in variables:
        require_context_identifier(variable)
    return PeriodoDecl(fuente, variables)


def cargar_arquitectura(path: Path) -> Arquitectura:
    """Lee la arquitectura. Un archivo mal formado falla con su nombre y el motivo."""
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    proyecto = str(data.get("proyecto") or "").strip()
    if not proyecto:
        raise ValueError(f"{path}: falta proyecto")
    jobs = data.get("jobs") or {}
    faltan = [k for k in JOBS_REQUERIDOS if not str(jobs.get(k) or "").strip()]
    if faltan:
        raise ValueError(f"{path}: faltan los Jobs {faltan}")
    entornos = tuple(str(e).strip() for e in (data.get("entornos") or []) if str(e).strip())
    if not entornos:
        raise ValueError(f"{path}: falta entornos")
    return Arquitectura(
        proyecto,
        entornos,
        *(str(jobs[k]).strip() for k in JOBS_REQUERIDOS),
        mensaje_fin=str(data.get("mensaje_fin") or "").strip(),
        periodo=_periodo(path, data.get("periodo")),
        lookups=tuple(str(x).strip() for x in (data.get("lookups_producto") or [])),
        columna_saldo=str((data.get("total_origen") or {}).get("columna_saldo") or "").strip(),
        validaciones=_validaciones(path, data.get("validaciones_producto")),
        archivo_totales=str(data.get("archivo_totales") or "").strip(),
    )
