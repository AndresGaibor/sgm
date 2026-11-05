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
MOTIVO_CSV_DEPOSITOS = (
    "el origen es un CSV bajado con PROC DOWNLOAD (DBIFTCD.csv, DBIFTCS.csv, F_1019.csv; "
    "hito 64), no una tabla de Impala"
)
MOTIVO_SIN_LOOKUP_UBICACION = (
    "no hay caché ni lookup: la validación de ubicación no está en el job_producto de este "
    "programa (R1-05)"
)
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
    # Sección 1.1: el manual da los depósitos como tablas Impala; el SAS los lee como CSV.
    "F06": MOTIVO_CSV_DEPOSITOS,
    "F07": MOTIVO_CSV_DEPOSITOS,
    "F08": MOTIVO_CSV_DEPOSITOS,
    # Sección 1.2: el SAS no tiene cachés; el emisor usa lookups de Excel y archivos de totales.
    "C01": "no hay caché: job_producto lee el Excel de tipo de documento (hitos 70 y 85)",
    "C02": "no hay caché ni lookup de NEQUI en job_producto: pendiente (R1-16)",
    "C03": MOTIVO_SIN_LOOKUP_UBICACION,
    "C04": MOTIVO_SIN_LOOKUP_UBICACION,
    **{
        f"C{n:02d}": (
            "no hay caché: los totales viajan en archivos por producto en la carpeta de trabajo "
            "(hito 97d, mecanismo b); job_producto aún no los escribe"
        )
        for n in range(5, 11)
    },
    # Sección 1.3: el periodo lo lee el padre y lo hereda por contexto (hito 63).
    **{
        f"G{n:02d}": (
            "el padre lee la fecha y la pasa por contexto (hito 63); no la lee job_insumos, "
            "que se eliminó"
        )
        for n in range(1, 4)
    },
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
    difs = diferencias_fila(fila, obtenida)
    if difs and fila.id in conocidas:
        return "diferente", conocidas[fila.id]
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
