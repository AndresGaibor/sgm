"""Índice sección → página de cada PDF de SAS, a partir de los marcadores del PDF.

Los PDF oficiales de SAS traen marcadores (`outline`) con el título de cada sección y su página.
Con eso se escribe `<guía>.INDEX.md` junto a cada PDF: una línea por sección, con la página.
El `.txt` de cada guía se busca por página, porque cada una empieza con `<!-- página N -->`.

Requiere `pypdf`, que es una herramienta de documentación y no una dependencia de `sgm`. Si no
está instalado, el comando avisa y no escribe nada.
"""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path


def aplanar(marcadores: Iterable, pagina_de, nivel: int = 0) -> list[tuple[int, str, int | None]]:
    """Lista (nivel, título, página) en orden de lectura.

    `marcadores` es la estructura `outline` de pypdf: los elementos son destinos o listas anidadas.
    `pagina_de(destino)` devuelve el número de página (desde 1) o None si no se puede resolver.
    """
    filas: list[tuple[int, str, int | None]] = []
    previo = None
    for elemento in marcadores:
        if isinstance(elemento, list):
            filas.extend(aplanar(elemento, pagina_de, nivel + 1))
            continue
        titulo = str(getattr(elemento, "title", "") or "").strip()
        if titulo and titulo != previo:
            filas.append((nivel, titulo, pagina_de(elemento)))
            previo = titulo
    return filas


def markdown_indice(titulo: str, archivo_txt: str, filas: list[tuple[int, str, int | None]]) -> str:
    """Documento Markdown con el índice de una guía, sangrado por nivel."""
    lineas = [
        f"# Índice: {titulo}",
        "",
        f"Texto completo: `{archivo_txt}`. Para ir a una página, busca `<!-- página N -->`.",
        "",
    ]
    for nivel, texto, pagina in filas:
        sangria = "  " * nivel
        marca = f"p. {pagina}" if pagina is not None else "p. ?"
        lineas.append(f"{sangria}- {texto} ({marca})")
    return "\n".join(lineas) + "\n"


def escribir_indice(pdf: Path, titulo: str) -> Path:
    """Escribe `<pdf>.INDEX.md` junto al PDF, usando sus marcadores. Devuelve la ruta escrita."""
    try:
        from pypdf import PdfReader  # import tardío: herramienta opcional
    except ImportError as error:
        raise RuntimeError("falta pypdf: instálalo solo para esta herramienta") from error
    lector = PdfReader(str(pdf))
    filas = aplanar(lector.outline, lambda d: lector.get_destination_page_number(d) + 1)
    destino = pdf.with_suffix(".INDEX.md")
    destino.write_text(
        markdown_indice(titulo, pdf.with_suffix(".txt").name, filas), encoding="utf-8"
    )
    return destino
