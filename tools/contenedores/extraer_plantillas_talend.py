"""Extrae plantillas de componentes desde un `.item` de Talend validado por ejecución.

Es la misma extracción que `tools/extraer_plantilla.py`, pero escribe en
`tools/contenedores/talend_plantillas/` para no tocar `src/` desde esta tarea. Las plantillas
quedan listas para moverse a `src/sgm/talend_item/plantillas/` cuando su dueño lo decida.

Uso: uv run python tools/contenedores/extraer_plantillas_talend.py <archivo.item> <Componente>...
"""

import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from sgm.talend_item.extraccion import plantilla_desde_nodo

DESTINO = Path(__file__).resolve().parent / "talend_plantillas"


def _sin_contrasenas(plantilla: dict[str, object]) -> dict[str, object]:
    """Vacía `PASS` aunque el escritor offline lo guardara como campo TEXT y no PASSWORD."""
    for fila in plantilla.get("parametros", []):
        if isinstance(fila, list) and len(fila) >= 3 and fila[1] == "PASS":
            fila[2] = ""
    return plantilla


def main(argv: list[str]) -> int:
    if len(argv) < 3:
        print(__doc__)
        return 2
    raiz = ET.parse(argv[1]).getroot()
    DESTINO.mkdir(exist_ok=True)
    estado = 0
    for componente in argv[2:]:
        nodo = next((n for n in raiz.iter("node") if n.get("componentName") == componente), None)
        if nodo is None:
            print(f"{componente}: no está en {argv[1]}")
            estado = 1
            continue
        destino = DESTINO / f"{componente}.json"
        destino.write_text(
            json.dumps(_sin_contrasenas(plantilla_desde_nodo(nodo)), ensure_ascii=False, indent=1)
            + "\n",
            encoding="utf-8",
        )
        print(f"{componente}: {destino}")
    return estado


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
