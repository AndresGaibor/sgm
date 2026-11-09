"""Bloque `esquemas` de `caso.yaml`: forma válida, tipos demostrados y pendientes con motivo."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))

from corpus_lib import esquemas_caso  # noqa: E402
from corpus_lib.caso import cargar_caso  # noqa: E402

CORPUS = REPO / "tests" / "corpus"


def test_tipo_demostrado_con_linea_y_longitud():
    bloque = {"WORK.t": {"nivel": {"tipo": "String", "longitud": 5, "linea": 12}}}
    assert esquemas_caso.validar(bloque) == bloque


def test_pendiente_con_motivo():
    bloque = {"WORK.t": {"saldo": {"tipo": "pendiente", "motivo": "dato"}}}
    assert esquemas_caso.validar(bloque) == bloque


@pytest.mark.parametrize(
    "entrada, error",
    [
        ({"tipo": "Inventado", "linea": 1}, "debe ser"),
        ({"tipo": "Double"}, "necesita 'linea'"),
        ({"tipo": "Double", "linea": 0}, "necesita 'linea'"),
        ({"tipo": "pendiente"}, "necesita 'motivo'"),
        ({"tipo": "pendiente", "motivo": "  "}, "necesita 'motivo'"),
        ({"tipo": "Double", "linea": 3, "longitud": 8}, "solo aplica a String"),
        ({"tipo": "String", "linea": 3, "longitud": 0}, "entero >= 1"),
        ({"tipo": "Double", "linea": 3, "rareza": 1}, "no reconocidos"),
    ],
)
def test_entrada_invalida_se_rechaza(entrada, error):
    with pytest.raises(ValueError, match=error):
        esquemas_caso.validar({"WORK.t": {"c": entrada}})


def test_nombres_no_validos_se_rechazan():
    with pytest.raises(ValueError, match="tabla no válido"):
        esquemas_caso.validar({"1mal": {"c": {"tipo": "Double", "linea": 1}}})
    with pytest.raises(ValueError, match="columna no válido"):
        esquemas_caso.validar({"WORK.t": {"con espacio": {"tipo": "Double", "linea": 1}}})


def test_bloque_vacio_se_rechaza():
    with pytest.raises(ValueError, match="mapa no vacío"):
        esquemas_caso.validar({})


def test_casos_piloto_cargan_su_bloque():
    caso = cargar_caso(CORPUS / "L0" / "l0_07_if_then_else")
    assert caso.extra["esquemas"]["WORK.clientes_nivel"]["nivel"] == {
        "tipo": "String",
        "linea": 12,
        "longitud": 5,
    }
    caso = cargar_caso(CORPUS / "L1" / "l1_01_select_columnas")
    assert caso.extra["esquemas"]["WORK.clientes"]["saldo"]["tipo"] == "pendiente"


def _casos_con_esquemas():
    for carpeta in sorted(CORPUS.glob("L*/**/caso.yaml")):
        caso = cargar_caso(carpeta.parent)
        if caso.extra.get("esquemas"):
            yield caso


def test_todo_tipo_demostrado_cita_una_linea_con_su_declaracion():
    """Cada tipo demostrado apunta a una línea del SAS que declara esa columna (LENGTH/FORMAT)."""
    for caso in _casos_con_esquemas():
        lineas = caso.programa.read_text(encoding="utf-8").splitlines()
        for tabla, columnas in caso.extra["esquemas"].items():
            for columna, entrada in columnas.items():
                if entrada["tipo"] == "pendiente":
                    continue
                linea = lineas[entrada["linea"] - 1]
                assert columna.lower() in linea.lower(), (caso.nombre, tabla, columna, linea)
                assert "LENGTH" in linea.upper() or "FORMAT" in linea.upper(), (caso.nombre, linea)


def test_el_corpus_l0_a_l2_declara_esquemas():
    nombres = {caso.nombre for caso in _casos_con_esquemas()}
    assert len(nombres) >= 44
