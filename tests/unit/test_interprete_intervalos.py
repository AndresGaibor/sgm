"""Pruebas de INTNX sobre intervalos de calendario documentados por SAS."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))

import corpus_semantica as cs  # noqa: E402
from corpus_lib.especificaciones_l4_vectores import especificaciones_de_vectores  # noqa: E402
from corpus_lib.generar_entradas_l4l6 import calcular_l4  # noqa: E402

from sgm.expressions.talend_translator import Unsupported, translate_to_talend  # noqa: E402
from sgm.migrar.interprete_errores import NoSoportadoEnInterprete  # noqa: E402
from sgm.migrar.interprete_funciones import llamar  # noqa: E402

VECTORES_INTNX = {f"intnx-{numero:02d}" for numero in range(1, 23)}


@pytest.mark.parametrize(
    "vector",
    [v for v in cs.cargar_vectores() if v["id"] in VECTORES_INTNX],
    ids=lambda vector: vector["id"],
)
def test_interprete_intnx_coincide_con_cada_vector(vector: dict) -> None:
    resultado = llamar("intnx", vector["entrada"])

    assert cs._coincide_interprete(resultado, vector["esperado"]), (
        f"{vector['id']}: esperado {vector['esperado']!r}, obtenido {resultado!r}"
    )


@pytest.mark.parametrize(
    ("argumentos", "motivo"),
    [
        (["month2", 23406, 1], "P-INTNX-MULTIUNIDAD"),
        (["month.2", 23406, 1], "P-INTNX-DESPLAZADO"),
        (["month", 23406, 1, "middle"], "P-INTNX-ALINEACION-M"),
        (["quarter", 23406, 1], "P-INTNX-INTERVALO"),
        (["month", 23406, 1.5], "P-INTNX-INCREMENTO-NO-ENTERO"),
    ],
)
def test_interprete_intnx_deja_las_formas_fuera_del_subconjunto_pendientes(
    argumentos: list[object], motivo: str
) -> None:
    with pytest.raises(NoSoportadoEnInterprete, match=motivo):
        llamar("intnx", argumentos)


def test_oraculo_y_interprete_pasan_los_vectores_de_intnx() -> None:
    assert cs.verificar()["fallos"] == []
    resultado = cs.verificar(motor="interprete")
    assert resultado["fallos"] == []
    assert resultado["diferencias_motores"] == []


def test_generador_l4_acepta_literales_antes_y_despues_de_columnas() -> None:
    vectores = [v for v in cs.cargar_vectores() if v["id"] in VECTORES_INTNX]
    especificaciones = especificaciones_de_vectores(vectores)
    razonamientos = " ".join(spec["razonamiento"] for spec in especificaciones.values())

    assert len(especificaciones) >= 8
    assert all(vector_id in razonamientos for vector_id in VECTORES_INTNX)
    for spec in especificaciones.values():
        esperados = [
            cs.evaluar("intnx", *vector["entrada"])
            for vector in vectores
            if vector["id"] in spec["razonamiento"]
        ]
        esperado = [None if isinstance(valor, cs.Faltante) else valor for valor in esperados]
        assert [fila[-1] for fila in calcular_l4(spec).filas] == esperado


def test_talend_convierte_el_serial_sas_a_date_antes_de_intnx() -> None:
    resultado = translate_to_talend(
        "intnx('month', fecha_sas, 1, 'same')", expected_kind="num"
    )

    assert "TalendDate.addDate(" in resultado.java
    assert 'TalendDate.parseDate("yyyy-MM-dd", "1960-01-01")' in resultado.java
    assert "TalendDate.diffDate(" in resultado.java
    assert "Math.min(" in resultado.java


def test_talend_emite_intnx_de_qtr_y_week_con_alineaciones_b_e_s() -> None:
    for expression in (
        "intnx('qtr', fecha_sas, 1)",
        "intnx('qtr', fecha_sas, 1, 'end')",
        "intnx('qtr', fecha_sas, 1, 'same')",
        "intnx('year', fecha_sas, 1, 'same')",
        "intnx('week', fecha_sas, 1)",
        "intnx('week', fecha_sas, 1, 'end')",
        "intnx('week', fecha_sas, 1, 'same')",
    ):
        assert translate_to_talend(expression, expected_kind="num").java


def test_talend_identifica_intervalo_multiple_y_alineacion_m_pendientes() -> None:
    with pytest.raises(Unsupported, match="P-INTNX-MULTIUNIDAD"):
        translate_to_talend("intnx('month2', fecha_sas, 1)")
    with pytest.raises(Unsupported, match="P-INTNX-ALINEACION-M"):
        translate_to_talend("intnx('month', fecha_sas, 1, 'middle')")
