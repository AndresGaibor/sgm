"""Agrupación de regiones por proceso sin reglas de nombres (ver `sgm.agrupacion`)."""

from __future__ import annotations

from sgm.agrupacion import agrupar, inicios_de, palabras_por_region
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
