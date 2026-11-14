"""Medición reproducible de las construcciones de entrada y salida."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

import linea_base_es as base  # noqa: E402


def _caso(corpus: Path, nombre: str, construcciones: list[str]) -> None:
    carpeta = corpus / "L0" / nombre
    carpeta.mkdir(parents=True)
    (carpeta / "programa.sas").write_text("/* fixture */\n", encoding="utf-8")
    lista = ", ".join(construcciones)
    (carpeta / "caso.yaml").write_text(
        "\n".join(
            (
                "nivel: L0",
                f"construcciones: [{lista}]",
                "capa: B",
                "estado: traducible",
                "salidas: []",
            )
        ),
        encoding="utf-8",
    )


def test_medir_cuenta_construcciones_casos_pendientes_y_usos(tmp_path: Path) -> None:
    corpus = tmp_path / "corpus"
    _caso(corpus, "l0_archivo", ["PROC IMPORT", "KEEP"])
    _caso(corpus, "l0_infile", ["INFILE", "INPUT"])
    (corpus / "migrar_pendientes.yaml").write_text(
        "l0_infile: P-FORMATO-SIN-SOPORTE\n", encoding="utf-8"
    )
    programa = tmp_path / "programa.sas"
    programa.write_text(
        "connect to impala (dsn=x);\nconnect to impala (dsn=x);\n", encoding="utf-8"
    )

    resultado = base.medir(corpus, [programa])

    assert resultado["construcciones"]["PROC IMPORT"] == {
        "casos": 1,
        "pendientes": {},
        "usos_programas": 0,
    }
    assert resultado["construcciones"]["INFILE"]["casos"] == 1
    assert resultado["construcciones"]["INPUT"]["pendientes"] == {
        "P-FORMATO-SIN-SOPORTE": 1
    }
    assert resultado["construcciones"]["CONNECT TO"]["usos_programas"] == 2


def test_medir_solo_cuenta_casos_que_declaran_la_construccion(tmp_path: Path) -> None:
    corpus = tmp_path / "corpus"
    _caso(corpus, "l0_archivo", ["PROC IMPORT", "KEEP"])

    resultado = base.medir(corpus)

    assert resultado["construcciones"]["PROC EXPORT"]["casos"] == 0
    assert resultado["casos_por_nivel"]["L0"]["PROC IMPORT"] == 1
    assert resultado["casos_por_nivel"]["L0"]["PROC EXPORT"] == 0
