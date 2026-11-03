"""Agrupación de regiones por proceso sin reglas de nombres (ver `sgm.agrupacion`)."""

from __future__ import annotations

from pathlib import Path

import pytest

from sgm.agrupacion import (
    agrupar,
    cargar_declaracion,
    grupos_declarados,
    inicios_de,
    palabras_por_region,
)
from sgm.facts.project import facts_for_project


def _region(nombre: str, tablas: list[str]) -> str:
    cuerpo = "".join(f"data work.{t}; set work.{nombre}_{t}; run;\n" for t in tablas)
    return f"%macro bloque;\n{cuerpo}%mend bloque;\n"


def test_dos_procesos_repetidos_forman_dos_grupos_sin_sufijos() -> None:
    ventas = ["ventas_detalle", "ventas_resumen", "ventas_cierre"]
    compras = ["compras_detalle", "compras_resumen", "compras_cierre"]
    texto = "".join(_region(f"a{i}", ventas) for i in range(3)) + "".join(
        _region(f"b{i}", compras) for i in range(3)
    )
    lineas = texto.splitlines()
    inicios = inicios_de(lineas, r"^\s*%macro\s+bloque\b")
    hechos = facts_for_project({"p.sas": texto})["p.sas"]
    grupos = agrupar(palabras_por_region(hechos, inicios), umbral=0.3).grupos
    tamanos = sorted(len(g) for g in grupos)
    assert tamanos == [3, 3]


DECLARACION = """region_marcador: "%macro bloque"
productos:
  - nombre: ventas
    sufijos: [UNO]
  - nombre: compras
    sufijos: [DOS]
"""


def test_declaracion_agrupa_por_sufijo_y_deja_fuera_la_region_sin_producto(
    tmp_path: Path,
) -> None:
    texto = (
        _region("a", ["pagos_uno"])
        + _region("b", ["cobros_dos"])
        + _region("c", ["otros_uno"])
        + _region("d", ["otros_dos"])
        + _region("e", ["generica"])
    )
    ruta = tmp_path / "declaracion.yaml"
    ruta.write_text(DECLARACION, encoding="utf-8")
    declaracion = cargar_declaracion(ruta)
    inicios = inicios_de(texto.splitlines(), declaracion.marcador)
    hechos = facts_for_project({"p.sas": texto})["p.sas"]
    grupos = grupos_declarados(hechos, inicios, declaracion)
    assert [list(g) for g in grupos] == [[0, 2], [1, 3]]

def test_declaracion_mal_formada_falla_con_el_motivo(tmp_path: Path) -> None:
    ruta = tmp_path / "mala.yaml"
    ruta.write_text("productos:\n  - nombre: ventas\n    sufijos: [UNO]\n", encoding="utf-8")
    with pytest.raises(ValueError, match="region_marcador"):
        cargar_declaracion(ruta)
    ruta.write_text("region_marcador: '%macro bloque'\n", encoding="utf-8")
    with pytest.raises(ValueError, match="productos"):
        cargar_declaracion(ruta)
