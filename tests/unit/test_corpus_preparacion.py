"""Pruebas del bloque `preparacion` (DATA step antes del PROC SQL) y del generador de L2 y L3.

El DATA step `input(left(x), 20.)` se calcula con la capa B. Un faltante de texto es blanco, como en
SAS. La prueba de regeneración copia los casos a una carpeta temporal y comprueba que el generador da los
mismos bytes que los archivos del repositorio.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))

from corpus_lib import preparacion  # noqa: E402
from corpus_lib.csv_tabla import Tabla  # noqa: E402
from corpus_lib.generar_entradas_l2l3 import ESPECIFICACIONES, generar_todo  # noqa: E402

from corpus import main  # noqa: E402

CORPUS = REPO / "tests" / "corpus"
PREPARACION = {
    "origen": "columnas_depositos",
    "destino": "FORM_SALDO_CTA_CTE",
    "asignaciones": [
        {
            "variable": "FORM_FIN_SALDO_CTA",
            "columna": "fin_saldo_cta",
            "pasos": [["left"], ["input", 20, 0]],
        }
    ],
}


def _origen() -> Tabla:
    return Tabla(
        ["id", "fin_saldo_cta"],
        [(1, " 1523.40"), (2, None), (3, "  2300"), (4, "  12.5")],
        ["INTEGER", "TEXT"],
    )


def test_input_left_convierte_texto_con_blancos_y_faltantes():
    resultado = preparacion.aplicar(_origen(), preparacion.validar(PREPARACION))
    assert resultado.columnas == ["id", "fin_saldo_cta", "FORM_FIN_SALDO_CTA"]
    assert [fila[2] for fila in resultado.filas] == [1523.4, None, 2300, 12.5]
    assert resultado.tipos[2] == "REAL"


def test_valor_de_origen_inexistente_es_error_claro():
    datos = {**PREPARACION, "asignaciones": [{**PREPARACION["asignaciones"][0], "columna": "x"}]}
    with pytest.raises(ValueError, match="no existe en el origen"):
        preparacion.aplicar(_origen(), preparacion.validar(datos))


@pytest.mark.parametrize(
    ("cambio", "motivo"),
    [
        ({"asignaciones": []}, "no vacía"),
        ({"origen": "con espacios"}, "identificador"),
        ({"asignaciones": [{"variable": "v", "columna": "c", "pasos": [["funcion_inexistente"]]}]},
         "no implementada"),
        ({"asignaciones": [{"variable": "v", "columna": "c", "pasos": [["input", True]]}]},
         "argumento"),
    ],
)
def test_preparacion_mal_formada_se_rechaza(cambio, motivo):
    with pytest.raises(ValueError, match=motivo):
        preparacion.validar({**PREPARACION, **cambio})


def test_caso_con_preparacion_pasa_el_oraculo(capsys):
    assert main(["oraculo", "l3_08_preparacion_input_left", "--verificar"]) == 0
    assert "VERIFICADO" in capsys.readouterr().out


def test_entradas_preparadas_alteradas_hacen_fallar_el_oraculo(tmp_path, capsys):
    caso = tmp_path / "L3" / "l3_08_preparacion_input_left"
    shutil.copytree(CORPUS / "L3" / "l3_08_preparacion_input_left", caso)
    (caso / "entradas_preparadas" / "FORM_SALDO_CTA_CTE.csv").write_text(
        "id_cuenta,tipo_cta,fin_saldo_cta,FORM_FIN_SALDO_CTA\n5001,AHORROS,  3080.94,9999\n",
        encoding="utf-8",
    )
    assert main(["oraculo", "l3_08_preparacion_input_left", "--verificar", "--corpus",
                 str(tmp_path)]) == 1
    assert "entradas_preparadas no coincide" in capsys.readouterr().out


def test_generador_de_l2_y_l3_es_reproducible(tmp_path):
    """Dos generaciones dan los mismos bytes que los archivos guardados en el repositorio."""
    copia = tmp_path / "corpus"
    for nivel in ("L2", "L3"):
        shutil.copytree(CORPUS / nivel, copia / nivel)
    escritos = generar_todo(copia)
    assert len(ESPECIFICACIONES) == 27
    assert len(escritos) == 46  # 30 de L2, 15 de L3 y el archivo preparado de l3_08
    for ruta in escritos:
        relativa = ruta.relative_to(copia)
        assert ruta.read_bytes() == (CORPUS / relativa).read_bytes(), relativa
