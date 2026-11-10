"""Optimización del plan antes de escribir los Jobs: el diseño que haría una persona en Talend.

El plan que sale del SAS conserva su forma: un paso por sentencia y una tabla de `WORK` entre cada
dos. Traducido tal cual da un Job literal. Aquí el plan se reescribe para que diga lo mismo con el
diseño de Talend: las tablas intermedias que nadie más usa desaparecen y sus pasos se hacen en un
solo `tMap`.

Cada cambio se demuestra antes de hacerse y queda anotado en `Informe.decisiones`, que el comando
escribe en `decisiones-tomadas.md`. Lo que no se puede demostrar se deja como estaba.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field

from sgm.ir.models import Plan
from sgm.optimizar.cadenas import FUSIONABLES, NoFusionable, fundir, lecturas_por_tabla
from sgm.optimizar.duplicados import unir_duplicados


@dataclass(frozen=True)
class Decision:
    """Un cambio de diseño: qué se hizo, sobre qué líneas del SAS y por qué es lo mismo."""

    regla: str
    resumen: str
    lineas: tuple[int, ...] = ()
    tabla: str = ""  # tabla intermedia que dejó de existir, sin biblioteca


@dataclass
class Informe:
    decisiones: list[Decision] = field(default_factory=list)
    # Operadores del plan original que ya no están: los representa el operador que los absorbió.
    absorbidos: dict[str, str] = field(default_factory=dict)


def _lineas(plan: Plan, op_id: str) -> tuple[int, ...]:
    return tuple(sorted({ev.line_start for ev in plan.graph.operator(op_id).evidence}))


def _quitar_de_trabajos(plan: Plan, quitados: set[str]) -> None:
    for job in _trabajos(plan):
        job.subjobs = [[i for i in sub if i not in quitados] for sub in job.subjobs]


def _unir_duplicados(plan: Plan, informe: Informe) -> bool:
    lineas = {op.id: _lineas(plan, op.id) for op in plan.graph.operators()}
    clases = {op.id: op.kind for op in plan.graph.operators()}
    unidos = unir_duplicados(plan)
    for sobra, queda in unidos:
        informe.absorbidos[sobra] = queda
        if clases[sobra] == "read":
            continue  # leer dos veces la misma tabla no es un paso: es el mismo flujo
        donde = ", ".join(str(n) for n in lineas[sobra]) or "?"
        informe.decisiones.append(
            Decision(
                "calcular-una-vez",
                f"el paso de la línea {donde} repite un cálculo anterior con las mismas "
                "entradas: se hace una sola vez y el resultado se reparte",
                lineas[queda],
            )
        )
    _quitar_de_trabajos(plan, {sobra for sobra, _ in unidos})
    return bool(unidos)


def _fundir_cadenas(plan: Plan, informe: Informe) -> bool:
    """Una pasada en orden de flujo: el operador que queda de una fusión se vuelve a intentar."""
    lecturas_de = lecturas_por_tabla(plan)
    todos: set[str] = set()
    for op_id in plan.graph.topological():
        if op_id not in plan.graph or plan.graph.operator(op_id).kind not in FUSIONABLES:
            continue
        try:
            queda, quitados, tabla = fundir(plan, op_id, lecturas_de)
        except NoFusionable:
            continue
        todos |= set(quitados)
        for quitado in quitados:
            informe.absorbidos[quitado] = queda
        nombre = f"`WORK.{tabla}`" if tabla else "el cruce intermedio"
        informe.decisiones.append(
            Decision(
                "fundir-pasos-encadenados",
                f"{nombre} no se escribe: solo la lee el paso siguiente, y los dos se hacen "
                "en un mismo `tMap`",
                _lineas(plan, queda),
                tabla or "",
            )
        )
    if todos:
        _quitar_de_trabajos(plan, todos)
    return bool(todos)


def _trabajos(plan: Plan):
    pila = list(plan.jobs)
    while pila:
        job = pila.pop()
        yield job
        pila.extend(job.children)


def optimizar(plan: Plan) -> tuple[Plan, Informe]:
    """Copia del plan con el diseño optimizado y el informe de lo que cambió."""
    informe = Informe()
    copia = copy.deepcopy(plan)
    # Unir duplicados deja pasos con la misma entrada, y fundir cadenas deja pasos iguales: se
    # repite hasta que ninguna de las dos reglas cambia nada.
    while _unir_duplicados(copia, informe) | _fundir_cadenas(copia, informe):
        pass
    return (copia if informe.absorbidos else plan), informe


__all__ = ["Decision", "Informe", "optimizar"]
