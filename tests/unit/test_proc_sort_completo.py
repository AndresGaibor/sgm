"""Regresiones de MG-P6-01: opciones de PROC SORT y casos de corpus."""

from __future__ import annotations

import inspect
import sys
from pathlib import Path

import pytest

from sgm.cli_migrar import migrar
from sgm.frontend.program import analyze_program
from sgm.ir.lower import lower_items
from sgm.ir.models import Plan

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))

from corpus_lib import referencia_datastep as referencia  # noqa: E402
from corpus_lib.csv_tabla import Tabla, comparar_con_guardado  # noqa: E402
from corpus_lib.generar_entradas_l4l6 import ESPECIFICACIONES  # noqa: E402
from corpus_lib.studio_comparar import comparar_archivos  # noqa: E402


def _ops(texto: str):
    plan = Plan(program="orden.sas")
    lower_items(analyze_program({"orden.sas": texto}).items, plan.graph)
    return plan.graph.operators()


def test_oraculo_noduprec_quita_solo_repeticiones_completas_adyacentes() -> None:
    ordenar_y_filtrar = getattr(referencia, "proc_sort_noduprec_por_llave", None)
    assert callable(ordenar_y_filtrar), "falta el oráculo PROC SORT NODUPREC por llave"
    if not callable(ordenar_y_filtrar):
        return

    no_adyacentes = [
        {"id": 1, "v": "a"},
        {"id": 1, "v": "b"},
        {"id": 1, "v": "a"},
        {"id": 2, "v": "c"},
    ]
    adyacentes = [
        {"id": 1, "v": "a"},
        {"id": 1, "v": "a"},
        {"id": 2, "v": "c"},
    ]

    assert ordenar_y_filtrar(no_adyacentes, ["id"]) == no_adyacentes
    assert ordenar_y_filtrar(adyacentes, ["id"]) == [adyacentes[0], adyacentes[2]]


def test_oraculo_proc_sort_aplica_descending_por_llave() -> None:
    filas = [{"id": 1, "v": "a"}, {"id": 3, "v": "c"}, {"id": 2, "v": "b"}]

    assert referencia.proc_sort(filas, ["id"], descending=[True]) == [
        {"id": 3, "v": "c"},
        {"id": 2, "v": "b"},
        {"id": 1, "v": "a"},
    ]


def test_noduprec_por_llave_parcial_deja_codigo_de_pendiente() -> None:
    (orden,) = _ops("PROC SORT DATA=WORK.r OUT=WORK.r_sin NODUPREC; BY id; RUN;")

    assert orden.kind == "sort"
    assert orden.status == "parcial"
    assert any("P-NODUPREC-NO-ADYACENTE" in nota for nota in orden.notes)


def test_comparador_admite_orden_de_grupos_sin_ordenar_empates(tmp_path: Path) -> None:
    assert "orden_grupo" in inspect.signature(comparar_con_guardado).parameters
    if "orden_grupo" not in inspect.signature(comparar_con_guardado).parameters:
        return

    esperado = tmp_path / "esperado.csv"
    esperado.write_text("id,v\n3,c\n3,d\n2,b\n1,a\n", encoding="utf-8")
    orden_grupo = [{"columna": "id", "descendente": True}]
    try:
        empates_reordenados = Tabla(
            ["id", "v"], [("3", "d"), ("3", "c"), ("2", "b"), ("1", "a")]
        )
        grupos_fuera_de_orden = Tabla(
            ["id", "v"], [("1", "a"), ("2", "b"), ("3", "d"), ("3", "c")]
        )

        assert comparar_con_guardado(
            esperado, empates_reordenados, 0, False, orden_grupo=orden_grupo
        ) == []
        diferencias = comparar_con_guardado(
            esperado, grupos_fuera_de_orden, 0, False, orden_grupo=orden_grupo
        )
        assert diferencias and "grupo" in diferencias[0].lower()

        salida = tmp_path / "salida.csv"
        salida.write_text("id,v\n3,d\n3,c\n2,b\n1,a\n", encoding="utf-8")
        resultado = comparar_archivos(
            esperado,
            salida,
            orden_relevante=False,
            orden_grupo=orden_grupo,
        )
        assert resultado.coincide
    finally:
        esperado.unlink(missing_ok=True)


def test_casos_l6_60_a_62_estan_en_la_especificacion() -> None:
    nombres = {
        "l6_60_noduprec_por_llave",
        "l6_61_nodupkey_dupout",
        "l6_62_sort_descending_noequals",
    }
    existentes = set(ESPECIFICACIONES["L6"])

    assert nombres <= existentes, f"faltan casos de PROC SORT: {sorted(nombres - existentes)}"
    if not nombres <= existentes:
        return

    for nombre in nombres:
        programa = ESPECIFICACIONES["L6"][nombre]["programa"]
        assert "PROC IMPORT DATAFILE='.../entradas/R.csv' OUT=WORK.R" in programa

    caso = ESPECIFICACIONES["L6"]["l6_62_sort_descending_noequals"]
    assert caso["orden_grupo"] == [{"columna": "id", "descendente": True}]
    assert caso["programa"].count("DESCENDING id") == 1


@pytest.mark.parametrize(
    ("nombre", "codigo"),
    [
        ("l6_60_noduprec_por_llave", "P-NODUPREC-NO-ADYACENTE"),
        ("l6_61_nodupkey_dupout", "P-NODUPKEY-ESTABILIDAD-NO-VALIDADA"),
    ],
)
def test_migracion_publica_los_pendientes_semanticos_de_sort(
    nombre: str, codigo: str, tmp_path: Path
) -> None:
    caso = REPO / "tests" / "corpus" / "L6" / nombre
    resultado = migrar(
        caso / "programa.sas",
        tmp_path / nombre,
        muestra=caso / "entradas",
    )

    assert any(pendiente.codigo == codigo for pendiente in resultado.pendientes)
    informe = (resultado.carpeta / "pendientes.md").read_text(encoding="utf-8")
    assert codigo in informe
