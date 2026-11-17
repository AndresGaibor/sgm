"""Inventario reproducible de PROC: genera el subinforme que integra G-17."""

from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

from sgm.ir.lower_procs import REPORT_PROCS
from sgm.ir.proc_rules import PROCS_DIR, load
from sgm.yaml_io import cargar_yaml

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "docs/referencia/sas/proc.INDEX.md"
CATALOG = ROOT / "rules/sas/catalogo/procs-usados.yaml"
DESTINATION = ROOT / "docs/cobertura-procedimientos.md"
CHAPTER = re.compile(r"^  - ([A-Z][A-Z0-9_]*) Procedure \(p\. (\d+)\)", re.M)
PENDING = re.compile(r"\bP-[A-Z][A-Z0-9-]*")

# Las familias describen el alcance del producto, no equivalencias de datos.
# proc.pdf, pp. 53–54 (gráficos), 60–64 (utilidades y sesión).
FAMILIES = {
    "reportes especializados": (
        {"calendar"},
        "Presentación de calendarios fuera de la migración de datos (proc.pdf, p. 64).",
    ),
    "gráficos": (
        {"chart", "plot", "timeplot"},
        "Salida gráfica SAS sin equivalencia de datos del migrador (proc.pdf, pp. 53–54).",
    ),
    "infraestructura SAS": (
        {"authlib", "catalog", "cimport", "cport", "migrate", "registry", "pwencode"},
        "Catálogos, transporte, versiones, registro o credenciales propios de SAS "
        "fuera de la migración de filas (proc.pdf, pp. 62–64).",
    ),
    "administración de la sesión": (
        {
            "javainfo",
            "options",
            "optload",
            "optsave",
            "presenv",
            "scaproc",
            "fontreg",
            "printto",
            "prtdef",
            "prtexp",
            "pmenu",
            "display",
        },
        "Configuración, diagnóstico, impresión o ventanas de la sesión SAS "
        "fuera del Job de datos (proc.pdf, pp. 60–63); PROC OPTIONS no es la sentencia OPTIONS.",
    ),
}
BRANCHES = {
    "format": "VALUE discreto de carácter y OTHER en el plan/intérprete B (pp. 1173, 1178, "
    "1181); rangos: P-FORMATO-RANGO-SIN-SOPORTE; Talend: P-FORMATO-USUARIO-SIN-EMISOR.",
    "sort": "BY/NODUPKEY/NODUPREC/DUPOUT/NOEQUALS; conserva sus pendientes de estabilidad.",
    "copy": "SELECT estático con IN distinto de OUT=WORK; otras formas conservan pendientes.",
    "import": "Lectura de archivos; formato, esquema y opciones deben estar demostrados.",
    "export": "Subconjunto de escritura de archivos; formato y destino deben estar demostrados.",
    "sql": "Parser y lowering propios de PROC SQL; soporte parcial según sentencia y expresión.",
}


def _catalog_entries(path: Path) -> dict[str, dict]:
    """Catálogo solicitado y el general de procedimientos cuando existe junto a él."""
    entries = {}
    for source in dict.fromkeys([path, path.with_name("procedimientos-migrador.yaml")]):
        if source.exists():
            for entry in cargar_yaml(source).get("entries", []):
                entries[str(entry["id"]).lower()] = entry
    return entries


def _classification(name: str, spec: dict, entry: dict) -> tuple[str, str]:
    note = entry.get("nota", "")
    if name in {"delete", "datasets"}:
        return (
            "limpieza",
            "Solo WORK demostrado; bibliotecas persistentes o ambiguas quedan pendientes.",
        )
    if name in REPORT_PROCS:
        detail = "Sin OUT=: reports=discard omite con aviso; log/csv solo materializan PRINT."
        if name == "freq":
            detail += " TABLES OUT=: P-FREQ-OUT-SIN-PAGINA; p. 89 solo documenta MISSPRINT."
        elif name == "contents":
            detail += (
                " WORK._ALL_ OUT=: P-WORK-INTROSPECCION; otras salidas OUT= siguen pendientes."
            )
        else:
            detail += " OUT= no se descarta como reporte."
        return "reporte", detail
    if name == "transpose":
        return (
            "pendiente",
            "P-OPERADOR-PIVOTAR: pivote sin componente ni equivalencia completa demostrada.",
        )
    if name in BRANCHES:
        return "traducido", BRANCHES[name]
    if spec.get("ops") and spec.get("status") in {"soportado", "parcial"}:
        return "traducido", note or spec.get(
            "description", "Regla declarativa; revisar sus condiciones y fallback."
        )
    fallback = spec.get("fallback", {}).get("note", "")
    if PENDING.search(fallback):
        return "pendiente", fallback
    for family, (members, reason) in FAMILIES.items():
        if name in members:
            return "fuera_de_alcance", f"{family}: {reason}"
    return "no_verificado", note or "Sin regla de traducción ni familia de alcance verificada."


def clasificar(indice: Path, catalogo: Path, reglas: Path) -> list[dict]:
    """Clasifica capítulos y menciones adicionales; reconocer no demuestra equivalencia total."""
    index_text = indice.read_text(encoding="utf-8")
    chapters = {name.lower(): int(page) for name, page in CHAPTER.findall(index_text)}
    pages = set(re.findall(r"\(p\. (\d+)\)", index_text))
    entries, specs = _catalog_entries(catalogo), load(reglas)
    rows = []
    for name in sorted(chapters.keys() | entries.keys() | specs.keys()):
        entry = entries.get(name, {})
        page = chapters.get(name)
        if name == "format" and entry.get("estado") == "reconocida":
            # VALUE es la equivalencia; el encabezado de capítulo p.1127 solo la localiza.
            citation = re.search(r"proc\.pdf, p\. (\d+)", entry.get("fuente", ""))
            if citation and citation[1] in pages:
                page = int(citation[1])
        if page is None:
            citation = re.search(r"proc\.pdf, p\. (\d+)", entry.get("fuente", ""))
            page = int(citation[1]) if citation and citation[1] in pages else None
        state, reason = _classification(name, specs.get(name, {}), entry)
        if name not in chapters:
            reason = "Mención sin capítulo propio; no cuenta entre los capítulos. " + reason
        if page is None:
            state, reason = "no_verificado", f"Sin página verificable en el índice local. {reason}"
        rows.append(
            {
                "procedimiento": name.upper(),
                "estado": state,
                "pagina": page,
                "capitulo": name in chapters,
                "motivo": reason,
            }
        )
    return rows


def _table(rows: list[dict]) -> list[str]:
    lines = ["| Procedimiento | Estado | Página proc.pdf | Motivo y límites |", "|---|---|---|---|"]
    for row in rows:
        reason = " ".join(row["motivo"].split()).replace("|", "\\|")
        lines.append(
            f"| {row['procedimiento']} | {row['estado']} | "
            f"{row['pagina'] or 'sin página'} | {reason} |"
        )
    return lines


def escribir(destino: Path, filas: list[dict]) -> None:
    """Escribe un Markdown estable sin fechas ni rutas de la máquina."""
    indexed = [row for row in filas if row["capitulo"]]
    extra = [row for row in filas if not row["capitulo"]]
    counts = Counter(row["estado"] for row in indexed)
    lines = [
        "# Cobertura de procedimientos",
        "",
        "Generado por `uv run python tools/cobertura_procs.py`. Subinforme de C-22; "
        "G-17 lo integra en `docs/cobertura.md` sin sobrescribir este archivo.",
        "",
        f"El índice local contiene **{len(indexed)} capítulos únicos** de procedimientos. "
        "Las menciones sin capítulo se presentan aparte y no aumentan ese denominador.",
        "",
        "`traducido` significa que hay una rama o regla ejecutable para un subconjunto, "
        "no cobertura completa ni validación en Studio. `reporte` y `limpieza` son políticas "
        "condicionadas; `pendiente` conserva código P-; `no_verificado` no tiene equivalencia "
        "ni familia asignada. `fuera_de_alcance` es una decisión del producto con motivo y página, "
        "no una equivalencia ni permiso para omitir silenciosamente ese PROC.",
        "",
        "Fuentes: `docs/referencia/sas/proc.INDEX.md`, `rules/sas/catalogo/procs-usados.yaml`, "
        "`procedimientos-migrador.yaml`, `rules/sas/procs/*.yaml` y ramas de `lower_procs.py`/"
        "`lower_sql.py`. Las páginas de capítulo localizan documentación; no prueban todas "
        "sus opciones. Las equivalencias puntuales se documentan en las reglas y la política.",
        "",
        "## Resumen de capítulos",
        "",
        "| Estado | Capítulos |",
        "|---|---|",
    ]
    lines += [f"| {state} | {count} |" for state, count in sorted(counts.items())]
    lines += ["", "## Procedimientos de la guía", "", *_table(indexed)]
    lines += ["", "## Menciones de catálogo o reglas sin capítulo propio", "", *_table(extra), ""]
    destino.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    escribir(DESTINATION, clasificar(INDEX, CATALOG, PROCS_DIR))
