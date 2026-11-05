"""Hito 89: la forma del SAS real de R1-06 se lee del programa, no se inventa ni se unifica."""

from __future__ import annotations

from pathlib import Path

import pytest

from sgm.proceso.reglas import reglas
from sgm.proceso.reglas_cuenta_real import (
    INCONSISTENCIA,
    MODOS,
    TABLAS,
    proyeccion,
    reglas_cuenta_real,
)

RAIZ = Path(__file__).resolve().parents[2]
PROGRAMA = RAIZ / "tests" / "fixtures" / "sas" / "client" / "client_large.sas"
V04 = RAIZ / "tests" / "corpus" / "L8" / "validaciones" / "v04_tipo_cta_gmf" / "programa.sas"
TEXTO = PROGRAMA.read_text(encoding="utf-8", errors="replace")


@pytest.fixture(scope="module")
def real():
    return reglas_cuenta_real(TEXTO)


def test_las_dos_reglas_son_los_not_between_del_sas_real(real):
    reglas_cuenta, _ = real
    assert (reglas_cuenta.tipo_cta.columna, reglas_cuenta.tipo_cta.desde,
            reglas_cuenta.tipo_cta.hasta) == ("TIPO_CTA", 1, 5)
    assert (reglas_cuenta.codex.columna, reglas_cuenta.codex.desde,
            reglas_cuenta.codex.hasta) == ("GMF", 1, 10)
    assert reglas_cuenta.tipo_cta.permite is False
    assert reglas_cuenta.codex.permite is False
    assert reglas_cuenta.control == ("RELACION", "1000")
    assert reglas_cuenta.motivos == {
        "tipo_cta": "TIPO CTA INVALIDO",
        "codex": "CODEX INVALIDO",
    }


def test_los_motivos_salen_del_paso_data_y_no_de_v04(real):
    reglas_cuenta, _ = real
    assert "GMF NO NUMERICO" not in reglas_cuenta.motivos.values()
    # `v04` escribe `NOT IN (...)`, así que el lector de la forma real no encuentra la pareja.
    with pytest.raises(ValueError, match="no declara la regla 'tipo_cta'"):
        reglas_cuenta_real(V04.read_text(encoding="utf-8"))


def test_las_lineas_del_sas_real_quedan_ancladas(real):
    reglas_cuenta, _ = real
    # Además de los cuatro rechazos de cuenta, el SAS tiene tres `FINAL_VALIDAR_CTA_Y_GMF_*`
    # con el mismo control: quedan entre los pendientes, no se emiten como rechazos.
    lineas = {r.linea for r in reglas(TEXTO) if r.control == ("RELACION", "1000")}
    assert lineas == {3572, 3656, 6088, 6172, 22834, 23457, 23783}
    assert reglas_cuenta.tipo_cta.linea == 3572
    assert reglas_cuenta.codex.linea == 3656


def test_los_productos_declaran_la_misma_forma(real):
    reglas_cuenta, _ = real
    seleccion = [
        r for r in reglas(TEXTO)
        if r.destino.startswith(("INCONS_TIPO_CTA_INVALIDO_", "INCONS_CODEX_INVALIDO_"))
    ]
    assert {r.destino.rsplit("_", 1)[-1] for r in seleccion} == {"CTE", "AHO"}
    por_regla = {
        prefijo: {(r.columna, r.desde, r.hasta, r.permite, r.motivo, r.control)
                  for r in seleccion if r.destino.startswith(prefijo)}
        for prefijo in ("INCONS_TIPO_CTA_INVALIDO_", "INCONS_CODEX_INVALIDO_")
    }
    assert all(len(formas) == 1 for formas in por_regla.values())


def test_la_proyeccion_son_las_19_columnas_del_select(real):
    reglas_cuenta, _ = real
    assert len(reglas_cuenta.columnas) == 19
    assert reglas_cuenta.columnas[0] == "RELACION"
    assert reglas_cuenta.columnas[-1] == "FIN_SALDO_CTA"
    assert "GMF" in reglas_cuenta.columnas and "TIPO_CTA" in reglas_cuenta.columnas


def test_las_tablas_con_motivo_proyectan_19_mas_inconsistencia(real):
    reglas_cuenta, _ = real
    esperado = (*reglas_cuenta.columnas, INCONSISTENCIA)
    for producto in ("CTE", "AHO"):
        for tabla in (f"INCONS_PAQ_TIPO_CTA_INV_{producto}", f"INCONS_PAQ_GMF_INV_{producto}"):
            assert proyeccion(TEXTO, tabla) == esperado
        assert proyeccion(TEXTO, f"SABANA_CODEX_VALIDO_{producto}") == reglas_cuenta.columnas


def test_un_select_asterisco_no_se_lee_como_proyeccion():
    with pytest.raises(ValueError, match="no se puede leer la columna"):
        proyeccion(TEXTO, "INCONS_DEP_AHORROS")


def test_una_tabla_que_no_existe_no_se_inventa():
    with pytest.raises(ValueError, match="no declara"):
        proyeccion(TEXTO, "TABLA_QUE_NO_EXISTE")


def test_los_nombres_de_salida_son_los_del_sas(real):
    reglas_cuenta, _ = real
    assert reglas_cuenta.tablas == TABLAS
    assert sorted(reglas_cuenta.tablas) == sorted(MODOS)


def test_las_reglas_fuera_de_la_cadena_no_se_descartan_en_silencio(real):
    _, pendientes = real
    assert any("29 reglas de rango" in p for p in pendientes)
    assert any("NEQUI" in p for p in pendientes)
    assert any("OUTER UNION CORR" in p for p in pendientes)
    assert any("R1-07" in p for p in pendientes)


def test_un_programa_sin_la_pareja_no_emite_reglas_a_medias():
    with pytest.raises(ValueError, match="no declara la regla"):
        reglas_cuenta_real("PROC SQL; QUIT;")
