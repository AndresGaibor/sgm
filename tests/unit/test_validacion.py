"""Candado de cierre: huella del árbol, estado, historial y bloqueo del commit."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))

import instalar_ganchos  # noqa: E402
import validacion  # noqa: E402


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """Repositorio Git mínimo, con un archivo versionado."""
    raiz = tmp_path / "repo"
    raiz.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=raiz, check=True)
    subprocess.run(["git", "config", "user.email", "prueba@ejemplo.com"], cwd=raiz, check=True)
    subprocess.run(["git", "config", "user.name", "Prueba"], cwd=raiz, check=True)
    (raiz / "a.txt").write_text("uno\n", encoding="utf-8")
    subprocess.run(["git", "add", "a.txt"], cwd=raiz, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "inicial"], cwd=raiz, check=True)
    return raiz


@pytest.fixture
def base(tmp_path: Path) -> Path:
    return tmp_path / "validacion"


def _eventos(base: Path) -> list[dict]:
    ruta = base / validacion.NOMBRE_HISTORIAL
    return [json.loads(linea) for linea in ruta.read_text(encoding="utf-8").splitlines()]


def test_la_huella_es_estable_sin_cambios(repo: Path):
    assert validacion.huella_arbol(repo) == validacion.huella_arbol(repo)


def test_la_huella_cambia_al_editar_un_archivo(repo: Path):
    antes = validacion.huella_arbol(repo)
    (repo / "a.txt").write_text("dos\n", encoding="utf-8")
    assert validacion.huella_arbol(repo) != antes


def test_la_huella_cambia_al_editar_dos_veces_un_archivo_ya_modificado(repo: Path):
    # El primer cambio deja el archivo en estado ` M`; el segundo tiene que mover la huella igual.
    (repo / "a.txt").write_text("dos\n", encoding="utf-8")
    antes = validacion.huella_arbol(repo)
    (repo / "a.txt").write_text("tres\n", encoding="utf-8")
    assert validacion.huella_arbol(repo) != antes


def test_la_huella_cambia_con_un_archivo_nuevo(repo: Path):
    antes = validacion.huella_arbol(repo)
    (repo / "b.txt").write_text("nuevo\n", encoding="utf-8")
    assert validacion.huella_arbol(repo) != antes


def test_sin_validacion_el_commit_se_bloquea(repo: Path, base: Path):
    resultado = validacion.evaluar(repo, base)

    assert resultado["permitido"] is False
    assert "No hay ninguna validación" in resultado["motivo"]


def test_pytest_y_ruff_en_verde_permiten_el_commit(repo: Path, base: Path):
    validacion.registrar("pytest", True, "3128 passed", repo=repo, base=base)
    validacion.registrar("ruff", True, "All checks passed", repo=repo, base=base)

    resultado = validacion.evaluar(repo, base)

    assert resultado["permitido"] is True
    assert "Suite completa" in resultado["motivo"]


def test_si_falta_ruff_el_commit_se_bloquea(repo: Path, base: Path):
    validacion.registrar("pytest", True, "3128 passed", repo=repo, base=base)

    resultado = validacion.evaluar(repo, base)

    assert resultado["permitido"] is False
    assert "ruff" in resultado["motivo"]


def test_editar_despues_de_validar_bloquea_el_commit(repo: Path, base: Path):
    validacion.registrar("pytest", True, "", repo=repo, base=base)
    validacion.registrar("ruff", True, "", repo=repo, base=base)
    (repo / "a.txt").write_text("cambio\n", encoding="utf-8")

    resultado = validacion.evaluar(repo, base)

    assert resultado["permitido"] is False
    assert "cambió" in resultado["motivo"]


def test_un_cierre_rojo_bloquea_aunque_pytest_y_ruff_esten_verdes(repo: Path, base: Path):
    validacion.registrar("pytest", True, "", repo=repo, base=base)
    validacion.registrar("ruff", True, "", repo=repo, base=base)
    validacion.registrar("ci", False, "Falla: cruces del corpus", repo=repo, base=base)

    resultado = validacion.evaluar(repo, base)

    assert resultado["permitido"] is False
    assert "cruces del corpus" in resultado["motivo"]


def test_un_cierre_verde_permite_el_commit(repo: Path, base: Path):
    validacion.registrar("ci", True, "Todo verde", repo=repo, base=base)

    resultado = validacion.evaluar(repo, base)

    assert resultado["permitido"] is True
    assert "Cierre completo" in resultado["motivo"]


def test_el_historial_registra_validaciones_e_intentos(repo: Path, base: Path):
    validacion.registrar("pytest", True, "3128 passed", repo=repo, base=base)
    validacion.exigir(repo=repo, base=base, salida=None)

    eventos = _eventos(base)

    assert [evento["evento"] for evento in eventos] == ["validacion", "commit"]
    assert eventos[0]["paso"] == "pytest"
    assert eventos[1]["permitido"] is False


def test_guardia_ignora_comandos_que_no_son_commit(repo: Path, base: Path):
    entrada = json.dumps({"tool_name": "Bash", "tool_input": {"command": "git status"}})

    assert validacion.guardia(entrada, repo=repo, base=base) == (0, "")


def test_guardia_bloquea_un_commit_sin_cierre(repo: Path, base: Path):
    entrada = json.dumps({"tool_name": "Bash", "tool_input": {"command": "git commit -m hito"}})

    codigo, aviso = validacion.guardia(entrada, repo=repo, base=base)

    assert codigo == 2
    assert "tools/ci.py" in aviso


def test_guardia_bloquea_no_verify(repo: Path, base: Path):
    entrada = json.dumps(
        {"tool_name": "Bash", "tool_input": {"command": "git commit --no-verify -m hito"}}
    )

    codigo, aviso = validacion.guardia(entrada, repo=repo, base=base)

    assert codigo == 2
    assert "--no-verify" in aviso


def test_guardia_detecta_git_con_directorio(repo: Path, base: Path):
    entrada = json.dumps(
        {"tool_name": "Bash", "tool_input": {"command": "git -C repo commit -m hito"}}
    )

    codigo, _ = validacion.guardia(entrada, repo=repo, base=base)

    assert codigo == 2


def test_guardia_deja_pasar_el_commit_si_el_comando_corre_el_cierre(repo: Path, base: Path):
    entrada = json.dumps(
        {
            "tool_name": "Bash",
            "tool_input": {"command": "uv run python tools/ci.py && git commit -m hito"},
        }
    )

    assert validacion.guardia(entrada, repo=repo, base=base) == (0, "")


def test_guardia_deja_pasar_un_commit_con_cierre_verde(repo: Path, base: Path):
    validacion.registrar("ci", True, "Todo verde", repo=repo, base=base)
    entrada = json.dumps({"tool_name": "Bash", "tool_input": {"command": "git commit -m hito"}})

    assert validacion.guardia(entrada, repo=repo, base=base) == (0, "")


def test_instalar_apunta_los_ganchos_a_githooks(repo: Path):
    (repo / ".githooks").mkdir()
    (repo / ".githooks" / "pre-commit").write_text("#!/bin/sh\n", encoding="utf-8")

    assert instalar_ganchos.instalar(repo, salida=lambda _: None) == 0
    configurado = subprocess.run(
        ["git", "config", "--get", "core.hooksPath"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    )

    assert configurado.stdout.strip() == ".githooks"


def test_instalar_falla_si_no_esta_el_gancho(repo: Path):
    assert instalar_ganchos.instalar(repo, salida=lambda _: None) == 1
