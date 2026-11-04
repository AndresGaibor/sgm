"""Extrae la plantilla de un componente de un `.item` real guardado por Talend Studio.

Uso: uv run python tools/extraer_plantilla.py <archivo.item> <Componente> [<Componente> ...]

Escribe `src/sgm/talend_item/plantillas/<Componente>.json` con el primer nodo de ese componente.
Vacía las contraseñas y los datos del entorno (ver `SENSIBLES`); revisa el JSON antes de commitear.
"""

from __future__ import annotations

import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from sgm.talend_item.extraccion import plantilla_desde_nodo
from sgm.talend_item.plantillas import DIRECTORIO


def main(argv: list[str]) -> int:
    if len(argv) < 3:
        print(__doc__)
        return 2
    raiz = ET.parse(argv[1]).getroot()
    DIRECTORIO.mkdir(exist_ok=True)
    estado = 0
    for componente in argv[2:]:
        nodo = next((n for n in raiz.iter("node") if n.get("componentName") == componente), None)
        if nodo is None:
            print(f"{componente}: no está en {argv[1]}")
            estado = 1
            continue
        destino = Path(DIRECTORIO) / f"{componente}.json"
        destino.write_text(
            json.dumps(plantilla_desde_nodo(nodo), ensure_ascii=False, indent=1) + "\n",
            encoding="utf-8",
        )
        print(f"{componente}: {destino}")
    return estado


if __name__ == "__main__":
    sys.exit(main(sys.argv))
