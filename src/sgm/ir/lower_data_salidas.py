"""Salidas condicionales del DATA step (OUTPUT dentro de IF o en varias ramas) a operadores `split`.

Se extrajo de `lower_data.py` sin cambio de comportamiento (B-5, límite de 300 líneas).
"""

from __future__ import annotations

import re

from sgm.frontend.datastep import DsStatement
from sgm.ir.builder import qualify
from sgm.ir.models import Operator

_OUTPUT_IN_IF = re.compile(
    r"(?is)^(?:if\s+(?P<cond>.*?)\s+then\s+|else\s+if\s+(?P<else_if>.*?)\s+then\s+|else\s+)"
    r"output(?:\s+(?P<targets>[\w.&]+(?:\s+[\w.&]+)*))?"
)


def _conditional_output(s: DsStatement) -> dict | None:
    """`if c then output t;` o `else output t;` como división. None si no aplica."""
    if s.fields.get("first_last"):
        return None
    m = _OUTPUT_IN_IF.match(s.text.strip())
    if not m:
        return None
    cond = m.group("cond") or m.group("else_if")
    targets = re.findall(r"[\w.&]+", m.group("targets") or "")
    result = {
        "target": targets[0] if targets else None,
        "condition": cond.strip() if cond else None,
        "branch": "then" if m.group("cond") else "else_if" if m.group("else_if") else "else",
    }
    if len(targets) > 1:
        result["targets"] = targets
    return result


def _conditional_output_chain(
    stmts: list[DsStatement], index: int, default_targets: list[str]
) -> tuple[list[dict], list[str], int, bool] | None:
    """Agrupa salidas condicionales y deja una rama sin filtro para continuar el DATA step."""
    primera = _conditional_output(stmts[index])
    if primera is None or primera.get("branch") != "then" or not primera.get("condition"):
        return None
    sin_destino = not primera.get("target") and not primera.get("targets")
    destinos_iniciales = primera.get("targets") or (
        [primera["target"]] if primera.get("target") else []
    )
    if not destinos_iniciales:
        destinos_iniciales = default_targets
    alternativas = [(str(primera["condition"]), destinos_iniciales)]
    cursor = index + 1
    hay_else = False
    while cursor < len(stmts):
        siguiente = _conditional_output(stmts[cursor])
        if siguiente is None:
            break
        if siguiente.get("branch") == "else_if" and not hay_else:
            objetivos = siguiente.get("targets") or (
                [siguiente["target"]] if siguiente.get("target") else default_targets
            )
            alternativas.append((str(siguiente["condition"]), objetivos))
            cursor += 1
            continue
        if siguiente.get("branch") == "else" and not hay_else:
            objetivos = siguiente.get("targets") or (
                [siguiente["target"]] if siguiente.get("target") else default_targets
            )
            alternativas.append(("", objetivos))
            hay_else = True
            cursor += 1
        break
    terminal = cursor == len(stmts)
    if cursor <= index + 1 and terminal and not sin_destino:
        return None  # IF ... THEN OUTPUT terminal se conserva como split simple.
    if cursor < len(stmts):
        siguiente = _conditional_output(stmts[cursor])
        if siguiente and siguiente.get("branch") in {"else_if", "else"}:
            return None
    if any(
        not destino or destino.lower() == "_null_"
        for _condicion, objetivos in alternativas
        for destino in objetivos
    ):
        return None
    if any(
        len({destino.casefold() for destino in objetivos}) != len(objetivos)
        for _condicion, objetivos in alternativas
    ):
        return None
    condiciones = [condicion for condicion, _objetivos in alternativas if condicion]
    ramas_alternativas: list[tuple[str, list[str]]] = []
    anteriores: list[str] = []
    for condicion, objetivos in alternativas:
        if condicion:
            predicados = [*(f"not ({anterior})" for anterior in anteriores), f"({condicion})"]
            expresion_rama = " and ".join(predicados)
            anteriores.append(condicion)
        else:
            expresion_rama = " and ".join(f"not ({anterior})" for anterior in condiciones)
        ramas_alternativas.append((expresion_rama, objetivos))
    expresiones_por_destino: dict[str, list[str]] = {}
    destino_por_clave: dict[str, str] = {}
    for expresion_rama, objetivos in ramas_alternativas:
        for destino in objetivos:
            clave = qualify(destino).casefold()
            destino_por_clave.setdefault(clave, qualify(destino))
            expresiones_por_destino.setdefault(clave, []).append(expresion_rama)
    todas_las_ramas_tienen_else = hay_else
    ramas: list[dict] = []
    destinos_unicos = list(destino_por_clave.values())
    for clave, destino in destino_por_clave.items():
        expresiones = expresiones_por_destino[clave]
        if todas_las_ramas_tienen_else and len(expresiones) == len(alternativas):
            ramas.append({"outputs": [destino]})
        else:
            combinada = (
                expresiones[0]
                if len(expresiones) == 1
                else " or ".join(f"({expresion})" for expresion in expresiones)
            )
            ramas.append({"expression": combinada, "outputs": [destino]})
    return ramas, destinos_unicos, cursor - 1, terminal


def _output_sequence(stmts: list[DsStatement], index: int) -> tuple[list[str], int] | None:
    """Agrupa OUTPUT consecutivos sin condición ni destinos repetidos."""
    if index >= len(stmts) or stmts[index].kind != "output":
        return None
    destinos: list[str] = []
    cursor = index
    while cursor < len(stmts) and stmts[cursor].kind == "output":
        actuales = stmts[cursor].fields.get("targets") or []
        if not actuales:
            return None
        destinos.extend(nombre for nombre in actuales if nombre.lower() != "_null_")
        cursor += 1
    if cursor - index < 2 or not destinos:
        return None
    if len({nombre.lower() for nombre in destinos}) != len(destinos):
        return None
    return destinos, cursor - 1


def _undeclared_output_targets(
    stmts: list[DsStatement], declared_outputs: list[str]
) -> tuple[list[DsStatement], set[str]] | None:
    """SAS exige destinos declarados en DATA (`lestmtsref`, PDF p. 274; impresa p. 261)."""
    declarados = {qualify(destino).casefold() for destino in declared_outputs}
    sentencias: list[DsStatement] = []
    faltantes: set[str] = set()
    for sentencia in stmts:
        destinos = _output_targets(sentencia)
        no_declarados = {
            destino for destino in destinos if qualify(destino).casefold() not in declarados
        }
        if no_declarados:
            sentencias.append(sentencia)
            faltantes.update(no_declarados)
    return (sentencias, faltantes) if sentencias else None


def _repeated_output_targets(
    stmts: list[DsStatement], default_outputs: list[str]
) -> tuple[list[DsStatement], set[str]] | None:
    """Detecta escrituras múltiples al mismo destino en una iteración del DATA step."""
    vistos: dict[str, DsStatement] = {}
    sentencias: list[DsStatement] = []
    repetidos: set[str] = set()
    index = 0
    while index < len(stmts):
        sentencia = stmts[index]
        cadena = _conditional_output_chain(stmts, index, default_outputs)
        if cadena is not None:
            _ramas, destinos, ultimo, _terminal = cadena
            index = ultimo + 1
        else:
            destinos = _output_targets(sentencia, default_outputs)
            index += 1
        for destino in destinos:
            clave = qualify(destino).casefold()
            if clave in vistos:
                if vistos[clave] not in sentencias:
                    sentencias.append(vistos[clave])
                if sentencia not in sentencias:
                    sentencias.append(sentencia)
                repetidos.add(destino)
            else:
                vistos[clave] = sentencia
    return (sentencias, repetidos) if sentencias else None


def _output_targets(
    stmt: DsStatement, default_outputs: list[str] | None = None
) -> list[str]:
    destinos_por_defecto = default_outputs or []
    if stmt.kind == "output":
        return list(stmt.fields.get("targets") or destinos_por_defecto)
    if stmt.kind == "if":
        salida = _conditional_output(stmt)
        if salida:
            destinos = salida.get("targets") or ([salida["target"]] if salida.get("target") else [])
            return list(destinos or destinos_por_defecto)
    return []


def _note(op: Operator | None, text: str, status: str | None = None) -> None:
    if op is None:
        return
    op.notes.append(text)
    if status is not None and op.status == "soportado":
        op.status = status
