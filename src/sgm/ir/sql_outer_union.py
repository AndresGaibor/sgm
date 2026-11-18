"""OUTER UNION de SAS: reconocimiento léxico y límites (sqlproc.pdf, p. 135)."""

from __future__ import annotations

from sqlglot import Tokenizer
from sqlglot.tokens import TokenType


class SqlOuterUnionError(ValueError):
    """La construcción queda pendiente sin inventar columnas ni equivalencias."""

    def __init__(self, detail: str, code: str = "P-OUTER-UNION-CORR-SIN-SOPORTE"):
        self.code = code
        super().__init__(f"{detail} (sqlproc.pdf, p. 135)")


def prepare(sql: str) -> tuple[str, str | None]:
    """Adapta solo tokens del operador; los literales y comentarios quedan intactos."""
    tokens = Tokenizer().tokenize(sql)
    replacements = []
    modes = []
    depth = 0
    unions = 0
    for i, token in enumerate(tokens):
        depth += (token.token_type == TokenType.L_PAREN) - (
            token.token_type == TokenType.R_PAREN
        )
        if token.token_type in (TokenType.UNION, TokenType.EXCEPT, TokenType.INTERSECT):
            unions += 1
        if token.token_type != TokenType.OUTER or i + 1 >= len(tokens):
            continue
        if tokens[i + 1].token_type != TokenType.UNION:
            continue
        if depth:
            raise SqlOuterUnionError("OUTER UNION anidado sin semántica demostrada")
        end = tokens[i + 1]
        corr = i + 2 < len(tokens) and tokens[i + 2].text.upper() in ("CORR", "CORRESPONDING")
        if corr:
            end = tokens[i + 2]
        modes.append("corr" if corr else "plain")
        replacements.append((token.start, end.end + 1))
    if not replacements:
        return sql, None
    if len(set(modes)) != 1 or unions != len(replacements):
        raise SqlOuterUnionError("OUTER UNION combinado con otros operadores de conjuntos")
    for start, end in reversed(replacements):
        sql = sql[:start] + "UNION ALL" + sql[end:]
    return sql, modes[0]


def validate(selects, mode: str) -> None:
    """Exige nombres demostrados por SELECT; no asigna alias a expresiones anónimas."""
    if mode == "plain":
        seen = set()
        for spec in selects:
            explicit = {
                (item.alias or item.column).casefold() for item in spec.items
                if not item.star and item.column != "*" and (item.alias or item.column)
            }
            if seen.intersection(explicit):
                raise SqlOuterUnionError(
                    "OUTER UNION sin CORR repite nombres entre ramas; no se inventan alias",
                    "P-OUTER-UNION-COLUMNAS-REPETIDAS",
                )
            seen.update(explicit)
        raise SqlOuterUnionError(
            "OUTER UNION sin CORR conserva columnas separadas y sigue pendiente",
            "P-OUTER-UNION-SIN-CORR",
        )
    for spec in selects:
        explicit = [
            (item.alias or item.column or "").casefold() for item in spec.items if not item.star
        ]
        if (
            any(not name for name in explicit)
            or len(explicit) != len(set(explicit))
            or any(item.column == "*" for item in spec.items)
            or (any(item.star for item in spec.items) and len(spec.items) != 1)
            or spec.order_by or spec.distinct or spec.subqueries or spec.semis or spec.windows
        ):
            raise SqlOuterUnionError("rama con nombres o cláusulas fuera del alcance demostrado")
