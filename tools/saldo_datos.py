"""Hito 90 / R1-07: saldos negativos del `job_producto` contra `v05_codex_saldos`.

El Job separa `INCONS_SALDO_NEG_<P>` (filas con `FIN_SALDO_CTA < 0` sobre la sábana entera) y
`SABANA_VALIDA_<P>` (cuenta válida y sin saldo negativo). Se comparan con `RECHAZO_SALDO_<P>` y
`SABANA_VALIDA_<P>` del corpus, y se comprueba la sábana contra los rechazos de codex del mismo
Job (`INCONS_CODEX_INVALIDO_<P>`, que sale de R1-06).

Columnas comparadas: `RELACION`, `TIPO_CTA`, `NRO_CTA`, `GMF` y `FIN_SALDO_CTA`, por nombre. La
normalización de R1-02 vacía `TIPO_DOC` y `LLAVE_NOMBRE` y quita ceros de `NRO_DOC` (salvedad
del hito 85), así que esas columnas no entran. `NRO_CTA` es única, así que el multiconjunto es
fila por fila. El esperado no se rellena ni se transforma.

Además hay **vectores propios** con la clasificación escrita a mano desde la semántica de SAS:
saldo `-1`, `0`, `0.01`, `-0.01`, `-0.00`, faltante, `-12345678901234`, `1.5`, y las filas que
cruzan la cuenta (codex por GMF 11 y 99, tipo 9 con y sin `RELACION = 1000`, GMF en el borde 10).
Cada fila lleva a mano si entra en `INCONS_SALDO_NEG` y si entra en `SABANA_VALIDA`.

Uso desde `tools/prueba_saldo.py`; no se importa desde `src/`.
"""

from __future__ import annotations

import csv
from decimal import Decimal
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[1]
CASO = REPO / "tests" / "corpus" / "L8" / "validaciones" / "v05_codex_saldos"
PRODUCTOS = ("CTE", "AHO")
SUFIJO_VECTORES = "VECTORES"
ESTABLES = ("RELACION", "TIPO_CTA", "NRO_CTA", "GMF", "FIN_SALDO_CTA")
ESTABLES_NEG = (*ESTABLES, "INCONSISTENCIA")

# Lo que escribe el Job emitido, con el sufijo al final.
ARCHIVOS = {
    "neg": "INCONS_SALDO_NEG_{p}.csv",
    "valida": "SABANA_VALIDA_{p}.csv",
    "codex": "INCONS_CODEX_INVALIDO_{p}.csv",
    "tipo": "INCONS_TIPO_CTA_INVALIDO_{p}.csv",
}
# Lo que el corpus declara, con el producto en el nombre.
ESPERADO = {
    "neg": "RECHAZO_SALDO_{p}.csv",
    "valida": "SABANA_VALIDA_{p}.csv",
    "suma": "SUMA_SALDO_VALIDA_{p}.csv",
    "sabana": "SABANA_{p}.csv",
}

# 23 campos del CSV de origen, en el orden de `esquema_csv`. Se sobreescriben RELACION (4),
# TIPO_CTA (6), NRO_CTA (7), GMF (11) y FIN_SALDO_CTA (23).
_BASE = (
    "2026", "10", "FIC", "1000", "S", "1", "5000000001", "LLV00001", "TD01", "00000001",
    "11", "1001", "2001", "3001", "4001", "5001", "6001", "7001", "8001", "9001",
    "10001", "11001", "12001",
)  # fmt: skip

# (relacion, tipo_cta, gmf, nro_cta, saldo, en_neg, en_valida). `en_neg` y `en_valida` son la
# clasificación escrita a mano; `saldo` es el texto que llega al CSV de origen.
VECTORES = (
    ("1000", "1", "1", "9000000101", "-1", True, False),
    ("1000", "1", "1", "9000000102", "0", False, True),
    ("1000", "1", "1", "9000000103", "0.01", False, True),
    ("1000", "1", "1", "9000000104", "", True, False),
    ("1000", "1", "1", "9000000105", "-0.00", False, True),
    ("1000", "1", "1", "9000000106", "-0.01", True, False),
    ("1000", "1", "99", "9000000107", "12107", False, False),
    ("1000", "1", "99", "9000000108", "-5", True, False),
    ("1001", "1", "99", "9000000109", "-3", True, False),
    ("1001", "9", "1", "9000000110", "12110", False, True),
    ("1000", "9", "1", "9000000111", "-7", True, False),
    ("1000", "2", "10", "9000000112", "12112", False, True),
    ("1000", "3", "11", "9000000113", "0", False, False),
    ("1000", "5", "5", "9000000114", "-12345678901234", True, False),
    ("1000", "1", "1", "9000000115", "1.5", False, True),
)


def _csv(ruta: Path) -> list[list[str]]:
    with ruta.open(encoding="utf-8", newline="") as archivo:
        return list(csv.reader(archivo, delimiter=","))


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
    """Los CSV que escribe el Job para un sufijo, proyectados por nombre de columna."""
    return {
        "neg": _proyectar(salida / ARCHIVOS["neg"].format(p=sufijo), ESTABLES_NEG),
        "valida": _proyectar(salida / ARCHIVOS["valida"].format(p=sufijo), ESTABLES),
        "codex": _proyectar(salida / ARCHIVOS["codex"].format(p=sufijo), ("NRO_CTA",)),
        "tipo": _proyectar(salida / ARCHIVOS["tipo"].format(p=sufijo), ("NRO_CTA",)),
    }


def anomalias_plantadas() -> dict[str, dict]:
    with (CASO / "caso.yaml").open(encoding="utf-8") as archivo:
        return yaml.safe_load(archivo)["anomalias_plantadas"]


def _saldo(texto: str) -> Decimal | None:
    """`FIN_SALDO_CTA` como número; vacío es faltante y `-0.00` es cero."""
    return None if texto == "" else Decimal(texto)


def _multiconjunto(filas: list[tuple[str, ...]]) -> list[tuple[str, ...]]:
    return sorted(filas)


def _suma(filas: list[tuple[str, ...]]) -> Decimal:
    total = Decimal(0)
    for fila in filas:
        valor = _saldo(fila[ESTABLES.index("FIN_SALDO_CTA")])
        if valor is not None:
            total += valor
    return total


def informe(producto: str, obs: dict[str, list[tuple[str, ...]]]) -> bool:
    """Compara rechazo de saldo, sábana válida, suma y el desglose plantado del corpus."""
    plantado = anomalias_plantadas()[producto.casefold()]
    bueno = True
    comparaciones = {
        "neg": (esperado(producto, "neg", ESTABLES_NEG), obs["neg"]),
        "valida": (esperado(producto, "valida"), obs["valida"]),
    }
    for clave, (esp, obtenido) in comparaciones.items():
        cuadra = _multiconjunto(esp) == _multiconjunto(obtenido)
        bueno &= cuadra
        print(
            f"{producto} {clave}: esperadas {len(esp)} filas, obtenidas {len(obtenido)}; "
            f"{'OK' if cuadra else 'DIFERENCIA'}"
        )
        if not cuadra:
            print(f"  esperado: {_multiconjunto(esp)[:3]}")
            print(f"  obtenido: {_multiconjunto(obtenido)[:3]}")
    suma_esperada = Decimal(esperado(producto, "suma", ("SUMA_SALDO_FINAL_" + producto,))[0][0])
    suma_obtenida = _suma(obs["valida"])
    cuadra = suma_esperada == suma_obtenida
    bueno &= cuadra
    print(
        f"{producto} suma valida: esperada {suma_esperada}, obtenida {suma_obtenida}; "
        f"{'OK' if cuadra else 'DIFERENCIA'}"
    )
    desglose = {"saldo_negativo": len(obs["neg"]), "validos": len(obs["valida"])}
    plantado_cmp = {"saldo_negativo": plantado["saldo_negativo"], "validos": plantado["validos"]}
    cuadra = desglose == plantado_cmp
    bueno &= cuadra
    print(
        f"{producto} anomalías plantadas {plantado_cmp}; obtenidas {desglose}; "
        f"{'OK' if cuadra else 'DIFERENCIA'}"
    )
    return bool(bueno)


def _cubre(o: dict[str, list[tuple[str, ...]]], sabana: set[str]) -> tuple[int, int, bool]:
    """Filas válidas y rechazadas (codex, tipo o saldo) por NRO_CTA, y si cuadran con la sábana.

    Las llaves de rechazo pueden repetirse entre tablas (un codex inválido con saldo negativo sale
    en las dos). Por eso se cuentan NRO_CTA distintas, no filas sumadas.
    """
    # `valida` y `neg` proyectan ESTABLES (NRO_CTA en la posición 2); codex y tipo solo NRO_CTA.
    validos = {f[ESTABLES.index("NRO_CTA")] for f in o["valida"]}
    rechazos = (
        {f[ESTABLES.index("NRO_CTA")] for f in o["neg"]}
        | {f[0] for f in o["codex"]}
        | {f[0] for f in o["tipo"]}
    )
    cuadra = validos.isdisjoint(rechazos) and validos | rechazos == sabana
    return len(validos), len(rechazos), cuadra


def invariantes(resultados: dict[str, dict[str, list[tuple[str, ...]]]]) -> bool:
    """La sábana del corpus es válidos más rechazos, sin solapamiento entre válidos y rechazos."""
    uno = True
    for p in PRODUCTOS:
        sabana = {f[0] for f in esperado(p, "sabana", ("NRO_CTA",))}
        validos, rechazos, cuadra = _cubre(resultados[p], sabana)
        uno &= cuadra
        print(
            f"{p} invariante sábana: válidos {validos} + rechazos {rechazos} = "
            f"{validos + rechazos} frente a {len(sabana)}; {'OK' if cuadra else 'DIFERENCIA'}"
        )
    return uno


def vector_csv(destino: Path) -> Path:
    """Escribe el CSV sin cabecera de los vectores propios, con las 23 columnas del SAS."""
    destino.parent.mkdir(parents=True, exist_ok=True)
    with destino.open("w", encoding="utf-8", newline="") as archivo:
        escritor = csv.writer(archivo, delimiter=";", lineterminator="\n")
        for relacion, tipo, gmf, nro, saldo, _, _ in VECTORES:
            fila = list(_BASE)
            fila[3], fila[5], fila[6], fila[10], fila[22] = relacion, tipo, nro, gmf, saldo
            escritor.writerow(fila)
    return destino


def informe_vectores(salida: Path) -> bool:
    """Compara los dos flujos de saldo de los vectores con la clasificación escrita a mano."""
    neg_esp = sorted(
        (nro, _saldo(saldo)) for _, _, _, nro, saldo, en_neg, _ in VECTORES if en_neg
    )
    valida_esp = sorted(
        (nro, _saldo(saldo)) for _, _, _, nro, saldo, _, en_valida in VECTORES if en_valida
    )
    neg_obs = _proyectar(salida / ARCHIVOS["neg"].format(p=SUFIJO_VECTORES), ESTABLES_NEG)
    valida_obs = _proyectar(salida / ARCHIVOS["valida"].format(p=SUFIJO_VECTORES), ESTABLES)
    neg_obt = sorted((f[2], _saldo(f[4])) for f in neg_obs)
    valida_obt = sorted((f[2], _saldo(f[4])) for f in valida_obs)
    bueno = True
    for nombre, esp, obt in (("neg", neg_esp, neg_obt), ("valida", valida_esp, valida_obt)):
        cuadra = esp == obt
        bueno &= cuadra
        print(
            f"Vectores {nombre}: esperadas {len(esp)} filas, obtenidas {len(obt)}; "
            f"{'OK' if cuadra else 'DIFERENCIA'}"
        )
        if not cuadra:
            print(f"  esperado: {esp}")
            print(f"  obtenido: {obt}")
    sabana = {nro for _, _, _, nro, _, _, _ in VECTORES}
    observado_vectores = {
        "neg": neg_obs,
        "valida": valida_obs,
        "codex": _proyectar(salida / ARCHIVOS["codex"].format(p=SUFIJO_VECTORES), ("NRO_CTA",)),
        "tipo": _proyectar(salida / ARCHIVOS["tipo"].format(p=SUFIJO_VECTORES), ("NRO_CTA",)),
    }
    validos, rechazos, cuadra = _cubre(observado_vectores, sabana)
    bueno &= cuadra
    print(
        f"Vectores invariante: válidos {validos} + rechazos {rechazos} = {validos + rechazos} "
        f"frente a {len(sabana)}; {'OK' if cuadra else 'DIFERENCIA'}"
    )
    return bueno


__all__ = [
    "ARCHIVOS",
    "CASO",
    "ESTABLES",
    "ESTABLES_NEG",
    "PRODUCTOS",
    "SUFIJO_VECTORES",
    "VECTORES",
    "esperado",
    "informe",
    "informe_vectores",
    "invariantes",
    "observado",
    "vector_csv",
]
