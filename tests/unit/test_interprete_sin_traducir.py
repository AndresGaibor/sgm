"""B-13: el intérprete no ignora lo que no traduce. Una sentencia sin traducción o una asignación condicional sin
partes detiene la ejecución; antes salían filas sin la columna y la prueba pasaba sin probar nada.

`lrcon`, p. 500: el DATA step ejecuta cada sentencia en orden, así que ninguna se puede saltar.
La suma (`lestmtsref`, p. 360) y `LAG` (`lefunctionsref`, p. 1163) todavía no tienen estado por fila.
"""

from __future__ import annotations

import pytest

from sgm.compile import compile_file, project_base
from sgm.frontend.program import analyze_program
from sgm.migrar.interprete import NoSoportadoEnInterprete, ejecutar_plan

ENTRADA = "PROC IMPORT DATAFILE='.../t.csv' OUT=WORK.t DBMS=CSV REPLACE;\n  GETNAMES=YES;\nRUN;\n"
FILAS = [{"id": "1", "x": "2"}, {"id": "2", "x": ""}]


def _correr(cuerpo: str):
    texto = ENTRADA + "DATA WORK.r;\n  SET WORK.t;\n" + cuerpo + "RUN;\n"
    plan = compile_file(analyze_program({"p.sas": texto}), "p.sas", project_base()).plan
    return ejecutar_plan(plan, {"t": FILAS})


def test_select_sin_otherwise_no_sale_como_si_no_existiera():
    # lestmtsref, p. 340: si ningún WHEN coincide y no hay OTHERWISE, SAS da error; no se inventa rama.
    with pytest.raises(NoSoportadoEnInterprete, match="sentencia sin traducción"):
        _correr("  SELECT (x);\n    WHEN (1) y = 'a';\n  END;\n")


def test_lag_dentro_de_if_no_se_ignora():
    with pytest.raises(NoSoportadoEnInterprete, match="asignación condicional sin partes"):
        _correr("  IF x > 0 THEN prev = LAG(x);\n")
