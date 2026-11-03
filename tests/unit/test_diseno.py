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


def _correr(tmp_path: Path) -> tuple[dict, str, int]:
    fuente = tmp_path / "programa.sas"
    fuente.write_text(PROGRAMA, encoding="utf-8")
    salida = tmp_path / "out"
    resultado = CliRunner().invoke(app, ["diseno", str(fuente), "--out", str(salida)])
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


def test_diseno_no_escribe_la_contrasena_en_claro(tmp_path: Path) -> None:
    _, texto, codigo = _correr(tmp_path)
    assert codigo == 0
    assert "clave-del-programa" not in texto
    credencial = next(v for v in json.loads(texto)["contexto"]["variables"] if v["nombre"] == "credencial")
    assert credencial["valor"] == "***"
