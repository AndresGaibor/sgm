"""Inventario reproducible de funciones SAS por motor y catálogo."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from tools.funciones_inventario import _sin_catalogo_plan, inventario, resumen


def test_inventario_cruza_motores_vectores_catalogo_y_pagina(tmp_path: Path):
    catalogo = tmp_path / "rules" / "sas" / "catalogo" / "funciones-usadas.yaml"
    catalogo.parent.mkdir(parents=True)
    catalogo.write_text(
        yaml.safe_dump(
            {
                "id": "funciones-usadas",
                "kind": "catalogo",
                "version": 1,
                "description": "Funciones de prueba",
                "entries": [
                    {
                        "id": "trim-function",
                        "nombre": "TRIM Function",
                        "fuente": "lefunctionsref.pdf, p. 1624",
                        "estado": "reconocida",
                    }
                ],
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    vectores = tmp_path / "tests" / "corpus" / "semantica" / "vectores.yaml"
    vectores.parent.mkdir(parents=True)
    vectores.write_text(
        "vectores:\n"
        "  - id: trim-01\n"
        "    funcion: trim\n"
        "    entrada: ['ab  ']\n"
        "    esperado: ab\n"
        "    fuente_url: https://documentation.sas.com/\n"
        "    cita: lefunctionsref, p. 1624: TRIM Function\n"
        "    confianza: documentado\n",
        encoding="utf-8",
    )

    resultado = inventario(
        tmp_path,
        talend={"trim": object()},
        oraculo={"trim": object()},
        interprete={},
    )

    assert resultado == {
        "trim": {
            "talend": True,
            "oraculo": True,
            "interprete": False,
            "vectores": 1,
            "catalogo": "reconocida",
            "pagina": "lefunctionsref.pdf, p. 1624",
        }
    }
    assert resumen(resultado) == {
        "funciones": 1,
        "en_talend": 1,
        "en_oraculo": 1,
        "en_interprete": 0,
        "con_vectores": 1,
        "vectores_en_interprete": 0,
        "sin_catalogo": [],
    }
    with pytest.raises(ValueError, match="no hay función"):
        resumen(resultado, {"TRIM": 1})
    con_interprete = {"trim": {**resultado["trim"], "interprete": True}}
    assert resumen(con_interprete)["vectores_en_interprete"] == 0
    assert resumen(con_interprete, {"TRIM": 1})["vectores_en_interprete"] == 1
    with pytest.raises(ValueError, match="fuera de rango"):
        resumen(con_interprete, {"trim": 2})
    with pytest.raises(ValueError, match="duplicado"):
        resumen(con_interprete, {"TRIM": 1, "trim": 1})


def test_inventario_incluye_funciones_planeadas_y_normaliza_motores(tmp_path: Path):
    plan = tmp_path / "docs" / "plan-reescritura" / "plan-migrador-general.md"
    plan.parent.mkdir(parents=True)
    plan.write_text(
        "### 5.7 Funciones, formatos e informats\n\n"
        "| Familia | Funciones |\n"
        "|---|---|\n"
        "| Texto | `TRIM`, `CATS`, `CAT*`, `PRXMATCH/PRXCHANGE` |\n\n"
        "| Conversión | `INPUT`, `PUT`, ver `leforinforref.txt` |\n"
        "| Faltantes | `MISSING`, `.A`, `.Z` |\n\n"
        "Cada función tiene una ficha.\n",
        encoding="utf-8",
    )
    catalogo = tmp_path / "rules" / "sas" / "catalogo" / "funciones-usadas.yaml"
    catalogo.parent.mkdir(parents=True)
    catalogo.write_text(
        yaml.safe_dump(
            {
                "id": "funciones-usadas",
                "kind": "catalogo",
                "version": 1,
                "description": "Funciones de prueba",
                "entries": [
                    {
                        "id": "trim-function",
                        "nombre": "TRIM Function",
                        "fuente": "lefunctionsref.pdf, p. 1624",
                        "estado": "reconocida",
                    }
                ],
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    vectores = tmp_path / "tests" / "corpus" / "semantica" / "vectores.yaml"
    vectores.parent.mkdir(parents=True)
    vectores.write_text("vectores:\n  - funcion: catq\n", encoding="utf-8")

    resultado = inventario(
        tmp_path,
        talend={"CATX": object()},
        oraculo={"TRIM": object()},
        interprete={},
    )

    assert set(resultado) == {
        "trim",
        "cats",
        "catx",
        "catq",
        "prxmatch",
        "prxchange",
        "input",
        "put",
        "missing",
    }
    assert resultado["catx"]["talend"] is True
    assert resultado["catq"]["vectores"] == 1
    assert resultado["trim"]["oraculo"] is True
    assert resumen(resultado)["sin_catalogo"] == [
        "catq",
        "cats",
        "catx",
        "input",
        "missing",
        "prxchange",
        "prxmatch",
        "put",
    ]
    assert _sin_catalogo_plan(tmp_path, resultado) == [
        "cats",
        "catx",
        "input",
        "missing",
        "prxchange",
        "prxmatch",
        "put",
    ]
