"""B-21: `FIND` de un objeto hash como `unir` izquierdo con la tabla de búsqueda (decisión 6 del dueño).

Reglas de `lrcon`: una llave repetida en la carga conserva la primera observación (p. 632); `FIND` devuelve 0
si encuentra la llave y distinto de 0 si no (pp. 633-634). `rc` solo se traduce en comparaciones con 0, y
con la columna `rc` eliminada: si sobrevive, sale en la salida y queda pendiente.
"""

from __future__ import annotations

from sgm.cli_migrar import migrar
from sgm.compile import compile_file, project_base
from sgm.frontend.program import analyze_program
from sgm.migrar.interprete import ejecutar_plan

PRINCIPIO = (
    "PROC IMPORT DATAFILE='.../t.csv' OUT=WORK.t DBMS=CSV REPLACE;\n  GETNAMES=YES;\nRUN;\n"
    "PROC IMPORT DATAFILE='.../b.csv' OUT=WORK.b DBMS=CSV REPLACE;\n  GETNAMES=YES;\nRUN;\n"
)
CUERPO_BUSQUEDA = (
    "DATA WORK.r;\n  SET WORK.t;\n"
    "  DECLARE HASH h(DATASET: 'work.b');\n"
    "  h.DEFINEKEY('k');\n  h.DEFINEDATA('v');\n  h.DEFINEDONE();\n"
    "  rc = h.FIND();\n"
    "  IF rc = 0 THEN encontrado = 'si';\n  ELSE encontrado = 'no';\n"
    "  DROP rc;\nRUN;\n"
)


def _plan(texto: str):
    return compile_file(analyze_program({"p.sas": texto}), "p.sas", project_base()).plan


def test_busqueda_con_llave_repetida_conserva_la_primera_y_marca_coincidencia():
    # t: (id, k). b: (k, v) con la llave 1 repetida: gana la primera, 'a' (lrcon, p. 632).
    plan = _plan(PRINCIPIO + CUERPO_BUSQUEDA)
    salida = ejecutar_plan(
        plan,
        {
            "t": [{"id": "1", "k": "1"}, {"id": "2", "k": "2"}, {"id": "3", "k": "9"}],
            "b": [{"k": "1", "v": "a"}, {"k": "1", "v": "b"}, {"k": "2", "v": "c"}],
        },
    )["r"]
    filas = [{k.lower(): v for k, v in f.items()} for f in salida]
    assert [f["id"] for f in filas] == ["1", "2", "3"]
    assert [f["v"] for f in filas] == ["a", "c", None]
    assert [f["encontrado"] for f in filas] == ["si", "si", "no"]
    assert all("rc" not in f and "_hit_" not in f for f in filas)


def test_rc_fuera_de_una_comparacion_con_cero_queda_pendiente_y_sin_job(tmp_path):
    texto = CUERPO_BUSQUEDA.replace("IF rc = 0 THEN encontrado = 'si';", "encontrado = rc;")
    programa = tmp_path / "p.sas"
    programa.write_text(PRINCIPIO + texto + "PROC EXPORT DATA=WORK.r OUTFILE='r.csv' DBMS=CSV REPLACE;\nRUN;\n",
                        encoding="utf-8")
    muestra = tmp_path / "m"
    muestra.mkdir()
    (muestra / "t.csv").write_text("id,k\n1,1\n", encoding="utf-8")
    (muestra / "b.csv").write_text("k,v\n1,a\n", encoding="utf-8")
    resultado = migrar(programa, tmp_path / "salida", muestra=muestra)
    assert resultado.jobs == []
    assert "P-HASH-RC-SIN-SOPORTE" in {p.codigo for p in resultado.pendientes}
