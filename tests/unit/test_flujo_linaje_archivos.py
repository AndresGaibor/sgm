"""Linaje de archivos externos en `sgm flujo`: PROC APPEND, IMPORT, EXPORT y DATA step con FILE/INFILE."""

from __future__ import annotations

from sgm.flow.model import build_flows


def _flow(texto: str, nombre: str = "p.sas"):
    return build_flows({nombre: texto})[nombre]


def _pares(flujo) -> set[tuple[str, str, str]]:
    return {(e.source, e.target, e.dataset) for e in flujo.edges}


def test_proc_append_lee_data_y_base_y_escribe_base():
    texto = (
        "data base; set origen; run;\n"
        "data nuevos; set origen2; run;\n"
        "proc append base=base data=nuevos; run;\n"
        "proc print data=base; run;\n"
    )
    flujo = _flow(texto)
    append = flujo.steps[2]
    assert append.type_name == "PROC APPEND"
    assert append.reads == ["nuevos", "base"]
    assert append.writes == ["base"]
    pares = _pares(flujo)
    assert ("p1", "p3", "base") in pares
    assert ("p2", "p3", "nuevos") in pares
    assert ("p3", "p4", "base") in pares


def test_proc_append_sin_base_previa_deja_base_como_entrada_externa():
    flujo = _flow("proc append base=base data=nuevos; run;\n")
    assert flujo.external_inputs == ["nuevos", "base"]


def test_proc_import_lee_el_archivo_con_espacios_en_la_ruta():
    texto = (
        "proc import datafile='C:\\datos\\mi archivo.csv' out=t dbms=csv replace; run;\n"
        "proc print data=t; run;\n"
    )
    flujo = _flow(texto)
    imp = flujo.steps[0]
    assert imp.reads == ["file:C:\\datos\\mi archivo.csv"]
    assert imp.writes == ["t"]
    assert flujo.external_inputs == ["file:C:\\datos\\mi archivo.csv"]
    assert ("p1", "p2", "t") in _pares(flujo)


def test_proc_export_escribe_el_archivo_y_un_paso_posterior_lo_lee():
    texto = (
        "data t; set origen; run;\n"
        'proc export data=t outfile="C:\\salida\\a b.csv" dbms=csv; run;\n'
        "data z; infile 'C:\\salida\\a b.csv' dlm=','; input x; run;\n"
    )
    flujo = _flow(texto)
    exp = flujo.steps[1]
    assert exp.reads == ["t"]
    assert exp.writes == ["file:C:\\salida\\a b.csv"]
    assert ("p2", "p3", "file:C:\\salida\\a b.csv") in _pares(flujo)
    assert flujo.external_inputs == ["origen"]


def test_infile_sin_escritor_previo_es_entrada_externa():
    flujo = _flow("data a; infile 'C:\\in\\f.txt' dlm=','; input x; run;\n")
    assert flujo.steps[0].reads == ["file:C:\\in\\f.txt"]
    assert flujo.external_inputs == ["file:C:\\in\\f.txt"]


def test_file_escribe_el_archivo_y_otro_paso_lo_lee_sin_entrada_externa():
    texto = (
        "data _null_; set origen; file 'C:\\out\\g.txt'; put x; run;\n"
        "data h; infile 'C:\\out\\g.txt'; input x; run;\n"
    )
    flujo = _flow(texto)
    assert flujo.steps[0].writes == ["_null_", "file:C:\\out\\g.txt"]
    assert ("p1", "p2", "file:C:\\out\\g.txt") in _pares(flujo)
    assert flujo.external_inputs == ["origen"]


def test_file_log_print_e_infile_datalines_no_son_rutas():
    texto = (
        "data b; set origen; file log; put 'hola'; run;\n"
        "data c; set origen; file print; put x; run;\n"
        "data d; infile datalines; input x;\ndatalines;\n1\n;\nrun;\n"
    )
    flujo = _flow(texto)
    assert flujo.steps[0].writes == ["b"]
    assert flujo.steps[1].writes == ["c"]
    assert flujo.steps[2].reads == []
    assert not any(k.startswith("file:") for k in flujo.external_inputs)
