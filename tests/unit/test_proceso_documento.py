"""Tests del documento de diseño: render a Markdown y comando `sgm proceso`."""

from __future__ import annotations

from typer.testing import CliRunner

from sgm.cli import app
from sgm.proceso.diseno_doc import DocumentoDiseno
from sgm.proceso.render_md import render_markdown

AGRUPACION = """\
region_marcador: "%macro ambiente"
productos:
  - {nombre: a, sufijos: [AAA]}
  - {nombre: b, sufijos: [BBB]}
"""

DISENO = r"""
etapas:
  - {nombre: cargar, patrones: ["^carga"]}
fuentes:
  - {clave: Lookup, busca: 'lk\.xlsx$', ubicacion: 'ruta + lk', uso: 'Busca'}
salidas:
  - {clave: reporte, creado_en: job_x, contenido: Reporte, equivalente_busca: '^REP'}
"""

PROGRAMA = """\
%macro ambiente;
%mend;
proc import datafile="/in/lk.xlsx" out=work.lk dbms=xlsx replace; run;
/* Etiqueta: carga inicial */
data work.t_AAA; set work.lk; run;
%put listo;
%macro ambiente;
%mend;
/* Etiqueta: otra cosa */
data work.t_BBB; set work.lk; run;
proc export data=work.t_AAA outfile="/out/REP_AAA.csv" dbms=csv replace; run;
"""


def test_render_incluye_resumen_secciones_y_pendientes():
    doc = DocumentoDiseno(
        "p.sas",
        {"1.1": {"Lookup | x": {"tipo": "Excel", "estado": "ok"}}},
        [("algo", "porque sí")],
        {"regiones": 2},
    )
    md = render_markdown(doc)
    assert "# Diseño deducido de `p.sas`" in md
    assert "| Regiones | 2 |" in md
    assert "## 1.1. Fuentes externas" in md
    assert r"Lookup \| x" in md  # la barra vertical se escapa
    assert "| algo | porque sí |" in md


def test_render_sin_filas_ni_pendientes_lo_dice():
    md = render_markdown(DocumentoDiseno("p.sas", {"6": {}}, []))
    assert "_Sin filas._" in md and "_Sin pendientes._" in md


def test_comando_proceso_escribe_el_documento(tmp_path):
    (tmp_path / "p.sas").write_text(PROGRAMA, encoding="utf-8")
    (tmp_path / "a.yaml").write_text(AGRUPACION, encoding="utf-8")
    (tmp_path / "d.yaml").write_text(DISENO, encoding="utf-8")
    resultado = CliRunner().invoke(
        app,
        [
            "proceso", str(tmp_path / "p.sas"),
            "--out", str(tmp_path / "out"),
            "--agrupacion", str(tmp_path / "a.yaml"),
            "--diseno", str(tmp_path / "d.yaml"),
        ],
    )  # fmt: skip
    assert resultado.exit_code == 0, resultado.output
    md = (tmp_path / "out" / "p.diseno.md").read_text(encoding="utf-8")
    assert "| Lookup | Excel | ruta + lk | Busca | Ruta confirmada en SAS |" in md
    assert "REP_AAA.csv" in md
    assert "| Etiquetas con etapa asignada | 1 |" in md


def test_comando_proceso_sin_decisiones_falla_con_mensaje(tmp_path):
    (tmp_path / "zz_inexistente.sas").write_text("data a; run;\n", encoding="utf-8")
    resultado = CliRunner().invoke(app, ["proceso", str(tmp_path / "zz_inexistente.sas")])
    assert resultado.exit_code != 0
