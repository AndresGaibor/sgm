"""Fase 5.1 de `docs/automatizacion/03-plan-produccion.md`: invariantes de producción.

Determinismo del plan, etiqueta de versión en lo que se escribe y ausencia de secretos en
cualquier salida.
"""

from __future__ import annotations

import json

from sgm.compile import compile_project
from sgm.emit.guide_md import render_guide
from sgm.emit.plan_json import metadatos_de_salida, plan_to_dict

PROGRAMA = (
    "proc sql;\n"
    "connect to impala (dsn=IMPALA user=ana password='secreto-123');\n"
    "create table work.x as select * from connection to impala (select 1 from t);\n"
    "quit;\n"
    "data work.a1; set work.s1; x = 1; y = x + 2; z = y * 3; run;\n"
    "data work.a2; set work.s2; x = 1; y = x + 2; z = y * 3; run;\n"
)


def _salidas() -> tuple[str, str]:
    compilados, _ = compile_project({"p.sas": PROGRAMA})
    plan = compilados["p.sas"].plan
    return json.dumps(plan_to_dict(plan), sort_keys=True), render_guide(plan)


def test_mismo_programa_mismo_plan_byte_a_byte() -> None:
    primera, _ = _salidas()
    segunda, _ = _salidas()
    assert primera == segunda


def test_metadatos_con_version_y_hash_de_reglas() -> None:
    meta = metadatos_de_salida()
    assert meta["sgm_version"]
    assert len(meta["ruleset_hash"]) == 64


def test_ningun_secreto_en_plan_ni_guia() -> None:
    plan, guia = _salidas()
    assert "secreto-123" not in plan
    assert "secreto-123" not in guia


def test_archivo_grande_compila_dentro_del_limite() -> None:
    """Límite de rendimiento (5.4): el archivo de referencia compila en menos de 120 s."""
    import time
    from pathlib import Path

    ruta = Path(__file__).resolve().parents[1] / "fixtures" / "sas" / "client" / "client_large.sas"
    texto = ruta.read_text(encoding="utf-8-sig", errors="replace")
    inicio = time.time()
    compile_project({ruta.name: texto})
    assert time.time() - inicio < 120


def test_compilar_entradas_hostiles_no_lanza_excepciones() -> None:
    """Corpus hostil (5.3): ningún contenido de archivo debe hacer caer la compilación."""
    casos = {
        "vacio.sas": "",
        "sin_cerrar.sas": "%macro a;\ndata work.x;\nset work.y;\n",
        "comillas.sas": "proc sql;\nconnect to x (password='abc);\nquit;\n",
        "binario.sas": "\x00\x01 data \xff\xfe run;",
        "macro_circular.sas": "%macro a; %a; %mend a;\n%a;\n",
        "solo_comentario.sas": "/* nada */\n",
    }
    compilados, _ = compile_project(casos)
    assert set(compilados) == set(casos)
