"""`ARRAY` y `DO` con límites constantes del DATA step, desenrollados a asignaciones (B-16).

`ARRAY a{3} x1 x2 x3;` declara los elementos de `a` como las columnas `x1`, `x2` y `x3`.
Un `DO i = 1 TO 3; ... END;` con límites constantes, sin `DO` anidado y con solo asignaciones
dentro, se desenrolla: cada vuelta es una copia del cuerpo con `i` y `a{i}` sustituidos por su valor
y su columna. Al terminar, SAS deja `i` en el límite superior más uno (`lestmtsref`, sentencia
iterativa `DO`), y se emite esa asignación.

Lo que no se desenrolla queda como antes (sentencia sin traducción):

* límites no constantes, `DO WHILE`, `DO UNTIL` o `DO` anidado;
* un índice constante fuera de rango (`a{4}` con tres elementos): SAS no lo calla y no se
  inventa valor (`P-ARRAY-FUERA-DE-RANGO`, aún sin código emitido);
* un cuerpo con algo que no es una asignación (`OUTPUT`, `IF`, `PUT`...).
"""

from __future__ import annotations

import re

from sgm.frontend.datastep import DsStatement

_ARRAY = re.compile(r"(?is)^array\s+(\w+)\s*\{\s*(\d+)\s*\}\s+(.+)$")
_DO_TO = re.compile(r"(?is)^do\s+(\w+)\s*=\s*(-?\d+)\s+to\s+(-?\d+)\s*$")
_ASIGNA = re.compile(r"(?is)^(\w+(?:\{[^}]*\})?)\s*=(?!=)\s*(.+)$")
_ELEMENTO = re.compile(r"(?i)\b(\w+)\s*\{\s*(\w+)\s*\}")
_PALABRAS_NO_ASIGNABLES = frozenset({"if", "else", "do", "end", "output", "put", "select", "when"})


class _Fuera(Exception):
    """Un índice constante fuera de los elementos del arreglo."""


def arreglos_declarados(stmts: list[DsStatement]) -> dict[str, list[str]]:
    """`ARRAY` con lista explícita de elementos: nombre (en minúsculas) -> columnas en orden."""
    arreglos: dict[str, list[str]] = {}
    for s in stmts:
        if s.kind != "array":
            continue
        encontrada = _ARRAY.fullmatch(s.text.strip())
        if encontrada is None:
            continue
        nombre = encontrada.group(1).lower()
        n, lista = int(encontrada.group(2)), encontrada.group(3)
        elementos = [e.lower() for e in lista.split()]
        if len(elementos) == n and all(re.fullmatch(r"\w+", e) for e in elementos):
            arreglos[nombre] = elementos
    return arreglos


def _sustituir(texto: str, variable: str, valor: int, arreglos: dict[str, list[str]]) -> str:
    """Sustituye `a{i}` y `i` por el elemento y el valor, fuera de los literales de texto."""

    def elemento(m: re.Match) -> str:
        nombre = m.group(1).lower()
        if nombre not in arreglos:
            return m.group(0)
        indice = valor if m.group(2).lower() == variable else int(m.group(2))
        if not 1 <= indice <= len(arreglos[nombre]):
            raise _Fuera(f"{nombre}{{{indice}}}")
        return arreglos[nombre][indice - 1]

    partes = re.split(r"('[^']*'|\"[^\"]*\")", texto)
    for k in range(0, len(partes), 2):  # solo los trozos fuera de literales
        partes[k] = _ELEMENTO.sub(elemento, partes[k])
        partes[k] = re.sub(rf"(?i)\b{re.escape(variable)}\b", str(valor), partes[k])
    return "".join(partes)


def bucle_desenrollado(
    stmts: list[DsStatement], index: int, arreglos: dict[str, list[str]]
) -> tuple[list[tuple[str, str]], int] | None:
    """Asignaciones (destino, expresión) del `DO` en `index`, y el índice de su `END`."""
    cabecera = _DO_TO.fullmatch(stmts[index].text.strip())
    if cabecera is None:
        return None
    variable = cabecera.group(1).lower()
    desde, hasta = int(cabecera.group(2)), int(cabecera.group(3))
    cuerpo: list[tuple[str, str]] = []
    cursor = index + 1
    while cursor < len(stmts) and stmts[cursor].kind != "end":
        texto = stmts[cursor].text.strip()
        asigna = _ASIGNA.fullmatch(texto)
        if asigna is None or asigna.group(1).split("{")[0].lower() in _PALABRAS_NO_ASIGNABLES:
            return None
        cuerpo.append((asigna.group(1), asigna.group(2).strip()))
        cursor += 1
    if cursor >= len(stmts) or not cuerpo or hasta < desde:
        return None
    try:
        salida: list[tuple[str, str]] = []
        for valor in range(desde, hasta + 1):
            for destino, expresion in cuerpo:
                salida.append(
                    (
                        _sustituir(destino, variable, valor, arreglos).lower(),
                        _sustituir(expresion, variable, valor, arreglos),
                    )
                )
    except _Fuera:
        return None
    salida.append((variable, str(hasta + 1)))  # tras el bucle, la variable vale el límite más uno
    return salida, cursor
