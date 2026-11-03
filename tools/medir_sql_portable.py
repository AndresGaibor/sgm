"""Mide cuántas sentencias de PROC SQL de un archivo SAS son portables a SQL de base (WITH).

Uso: uv run python tools/medir_sql_portable.py <archivo.sas>

Clasifica cada sentencia de PROC SQL con las mismas reglas del código:
- `no_consulta`: pass-through, EXECUTE, CONNECT, INSERT, DELETE, DROP u otra sentencia que no es
  una consulta.
- `into`: SELECT ... INTO :macro; el valor va al programa anfitrión (sql-semantica.yaml).
- `macro`: referencias a macro variables en la consulta (no se conocen hasta ejecutar).
- `parse_error`: sqlglot no puede leer la sentencia.
- `subconsulta_o_ventana`: subconsultas o funciones de ventana (no se traducen todavía).
- `agregado_sin_group_by`: columnas sin agregar junto a agregados (pendiente).
- `funcion_no_portable`: alguna función sin status portable en sql-functions.json.
- `portable`: el resto.

Imprime el recuento por clase y por función no portable. No escribe archivos.
"""

from __future__ import annotations

import re
import sys
from collections import Counter
from pathlib import Path

from sgm.frontend.splitter import split_nodes
from sgm.frontend.sql import SqlStatement
from sgm.frontend.sql_normalize import normalize
from sgm.frontend.steps import ProcSql, parse_node
from sgm.ir.sql_portability import unportable_functions
from sgm.ir.sql_tree import SqlNotSelect, SqlParseError, build

NO_CONSULTA = {"select_passthrough", "execute", "connect", "disconnect", "insert", "delete"}
NO_CONSULTA |= {"drop_table", "create_like", "other"}
_AGREGADO = re.compile(r"(?i)\b(sum|count|avg|mean|min|max|std|stddev|n|nmiss|range|median)\s*\(")


def _clasificar(st: SqlStatement) -> tuple[str, list[str]]:
    """Clase de una sentencia y, si es `funcion_no_portable`, los nombres de función."""
    if st.kind in NO_CONSULTA:
        return "no_consulta", []
    normalized = normalize(st.text)
    if normalized.into_vars:
        return "into", []
    if normalized.macros:
        return "macro", []
    try:
        tree = build(normalized.text)
    except SqlParseError:
        return "parse_error", []
    except SqlNotSelect:
        return "no_consulta", []
    if any(spec.subqueries or spec.windows for spec in tree.selects):
        return "subconsulta_o_ventana", []
    for spec in tree.selects:
        agregados = [it for it in spec.items if not it.star and _AGREGADO.search(it.expression)]
        plain = [it for it in spec.items if not it.star and not _AGREGADO.search(it.expression)]
        if agregados and plain and not spec.group_by:
            return "agregado_sin_group_by", []
    nombres: list[str] = []
    for spec in tree.selects:
        textos = [it.expression for it in spec.items if not it.star]
        textos += [spec.where or "", spec.having or ""]
        textos += [j.on or "" for j in spec.joins]
        textos += [expr for expr, _ in spec.order_by] + spec.group_by
        for texto in textos:
            if texto:
                nombres += unportable_functions(texto)
    if nombres:
        return "funcion_no_portable", sorted(set(nombres))
    return "portable", []


def medir(texto: str) -> tuple[Counter, Counter]:
    clases: Counter = Counter()
    funciones: Counter = Counter()
    for node in split_nodes(texto):
        for step in parse_node(node).steps:
            if not isinstance(step, ProcSql):
                continue
            for st in step.statements:
                clase, nombres = _clasificar(st)
                clases[clase] += 1
                funciones.update(nombres)
    return clases, funciones


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("uso: medir_sql_portable.py <archivo.sas>", file=sys.stderr)
        return 2
    texto = Path(argv[1]).read_text(encoding="utf-8", errors="replace")
    clases, funciones = medir(texto)
    total = sum(clases.values())
    print(f"sentencias de PROC SQL: {total}")
    for clase, n in clases.most_common():
        print(f"  {clase}: {n}")
    if funciones:
        print("funciones no portables:")
        for nombre, n in funciones.most_common():
            print(f"  {nombre}: {n}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
