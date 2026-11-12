"""Pruebas de tools/avance_creditos.py: la tabla 11b sale de un YAML de créditos (G-4)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))

import avance_creditos as ac  # noqa: E402

YAML_MINIMO = """\
fases:
  - id: MG-P0
    nombre: Preparación
    horas: 37
    credito_sin_desglosar: 25.0
    tareas: []
    sostiene: Backend hecho
  - id: MG-P5
    nombre: "`PROC SQL`"
    horas: 80
    credito_sin_desglosar: 10.0
    tareas:
      - id: MG-P5-02
        horas: 8
        fraccion: 0.5
    sostiene: Agregados
"""

PLAN_CON_MARCAS = """\
# Plan

Texto antes.

<!-- avance:inicio -->
vieja
<!-- avance:fin -->

Texto después.
"""


def _yaml(tmp_path: Path, texto: str = YAML_MINIMO) -> Path:
    ruta = tmp_path / "creditos.yaml"
    ruta.write_text(texto, encoding="utf-8")
    return ruta


def test_credito_suma_lo_sin_desglosar_y_las_tareas(tmp_path: Path) -> None:
    fases = ac.cargar(_yaml(tmp_path))
    assert ac.credito(fases[0]) == 25.0
    assert ac.credito(fases[1]) == 14.0  # 10 sin desglosar + 8 * 0,5


def test_porcentaje_redondea_medio_hacia_arriba() -> None:
    assert ac.porcentaje(37, 25.0) == 68
    assert ac.porcentaje(895, 237.25) == 27  # 26,5 % redondea a 27 por fase, el total se imprime con decimal


def test_formato_credito_usa_coma_y_al_menos_un_decimal() -> None:
    assert ac.formato_credito(25.0) == "25,0"
    assert ac.formato_credito(0.75) == "0,75"
    assert ac.formato_credito(237.25) == "237,25"


def test_tabla_incluye_fila_de_fase_y_total(tmp_path: Path) -> None:
    fases = ac.cargar(_yaml(tmp_path))
    tabla = ac.tabla_markdown(fases)
    assert "| MG-P0 Preparación | 37 | 25,0 | 68 % | Backend hecho |" in tabla
    assert "| **Total** | **117** |" in tabla


def test_total_de_la_tabla_real_con_decimal() -> None:
    fases = (
        ac.Fase("MG-P0", "Preparación", 37.0, 25.0, (), "x"),
        ac.Fase("MG-P1", "Modelo", 70.0, 37.5, (), "y"),
        ac.Fase("MG-P2", "Entrada", 788.0, 174.75, (), "z"),
    )
    assert "| **Total** | **895** | **237,25** | **26,5 %** | |" in ac.tabla_markdown(fases)


def test_cargar_rechaza_fraccion_fuera_de_rango(tmp_path: Path) -> None:
    texto = YAML_MINIMO.replace("fraccion: 0.5", "fraccion: 1.5")
    with pytest.raises(ValueError, match="MG-P5-02"):
        ac.cargar(_yaml(tmp_path, texto))


def test_cargar_rechaza_ids_repetidos(tmp_path: Path) -> None:
    texto = YAML_MINIMO.replace("id: MG-P5\n", "id: MG-P0\n")
    with pytest.raises(ValueError, match="MG-P0"):
        ac.cargar(_yaml(tmp_path, texto))


def test_cargar_rechaza_horas_de_tareas_mayores_que_la_fase(tmp_path: Path) -> None:
    texto = YAML_MINIMO.replace("horas: 80", "horas: 5")
    with pytest.raises(ValueError, match="MG-P5"):
        ac.cargar(_yaml(tmp_path, texto))


def test_actualizar_plan_cambia_solo_lo_de_entre_marcas(tmp_path: Path) -> None:
    plan = tmp_path / "plan.md"
    plan.write_bytes(PLAN_CON_MARCAS.encode("utf-8"))
    assert ac.actualizar_plan(plan, "nueva tabla") is True
    assert plan.read_text(encoding="utf-8") == (
        "# Plan\n\nTexto antes.\n\n<!-- avance:inicio -->\nnueva tabla\n<!-- avance:fin -->\n\nTexto después.\n"
    )


def test_actualizar_plan_sin_marcas_no_toca_nada(tmp_path: Path) -> None:
    plan = tmp_path / "plan.md"
    original = "# Sin marcas\n"
    plan.write_text(original, encoding="utf-8")
    assert ac.actualizar_plan(plan, "x") is False
    assert plan.read_text(encoding="utf-8") == original


def test_importar_lee_la_tabla_actual(tmp_path: Path) -> None:
    plan = tmp_path / "plan.md"
    plan.write_text(
        "| Fase | Horas | Crédito | % de la fase | Qué sostiene la cifra |\n"
        "|---|---|---|---|---|\n"
        "| MG-P0 Preparación | 37 | 25,0 | 68 % | Backend hecho |\n"
        "| MG-P5 `PROC SQL` | 80 | 37,0 | 46 % | Agregados |\n"
        "| **Total** | **117** | **62,0** | **53,0 %** | |\n",
        encoding="utf-8",
    )
    texto = ac.importar(plan)
    assert "MG-P0" in texto and "credito_sin_desglosar: 25.0" in texto
    assert "MG-P5" in texto and "credito_sin_desglosar: 37.0" in texto
    assert "Total" not in texto


def test_la_tabla_del_plan_sale_del_yaml() -> None:
    """Trinquete: la tabla del plan maestro es la que sale del YAML de créditos."""
    yaml_real = REPO / "docs" / "plan-reescritura" / "creditos.yaml"
    plan = REPO / "docs" / "plan-reescritura" / "plan-migrador-general.md"
    assert ac.verificar(yaml_real, plan) is True
