"""Resolución de FILENAME hacia rutas y diagnósticos seguros."""

from pathlib import Path

from sgm.compile import compile_file, project_base
from sgm.emit.plan_json import plan_to_dict
from sgm.frontend.program import analyze_program
from sgm.frontend.steps_tipos import Filename
from sgm.ir.pase_filerefs import filerefs_de_programa
from sgm.migrar.preparar_plan import preparar_plan
from sgm.talend_item.desde_plan_contextos import contextos_de_plan


def _analizar(programa: str):
    return analyze_program({"programa.sas": programa})


def _plan(programa: str):
    analisis = _analizar(programa)
    return analisis, compile_file(analisis, "programa.sas", project_base()).plan


def test_filename_se_conserva_en_el_plan_y_redacta_el_comando():
    _, plan = _plan("FILENAME cmd PIPE 'echo --password supersecreto';")

    (declaracion,) = [
        operador
        for operador in plan.graph.operators()
        if operador.params.get("reason") == "CONFIGURACION"
        and "FILENAME" in operador.params.get("statement", "").upper()
    ]

    assert declaracion.status == "reemplazado"
    assert "supersecreto" not in repr(plan_to_dict(plan))


def test_filename_y_clear_conservan_solo_la_declaracion_activa_y_redactan_secretos():
    analisis = _analizar(
        "FILENAME temporal 'antes.csv';\n"
        "FILENAME remoto PIPE 'echo --password supersecreto';\n"
        "FILENAME temporal 'despues.csv';\n"
        "FILENAME TEMPORAL CLEAR;\n"
    )

    declaracion = next(item.item for item in analisis.items if isinstance(item.item, Filename))
    assert declaracion.name == "temporal"

    filerefs = filerefs_de_programa(analisis.items)

    assert set(filerefs) == {"remoto"}
    assert filerefs["remoto"].metodo == "pipe"
    assert "supersecreto" not in repr(filerefs["remoto"])
    assert "--password ***" in filerefs["remoto"].destino


def test_filerefs_resuelven_lectura_escritura_y_contextos(tmp_path: Path):
    programa = """FILENAME entrada '.../entradas/lista.csv';
FILENAME salida '.../salida/copia.csv';
DATA WORK.lista;
  INFILE entrada DLM=',' DSD FIRSTOBS=2;
  INPUT codigo :$4. cantidad :8.;
RUN;
DATA _NULL_;
  SET WORK.lista;
  FILE salida DSD;
  PUT codigo cantidad;
RUN;
"""
    analisis, plan = _plan(programa)

    plan, pendientes = preparar_plan(plan, texto=programa, items=analisis.items)

    assert pendientes == []
    lectura = next(op for op in plan.graph.operators() if op.kind == "read_file")
    escritura = next(op for op in plan.graph.operators() if op.kind == "write_file")
    assert lectura.params["datafile"] == "'.../entradas/lista.csv'"
    assert escritura.params["outfile"] == "'.../salida/copia.csv'"
    assert "fileref" not in lectura.params and "fileref" not in escritura.params

    default = {item.nombre: item.valor for item in contextos_de_plan(plan)["Default"]}
    assert default["ruta_lista"] == ".../entradas/lista.csv"
    assert default["ruta_lista_2"] == ".../salida/copia.csv"


def test_proc_import_resuelve_datafile_que_nombra_un_fileref():
    programa = """FILENAME entrada '.../entradas/lista.csv';
PROC IMPORT DATAFILE=entrada OUT=WORK.lista DBMS=CSV;
  GETNAMES=YES;
RUN;
"""
    analisis, plan = _plan(programa)
    operador = next(op for op in plan.graph.operators() if op.kind == "read_file")

    assert operador.params["fileref"] == "entrada"
    plan, pendientes = preparar_plan(plan, texto=programa, items=analisis.items)

    assert pendientes == []
    assert operador.params["datafile"] == "'.../entradas/lista.csv'"
    assert "fileref" not in operador.params


def test_referencia_sin_declaracion_filename_queda_pendiente():
    programa = "DATA WORK.lista; INFILE ausente; INPUT codigo $; RUN;"
    analisis, plan = _plan(programa)

    _, pendientes = preparar_plan(plan, texto=programa, items=analisis.items)

    assert [(item.codigo, item.linea) for item in pendientes] == [
        ("P-FILEREF-SIN-DEFINIR", 1)
    ]


def test_pipe_no_se_ejecuta_y_no_publica_job_parcial(tmp_path: Path):
    from sgm.cli_migrar import migrar

    source = tmp_path / "programa.sas"
    source.write_text(
        "FILENAME origen PIPE 'echo --password supersecreto';\n"
        "DATA WORK.datos; INFILE origen; INPUT valor $; RUN;\n",
        encoding="utf-8",
    )

    resultado = migrar(source, tmp_path / "out")

    assert "P-FILENAME-PIPE" in {item.codigo for item in resultado.pendientes}
    assert not any(
        item.codigo == "P-OPERADOR-SIN-SOPORTE" and item.linea == 1
        for item in resultado.pendientes
    )
    assert resultado.jobs == []
    assert list((tmp_path / "out").rglob("*.item")) == []
    informe = "\n".join(item.mensaje for item in resultado.pendientes)
    assert "supersecreto" not in informe
    assert "echo" in informe
