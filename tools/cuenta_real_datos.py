"""Comparación de datos del hito 89: el `job_producto` emitido contra `v05_codex_saldos`.

`v05` es el único caso del corpus que escribe la forma del SAS real (`GMF NOT BETWEEN 1 AND 10
AND RELACION = 1000` con motivo `CODEX INVALIDO`). El Job emitido separa **solo R1-06**: R1-07
(saldos negativos) no está implementado, así que `SABANA_CODEX_VALIDO_*` **no** se compara con
`SABANA_VALIDA_*`; al contrario, se comprueba que las filas de saldo negativo siguen ahí.

Columnas comparadas: `RELACION`, `TIPO_CTA`, `NRO_CTA`, `GMF` y `FIN_SALDO_CTA`. Las demás no se
comparan porque R1-02 normaliza 15 columnas del SAS real: `TIPO_DOC=TDxx` y `LLAVE_NOMBRE=LLVxxxxx`
quedan vacías y `NRO_DOC=00000001` pierde los ceros a la izquierda (salvedad medida en el hito 85
y usada igual en el hito 87). `NRO_CTA` es única por fila, así que la igualdad de multisets es
fila por fila. No se rellena ni se transforma el esperado.

Además hay **vectores propios** (no corpus, con el esperado escrito a mano desde la semántica del
SAS) para lo que `v05` no planta: `TIPO_CTA NOT BETWEEN 1 AND 5`, la exención de `RELACION <> 1000`,
el faltante de GMF y la prioridad del motivo cuando una fila viola las dos reglas.
"""

from __future__ import annotations

import csv
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[1]
CASO = REPO / "tests" / "corpus" / "L8" / "validaciones" / "v05_codex_saldos"
PRODUCTOS = ("CTE", "AHO")
SUFIJO_VECTORES = "VECTORES"
MODOS = ("tipo_cta", "codex", "valido", "cuenta")

# Nombres que escribe el Job emitido, leídos de las tablas del SAS real.
ARCHIVOS = {
    "tipo_cta": "INCONS_TIPO_CTA_INVALIDO_{p}.csv",
    "codex": "INCONS_CODEX_INVALIDO_{p}.csv",
    "valido": "SABANA_CODEX_VALIDO_{p}.csv",
    "cuenta": "INCONS_CUENTA_{p}.csv",
}
ESPERADO = {
    "codex": "INCONS_CODEX_INVALIDO_{p}.csv",
    "cuenta": "RECHAZO_CODEX_{p}.csv",
    "saldo": "RECHAZO_SALDO_{p}.csv",
    "sabana": "SABANA_{p}.csv",
}
ESTABLES = ("RELACION", "TIPO_CTA", "NRO_CTA", "GMF", "FIN_SALDO_CTA")
ESTABLES_CUENTA = (*ESTABLES, "INCONSISTENCIA")

# 23 campos del CSV de origen del SAS real, en el orden de `esquema_csv`. Se sobreescriben solo
# RELACION (4), TIPO_CTA (6), NRO_CTA (7), GMF (11) y FIN_SALDO_CTA (23).
_BASE = (
    "2026", "10", "FIC", "1000", "S", "1", "5000000001", "LLV00001", "TD01", "00000001",
    "11", "1001", "2001", "3001", "4001", "5001", "6001", "7001", "8001", "9001",
    "10001", "11001", "12001",
)  # fmt: skip
# (relacion, tipo_cta, gmf, nro_cta, fin_saldo, flujo_esperado, inconsistencia_esperada)
VECTORES = (
    ("1000", "9", "11", "9000000001", "12001", "tipo_cta", "TIPO CTA INVALIDO"),
    ("1000", "2", "99", "9000000002", "12002", "codex", "CODEX INVALIDO"),
    ("1000", "3", "", "9000000003", "12003", "codex", "CODEX INVALIDO"),
    ("1001", "9", "99", "9000000004", "12004", "valido", ""),
    ("9902", "1", "1", "9000000005", "12005", "valido", ""),
    ("1000", "5", "10", "9000000006", "12006", "valido", ""),
    ("1000", "1", "1", "9000000007", "12007", "valido", ""),
    ("1000", "XX", "0", "9000000008", "12008", "tipo_cta", "TIPO CTA INVALIDO"),
)


def _csv(ruta: Path) -> list[list[str]]:
    with ruta.open(encoding="utf-8", newline="") as archivo:
        return [fila for fila in csv.reader(archivo, delimiter=",")]


def _proyectar(ruta: Path, columnas: tuple[str, ...]) -> list[tuple[str, ...]]:
    """Filas de un CSV con cabecera, reducidas a `columnas` por **nombre**."""
    filas = _csv(ruta)
    if not filas:
        raise ValueError(f"CSV vacío: {ruta}")
    cabecera = filas[0]
    faltan = [c for c in columnas if c not in cabecera]
    if faltan:
        raise ValueError(f"{ruta.name} no trae las columnas {faltan}: {cabecera}")
    indices = [cabecera.index(c) for c in columnas]
    return [tuple(fila[i] for i in indices) for fila in filas[1:] if fila]


def esperado(producto: str, clave: str, columnas: tuple[str, ...] = ESTABLES):
    return _proyectar(CASO / "esperado" / ESPERADO[clave].format(p=producto), columnas)


def observado(salida: Path, sufijo: str) -> dict[str, list[tuple[str, ...]]]:
    """Los cuatro CSV que escribió el Job, proyectados por nombre de columna."""
    return {
        modo: _proyectar(
            salida / ARCHIVOS[modo].format(p=sufijo),
            ESTABLES_CUENTA if modo == "cuenta" else ESTABLES,
        )
        for modo in MODOS
    }


def anomalias_plantadas() -> dict[str, dict]:
    with (CASO / "caso.yaml").open(encoding="utf-8") as archivo:
        return yaml.safe_load(archivo)["anomalias_plantadas"]


def informe(producto: str, obs: dict[str, list[tuple[str, ...]]]) -> bool:
    """Compara los dos rechazos, el vacío de tipo de cuenta y el desglose plantado."""
    plantado = anomalias_plantadas()[producto.casefold()]
    bueno = True
    comparaciones = {
        "codex": (sorted(esperado(producto, "codex")), sorted(obs["codex"])),
        "cuenta": (
            sorted(esperado(producto, "cuenta", ESTABLES_CUENTA)),
            sorted(obs["cuenta"]),
        ),
    }
    for modo, (esp, obtenido) in comparaciones.items():
        cuadra = esp == obtenido
        bueno &= cuadra
        print(
            f"{producto} {modo}: esperadas {len(esp)} filas, obtenidas {len(obtenido)}; "
            f"{'OK' if cuadra else 'DIFERENCIA'}"
        )
        if not cuadra:
            print(f"  esperado: {esp[:3]}")
            print(f"  obtenido: {obtenido[:3]}")
    vacias = not obs["tipo_cta"]
    bueno &= vacias
    print(f"{producto} tipo_cta: {len(obs['tipo_cta'])} filas (v05 no planta este rechazo); "
          f"{'OK' if vacias else 'DIFERENCIA'}")
    sabana = len(esperado(producto, "sabana", ("RELACION",)))
    complemento = len(obs["valido"]) + len(obs["codex"]) + len(obs["tipo_cta"])
    cuadra = sabana == complemento
    bueno &= cuadra
    print(f"{producto} válidos: {len(obs['valido'])} + rechazos "
          f"{len(obs['codex']) + len(obs['tipo_cta'])} = {complemento} frente a sábana {sabana}; "
          f"{'OK' if cuadra else 'DIFERENCIA'}")
    desglose = {"codex_invalido": len(obs["codex"])}
    cuadra = desglose["codex_invalido"] == plantado["codex_invalido"]
    bueno &= cuadra
    print(f"{producto} anomalías plantadas {{'codex_invalido': {plantado['codex_invalido']}}}; "
          f"obtenidas {desglose}; {'OK' if cuadra else 'DIFERENCIA'}")
    return bool(bueno)


def invariantes(resultados: dict[str, dict[str, list[tuple[str, ...]]]]) -> bool:
    """Tres invariantes: cobertura, conteo del corpus y la salvedad de R1-07."""
    uno = all(
        len(esperado(p, "sabana", ("RELACION",)))
        == len(resultados[p]["valido"])
        + len(resultados[p]["codex"])
        + len(resultados[p]["tipo_cta"])
        for p in PRODUCTOS
    )
    conteos = _csv(CASO / "esperado" / "CONTEO_CODEX_SALDO.csv")
    codex_esperado = sum(
        int(fila[1]) for fila in conteos[1:] if fila and fila[0].endswith("CODEX")
    )
    codex_obtenido = sum(len(resultados[p]["codex"]) for p in PRODUCTOS)
    dos = codex_esperado == codex_obtenido
    tres = True
    for p in PRODUCTOS:
        llaves_validas = {fila[2] for fila in resultados[p]["valido"]}
        llaves_saldo = {fila[0] for fila in _proyectar(
            CASO / "esperado" / ESPERADO["saldo"].format(p=p), ("NRO_CTA",)
        )}
        tres &= llaves_saldo <= llaves_validas
    print(
        f"Invariantes: sábana=válidos+rechazos {'sí' if uno else 'NO'}; "
        f"codex del corpus={codex_esperado} frente a {codex_obtenido} {'sí' if dos else 'NO'}; "
        f"saldo negativo sigue en válidos (R1-07 fuera) {'sí' if tres else 'NO'}"
    )
    return uno and dos and tres


def vector_csv(destino: Path) -> Path:
    """Escribe el CSV sin cabecera de los vectores propios, con las 23 columnas del SAS."""
    destino.parent.mkdir(parents=True, exist_ok=True)
    with destino.open("w", encoding="utf-8", newline="") as archivo:
        escritor = csv.writer(archivo, delimiter=";", lineterminator="\n")
        for relacion, tipo_cta, gmf, nro_cta, saldo, _, _ in VECTORES:
            fila = list(_BASE)
            fila[3], fila[5], fila[6], fila[10], fila[22] = relacion, tipo_cta, nro_cta, gmf, saldo
            escritor.writerow(fila)
    return destino


def esperado_vectores() -> dict[str, list[tuple[str, ...]]]:
    """Clasificación escrita a mano desde el SAS, no calculada por el traductor de Java."""
    resultado: dict[str, list[tuple[str, ...]]] = {m: [] for m in MODOS}
    for _, _, _, nro_cta, _, modo, motivo in VECTORES:
        resultado[modo].append((nro_cta,))
        if modo != "valido":
            resultado["cuenta"].append((nro_cta, motivo))
    return {m: sorted(filas) for m, filas in resultado.items()}


def informe_vectores(salida: Path) -> bool:
    """Compara los cuatro flujos de los vectores propios contra la clasificación escrita."""
    esp = esperado_vectores()
    bueno = True
    for modo in MODOS:
        columnas = ("NRO_CTA", "INCONSISTENCIA") if modo == "cuenta" else ("NRO_CTA",)
        obtenido = sorted(_proyectar(salida / ARCHIVOS[modo].format(p=SUFIJO_VECTORES), columnas))
        cuadra = esp[modo] == obtenido
        bueno &= cuadra
        print(
            f"Vectores {modo}: esperadas {len(esp[modo])} filas, obtenidas {len(obtenido)}; "
            f"{'OK' if cuadra else 'DIFERENCIA'}"
        )
        if not cuadra:
            print(f"  esperado: {esp[modo]}")
            print(f"  obtenido: {obtenido}")
    return bueno


__all__ = [
    "ARCHIVOS",
    "CASO",
    "ESTABLES",
    "ESTABLES_CUENTA",
    "MODOS",
    "PRODUCTOS",
    "SUFIJO_VECTORES",
    "VECTORES",
    "anomalias_plantadas",
    "esperado",
    "esperado_vectores",
    "informe",
    "informe_vectores",
    "invariantes",
    "observado",
    "vector_csv",
]
