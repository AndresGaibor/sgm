"""Fuentes y salidas de un programa, deducidas del linaje (sin nombres del cliente).

- Una entrada de la base cuyo nombre (sin biblioteca) coincide con un dataset que el programa
  escribe como WORK es una persistencia intermedia propia, no una fuente: el diseño la elimina.
- Una entrada con macrovariable o `_all_` no se puede resolver sin ejecutar: queda pendiente.
- Una entrada WORK sin escritor previo se lee antes de crearse: queda pendiente con su motivo.
- Las salidas de archivo se agrupan por plantilla: el nombre con el sufijo de producto como `{P}`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import PurePosixPath, PureWindowsPath

from sgm.flow.model import FlowModel, dataset_key
from sgm.proceso.familias import MARCADOR_PRODUCTO, patron_sufijos

PREFIJO_ARCHIVO = "file:"
_EXCEL = {".xlsx", ".xls", ".xlsm"}
_TEXTO = {".csv", ".txt", ".dat"}


@dataclass(frozen=True)
class Fuente:
    tipo: str  # excel, csv, archivo, tabla_base
    ubicacion: str  # ruta del archivo o tabla con su biblioteca
    linea: int  # primera lectura en el programa


@dataclass(frozen=True)
class Pendiente:
    nombre: str
    motivo: str


@dataclass(frozen=True)
class Plantilla:
    """Salida de archivo con el producto como parámetro: una instancia por producto."""

    plantilla: str  # nombre con `{P}`
    instancias: tuple[tuple[str | None, str], ...]  # (producto o None, ruta)


@dataclass
class EntradasSalidas:
    fuentes: list[Fuente] = field(default_factory=list)
    persistidas: list[str] = field(default_factory=list)  # tablas de la base propias
    pendientes: list[Pendiente] = field(default_factory=list)
    salidas: list[Plantilla] = field(default_factory=list)


def nombre_archivo(ruta: str) -> str:
    """Último componente de la ruta, con barras de Windows o de Unix."""
    clase = PureWindowsPath if "\\" in ruta else PurePosixPath
    return clase(ruta).name


def _tipo_archivo(ruta: str) -> str:
    sufijo = PurePosixPath(nombre_archivo(ruta).lower()).suffix
    if sufijo in _EXCEL:
        return "excel"
    return "csv" if sufijo in _TEXTO else "archivo"


def _sin_resolver(nombre: str) -> bool:
    return "&" in nombre or nombre.lower().endswith("._all_")


def _base(nombre: str) -> str:
    return dataset_key(nombre).split(".")[-1]


def _primera_linea(modelo: FlowModel, nombre: str) -> int:
    return min((s.line for s in modelo.steps if nombre in s.reads), default=0)


def _escritos_en_work(modelo: FlowModel) -> set[str]:
    return {
        _base(w)
        for s in modelo.steps
        for w in s.writes
        if not w.startswith(PREFIJO_ARCHIVO) and w.lower().startswith("work.")
    }


def clasificar_entradas(modelo: FlowModel) -> EntradasSalidas:
    """Reparte las entradas externas en fuentes, persistencias propias y pendientes."""
    res = EntradasSalidas()
    en_work = _escritos_en_work(modelo)
    for nombre in modelo.external_inputs:
        if nombre.startswith(PREFIJO_ARCHIVO):
            ruta = nombre[len(PREFIJO_ARCHIVO) :]
            res.fuentes.append(Fuente(_tipo_archivo(ruta), ruta, _primera_linea(modelo, nombre)))
        elif _sin_resolver(nombre):
            res.pendientes.append(
                Pendiente(nombre, "el nombre depende de una macrovariable o de todos los datasets")
            )
        elif nombre.lower().startswith("work."):
            res.pendientes.append(Pendiente(nombre, "se lee antes de que el programa la cree"))
        elif _base(nombre) in en_work:
            res.persistidas.append(nombre)
        else:
            res.fuentes.append(Fuente("tabla_base", nombre, _primera_linea(modelo, nombre)))
    return res


def _plantilla_de(nombre: str, productos: dict[str, tuple[str, ...]]) -> tuple[str, str | None]:
    """Nombre con el sufijo de producto como `{P}` y el producto que se encontró."""
    for producto, sufijos in productos.items():
        patron = patron_sufijos(list(sufijos))
        if patron and patron.search(nombre):
            return patron.sub(MARCADOR_PRODUCTO, nombre), producto
    return nombre, None


def agrupar_salidas(modelo: FlowModel, productos: dict[str, tuple[str, ...]]) -> list[Plantilla]:
    """Salidas de archivo agrupadas por plantilla de nombre, en orden de aparición."""
    grupos: dict[str, list[tuple[str | None, str]]] = {}
    for paso in modelo.steps:
        for escrito in paso.writes:
            if not escrito.startswith(PREFIJO_ARCHIVO):
                continue
            ruta = escrito[len(PREFIJO_ARCHIVO) :]
            plantilla, producto = _plantilla_de(nombre_archivo(ruta), productos)
            instancia = (producto, ruta)
            lista = grupos.setdefault(plantilla, [])
            if instancia not in lista:
                lista.append(instancia)
    return [Plantilla(p, tuple(i)) for p, i in grupos.items()]


def entradas_y_salidas(modelo: FlowModel, productos: dict[str, tuple[str, ...]]) -> EntradasSalidas:
    res = clasificar_entradas(modelo)
    res.salidas = agrupar_salidas(modelo, productos)
    return res
