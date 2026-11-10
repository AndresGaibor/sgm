"""`IF cond THEN DO; ... END; ELSE ...` de un DATA step como asignaciones condicionales por columna.

SAS evalúa la cadena `IF / ELSE IF / ELSE` una vez por fila y ejecuta las asignaciones de la rama
que se cumple. Se baja a una asignación por cada columna que la cadena toca: «si se cumple la
condición de esta rama, el valor de esta rama; si no, el de la siguiente; al final el `ELSE` o, si
no hay, la columna tal como estaba». Es el mismo `conditional` que ya produce una asignación
`IF ... THEN x = ...`.

Lo que cambiaría el resultado respecto a SAS se deja sin traducir (devuelve `None` y la cadena sigue
el camino de siempre, con su nota):

* una columna asignada dos veces en la misma rama (la segunda ve el valor de la primera);
* una expresión que lee otra columna que la cadena también asigna (en SAS ve el valor nuevo);
* dos columnas asignadas que las condiciones también leen: la condición se evalúa una sola vez,
  antes de cualquier asignación, y reproducirlo exigiría una columna auxiliar;
* sentencias dentro del bloque que no son asignaciones (otro `IF`, `OUTPUT`...).
"""

from __future__ import annotations

import re

from sgm.frontend.datastep import DsStatement

_IF = re.compile(r"(?is)^if\s+(.*?)\s+then\s+(.+)$")
_ELSE_IF = re.compile(r"(?is)^else\s+if\s+(.*?)\s+then\s+(.+)$")
_ELSE = re.compile(r"(?is)^else\s+(.+)$")
_ASIGNA = re.compile(r"(?is)^(\w+)\s*=\s*(.+)$")
_DO = re.compile(r"(?is)^do$")

Rama = tuple[str | None, list[tuple[str, str]]]


def _palabras(texto: str) -> set[str]:
    sin_cadenas = re.sub(r"'[^']*'|\"[^\"]*\"", " ", texto)
    return {palabra.lower() for palabra in re.findall(r"[A-Za-z_]\w*", sin_cadenas)}


def _rama(
    stmts: list[DsStatement], cursor: int, cuerpo: str
) -> tuple[list[tuple[str, str]], int] | None:
    """Asignaciones de una rama: `x = e` en línea, o un bloque `DO; ...; END`."""
    cuerpo = cuerpo.strip()
    if _DO.fullmatch(cuerpo):
        asignaciones: list[tuple[str, str]] = []
        while cursor < len(stmts) and stmts[cursor].kind != "end":
            if stmts[cursor].kind != "assign":
                return None
            asignaciones.append(
                (stmts[cursor].fields["target"].lower(), stmts[cursor].fields["expression"])
            )
            cursor += 1
        if cursor >= len(stmts):
            return None
        return asignaciones, cursor + 1
    simple = _ASIGNA.fullmatch(cuerpo)
    if simple is None:
        return None
    return [(simple.group(1).lower(), simple.group(2).strip())], cursor


def bloque_condicional(stmts: list[DsStatement], index: int) -> tuple[list[dict], int] | None:
    """Asignaciones equivalentes a la cadena que empieza en `index`, y la sentencia que sigue."""
    inicio = stmts[index]
    if inicio.kind != "if":
        return None
    primera = _IF.fullmatch(inicio.text.strip())
    if primera is None:
        return None
    resultado = _rama(stmts, index + 1, primera.group(2))
    if resultado is None:
        return None
    asignaciones, cursor = resultado
    ramas: list[Rama] = [(primera.group(1).strip(), asignaciones)]
    hay_bloque = _DO.fullmatch(primera.group(2).strip()) is not None
    while cursor < len(stmts) and stmts[cursor].kind == "if":
        texto = stmts[cursor].text.strip()
        encontrada = _ELSE_IF.fullmatch(texto)
        condicion: str | None = None
        if encontrada:
            condicion, cuerpo = encontrada.group(1).strip(), encontrada.group(2)
        else:
            solo_else = _ELSE.fullmatch(texto)
            if solo_else is None:
                break
            cuerpo = solo_else.group(1)
        resultado = _rama(stmts, cursor + 1, cuerpo)
        if resultado is None:
            return None
        asignaciones, cursor = resultado
        hay_bloque = hay_bloque or _DO.fullmatch(cuerpo.strip()) is not None
        ramas.append((condicion, asignaciones))
        if condicion is None:
            break
    if not hay_bloque:
        return None  # sin DO lo resuelve `_conditional_assignment`
    return _como_asignaciones(ramas, cursor)


def _como_asignaciones(ramas: list[Rama], siguiente: int) -> tuple[list[dict], int] | None:
    con_condicion = [(c, a) for c, a in ramas if c is not None]
    por_defecto = next((a for c, a in ramas if c is None), [])
    objetivos: list[str] = []
    for _, asignaciones in ramas:
        nombres = [t for t, _ in asignaciones]
        if len(nombres) != len(set(nombres)):
            return None
        objetivos += [t for t in nombres if t not in objetivos]
    condiciones: set[str] = set()
    for condicion, _ in con_condicion:
        condiciones |= _palabras(condicion or "")
    leidos_en_condicion = [t for t in objetivos if t in condiciones]
    if len(leidos_en_condicion) > 1:
        return None
    for _, asignaciones in ramas:
        for objetivo, expresion in asignaciones:
            # Una autoasignación representa conservar el valor que ya tenga la columna (incluidas
            # asignaciones anteriores del DATA step); no lee otra asignación de esta cadena.
            if expresion.strip().lower() == objetivo:
                continue
            if _palabras(expresion) & set(objetivos):
                return None
    # La columna que las condiciones leen se asigna la última: hasta entonces conserva su valor.
    orden = [t for t in objetivos if t not in leidos_en_condicion] + leidos_en_condicion
    resultado: list[dict] = []
    for objetivo in orden:
        otra = _valor(por_defecto, objetivo)
        pares = [{"condition": c, "expression": _valor(a, objetivo)} for c, a in con_condicion]
        condicional = (
            {"condition": pares[0]["condition"], "otherwise": otra}
            if len(pares) == 1
            else {"branches": pares, "otherwise": otra}
        )
        resultado.append(
            {"target": objetivo, "expression": pares[0]["expression"], "conditional": condicional}
        )
    return resultado, siguiente


def _valor(asignaciones: list[tuple[str, str]], objetivo: str) -> str:
    """Lo que la rama le da a la columna; si no la toca, la columna tal como estaba."""
    return next((e for t, e in asignaciones if t == objetivo), objetivo)


__all__ = ["bloque_condicional"]
