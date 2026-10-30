"""Selector de ambiente: una macro cuyo cuerpo solo elige valores de variables según un ambiente.

Forma que se reconoce por estructura, sin mirar nombres:

    %if &X eq <lit> %then %do; %let Y=<valor>; ... %end;
    %else %if &X eq <lit> %then %do; %let Y=<valor>; ... %end;     (una o más veces)
    [%put ...;]

Cada rama es un contexto del Job, no código: el expansor no expande sus ramas. El resultado es un
grupo de contexto con una variable por cada `Y` y un contexto por cada literal de `X`.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from sgm.frontend.lexer import Stmt

_HEAD = re.compile(r"\s*(?:%else\s*)?%if\s+&(\w+)\s+eq\s+(\w+)\s*%then\s*;?\s*%do\s*;", re.I)
_LET = re.compile(r"\s*%let\s+(\w+)\s*=\s*([^;]*?)\s*;", re.I)
_END = re.compile(r"\s*%end\s*;", re.I)
_TAIL = re.compile(r"(\s*%put\b[^;]*;)*\s*", re.I)


@dataclass(frozen=True)
class Selector:
    name: str  # nombre de la macro
    variable: str  # X: la variable de ambiente
    contexts: dict[str, dict[str, str]] = field(default_factory=dict)  # literal -> {Y: valor}

    @property
    def variables(self) -> list[str]:
        """Variables Y, en el orden en que aparecen en el primer contexto."""
        first = next(iter(self.contexts.values()), {})
        return list(first)


@dataclass(frozen=True)
class SelectorUse:
    """Una invocación del selector en un archivo, en la línea indicada."""

    file: str
    line: int
    selector: Selector


def _normalized(body: list[Stmt]) -> str:
    """Texto del cuerpo con cada sentencia terminada en `;`, tal como el parser la verá."""
    return "".join(s.text.strip().rstrip(";").strip() + ";" for s in body)


def detect(name: str, body: list[Stmt]) -> Selector | None:
    """El selector de `body` si su forma es la de arriba; None si no lo es.

    Exige al menos dos literales distintos: con uno solo no hay una elección de ambiente.
    """
    text = _normalized(body)
    variable: str | None = None
    contexts: dict[str, dict[str, str]] = {}
    pos = 0
    while (head := _HEAD.match(text, pos)) is not None:
        found, literal = head.group(1).lower(), head.group(2)
        if variable is None:
            variable = found
        elif found != variable:
            return None
        if literal in contexts:
            return None
        pos = head.end()
        assigns: dict[str, str] = {}
        while (let := _LET.match(text, pos)) is not None:
            assigns[let.group(1)] = let.group(2)
            pos = let.end()
        end = _END.match(text, pos)
        if not assigns or end is None:
            return None
        contexts[literal] = assigns
        pos = end.end()
    if variable is None or len(contexts) < 2 or _TAIL.fullmatch(text, pos) is None:
        return None
    return Selector(name, variable, contexts)
