"""B-13: `LAG` y `DIF` con su cola (`lefunctionsref`, p. 1164 para LAG y p. 663 para DIF).

Cada aparición de `LAGn` tiene su propia cola, inicializada con n faltantes. La cola solo avanza cuando la función se
ejecuta: con `IF cond THEN ...`, guarda y devuelve valores solo de las observaciones que cumplen la condición (p. 1164).
`DIFn(x) = x - LAGn(x)` (p. 663). El traductor no tiene emisor para el estado entre filas: el paso no sale como Job
(decisión 5), y el intérprete lo calcula para probarlo.
"""

from __future__ import annotations

import pytest

from sgm.cli_migrar import migrar
from sgm.compile import compile_file, project_base
from sgm.frontend.program import analyze_program
from sgm.migrar.interprete import NoSoportadoEnInterprete, ejecutar_plan

ENTRADA = "PROC IMPORT DATAFILE='.../t.csv' OUT=WORK.t DBMS=CSV REPLACE;\n  GETNAMES=YES;\nRUN;\n"


def _correr(cuerpo: str, filas: list[dict]) -> list[dict]:
    texto = ENTRADA + "DATA WORK.r;\n  SET WORK.t;\n" + cuerpo + "RUN;\n"
    plan = compile_file(analyze_program({"p.sas": texto}), "p.sas", project_base()).plan
    salida = ejecutar_plan(plan, {"t": filas})["r"]
    return [{k.lower(): v for k, v in f.items()} for f in salida]


def _numeros(filas: list[dict], columna: str) -> list[float | None]:
    return [None if f[columna] in (None, "") else float(f[columna]) for f in filas]


def test_lag_devuelve_la_observacion_anterior():  # lefunctionsref, p. 1164
    filas = _correr("  prev = LAG(x);\n", [{"x": "2"}, {"x": "3"}, {"x": "5"}])
    assert _numeros(filas, "prev") == [None, 2.0, 3.0]


def test_lag_dentro_de_if_solo_avanza_cuando_se_ejecuta():  # lefunctionsref, p. 1164 (trampa de l6_40)
    # La fila con x = -1 no cumple la condición: la cola no guarda ese valor. La tercera fila devuelve 2,
    # el de la primera ejecución, y no el de la fila anterior (-1).
    filas = _correr(
        "  IF x > 0 THEN prev = LAG(x);\n",
        [{"x": "2"}, {"x": "-1"}, {"x": "3"}],
    )
    assert _numeros(filas, "prev") == [None, None, 2.0]


def test_dif_es_x_menos_su_lag_y_el_primero_falta():  # lefunctionsref, p. 663
    filas = _correr("  d = DIF(x);\n", [{"x": "2"}, {"x": "3"}, {"x": "5"}])
    assert _numeros(filas, "d") == [None, 1.0, 2.0]


def test_dif2_usa_la_cola_de_dos():  # lefunctionsref, p. 663 (DIFn = x - LAGn(x))
    filas = _correr("  d = DIF2(x);\n", [{"x": "1"}, {"x": "2"}, {"x": "4"}, {"x": "8"}])
    assert _numeros(filas, "d") == [None, None, 3.0, 6.0]


def test_lag_simple_queda_bloqueado_por_la_escritura(tmp_path):  # decisión 5 (B-13, orden de escritura)
    # El `tJavaRow` de LAG existe (desde_plan_lag.py), pero la escritura de WORK.r se emite antes que el
    # LAG y no ve sus columnas: P-ESCRITURA-SIN-COLUMNAS, y ese pendiente impide escribir el Job (decisión 5).
    # Se deja así hasta resolver el orden sin cambiar la posición de los componentes de los Jobs existentes.
    programa = tmp_path / "p.sas"
    programa.write_text(
        ENTRADA
        + "DATA WORK.r;\n  SET WORK.t;\n  prev = LAG(x);\nRUN;\n"
        + "PROC EXPORT DATA=WORK.r OUTFILE=\'r.csv\' DBMS=CSV REPLACE;\nRUN;\n",
        encoding="utf-8",
    )
    muestra = tmp_path / "m"
    muestra.mkdir()
    (muestra / "t.csv").write_text("id,x\n1,2\n2,3\n", encoding="utf-8")
    resultado = migrar(programa, tmp_path / "salida", muestra=muestra)
    assert resultado.jobs == []
    assert "P-ESCRITURA-SIN-COLUMNAS" in {p.codigo for p in resultado.pendientes}


@pytest.mark.parametrize("sentencia", ["  prev = LAG(x) + 1;\n", "  prev = LAG(x) + DIF(x);\n"])
def test_lag_anidado_no_se_ignora(sentencia):  # no se traduce: la expresión mezcla LAG con otra cosa
    with pytest.raises(NoSoportadoEnInterprete):
        _correr(sentencia, [{"x": "2"}, {"x": "3"}])


def test_lag_no_verificado_sigue_sin_job(tmp_path):  # decisión 5: la forma compuesta no tiene emisor
    programa = tmp_path / "p.sas"
    programa.write_text(
        ENTRADA
        + "DATA WORK.r;\n  SET WORK.t;\n  prev = LAG(x) + 1;\nRUN;\n"
        + "PROC EXPORT DATA=WORK.r OUTFILE='r.csv' DBMS=CSV REPLACE;\nRUN;\n",
        encoding="utf-8",
    )
    muestra = tmp_path / "m"
    muestra.mkdir()
    (muestra / "t.csv").write_text("id,x\n1,2\n2,3\n", encoding="utf-8")
    assert migrar(programa, tmp_path / "salida", muestra=muestra).jobs == []
