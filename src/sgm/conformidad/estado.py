"""Estado de cada fila de la referencia frente al diseño que emite el migrador.

- derivada: el migrador la produce y el SAS demuestra su valor (origen `sas`).
- declarada: el migrador la produce, pero el valor sale de `decisiones/`, no del SAS.
- pendiente: el migrador aún no la emite, o la fila requiere una decisión humana.
- diferente: el migrador la produce con otro valor; el motivo dice la diferencia.
"""

from __future__ import annotations

from dataclasses import dataclass

from sgm.conformidad.referencia import Fila, Seccion, todas_las_filas
from sgm.proceso.secciones_entrada import ORIGEN_SAS

ESTADOS = ("derivada", "declarada", "pendiente", "diferente")
DIFERENCIAS_CONOCIDAS = {
    "F04": (
        "el SAS sí lee CODIGOS_DANE.xlsx; el manual lo daba por pendiente "
        "(el migrador halla más)"
    ),
    "X01": (
        "el SAS da la misma carpeta de insumos; el manual pide confirmarla por entorno (DC-07) "
        "y el migrador no lo dice"
    ),
    "X06": (
        "el SAS sí nombra CODIGOS_DANE.xlsx, como en F04; el manual lo daba por pendiente"
    ),
}
MOTIVO_DECLARADA = "el SAS no demuestra el valor; sale de decisiones/"


@dataclass(frozen=True)
class EstadoFila:
    id: str
    seccion: str
    clave: str
    estado: str
    motivo: str


def _norm(valor: str) -> str:
    return " ".join(str(valor).split())


def diferencias_fila(esperada: Fila, obtenida: dict[str, str] | None) -> list[str]:
    """Lista de diferencias entre la fila esperada y la obtenida (vacía si coinciden)."""
    if obtenida is None:
        return [f"falta la fila {esperada.clave!r}"]
    difs = []
    for columna, valor in esperada.campos.items():
        if _norm(obtenida.get(columna, "")) != _norm(valor):
            difs.append(f"{columna}: esperado {valor!r}, obtenido {obtenida.get(columna)!r}")
    return difs


def _estado(
    fila: Fila,
    diseno: dict[str, dict[str, dict[str, str]]],
    origenes: dict[str, dict[str, str]],
    emitidas: tuple[str, ...],
    conocidas: dict[str, str],
) -> tuple[str, str]:
    obtenida = diseno.get(fila.seccion, {}).get(fila.clave)
    if fila.seccion not in emitidas or obtenida is None:
        return "pendiente", f"el migrador aún no emite esta fila: {fila.motivo}"
    if fila.id in conocidas:
        return "diferente", conocidas[fila.id]
    difs = diferencias_fila(fila, obtenida)
    if difs:
        return "diferente", "; ".join(difs)
    if fila.clasificacion == "humana":
        return "pendiente", f"requiere decisión humana: {fila.motivo}"
    origen = origenes.get(fila.seccion, {}).get(fila.clave)
    if fila.clasificacion == "derivable" and origen == ORIGEN_SAS:
        return "derivada", ""
    return "declarada", MOTIVO_DECLARADA


def clasificar_filas(
    secciones: dict[str, Seccion],
    diseno: dict[str, dict[str, dict[str, str]]],
    origenes: dict[str, dict[str, str]],
    emitidas: tuple[str, ...],
    conocidas: dict[str, str] = DIFERENCIAS_CONOCIDAS,
) -> list[EstadoFila]:
    """Estado de cada fila, en el orden de la referencia (estable entre corridas)."""
    filas = []
    for fila in todas_las_filas(secciones):
        estado, motivo = _estado(fila, diseno, origenes, emitidas, conocidas)
        filas.append(EstadoFila(fila.id, fila.seccion, fila.clave, estado, motivo))
    return filas
