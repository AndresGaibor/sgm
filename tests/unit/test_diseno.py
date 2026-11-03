"""Comando `sgm diseno`: el diseño de Jobs sale como JSON real, sin secretos."""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from sgm.cli import app

PROGRAMA = """%let server = anfitrion01 7551;
options remote=server comamid=tcp;
proc pwencode in='clave-del-programa';
run;
data work.entrada; set work.fuente; run;
%macro bloque;
data work.ventas_a; set work.ventas_a_origen; run;
%mend bloque;
%macro bloque;
data work.ventas_b; set work.ventas_b_origen; run;
%mend bloque;
"""


def _correr(tmp_path: Path, extra: list[str] | None = None) -> tuple[dict, str, int]:
    fuente = tmp_path / "programa.sas"
    fuente.write_text(PROGRAMA, encoding="utf-8")
    salida = tmp_path / "out"
    args = ["diseno", str(fuente), "--out", str(salida), *(extra or [])]
    resultado = CliRunner().invoke(app, args)
    archivo = salida / "programa.diseno.json"
    texto = archivo.read_text(encoding="utf-8") if archivo.exists() else ""
    return (json.loads(texto) if texto else {}), texto, resultado.exit_code


def test_diseno_escribe_joblets_contexto_y_job_padre(tmp_path: Path) -> None:
    diseno, _, codigo = _correr(tmp_path)
    assert codigo == 0
    assert diseno["programa"] == "programa.sas"
    assert diseno["contexto"]["id"] == "jl_contexto"
    assert diseno["job_padre"]["joblet_de_contexto"] == "jl_contexto"
    assert diseno["job_padre"]["nodos"] == (
        len(diseno["job_padre"]["llamadas"])
        + 1
        + diseno["job_padre"]["componentes_del_encabezado"]
        + diseno["job_padre"]["componentes_sueltos"]
    )
    assert diseno["regiones"] == 2


DECLARACION = """region_marcador: '/\\* seccion'
productos:
  - nombre: ventas
    sufijos: [UNO]
  - nombre: compras
    sufijos: [DOS]
"""

PROGRAMA_POR_SUFIJO = """data work.entrada; set work.fuente; run;
/* seccion 1 */
data work.a1; set work.pagos_uno; x = 1; run;
/* seccion 2 */
data work.a2; set work.otros_uno; x = 2; z = 1; run;
/* seccion 3 */
data work.b1; set work.cobros_dos; x = 3; z = 2; w = 1; run;
/* seccion 4 */
data work.b2; set work.moras_dos; x = 4; z = 3; w = 2; v = 1; run;
/* seccion 5 */
data work.c1; set work.generica; x = 5; z = 4; w = 3; v = 2; u = 1; run;
"""


def test_diseno_usa_la_agrupacion_declarada_y_deja_la_suelta(tmp_path: Path) -> None:
    """La agrupación declarada junto al programa decide los joblets; sin producto queda suelta."""
    fuente = tmp_path / "programa.sas"
    fuente.write_text(PROGRAMA_POR_SUFIJO, encoding="utf-8")
    (tmp_path / "programa.agrupacion.yaml").write_text(DECLARACION, encoding="utf-8")
    salida = tmp_path / "out"
    resultado = CliRunner().invoke(app, ["diseno", str(fuente), "--out", str(salida)])
    assert resultado.exit_code == 0, resultado.output
    diseno = json.loads((salida / "programa.diseno.json").read_text(encoding="utf-8"))
    assert diseno["agrupacion"] == {"modo": "declarada", "productos": ["ventas", "compras"]}
    assert [j["regiones"] for j in diseno["joblets"]] == [[0, 1], [2, 3]]
    assert diseno["job_padre"]["componentes_sueltos"] == 1


def test_diseno_no_escribe_la_contrasena_en_claro(tmp_path: Path) -> None:
    _, texto, codigo = _correr(tmp_path)
    assert codigo == 0
    assert "clave-del-programa" not in texto
    credencial = next(v for v in json.loads(texto)["contexto"]["variables"] if v["nombre"] == "credencial")
    assert credencial["valor"] == "***"
