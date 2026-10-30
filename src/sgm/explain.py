"""`sgm explain <archivo>:<línea>` (F1.8): qué operadores, pasadas, huecos y notas tiene una línea.

Compila el archivo y busca, por la evidencia de cada nodo, los que cubren la línea:
- operadores del plan final, con su estado y componente, y las pasadas que los crearon o que
  absorbieron otros en ellos (la fusión une la evidencia en el operador que sobrevive);
- huecos y entradas de `not_migrated` que cubren la línea, con su dueño y arreglo.

Límite: lo que la fontanería quita (pasada 2) no está en el plan final, así que no tiene línea que
mostrar. Si una línea es fontanería, la explicación lo dice en lugar de inventar una relación.
"""

from __future__ import annotations

from pathlib import Path

from sgm import motivos
from sgm.catalog.config import Env
from sgm.compile import compile_project
from sgm.ir.models import Evidence
from sgm.redaction import redact


def _cubre(evidencia: list[Evidence], archivo: str, linea: int) -> bool:
    return any(ev.file == archivo and ev.line_start <= linea <= ev.line_end for ev in evidencia)


def explicar(archivo: Path, linea: int, env: Env | None = None) -> str:
    """Texto de la explicación de una línea de un programa SAS. Lanza ValueError si no existe."""
    texto = archivo.read_text(encoding="utf-8", errors="replace")
    nombre = archivo.name
    lineas = texto.splitlines()
    if not 1 <= linea <= len(lineas):
        raise ValueError(f"la línea {linea} no existe: {nombre} tiene {len(lineas)} líneas")
    compiled, _ = compile_project({nombre: texto}, env=env)
    resultado = compiled[nombre]
    plan = resultado.plan
    mostrada = redact(texto, nombre).splitlines()[linea - 1].strip()

    salida = [f"{nombre}:{linea}  {mostrada}"]
    operadores = [op for op in plan.graph.operators() if _cubre(op.evidence, nombre, linea)]
    for op in operadores:
        componente = (op.component or {}).get("name", "ninguno")
        regla = (op.component or {}).get("rule")
        etiqueta = f", regla {regla}" if regla else ""
        salida.append(f"  operador {op.id} ({op.kind}, {op.status}) -> {componente}{etiqueta}")
        for ev in op.evidence:
            if ev.file == nombre and ev.label:
                salida.append(f"    paso SAS: {ev.label}")
                break
        for log in resultado.logs:
            if op.id in log.created:
                salida.append(f"    creado por la pasada {log.name}")
            if op.id in log.merged:
                salida.append(f"    absorbió otros operadores en la pasada {log.name}")
    for gap in plan.gaps:
        if _cubre(gap.evidence, nombre, linea):
            motivo = motivos.de(gap.reason)
            dueño = motivo.dueño if motivo else "sin dueño"
            arreglo = motivo.se_cierra_con if motivo else "sin arreglo registrado"
            salida.append(f"  hueco {gap.reason} (firma {gap.signature}, dueño {dueño})")
            salida.append(f"    se cierra con: {arreglo}")
    for nota in plan.not_migrated:
        if _cubre(nota.evidence, nombre, linea):
            salida.append(f"  no migrado: {nota.what} -> {nota.talend}")
    if len(salida) == 1:
        salida.append(
            "  ningún operador, hueco ni nota cubre esta línea. Puede ser un comentario, una "
            "cabecera, o fontanería quitada por una pasada (que no deja línea en el plan final)."
        )
    return "\n".join(salida)
