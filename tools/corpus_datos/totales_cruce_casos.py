"""Preparación del cruce por caso: tablas de entrada y resultado del cruce con el oráculo SQL.

Cada `prep_NN` reproduce en Python lo que el programa hace fuera de PROC SQL (PROC IMPORT, DATA
step, PROC SORT) y devuelve esas tablas; el oráculo ejecuta el resto del programa sobre ellas.
Esa parte en Python no es independiente del esperado: se usa la misma regla, y el cruce lo
declara. Lo que sí se verifica es el SQL: CREATE TABLE, INTO, CASE, COUNT, SUM y los joins.

Uso: uv run python tools/corpus_datos/totales_cruce_casos.py  (imprime el informe).
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))

from totales_base import COLUMNAS, DESTINO  # noqa: E402
from totales_cruce import Corrida, Resultado  # noqa: E402
from totales_cruce_io import comparar, leer_dlm, leer_esperado, leer_xlsx  # noqa: E402
from totales_esperado import COLUMNAS_FORM, LLAVE, SALIDA_SABANA_19, marcar  # noqa: E402
from totales_esperado_b import COLUMNAS_MARCA_08, marcar_08  # noqa: E402
from totales_sas import con_form, primera_por_llave, sin_duplicados_exactos  # noqa: E402

Entrada = tuple[list[str], list, dict[str, str]]


def _raw(carpeta: Path, nombre: str) -> tuple[list[str], list]:
    return leer_dlm(carpeta / "entradas" / f"{nombre}.csv", cabecera=False)


def _origen(raw: list) -> list[dict]:
    """Lo que hace el DATA step con el rename: VAR1..VAR23 pasan a los nombres del original."""
    return con_form([dict(zip(COLUMNAS, fila, strict=True)) for fila in raw])


def _tabla(cols: list[str], filas: list[dict]) -> Entrada:
    return cols, [[f[c] for c in cols] for f in filas], {}


def _importado(carpeta: Path, nombre: str) -> Entrada:
    cols, filas = _raw(carpeta, nombre)
    return cols, filas, {}


def _excel(carpeta: Path) -> tuple[list[str], list]:
    return leer_xlsx(carpeta / "entradas" / "Validacion_fecha.xlsx")


def prep_01(carpeta: Path) -> tuple[dict, list]:
    origen = _origen(_raw(carpeta, "origen_aho")[1])
    return {
        "IMPORT_ORIGEN_AHO": _importado(carpeta, "origen_aho"),
        "ORIGEN_AHO": _tabla(COLUMNAS_FORM, origen),
        "AHO_UNICOS": _tabla(COLUMNAS_FORM, primera_por_llave(origen, LLAVE)),
        "AHO_SIN_DUPLICADOS_EXACTOS": _tabla(COLUMNAS_FORM,
                                             sin_duplicados_exactos(origen, COLUMNAS_FORM)),
    }, []  # fmt: skip


def prep_02(carpeta: Path) -> tuple[dict, list]:
    origen = _origen(_raw(carpeta, "origen_aho")[1])
    return {
        "IMPORT_ORIGEN_AHO": _importado(carpeta, "origen_aho"),
        "ORIGEN_AHO": _tabla(COLUMNAS_FORM, origen),
        "MARCA_AHO": _tabla([*COLUMNAS_FORM, "INCONSISTENCIA", "CORREGIDA"], marcar(origen)),
    }, []  # fmt: skip


def prep_03(carpeta: Path) -> tuple[dict, list]:
    origen = _origen(_raw(carpeta, "origen_aho")[1])
    validas = [f for f in origen if f["NRO_CTA"] != ""]
    clasif = [{**f, "ORIGEN_PAIS": "EXT" if f["TIPO_DOC"] in ("PA", "CE") else "NAL"}
              for f in validas]  # fmt: skip
    return {
        "IMPORT_ORIGEN_AHO": _importado(carpeta, "origen_aho"),
        "ORIGEN_AHO": _tabla(COLUMNAS_FORM, origen),
        "SABANA_CLASIF_AHO": _tabla([*SALIDA_SABANA_19, "ORIGEN_PAIS"], clasif),
    }, []  # fmt: skip


def prep_04(carpeta: Path) -> tuple[dict, list]:
    cte = _origen(_raw(carpeta, "origen_cte")[1])
    aho = _origen(_raw(carpeta, "origen_aho")[1])
    return {
        "IMPORT_ORIGEN_CTE": _importado(carpeta, "origen_cte"),
        "IMPORT_ORIGEN_AHO": _importado(carpeta, "origen_aho"),
        "ORIGEN_CTE": _tabla(COLUMNAS_FORM, cte),
        "ORIGEN_AHO": _tabla(COLUMNAS_FORM, aho),
    }, []  # fmt: skip


def prep_05(carpeta: Path) -> tuple[dict, list]:
    return prep_04(carpeta)


def prep_06(carpeta: Path) -> tuple[dict, list]:
    origen = _origen(_raw(carpeta, "origen_aho")[1])
    cols_xl, filas_xl = _excel(carpeta)
    anio, mes, dia = filas_xl[0]
    formato = [[anio, mes, dia, f"{mes:02d}", f"{dia:02d}"]]
    return {
        "IMPORT_ORIGEN_AHO": _importado(carpeta, "origen_aho"),
        "ORIGEN_AHO": _tabla(COLUMNAS_FORM, origen),
        "VALIDACION_FECHA": (cols_xl, filas_xl, {}),
        "FORMATO_TEXTO_FECHA": (["AÑO", "MES", "DIA", "MES_VIG", "DIA_VIG"], formato, {}),
    }, []  # fmt: skip


def prep_07(carpeta: Path) -> tuple[dict, list]:
    """Las tablas de Impala son los CSV con cabecera, cargados como si fueran el contenedor."""
    maestro = leer_dlm(carpeta / "entradas" / "master_customer_data.csv", cabecera=True)
    mcdq = leer_dlm(carpeta / "entradas" / "mcdq.csv", cabecera=True)
    tipos = {"YEAR": "INTEGER", "MONTH": "INTEGER"}
    return {
        "master_customer_data": (maestro[0], maestro[1], tipos),
        "mcdq": (mcdq[0], mcdq[1], {}),
    }, []  # fmt: skip


def prep_08(carpeta: Path) -> tuple[dict, list]:
    entradas: dict = {}
    cols_xl, filas_xl = _excel(carpeta)
    anio, mes, dia = filas_xl[0]
    entradas["VALIDACION_FECHA"] = (cols_xl, filas_xl, {})
    entradas["FECHA_TEXTO"] = (["AÑO", "MES", "DIA", "MES_TXT", "DIA_TXT"],
                               [[anio, mes, dia, f"{mes:02d}", f"{dia:02d}"]], {})  # fmt: skip
    for prod, nombre in (("CTE", "origen_cte"), ("AHO", "origen_aho")):
        origen = _origen(_raw(carpeta, nombre)[1])
        unicos = sin_duplicados_exactos(origen, COLUMNAS_FORM)
        entradas[f"IMPORT_{prod}"] = _importado(carpeta, nombre)
        entradas[f"ORIGEN_{prod}"] = _tabla(COLUMNAS_FORM, origen)
        entradas[f"UNICOS_{prod}"] = _tabla(COLUMNAS_FORM, unicos)
        entradas[f"MARCA_{prod}"] = _tabla(COLUMNAS_MARCA_08, marcar_08(unicos))
    return entradas, []


PREPARACION = {
    "01_duplicados_frecuencias": prep_01,
    "02_inconsistencias_correccion": prep_02,
    "03_sabana_nal_ext": prep_03,
    "04_totales_origen_salida": prep_04,
    "05_conciliacion": prep_05,
    "06_periodo_fecha": prep_06,
    "07_impala_lectura": prep_07,
    "08_cadena_completa_macros": prep_08,
}


def cruzar(id_: str, carpeta: Path, vacio_nulo: bool = True) -> tuple[Resultado, list[str], list]:
    """Ejecuta el programa del caso sobre SQLite y compara lo que produce con `esperado/`.

    Devuelve (resultado, diferencias, tablas del esperado que el cruce no produjo)."""
    entradas, _ = PREPARACION[id_](carpeta)
    texto = (carpeta / "programa.sas").read_text(encoding="utf-8")
    datos = yaml.safe_load((carpeta / "caso.yaml").read_text(encoding="utf-8"))
    corrida = Corrida(id_, entradas, vacio_nulo=vacio_nulo)
    resultado = corrida.correr(texto)
    resultado.macros = dict(corrida.macros)
    diferencias: list[str] = []
    for nombre, obtenido in resultado.tablas.items():
        ruta = carpeta / "esperado" / f"{nombre}.csv"
        if ruta.exists():  # las intermedias (CUENTA_*, VALIDOS_*) no tienen esperado propio
            diferencias += comparar(nombre, obtenido, leer_esperado(ruta), datos["tolerancia"])
    no_cruzadas = [
        p.stem for p in sorted((carpeta / "esperado").glob("*.csv"))
        if p.stem not in resultado.tablas
    ]
    return resultado, diferencias, no_cruzadas


def main() -> int:
    for id_ in PREPARACION:
        resultado, diferencias, no_cruzadas = cruzar(id_, DESTINO / id_)
        print(f"== {id_}: {len(resultado.tablas)} tablas cruzadas, "
              f"{len(diferencias)} diferencias, {len(resultado.pendientes)} sentencias pendientes")
        for linea in diferencias:
            print(f"   DIF {linea}")
        for linea in resultado.pendientes:
            print(f"   PEND {linea}")
        for linea in resultado.renombres:
            print(f"   RENOM {linea}")
        for patron, n in resultado.sustituciones.items():
            print(f"   SUST {patron} x{n}")
        if no_cruzadas:
            print(f"   sin cruzar (por construcción): {', '.join(map(str, no_cruzadas))}")
        alterno, dif_alterno, _ = cruzar(id_, DESTINO / id_, vacio_nulo=False)
        print(f"   variante vacío=cadena: {len(dif_alterno)} diferencias")
        for linea in dif_alterno[:6]:
            print(f"      ALT {linea}")
        _ = alterno
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
