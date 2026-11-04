"""Textos que comparten página y diagrama: título visible de un paso y resumen en lenguaje llano.

Un paso de tipo PROC repite su tipo como título ("PROC SORT / PROC SORT"). En ese caso el título
muestra el dataset que el paso escribe, o el que lee si no escribe ninguno.
"""

from __future__ import annotations

from sgm.flow.model import FlowModel, FlowStep


def etiqueta_paso(step: FlowStep) -> str:
    """Texto principal de un paso: su título, o el dataset que produce si el título es el tipo."""
    if step.title != step.type_name:
        return step.title
    if step.writes:
        return f"→ {step.writes[0]}"
    if step.reads:
        return f"← {step.reads[0]}"
    return step.type_name


def es_dinamico(nombre: str) -> bool:
    """Un nombre con `&` lleva una macrovariable que no se resolvió: depende de la ejecución."""
    return "&" in nombre


def _cuenta(n: int, singular: str, plural: str) -> str:
    return f"{n} {singular if n == 1 else plural}"


def _lista(nombres: list[str]) -> str:
    """Nombres separados por comas, con `y` antes del último."""
    if len(nombres) <= 1:
        return "".join(nombres)
    return ", ".join(nombres[:-1]) + " y " + nombres[-1]


def frase_resumen(model: FlowModel, salidas: list[str]) -> str:
    """Una frase que dice qué lee el programa, cuántos pasos tiene y qué deja al final."""
    if not model.steps:
        return "El programa no tiene pasos de datos: solo define configuración o macros."
    frases: list[str] = []
    externas = model.external_inputs
    if externas:
        frases.append(
            f"lee {_cuenta(len(externas), 'entrada externa', 'entradas externas')} "
            f"({_lista(externas)})"
        )
    frases.append(f"ejecuta {_cuenta(len(model.steps), 'paso', 'pasos')}")
    if salidas:
        frases.append(
            f"deja {_cuenta(len(salidas), 'salida final', 'salidas finales')} ({_lista(salidas)})"
        )
    texto = ", ".join(frases) + "."
    return texto[0].upper() + texto[1:]
