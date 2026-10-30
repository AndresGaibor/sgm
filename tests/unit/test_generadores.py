"""Generadores (F1.6): `case new --from-gap` y `rules new --from-gap` producen archivos que validan."""

import shutil
from pathlib import Path

import pytest
import yaml

from sgm import generadores, rules_validate
from sgm.compile import compile_project
from sgm.store import gaps as gap_store
from sgm.store.db import Store

ROOT = Path(__file__).resolve().parents[2]

FUENTE = """\
proc transpose data=miclientesecreto out=salida;
  by cuenta;
  id mes;
  var saldo;
run;

%include "otro_externo.sas";

data resultado;
  set miclientesecreto;
  z = zzfuncionfalsa(saldo);
  /* comentario con dato del cliente */
  nombre_real = 'Juan Perez';
run;
"""


@pytest.fixture
def entorno(tmp_path, monkeypatch):
    """Base de huecos, programa de origen y carpetas de salida dentro de `tmp_path`."""
    monkeypatch.setenv("SGM_DB", str(tmp_path / "sgm.sqlite"))
    repo = tmp_path / "repo"
    shutil.copytree(ROOT / "schemas", repo / "schemas")
    cases = repo / "tests" / "cases"
    carpetas = {
        tipo: repo / ruta
        for tipo, ruta in {
            "proc": "rules/sas/procs",
            "statement": "rules/sas/statements",
            "function": "rules/sas/functions",
            "intrinsic": "rules/sas/intrinsics",
            "mapping": "rules/mapping",
        }.items()
    }
    monkeypatch.setattr(generadores, "CASES", cases)
    monkeypatch.setattr(generadores, "CARPETA", carpetas)
    monkeypatch.setattr(rules_validate, "ROOT", repo)

    fuente = tmp_path / "fuente"
    fuente.mkdir()
    (fuente / "programa.sas").write_text(FUENTE, encoding="utf-8")

    compiled, _ = compile_project({"programa.sas": FUENTE})
    with Store() as store:
        gap_store.save(store, gap_store.inventory([r.plan for r in compiled.values()]))
        firmas = {r["reason"]: r["signature"] for r in gap_store.top(store, 100)}
    return {"repo": repo, "cases": cases, "fuente": fuente, "firmas": firmas}


def test_normalizar_firma():
    assert generadores.normalizar("proc:Transpose:id+var") == "proc-transpose-id-var"


def test_anonimizar_quita_nombres_comentarios_y_literales():
    texto = generadores.anonimizar(
        "data miclientesecreto; set otra.tabla; /* dato */ c = substr(nombre, 1, 2);\n"
        "d = 'Juan Perez';\nrun;\n"
    )
    assert "miclientesecreto" not in texto and "nombre" not in texto and "Juan" not in texto
    assert "dato" not in texto
    assert "data" in texto and "substr(" in texto and "set" in texto


def test_fragmento_sigue_hasta_run_si_el_paso_no_cierra():
    texto = "proc sort data=a;\n  by x;\nrun;\ndata b;\n  set a;\nrun;\n"
    assert generadores.fragmento(texto, 1, 2) == "proc sort data=a;\n  by x;\nrun;\n"


def test_case_new_reproduce_el_hueco_y_no_filtra_nombres(entorno):
    firma = entorno["firmas"]["PROC_NO_SOPORTADO"]
    carpeta = generadores.crear_caso(firma, entorno["fuente"], cases=entorno["cases"])
    entrada = (carpeta / "input.sas").read_text(encoding="utf-8")
    assert "miclientesecreto" not in entrada and "Juan" not in entrada
    esperado = yaml.safe_load((carpeta / "expected.yaml").read_text(encoding="utf-8"))
    assert "PROC_NO_SOPORTADO" in esperado["expect"]["gaps"]
    assert (carpeta / "README.md").exists()


@pytest.mark.parametrize(
    ("motivo", "tipo"),
    [
        ("PROC_NO_SOPORTADO", "proc"),
        ("FUNCION_NO_MAPEADA", "function"),
    ],
)
def test_rules_new_produce_un_archivo_que_valida(entorno, motivo, tipo):
    destino = generadores.crear_regla(tipo, entorno["firmas"][motivo], entorno["fuente"])
    assert destino.exists()
    assert rules_validate.validate(entorno["repo"]) == []


@pytest.mark.parametrize("tipo", ["statement", "intrinsic", "mapping"])
def test_rules_new_para_tipos_sin_hueco_sintetico_valida(entorno, tipo):
    firma = f"{tipo}:sintetico"
    caso = entorno["cases"] / generadores.normalizar(firma)
    caso.mkdir(parents=True)
    (caso / "input.sas").write_text("data a; set b; run;\n", encoding="utf-8")
    (caso / "expected.yaml").write_text(
        "description: sintético\ninput: input.sas\nenv: default\nexpect:\n  gaps: []\n",
        encoding="utf-8",
    )
    destino = generadores.crear_regla(tipo, firma, None)
    assert destino.exists()
    assert rules_validate.validate(entorno["repo"]) == []


def test_rules_new_informats_no_crea_archivo(entorno):
    with pytest.raises(ValueError, match="informats"):
        generadores.crear_regla("informats", "x", None)


def test_case_new_no_sobrescribe(entorno):
    firma = entorno["firmas"]["PROC_NO_SOPORTADO"]
    generadores.crear_caso(firma, entorno["fuente"], cases=entorno["cases"])
    with pytest.raises(FileExistsError):
        generadores.crear_caso(firma, entorno["fuente"], cases=entorno["cases"])
