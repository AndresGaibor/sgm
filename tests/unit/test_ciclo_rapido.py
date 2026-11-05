"""Ciclo rápido: qué casos tocó un cambio y qué comandos correr, en orden."""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))

from ciclo_rapido import casos_tocados, comandos, main  # noqa: E402


def test_casos_tocados_detecta_el_directorio_del_caso():
    assert casos_tocados(["tests/corpus/L2/l2_01_x/programa.sas"]) == ["tests/corpus/L2/l2_01_x"]


def test_casos_tocados_no_repite_y_ordena():
    archivos = [
        "tests/corpus/L2/l2_01_x/programa.sas",
        "tests/corpus/L2/l2_01_x/entradas/a.csv",
        "tests/corpus/L0/l0_01_y/programa.sas",
    ]

    assert casos_tocados(archivos) == ["tests/corpus/L0/l0_01_y", "tests/corpus/L2/l2_01_x"]


def test_un_archivo_fuera_del_corpus_no_es_un_caso():
    assert casos_tocados(["src/sgm/cli.py", "docs/plan.md"]) == []


def test_sin_casos_no_hay_comando_de_oraculo():
    lista = comandos(["src/sgm/cli.py"])

    assert not [comando for comando in lista if "oraculo" in comando]


def test_ruff_solo_sobre_python():
    lista = comandos(["docs/plan.md"])

    assert not [comando for comando in lista if comando[2] == "ruff"]
    assert [comando for comando in lista if comando[2] == "pytest"]


def test_ruff_corre_sobre_los_python_tocados():
    lista = comandos(["src/sgm/cli.py", "docs/plan.md"])

    assert lista[0] == ["uv", "run", "ruff", "check", "src/sgm/cli.py"]


def test_el_oraculo_va_por_caso_y_al_final():
    lista = comandos(["tests/corpus/L2/l2_01_x/programa.sas"])

    assert lista[-1] == [
        "uv",
        "run",
        "python",
        "tools/corpus.py",
        "oraculo",
        "tests/corpus/L2/l2_01_x",
        "--verificar",
    ]


def test_sale_con_el_primer_fallo():
    corridos: list[list[str]] = []

    def ejecutar(comando: list[str]) -> int:
        corridos.append(comando)
        return 3 if len(corridos) == 2 else 0

    codigo = main(
        archivos=["src/sgm/cli.py", "tests/corpus/L2/l2_01_x/programa.sas"],
        ejecutar=ejecutar,
        salida=lambda _: None,
    )

    assert codigo == 3
    assert len(corridos) == 2
