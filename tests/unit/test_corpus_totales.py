"""Casos L8 de totales: el generador es reproducible y sus conteos plantados coinciden con los CSV.

El recuento de los CSV se hace aquí con reglas propias, por posición de columna, sin reutilizar
las estructuras del generador. Así el `caso.yaml` se compara con una segunda lectura de los datos.
Las comprobaciones del `esperado/` y del cruce SQL están en `test_corpus_totales_cruce.py`.
"""

from __future__ import annotations

import sys
from collections import Counter
from decimal import Decimal
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools" / "corpus_datos"))
sys.path.insert(0, str(REPO / "tools"))

import totales  # noqa: E402
from corpus_lib import invariantes  # noqa: E402
from corpus_lib.caso import cargar_caso  # noqa: E402
from corpus_lib.esquemas_caso import sin_bloque  # noqa: E402

CASOS_DIR = REPO / "tests" / "corpus" / "L8" / "totales"
IDS = [p.name for p in sorted(CASOS_DIR.iterdir()) if (p / "caso.yaml").is_file()]

# Posiciones (base 0) de las columnas del archivo de producto de 23 columnas.
ANIO, MES, RELACION, TIPO_CTA, NRO_CTA = 0, 1, 3, 5, 6
TIPO_DOC, NRO_DOC, GMF, FIN_SALDO = 8, 9, 10, 22
VALIDOS = {"CC", "TI", "CE", "PA"}
ESTADOS_PERMITIDOS = {"traducible", "parcial", "pendiente", "pendiente_revision", "revisado"}
# Claves de la plantilla de totales que `corpus_lib/caso.py` no admite (hallazgo, no se toca aquí).
CLAVES_SOLO_TOTALES = {"id", "productos", "supuestos"}


def _filas(ruta: Path) -> list[list[str]]:
    return [linea.split(";") for linea in ruta.read_text(encoding="utf-8").splitlines() if linea]


def _saldo(filas: list[list[str]]) -> str:
    total = sum((Decimal(f[FIN_SALDO].strip()) for f in filas if f[FIN_SALDO].strip()), Decimal(0))
    return f"{total:.2f}"


def _yaml(id_: str) -> dict:
    return yaml.safe_load((CASOS_DIR / id_ / "caso.yaml").read_text(encoding="utf-8"))


def test_regeneracion_coincide_con_lo_guardado(tmp_path: Path) -> None:
    escritos = totales.escribir(tmp_path)
    generados = {str(p.relative_to(tmp_path)) for p in escritos}
    guardados = {
        str(p.relative_to(CASOS_DIR))
        for p in CASOS_DIR.rglob("*")
        if p.is_file() and p.name != "programa.sas"
    }
    assert generados == guardados
    for ruta in escritos:
        relativa = ruta.relative_to(tmp_path)
        if relativa.name == "caso.yaml":
            # el bloque `esquemas` es derivado del programa: lo verifica test_esquemas_sincronizados
            guardado = (CASOS_DIR / relativa).read_text(encoding="utf-8")
            assert ruta.read_text(encoding="utf-8") == sin_bloque(guardado), str(relativa)
        else:
            assert ruta.read_bytes() == (CASOS_DIR / relativa).read_bytes(), str(relativa)


def test_cada_caso_tiene_programa_y_longitud_adecuada() -> None:
    for id_ in totales.generar():
        lineas = (CASOS_DIR / id_ / "programa.sas").read_text(encoding="utf-8").count("\n")
        assert 120 <= lineas <= 300, (id_, lineas)


@pytest.mark.parametrize("id_", IDS)
def test_campos_del_caso_y_salidas(id_: str) -> None:
    datos = _yaml(id_)
    for clave in ("nivel", "tema", "construcciones", "capa", "estado", "anomalias_plantadas",
                  "salidas_esperadas", "fuentes_url", "tolerancia", "invariantes"):
        assert clave in datos, clave
    assert datos["estado"] in ESTADOS_PERMITIDOS
    if datos["estado"] != "traducible":
        assert datos.get("motivo"), "un caso no traducible declara su motivo"
    esperados = {p.stem for p in (CASOS_DIR / id_ / "esperado").glob("*.csv")}
    declaradas = set(datos["salidas_esperadas"]["tablas_work"])
    declaradas |= {n[:-4] for n in datos["salidas_esperadas"]["archivos"]}
    assert declaradas <= esperados, declaradas - esperados


@pytest.mark.parametrize("id_", IDS)
def test_caso_pasa_el_cargador_del_corpus(id_: str, tmp_path: Path) -> None:
    """El resto del `caso.yaml` valida con `cargar_caso` (bajo un nivel L8, como exige el cargador)."""
    datos = {k: v for k, v in _yaml(id_).items() if k not in CLAVES_SOLO_TOTALES}
    destino = tmp_path / "L8" / id_
    destino.mkdir(parents=True)
    (destino / "caso.yaml").write_text(yaml.safe_dump(datos, allow_unicode=True), encoding="utf-8")
    assert cargar_caso(destino).capa in ("A", "B", "C")


@pytest.mark.parametrize("id_", IDS)
def test_invariantes_se_cumplen_sobre_el_esperado(id_: str) -> None:
    datos = _yaml(id_)
    fallos = invariantes.comprobar(datos["invariantes"], [CASOS_DIR / id_ / "esperado"],
                                   datos["tolerancia"])
    assert fallos == [], fallos


def test_duplicados_y_frecuencias() -> None:
    filas = _filas(CASOS_DIR / "01_duplicados_frecuencias" / "entradas" / "origen_aho.csv")
    exactas = Counter(tuple(f) for f in filas)
    llaves = Counter(tuple(f[i] for i in (RELACION, TIPO_CTA, NRO_CTA, TIPO_DOC, NRO_DOC))
                     for f in filas)  # fmt: skip
    anomalias = _yaml("01_duplicados_frecuencias")["anomalias_plantadas"]
    assert anomalias["filas_origen"] == len(filas)
    assert anomalias["grupos_duplicados_exactos"] == sum(1 for n in exactas.values() if n > 1)
    assert anomalias["filas_extra_duplicados_exactos"] == sum(n - 1 for n in exactas.values())
    assert anomalias["grupos_duplicados_por_llave"] == sum(1 for n in llaves.values() if n > 1)
    assert anomalias["filas_extra_por_llave"] == len(filas) - len(llaves)
    assert anomalias["llaves_unicas"] == len(llaves)
    assert anomalias["suma_saldo_origen"] == _saldo(filas)


def test_inconsistencias_corregidas_y_por_corregir() -> None:
    filas = _filas(CASOS_DIR / "02_inconsistencias_correccion" / "entradas" / "origen_aho.csv")
    por_corregir = [
        f for f in filas
        if f[TIPO_CTA] not in ("01", "02", "03") or f[GMF] not in ("S", "N") or f[NRO_CTA] == ""
    ]  # fmt: skip
    corregibles = [
        f for f in filas
        if f not in por_corregir and (f[TIPO_DOC] == "CEDULA" or f[NRO_DOC] == "")
    ]  # fmt: skip
    # El LEFT JOIN del original excluye por NRO_CTA; la fila sin cuenta vuelve (IS MISSING).
    excluidas = [f for f in por_corregir if f[NRO_CTA] != ""]
    sabana = [f for f in filas if f not in excluidas]
    anomalias = _yaml("02_inconsistencias_correccion")["anomalias_plantadas"]
    assert anomalias["filas_por_corregir"] == len(por_corregir)
    assert anomalias["filas_corregibles"] == len(corregibles)
    assert anomalias["filas_sabana_final"] == len(sabana) == len(filas) - 4
    assert anomalias["filas_sin_cuenta_que_vuelven_a_sabana"] == 1
    assert anomalias["suma_saldo_sabana_final"] == _saldo(sabana)


def test_sabana_nacional_y_extranjera() -> None:
    filas = _filas(CASOS_DIR / "03_sabana_nal_ext" / "entradas" / "origen_aho.csv")
    validas = [f for f in filas if f[NRO_CTA]]
    nal = [f for f in validas if f[TIPO_DOC] not in ("PA", "CE")]
    ext = [f for f in validas if f[TIPO_DOC] in ("PA", "CE")]
    anomalias = _yaml("03_sabana_nal_ext")["anomalias_plantadas"]
    assert anomalias["filas_resultado_nal"] == len(nal)
    assert anomalias["filas_resultado_ext"] == len(ext)
    assert anomalias["filas_sin_cuenta"] == len(filas) - len(validas)
    assert anomalias["suma_saldo_resultado_nal"] == _saldo(nal)
    assert anomalias["suma_saldo_resultado_ext"] == _saldo(ext)


def test_totales_por_producto() -> None:
    cte = _filas(CASOS_DIR / "04_totales_origen_salida" / "entradas" / "origen_cte.csv")
    aho = _filas(CASOS_DIR / "04_totales_origen_salida" / "entradas" / "origen_aho.csv")
    anomalias = _yaml("04_totales_origen_salida")["anomalias_plantadas"]
    assert anomalias["cte_filas_origen"] == len(cte)
    assert anomalias["cte_saldos_no_vacios_origen"] == sum(1 for f in cte if f[FIN_SALDO].strip())
    assert anomalias["cte_suma_saldo_origen"] == _saldo(cte)
    assert anomalias["aho_suma_saldo_origen"] == _saldo(aho)
    salida_cte = [f for f in cte if f[TIPO_CTA] != "03"]
    salida_aho = [f for f in aho if f[TIPO_CTA] != "03"]
    assert anomalias["cte_filas_salida"] == len(salida_cte)
    assert anomalias["cte_suma_saldo_salida"] == _saldo(salida_cte)
    assert anomalias["aho_filas_salida"] == len(salida_aho)
    assert anomalias["aho_suma_saldo_salida"] == _saldo(salida_aho)


def test_conciliacion_concilia_y_no_concilia() -> None:
    anomalias = _yaml("05_conciliacion")["anomalias_plantadas"]
    for prod, archivo in (("cte", "origen_cte.csv"), ("aho", "origen_aho.csv")):
        filas = _filas(CASOS_DIR / "05_conciliacion" / "entradas" / archivo)
        validas = [f for f in filas if f[TIPO_DOC] in VALIDOS and f[NRO_CTA]]
        rechazadas = [f for f in filas if f[TIPO_DOC] not in VALIDOS and f[TIPO_DOC]]
        assert anomalias[f"{prod}_filas_validas"] == len(validas)
        assert anomalias[f"{prod}_filas_rechazadas"] == len(rechazadas)
        dif_filas = len(filas) - len(validas) - len(rechazadas)
        assert anomalias[f"{prod}_diferencia_filas"] == dif_filas
        dif = Decimal(_saldo(filas)) - Decimal(_saldo(validas)) - Decimal(_saldo(rechazadas))
        assert anomalias[f"{prod}_diferencia_saldo"] == f"{dif:.2f}"
        concilia = dif_filas == 0 and abs(dif) <= Decimal("0.01")
        assert anomalias[f"{prod}_estado"] == ("CONCILIA" if concilia else "NO CONCILIA")
    assert anomalias["cte_estado"] == "CONCILIA"
    assert anomalias["aho_estado"] == "NO CONCILIA"


def test_periodo_y_nombre_de_salida() -> None:
    filas = _filas(CASOS_DIR / "06_periodo_fecha" / "entradas" / "origen_aho.csv")
    anomalias = _yaml("06_periodo_fecha")["anomalias_plantadas"]
    assert anomalias["filas_del_periodo"] == sum(1 for f in filas if f[MES] == "09")
    assert anomalias["fecha_concatenada"] == "20260930"
    assert anomalias["archivo_salida"] == "RESULTADO_AHO_20260930.csv"
    assert (CASOS_DIR / "06_periodo_fecha" / "esperado" / anomalias["archivo_salida"]).is_file()


def test_impala_ultimo_dia() -> None:
    filas = _filas(CASOS_DIR / "07_impala_lectura" / "entradas" / "master_customer_data.csv")[1:]
    maximo = max(f[2] for f in filas if f[0] == "2026" and f[1] == "9")
    ultimo = [f for f in filas if f[0] == "2026" and f[1] == "9" and f[2] == maximo]
    anomalias = _yaml("07_impala_lectura")["anomalias_plantadas"]
    assert anomalias["maxdia_para_anio_2026_mes_9"] == maximo
    assert anomalias["filas_ultimo_dia"] == len(ultimo)
    assert anomalias["filas_master_customer_data"] == len(filas)


@pytest.mark.parametrize("prod", ["cte", "aho"])
def test_cadena_completa_por_producto(prod: str) -> None:
    filas = _filas(CASOS_DIR / "08_cadena_completa_macros" / "entradas" / f"origen_{prod}.csv")
    unicas = Counter(tuple(f) for f in filas)
    extra = sum(n - 1 for n in unicas.values())
    base = filas[:30]
    por_corregir = [f for f in base if f[TIPO_CTA] not in ("01", "02", "03")]
    sabana = [f for f in base if f not in por_corregir]
    anomalias = _yaml("08_cadena_completa_macros")["anomalias_plantadas"]
    assert anomalias[f"{prod}_filas_origen"] == len(filas)
    assert anomalias[f"{prod}_duplicados_extra"] == extra
    assert anomalias[f"{prod}_por_corregir"] == len(por_corregir)
    assert anomalias[f"{prod}_filas_sabana"] == len(sabana)
    assert anomalias[f"{prod}_suma_saldo_sabana"] == _saldo(sabana)
    assert anomalias[f"{prod}_estado"] == "CONCILIA"
