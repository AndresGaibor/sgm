"""Descarga la documentación oficial de SAS y Talend a `docs/referencia/`.

Uso:
    uv run python tools/referencia/descargar.py sas
    uv run python tools/referencia/descargar.py talend
    uv run python tools/referencia/descargar.py talend --componentes tmap tfileinputdelimited

Solo usa la biblioteca estándar. Talend se baja en Markdown (versión oficial del sitio); si una
página no tiene `.md`, se anota como no descargada en el archivo de salida, en vez de convertir
HTML a mano.
Las páginas que no se pudieron bajar se listan en el archivo, nunca se omiten en silencio.
"""

from __future__ import annotations

import argparse
import datetime
import json
import re
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from fuentes import (
    SAS_DOCSETS,
    TALEND_COMPONENTES,
    TALEND_STUDIO_BASE,
    TALEND_STUDIO_RAICES,
    url_componente,
    url_guia,
    url_studio,
)

REPO = Path(__file__).resolve().parents[2]
CATALOGO_TALEND = REPO / "rules" / "talend" / "components.json"
REFERENCIA = REPO / "docs" / "referencia"
UA = {"User-Agent": "Mozilla/5.0 (documentation mirror)"}
_ENLACE = re.compile(r"\]\((https://help\.qlik\.com/talend/en-US/[^)\s#]+)\)")


def leer_url(url: str, timeout: int = 90) -> str:
    """Texto de una URL. Lanza excepción si la respuesta no es correcta."""
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")


def enlaces_de_subpaginas(markdown: str, base: str) -> list[str]:
    """URLs de subpáginas enlazadas desde `markdown` cuyo último segmento empieza como la base.

    Talend enlaza las subpáginas de un componente a veces desde una carpeta distinta (por ejemplo
    `jdbc/tjdbcinput-standard-properties`), así que se compara por nombre y no por carpeta.
    """
    slug = base.rstrip("/").rsplit("/", 1)[-1].lower()
    hallados: list[str] = []
    for href in _ENLACE.findall(markdown):
        href = href.rstrip("/").removesuffix(".md")
        ultimo = href.rsplit("/", 1)[-1].lower()
        if ultimo.startswith(slug) and href not in hallados and href != base:
            hallados.append(href)
    return hallados


def enlaces_de_la_guia(markdown: str, base: str) -> list[str]:
    """Subtemas de la guía de Studio: cualquier tema bajo su ruta, sin filtrar por nombre."""
    ruta = re.escape(TALEND_STUDIO_BASE)
    hallados: list[str] = []
    for tema in re.findall(ruta + r"([a-z0-9-]+)", markdown):
        url = TALEND_STUDIO_BASE + tema
        if url not in hallados and url != base:
            hallados.append(url)
    return hallados


def _es_markdown(texto: str) -> bool:
    return bool(texto.strip()) and not texto.lstrip().startswith("<")


def recorrer_componente(
    raiz: str, profundidad: int = 3, buscar=None
) -> tuple[list[tuple[str, str]], list[str]]:
    """Páginas (url, markdown) de un tema y sus subpáginas, y la lista de URLs que fallaron."""
    vistos: set[str] = set()
    cola: list[tuple[str, int]] = [(raiz, 0)]
    paginas: list[tuple[str, str]] = []
    fallos: list[str] = []
    while cola:
        url, nivel = cola.pop(0)
        if url in vistos or nivel > profundidad:
            continue
        vistos.add(url)
        try:
            texto = leer_url(url + ".md")
        except Exception as error:  # noqa: BLE001 - el fallo se reporta, no se propaga
            fallos.append(f"{url}: {error}")
            continue
        if not _es_markdown(texto):
            fallos.append(f"{url}: la respuesta no es Markdown")
            continue
        paginas.append((url, texto))
        hallar = buscar or enlaces_de_subpaginas
        cola.extend((hijo, nivel + 1) for hijo in hallar(texto, url))
    return paginas, fallos


def escribir_tema(destino: Path, titulo: str, fuente: str, paginas, fallos) -> None:
    hoy = datetime.date.today().isoformat()
    partes = [f"# {titulo}\n\n> Fuente oficial: {fuente}  \n> Descargado: {hoy}.\n"]
    for url, texto in paginas:
        partes.append(f"\n\n---\n\n<!-- fuente: {url} -->\n\n{texto.strip()}\n")
    if fallos:
        partes.append(
            "\n\n## Páginas no descargadas\n\n" + "\n".join(f"- {f}" for f in fallos) + "\n"
        )
    destino.write_text("".join(partes), encoding="utf-8")


def nombres_del_catalogo() -> list[str]:
    """Los componentes de rules/talend/components.json (539), en orden alfabético."""
    datos = json.loads(CATALOGO_TALEND.read_text(encoding="utf-8"))
    return sorted(datos["components"].keys(), key=str.lower)


def descargar_talend(
    componentes: list[str] | None = None, catalogo: bool = False
) -> dict[str, int]:
    """Baja componentes: los indicados, los del proyecto, o el catálogo completo.

    El catálogo se baja solo en su página raíz (sin subpáginas) y va a `talend/catalogo/`.
    """
    carpeta = REFERENCIA / "talend"
    if catalogo:
        carpeta = carpeta / "catalogo"
        nombres = [c.lower() for c in nombres_del_catalogo()]
        profundidad = 0
    else:
        nombres = [c.lower() for c in (componentes or TALEND_COMPONENTES)]
        profundidad = 3
    carpeta.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(6) as pool:
        resultados = list(
            pool.map(lambda n: (n, recorrer_componente(url_componente(n), profundidad)), nombres)
        )
    resumen: dict[str, int] = {}
    for nombre, (paginas, fallos) in resultados:
        escribir_tema(carpeta / f"{nombre}.md", nombre, url_componente(nombre), paginas, fallos)
        resumen[nombre] = len(paginas)
    return resumen


def descargar_guia_studio() -> int:
    """Baja los temas de la guía de Studio (R2026-09) y sus subtemas. Devuelve las páginas."""
    carpeta = REFERENCIA / "talend"
    carpeta.mkdir(parents=True, exist_ok=True)
    paginas: list[tuple[str, str]] = []
    fallos: list[str] = []
    vistos: set[str] = set()
    for raiz in TALEND_STUDIO_RAICES:
        p, f = recorrer_componente(url_studio(raiz), profundidad=1, buscar=enlaces_de_la_guia)
        # Dos raíces comparten subtemas (los joblets): cada página se escribe una sola vez.
        for url, texto in p:
            if url not in vistos:
                vistos.add(url)
                paginas.append((url, texto))
        fallos.extend(f)
    escribir_tema(
        carpeta / "studio-guia-jobs-contextos.md",
        "Talend Studio 8.0 (R2026-09): diseño de Jobs, joblets, contextos y conexiones",
        url_studio(""),
        paginas,
        fallos,
    )
    return len(paginas)


def descargar_sas(forzar: bool = False) -> dict[str, int]:
    """Baja los PDF oficiales de SAS. No vuelve a bajar un PDF que ya existe, salvo con `forzar`."""
    carpeta = REFERENCIA / "sas"
    carpeta.mkdir(parents=True, exist_ok=True)
    tamanos: dict[str, int] = {}
    for guia in SAS_DOCSETS:
        destino = carpeta / f"{guia.archivo}.pdf"
        if destino.exists() and not forzar:
            tamanos[guia.archivo] = destino.stat().st_size
            continue
        req = urllib.request.Request(url_guia(guia), headers=UA)
        with urllib.request.urlopen(req, timeout=300) as r:
            datos = r.read()
        destino.write_bytes(datos)
        tamanos[guia.archivo] = len(datos)
    return tamanos


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("fuente", choices=["sas", "talend"])
    parser.add_argument("--componentes", nargs="*", help="solo estos componentes de Talend")
    parser.add_argument("--forzar", action="store_true", help="vuelve a bajar los PDF de SAS")
    parser.add_argument(
        "--catalogo", action="store_true", help="baja los componentes de components.json"
    )
    parser.add_argument("--guia", action="store_true", help="baja la guía de Studio")
    args = parser.parse_args(argv)
    if args.fuente == "sas":
        for archivo, tam in descargar_sas(args.forzar).items():
            print(f"{archivo}.pdf: {tam} bytes")
    elif args.guia:
        print(f"guía de Studio: {descargar_guia_studio()} páginas")
    else:
        for nombre, paginas in descargar_talend(args.componentes, args.catalogo).items():
            print(f"{nombre}: {paginas} páginas")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
