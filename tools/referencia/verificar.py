"""Compara `rules/talend/components.json` con las páginas descargadas en `talend/catalogo/`.

Dos comprobaciones por componente:
- título: la primera línea `# nombre` de la página es el nombre del componente (sin importar
  mayúsculas);
- familia: si la página dice "belongs to the X family", X debe coincidir con la familia del
  catálogo. Las páginas que no dicen la familia quedan como "sin dato", no como error.

El resultado se escribe en `talend/catalogo/VERIFICACION.md`. No cambia el catálogo: solo lo revisa.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

_FAMILIA_EN_PAGINA = re.compile(r"belongs to the (.+?) family")
_TITULO = re.compile(r"^# (\S+)\s*$", re.MULTILINE)


def normalizar_familia(texto: str) -> str:
    """Forma comparable: sin mayúsculas; `_` y `&` pasan a espacio; sin espacios repetidos.

    La documentación escribe "Logs & Errors" y el catálogo "Logs_Errors": ambos quedan igual.
    """
    limpio = texto.replace("_", " ").replace("&", " ")
    return re.sub(r"\s+", " ", limpio).strip().lower()


def familias_del_catalogo(familias: list[str]) -> set[str]:
    """Primer nivel de cada familia del catálogo: `Databases/DB Specifics/AS400` -> `Databases`."""
    return {normalizar_familia(f.split("/")[0]) for f in familias}


@dataclass
class Resultado:
    componente: str
    problemas: list[str] = field(default_factory=list)
    sin_dato: bool = False


def verificar_pagina(nombre: str, familias: list[str], pagina: str) -> Resultado:
    """Revisa una página contra su entrada del catálogo."""
    res = Resultado(nombre)
    titulo = _TITULO.search(pagina)
    if not titulo or titulo.group(1).lower() != nombre.lower():
        encontrado = titulo.group(1) if titulo else "(sin título)"
        res.problemas.append(f"título {encontrado!r} no coincide con {nombre!r}")
    familia = _FAMILIA_EN_PAGINA.search(pagina)
    if not familia:
        res.sin_dato = True
    elif normalizar_familia(familia.group(1)) not in familias_del_catalogo(familias):
        res.problemas.append(
            f"la página dice familia {familia.group(1)!r}; el catálogo dice {familias}"
        )
    return res


def verificar_catalogo(catalogo: Path, carpeta: Path) -> list[Resultado]:
    """Revisa todos los componentes del catálogo. Un componente sin página es un problema."""
    datos = json.loads(catalogo.read_text(encoding="utf-8"))["components"]
    resultados: list[Resultado] = []
    for nombre in sorted(datos, key=str.lower):
        ruta = carpeta / f"{nombre.lower()}.md"
        if not ruta.exists():
            resultados.append(Resultado(nombre, [f"falta la página {ruta.name}"]))
            continue
        resultados.append(
            verificar_pagina(nombre, datos[nombre].get("families", []), ruta.read_text("utf-8"))
        )
    return resultados


def markdown_informe(resultados: list[Resultado]) -> str:
    """Informe con totales y la lista de problemas, para revisar a mano."""
    total = len(resultados)
    con_problemas = [r for r in resultados if r.problemas]
    sin_dato = sum(1 for r in resultados if r.sin_dato)
    lineas = [
        "# Verificación del catálogo de Talend contra la documentación",
        "",
        f"- Componentes en `rules/talend/components.json`: {total}",
        f"- Con problemas: {len(con_problemas)}",
        f"- Sin dato de familia en la página (no es error): {sin_dato}",
        "",
    ]
    if con_problemas:
        lineas += ["## Problemas", ""]
        lineas += [f"- `{r.componente}`: " + "; ".join(r.problemas) for r in con_problemas]
    else:
        lineas.append("Ningún componente tiene problemas.")
    return "\n".join(lineas) + "\n"


def main() -> int:
    """Escribe `talend/catalogo/VERIFICACION.md` y lo resume en la salida."""
    raiz = Path(__file__).resolve().parents[2]
    resultados = verificar_catalogo(
        raiz / "rules" / "talend" / "components.json",
        raiz / "docs" / "referencia" / "talend" / "catalogo",
    )
    destino = raiz / "docs" / "referencia" / "talend" / "catalogo" / "VERIFICACION.md"
    destino.write_text(markdown_informe(resultados), encoding="utf-8")
    con_problemas = sum(1 for r in resultados if r.problemas)
    print(f"{len(resultados)} componentes, {con_problemas} con problemas -> {destino}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
