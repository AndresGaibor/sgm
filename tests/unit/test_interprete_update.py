"""B-19: `UPDATE` con la semántica de `lrcon` (pp. 604 a 609) y `MODIFY` como pendiente.

Los valores esperados son los de las salidas de lrcon, Output 23.14 a 23.16 (pp. 607 a 610). Un faltante
del CSV es cadena vacía, como en la entrada del traductor.
"""

from __future__ import annotations

import pytest

from sgm.cli_migrar import migrar
from sgm.compile import compile_file, project_base
from sgm.frontend.program import analyze_program
from sgm.migrar.interprete import NoSoportadoEnInterprete, ejecutar_plan
from sgm.migrar.interprete_update import _actualizar

MASTER = [
    {"common": "a", "animal": "Ant", "plant": "Apple"},
    {"common": "b", "animal": "Bird", "plant": "Banana"},
    {"common": "c", "animal": "Cat", "plant": "Coconut"},
    {"common": "d", "animal": "Dog", "plant": "Dewberry"},
    {"common": "e", "animal": "Eagle", "plant": "Eggplant"},
    {"common": "f", "animal": "Frog", "plant": "Fig"},
]
NEWPLANT = [
    {"common": "a", "plant": "Apricot"},
    {"common": "b", "plant": "Barley"},
    {"common": "c", "plant": "Cactus"},
    {"common": "d", "plant": "Date"},
    {"common": "e", "plant": "Escarole"},
    {"common": "f", "plant": "Fennel"},
]


def _plantas(filas: list[dict]) -> list[tuple]:
    return [(f["common"], f["animal"], f["plant"]) for f in filas]


def test_ejemplo_1_la_transaccion_cambia_la_planta():  # lrcon, Output 23.14 (p. 607)
    filas = _actualizar([MASTER, NEWPLANT], {"by": ["common"]})
    assert _plantas(filas) == [
        ("a", "Ant", "Apricot"),
        ("b", "Bird", "Barley"),
        ("c", "Cat", "Cactus"),
        ("d", "Dog", "Date"),
        ("e", "Eagle", "Escarole"),
        ("f", "Frog", "Fennel"),
    ]


def test_ejemplo_2_maestro_repetido_actualiza_solo_el_primero_y_transacciones_en_orden():
    # lrcon, Output 23.15 (p. 609): dos transacciones de la llave d, la última gana; el segundo b del
    # maestro sale sin tocar.
    maestro = [
        {"common": "a", "animal1": "Ant", "plant1": "Apple"},
        {"common": "b", "animal1": "Bird", "plant1": "Banana"},
        {"common": "b", "animal1": "Bird", "plant1": "Banana"},
        {"common": "c", "animal1": "Cat", "plant1": "Coconut"},
        {"common": "d", "animal1": "Dog", "plant1": "Dewberry"},
        {"common": "e", "animal1": "Eagle", "plant1": "Eggplant"},
        {"common": "f", "animal1": "Frog", "plant1": "Fig"},
    ]
    dup = [
        {"common": "a", "plant1": "Apricot"},
        {"common": "b", "plant1": "Barley"},
        {"common": "c", "plant1": "Cactus"},
        {"common": "d", "plant1": "Date"},
        {"common": "d", "plant1": "Dill"},
        {"common": "e", "plant1": "Escarole"},
        {"common": "f", "plant1": "Fennel"},
    ]
    filas = _actualizar([maestro, dup], {"by": ["common"]})
    assert [f["plant1"] for f in filas] == [
        "Apricot", "Barley", "Banana", "Cactus", "Dill", "Escarole", "Fennel",
    ]
    assert len(filas) == 7


def test_ejemplo_3_faltante_no_sobrescribe_agrega_llaves_y_variables_nuevas():
    # lrcon, Output 23.16 (p. 610): Plant2 de e no cambia a faltante; b y g son observaciones nuevas;
    # d sale sin cambio; Mineral es nueva y queda faltante donde la transacción no la trae.
    maestro = [
        {"common": "a", "animal2": "Ant", "plant2": ""},
        {"common": "c", "animal2": "Cat", "plant2": "Coconut"},
        {"common": "d", "animal2": "Dog", "plant2": "Dewberry"},
        {"common": "e", "animal2": "Eagle", "plant2": "Eggplant"},
        {"common": "f", "animal2": "Frog", "plant2": "Fig"},
    ]
    nonplant = [
        {"common": "a", "plant2": "Apricot", "mineral": "Amethyst"},
        {"common": "b", "plant2": "Barley", "mineral": "Beryl"},
        {"common": "c", "plant2": "Cactus", "mineral": ""},
        {"common": "e", "plant2": "", "mineral": ""},
        {"common": "f", "plant2": "Fennel", "mineral": ""},
        {"common": "g", "plant2": "Grape", "mineral": "Garnet"},
    ]
    filas = _actualizar([maestro, nonplant], {"by": ["common"]})
    assert [(f["common"], f["plant2"], f["mineral"]) for f in filas] == [
        ("a", "Apricot", "Amethyst"),
        ("b", "Barley", "Beryl"),
        ("c", "Cactus", None),
        ("d", "Dewberry", None),
        ("e", "Eggplant", None),
        ("f", "Fennel", None),
        ("g", "Grape", "Garnet"),
    ]


def test_maestro_sin_transaccion_sale_sin_cambios():  # lrcon, p. 604
    filas = _actualizar([MASTER[:1], []], {"by": ["common"]})
    assert _plantas(filas) == [("a", "Ant", "Apple")]


def test_entrada_desordenada_no_se_ordena_sola():  # lrcon, p. 605 (requisito de orden)
    with pytest.raises(NoSoportadoEnInterprete, match="no ordenada por BY"):
        _actualizar([MASTER[::-1], NEWPLANT], {"by": ["common"]})


def test_updatemode_no_se_interpreta_como_el_caso_normal():  # lrcon, p. 610 (P-UPDATEMODE)
    with pytest.raises(NoSoportadoEnInterprete, match="UPDATEMODE"):
        _actualizar([MASTER, NEWPLANT], {"by": ["common"], "updatemode": True})


def _plan(cuerpo: str):
    texto = (
        "PROC IMPORT DATAFILE='.../master.csv' OUT=WORK.master DBMS=CSV REPLACE;\n  GETNAMES=YES;\nRUN;\n"
        "PROC IMPORT DATAFILE='.../trans.csv' OUT=WORK.trans DBMS=CSV REPLACE;\n  GETNAMES=YES;\nRUN;\n"
        "DATA WORK.r;\n" + cuerpo + "RUN;\n"
    )
    return compile_file(analyze_program({"p.sas": texto}), "p.sas", project_base()).plan


def test_el_plan_ejecuta_update_con_su_by():  # lrcon, p. 604 (ejemplo 1 desde un programa SAS)
    plan = _plan("  UPDATE WORK.master WORK.trans;\n  BY common;\n")
    salida = ejecutar_plan(plan, {"master": MASTER, "trans": NEWPLANT})["r"]
    filas = [{k.lower(): v for k, v in f.items()} for f in salida]
    assert [f["plant"] for f in filas] == ["Apricot", "Barley", "Cactus", "Date", "Escarole", "Fennel"]


def test_update_sin_emisor_no_sale_como_job_y_reporta_su_codigo(tmp_path):  # decisión 5 (B-19)
    programa = tmp_path / "p.sas"
    programa.write_text(
        "PROC IMPORT DATAFILE='.../master.csv' OUT=WORK.master DBMS=CSV REPLACE;\n  GETNAMES=YES;\nRUN;\n"
        "PROC IMPORT DATAFILE='.../trans.csv' OUT=WORK.trans DBMS=CSV REPLACE;\n  GETNAMES=YES;\nRUN;\n"
        "DATA WORK.r;\n  UPDATE WORK.master WORK.trans;\n  BY common;\nRUN;\n"
        "PROC EXPORT DATA=WORK.r OUTFILE='r.csv' DBMS=CSV REPLACE;\nRUN;\n",
        encoding="utf-8",
    )
    muestra = tmp_path / "m"
    muestra.mkdir()
    (muestra / "master.csv").write_text("common,animal,plant\na,Ant,Apple\n", encoding="utf-8")
    (muestra / "trans.csv").write_text("common,plant\na,Apricot\n", encoding="utf-8")
    resultado = migrar(programa, tmp_path / "salida", muestra=muestra)
    assert resultado.jobs == []
    assert "P-UPDATE-SIN-EMISOR" in {p.codigo for p in resultado.pendientes}


def test_modify_es_pendiente_sin_nodo(tmp_path):  # lestmtsref, p. 252 (P-MODIFY-EN-SITIO)
    programa = tmp_path / "p.sas"
    programa.write_text(
        "PROC IMPORT DATAFILE='.../master.csv' OUT=WORK.master DBMS=CSV REPLACE;\n  GETNAMES=YES;\nRUN;\n"
        "DATA WORK.master;\n  MODIFY WORK.master;\n  plant = 'X';\nRUN;\n"
        "PROC EXPORT DATA=WORK.master OUTFILE='m.csv' DBMS=CSV REPLACE;\nRUN;\n",
        encoding="utf-8",
    )
    muestra = tmp_path / "m"
    muestra.mkdir()
    (muestra / "master.csv").write_text("common,plant\na,Apple\n", encoding="utf-8")
    resultado = migrar(programa, tmp_path / "salida", muestra=muestra)
    assert resultado.jobs == []
    assert "P-MODIFY-EN-SITIO" in {p.codigo for p in resultado.pendientes}
