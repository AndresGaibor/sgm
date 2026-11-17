"""Cada función de rules/sas/sql-functions.json tiene su página en la guía, o su motivo (plan C, C-15).

La página se comprueba contra el índice de lefunctionsref: una página inventada no pasa.
"""

from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
FUNCIONES = json.loads((REPO / "rules" / "sas" / "sql-functions.json").read_text(encoding="utf-8"))
INDICE = (REPO / "docs" / "referencia" / "sas" / "lefunctionsref.INDEX.md").read_text(encoding="utf-8")


def test_toda_funcion_tiene_pagina_o_motivo():
    for nombre, entrada in FUNCIONES["functions"].items():
        assert entrada.get("pagina") or entrada.get("nota_pagina"), nombre


def test_cada_pagina_citada_existe_en_el_indice_de_la_guia():
    for nombre, entrada in FUNCIONES["functions"].items():
        pagina = entrada.get("pagina")
        if not pagina:
            continue
        numero = pagina.rsplit("p. ", 1)[1]
        etiqueta = entrada.get("etiqueta_indice", nombre.upper())
        assert f"{etiqueta} Function (p. {numero})" in INDICE, (
            f"{nombre}: {etiqueta} p. {numero} no está en lefunctionsref.INDEX.md"
        )


def test_las_sin_pagina_dicen_por_que():
    sin_pagina = {
        nombre: entrada["nota_pagina"]
        for nombre, entrada in FUNCIONES["functions"].items()
        if not entrada.get("pagina")
    }
    assert sin_pagina, "se esperaba al menos una función sin página verificada"
    for nombre, motivo in sin_pagina.items():
        assert motivo.startswith(("Pendiente:", "No es función")), nombre
