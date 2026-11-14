"""Semántica de funciones SAS de fecha con la época 1960-01-01."""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))

import corpus_semantica as cs  # noqa: E402

from sgm.expressions.expressions import translate  # noqa: E402
from sgm.expressions.talend_translator import Unsupported, translate_to_talend  # noqa: E402
from sgm.migrar import interprete_fechas  # noqa: E402
from sgm.migrar.interprete_errores import NoSoportadoEnInterprete  # noqa: E402
from sgm.migrar.interprete_funciones import llamar  # noqa: E402

VECTORES_FECHA = {
    "mdy-01",
    "mdy-02",
    "mdy-03",
    "mdy-04",
    "mdy-05",
    "mdy-06",
    "year-01",
    "month-01",
    "day-01",
    "weekday-01",
    "weekday-02",
    "qtr-01",
    "datepart-01",
}


@pytest.mark.parametrize(
    "vector",
    [v for v in cs.cargar_vectores() if v["id"] in VECTORES_FECHA],
    ids=lambda vector: vector["id"],
)
def test_interprete_fecha_coincide_con_el_vector(vector: dict) -> None:
    resultado = llamar(vector["funcion"], vector["entrada"])
    assert cs._coincide_interprete(resultado, vector["esperado"]), (
        f"{vector['id']}: esperado {vector['esperado']!r}, obtenido {resultado!r}"
    )


def test_fechas_sas_se_convierten_con_la_epoca_y_el_reloj_inyectable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(interprete_fechas, "RELOJ", lambda: date(2024, 2, 29))

    assert interprete_fechas.EPOCA_SAS == date(1960, 1, 1)
    assert interprete_fechas.dias_a_fecha(23435) == date(2024, 2, 29)
    assert interprete_fechas.fecha_a_dias(date(2024, 2, 29)) == 23435
    assert llamar("today", []) == 23435
    assert llamar("date", []) == 23435


def test_fecha_de_dos_digitos_requiere_yearcutoff_explicito() -> None:
    with pytest.raises(NoSoportadoEnInterprete, match="P-YEARCUTOFF-EXPLICITO"):
        llamar("mdy", [8, 27, 10])


def test_fecha_de_tres_digitos_queda_pendiente_por_formato_de_anio() -> None:
    with pytest.raises(NoSoportadoEnInterprete, match="P-MDY-ANIO-3-CIFRAS"):
        llamar("mdy", [1, 1, 123])


def test_el_oraculo_y_el_interprete_pasan_todos_los_vectores_de_fecha() -> None:
    assert cs.verificar()["fallos"] == []
    assert cs.verificar(motor="interprete")["fallos"] == []
    assert cs.verificar(motor="interprete")["diferencias_motores"] == []


def test_fecha_sas_a_numero_java_convierte_desde_date() -> None:
    resultado = translate_to_talend("mdy(2, 29, 2024)", expected_kind="num")

    assert resultado.kind == "num"
    assert "TalendDate.diffDate(" in resultado.java
    assert 'TalendDate.parseDate("yyyy-MM-dd", "1960-01-01")' in resultado.java


def test_fecha_faltante_no_se_convierte_llamando_diffdate_con_null() -> None:
    resultado = translate_to_talend("mdy(., 1, 2024)", expected_kind="num")

    assert resultado.kind == "num"
    assert resultado.java == "null"


def test_datetime_no_se_emite_como_fecha_sas() -> None:
    with pytest.raises(Unsupported, match="datetime"):
        translate_to_talend("datetime()")


def test_el_anio_mdy_dinamico_queda_pendiente_por_yearcutoff() -> None:
    with pytest.raises(Unsupported, match="P-YEARCUTOFF-EXPLICITO"):
        translate_to_talend("mdy(mes, dia, anio)")


def test_la_fachada_publica_emite_serial_sas_para_fecha_y_partes() -> None:
    fecha = translate("mdy(2, 29, 2024)")
    parte = translate("year(fecha_sas)")
    datepart = translate("datepart(fecha_hora_sas)")
    hoy = translate("today()")

    assert fecha.kind == "num"
    assert fecha.engine == "talend"
    assert "TalendDate.diffDate(" in fecha.talend
    assert parte.kind == "num"
    assert 'TalendDate.getPartOfDate("YEAR",' in parte.talend
    assert 'TalendDate.parseDate("yyyy-MM-dd", "1960-01-01")' in parte.talend
    assert datepart.kind == "num" and "TalendDate.diffDate(" in datepart.talend
    assert hoy.kind == "num" and "TalendDate.diffDate(" in hoy.talend
