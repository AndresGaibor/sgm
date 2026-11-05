"""Texto plano de los PDF de SAS, con una marca `<!-- página N -->` por página.

Cada `.txt` de `docs/referencia/sas/` sale de aquí: el texto de cada página del PDF precedido por
`<!-- página N -->`, para poder saltar a una página con `Grep`. El `.INDEX.md` de al lado
(`indice.py`) dice en qué página empieza cada sección.

Requiere `pypdf`, que no es una dependencia de `sgm`; se instala solo para esta tarea.

Uso:
    uv run --with pypdf python tools/referencia/texto.py docs/referencia/sas/lepg.pdf
"""

from __future__ import annotations

import sys
from pathlib import Path

MARCA = "<!-- página {pagina} -->"


def texto_de_paginas(paginas: list[str | None]) -> str:
    """Texto del `.txt`: cada página con su marca delante y una línea en blanco de separación."""
    partes = [
        f"\n\n{MARCA.format(pagina=numero)}\n{(texto or '').rstrip()}"
        for numero, texto in enumerate(paginas, 1)
    ]
    return "".join(partes) + "\n"


def texto_del_pdf(pdf: Path) -> str:
    """Texto de todas las páginas del PDF, con las marcas."""
    try:
        from pypdf import PdfReader  # import tardío: herramienta opcional
    except ImportError as error:
        raise RuntimeError("falta pypdf: instálalo solo para esta herramienta") from error
    lector = PdfReader(str(pdf))
    return texto_de_paginas([pagina.extract_text() for pagina in lector.pages])


def escribir_texto(pdf: Path) -> Path:
    """Escribe `<pdf>.txt` junto al PDF. Devuelve la ruta escrita."""
    destino = pdf.with_suffix(".txt")
    with destino.open("w", encoding="utf-8", newline="\r\n") as archivo:
        archivo.write(texto_del_pdf(pdf))
    return destino


def main(argv: list[str] | None = None) -> int:
    rutas = argv if argv is not None else sys.argv[1:]
    if not rutas:
        print(__doc__)
        return 2
    for ruta in rutas:
        pdf = Path(ruta)
        if not pdf.exists():
            print(f"no existe: {pdf}")
            return 1
        destino = escribir_texto(pdf)
        print(f"{destino.name}: {destino.stat().st_size} bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
