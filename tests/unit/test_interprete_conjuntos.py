"""EXCEPT e INTERSECT en el intérprete del anillo B (plan C, tarea C-10). Reglas de sqlproc, pp. 129 a 134."""

from __future__ import annotations

from sgm.cli_migrar import ResultadoMigrar, _plan
from sgm.migrar.interprete import ejecutar_plan
from sgm.migrar.interprete_conjuntos import conjunto

A = [{"id": "1"}, {"id": "2"}, {"id": "3"}]
B = [{"id": "2"}, {"id": "3"}, {"id": "4"}]


def _ids(filas: list[dict]) -> list[str]:
    return [fila["id"] for fila in filas]


def test_intersect_deja_las_filas_presentes_en_las_dos_ramas():
    assert _ids(conjunto("intersect", [A, B])) == ["2", "3"]


def test_except_deja_las_filas_de_la_primera_que_no_estan_en_la_segunda():
    assert _ids(conjunto("except", [A, B])) == ["1"]


def test_los_repetidos_se_quitan_y_el_faltante_casa_con_otro_faltante():
    izquierda = [{"k": None}, {"k": None}, {"k": "x"}]
    derecha = [{"k": None}]

    assert [f["k"] for f in conjunto("intersect", [izquierda, derecha])] == [None]
    assert [f["k"] for f in conjunto("except", [izquierda, derecha])] == ["x"]


def test_la_sentencia_completa_se_ejecuta_en_el_plan(tmp_path):
    programa = (
        "PROC SQL;\n"
        "  CREATE TABLE WORK.i AS SELECT id FROM WORK.A INTERSECT SELECT id FROM WORK.B;\n"
        "  CREATE TABLE WORK.e AS SELECT id FROM WORK.A EXCEPT SELECT id FROM WORK.B;\n"
        "QUIT;\n"
    )
    plan = _plan(programa, "programa", ResultadoMigrar(carpeta=tmp_path))

    resultado = ejecutar_plan(plan, {"a": [dict(f) for f in A], "b": [dict(f) for f in B]})

    assert _ids(resultado["i"]) == ["2", "3"]
    assert _ids(resultado["e"]) == ["1"]
