"""Regresiones de atribución y diagnóstico de propuestas de esquema."""

from typer.testing import CliRunner

from sgm.cli import app
from sgm.migrar.esquemas_programa import a_json, esquemas_desde_programa, tablas_base_del_programa


def test_tipo_numerico_de_una_importacion_no_contamina_otra():
    text = """
    proc import datafile='a.csv' out=work.a dbms=dlm; getnames=yes; run;
    proc import datafile='b.csv' out=work.b dbms=dlm; getnames=yes; run;
    data work.x; set work.a; y = amount * 2; run;
    proc sql; select b.amount from work.b b; quit;
    """
    schemas, pending = esquemas_desde_programa(text)
    a = next(c for c in schemas["work.a"] if c.name.lower() == "amount")
    b = next(c for c in schemas["work.b"] if c.name.lower() == "amount")
    assert a.type == "Double"
    assert b.type == "String" and b.source == "unknown"
    assert a_json(schemas, "p")["work"]["tables"]["b"][0]["type"] is None
    assert any(p.codigo == "P-TIPO-DESCONOCIDO" and "work.b" in p.mensaje for p in pending)


def test_copia_sobrescrita_no_atribuye_columnas_de_version_posterior():
    text = """
    data work.c; set lib.t; run;
    data work.c; set lib.u; run;
    proc sql; select c.x from work.c c; quit;
    """
    sources = tablas_base_del_programa(text)
    assert "x" not in [c.lower() for c in sources.get("lib.t", [])]
    assert [c.lower() for c in sources["lib.u"]] == ["x"]


def test_cli_muestra_motivos_de_tabla_dinamica_y_copia_transformada(tmp_path):
    source = tmp_path / "p.sas"
    source.write_text(
        """
        data work.c; set lib.t; keep a; run;
        proc sql; select c.a from work.c c; select a from &lib..t; quit;
    """,
        encoding="utf-8",
    )
    result = CliRunner().invoke(
        app, ["esquemas", "--desde-programa", str(source), "--salida", str(tmp_path / "out")]
    )
    assert result.exit_code == 0, result.output
    assert "P-TABLA-DINAMICA" in result.output and "&lib..t" in result.output
    assert "P-COLUMNAS-NO-ATRIBUIDAS" in result.output and "lib.t" in result.output.lower()
