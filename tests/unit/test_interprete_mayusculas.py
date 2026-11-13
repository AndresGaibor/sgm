"""Defecto Z/z: en SAS los nombres de variable no distinguen mayúsculas, y se guarda la forma de la primera
referencia (`lrcon`, p. 49: `cat`, `Cat` y `CAT` son la misma variable). Una asignación a `VALOR` sobre una
columna `valor` sustituye esa columna y no crea una segunda. Antes, el intérprete dejaba las dos.
"""

from __future__ import annotations

from sgm.compile import compile_file, project_base
from sgm.frontend.program import analyze_program
from sgm.migrar.interprete import ejecutar_plan

ENTRADA = "PROC IMPORT DATAFILE='.../t.csv' OUT=WORK.t DBMS=CSV REPLACE;\n  GETNAMES=YES;\nRUN;\n"


def _salida(cuerpo: str, filas: list[dict]) -> list[dict]:
    texto = ENTRADA + "DATA WORK.r;\n  SET WORK.t;\n" + cuerpo + "RUN;\n"
    plan = compile_file(analyze_program({"p.sas": texto}), "p.sas", project_base()).plan
    return ejecutar_plan(plan, {"t": filas})["r"]


def test_asignacion_con_otra_mayuscula_sustituye_la_columna_de_entrada():
    salida = _salida("  VALOR = VALOR + 10;\n", [{"id": "a", "valor": "1"}])
    claves = list(salida[0].keys())
    assert len({k.lower() for k in claves}) == len(claves), claves
    assert float(salida[0]["valor"]) == 11.0


def test_columna_nueva_no_cambia_la_de_entrada():
    salida = _salida("  NUEVA = VALOR * 2;\n", [{"id": "a", "valor": "1"}])
    fila = {k.lower(): v for k, v in salida[0].items()}
    assert float(fila["nueva"]) == 2.0
    assert float(fila["valor"]) == 1.0
