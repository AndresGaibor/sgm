"""Constructores de los 14 operadores del plan lógico (MG-P1-03), con validación de parámetros.

Cada constructor corresponde a una operación de la sección 4 del plan maestro y devuelve un
`Operator` con su firma ya calculada. Valida sus parámetros y lanza `ValueError` con un mensaje en
español si faltan o no cumplen lo mínimo. El lowering existente sigue usando `Builder.op`; estos
constructores son la forma validada de crear operadores nuevos.

Correspondencia con `OPERATOR_KINDS` (ir/models.py):
  leer -> read | leer_archivo -> read_file | escribir -> write | filtrar -> filter
  proyectar -> select | renombrar -> rename | calcular -> derive | unir -> join
  combinar (MERGE) -> join | agregar -> aggregate | ordenar -> sort | deduplicar -> dedup
  concatenar -> union | pivotar -> pivot (sin lowering: hueco) | iterar -> iterate
  controlar -> stateful_row
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from sgm.ir.models import Evidence, Operator
from sgm.ir.signature import signature

TIPOS_UNION = ("inner", "left", "right", "full")
MODOS_SELECCION = ("keep", "drop")
MODOS_DEDUP = ("first", "last")


def _texto(valor: Any, nombre: str) -> str:
    if not isinstance(valor, str) or not valor.strip():
        raise ValueError(f"{nombre} debe ser un texto no vacío")
    return valor.strip()


def _lista(valor: Any, nombre: str, minimo: int = 1) -> list[str]:
    if isinstance(valor, str) or not isinstance(valor, Iterable):
        raise ValueError(f"{nombre} debe ser una lista de nombres")
    items = [_texto(v, f"cada elemento de {nombre}") for v in valor]
    if len(items) < minimo:
        raise ValueError(f"{nombre} necesita al menos {minimo} elemento(s)")
    return items


def _operador(
    op_id: str,
    kind: str,
    params: dict[str, Any],
    evidence: list[Evidence] | None,
    status: str = "soportado",
    notes: list[str] | None = None,
) -> Operator:
    return Operator(
        id=op_id,
        kind=kind,
        params=params,
        evidence=list(evidence or []),
        status=status,
        signature=signature(kind, params),
        notes=list(notes or []),
    )


def leer(op_id: str, dataset: str, in_flag: str | None = None, evidence=None) -> Operator:
    """Leer: una tabla del programa, con su bandera `IN=` si la tiene."""
    params = {"dataset": _texto(dataset, "dataset"), "in": in_flag or None}
    return _operador(op_id, "read", params, evidence)


def leer_archivo(
    op_id: str, datafile: str, outputs: list[str], evidence=None
) -> Operator:
    """Leer archivo: una fuente externa (PROC IMPORT, INFILE) que llena una o más tablas."""
    params = {
        "datafile": _texto(datafile, "datafile"),
        "outputs": _lista(outputs, "outputs"),
    }
    return _operador(op_id, "read_file", params, evidence)


def escribir(op_id: str, dataset: str, evidence=None) -> Operator:
    """Escribir: una tabla de salida del programa."""
    return _operador(op_id, "write", {"dataset": _texto(dataset, "dataset")}, evidence)


def filtrar(op_id: str, expression: str, evidence=None) -> Operator:
    """Filtrar: conserva las filas que cumplen la expresión (WHERE, subsetting IF)."""
    return _operador(op_id, "filter", {"expression": _texto(expression, "expression")}, evidence)


def proyectar(op_id: str, mode: str, names: list[str], evidence=None) -> Operator:
    """Proyectar: KEEP o DROP de columnas (SELECT de columnas en SQL)."""
    if mode not in MODOS_SELECCION:
        raise ValueError(f"mode debe ser {MODOS_SELECCION}, no '{mode}'")
    params = {"mode": mode, "names": [n.lower() for n in _lista(names, "names")]}
    return _operador(op_id, "select", params, evidence)


def renombrar(op_id: str, pairs: list[tuple[str, str]], evidence=None) -> Operator:
    """Renombrar: pares (origen, destino) de columnas."""
    if not pairs:
        raise ValueError("pairs necesita al menos un par")
    normal = []
    for par in pairs:
        if len(par) != 2:
            raise ValueError(f"cada par de renombrar debe tener origen y destino: {par!r}")
        normal.append([_texto(par[0], "origen").lower(), _texto(par[1], "destino").lower()])
    return _operador(op_id, "rename", {"pairs": normal}, evidence)


def calcular(op_id: str, assignments: list[dict[str, str]], evidence=None) -> Operator:
    """Calcular: asignaciones `target = expression` de columnas nuevas o modificadas."""
    if not assignments:
        raise ValueError("assignments necesita al menos una asignación")
    normal = []
    for asignacion in assignments:
        normal.append(
            {
                "target": _texto(asignacion.get("target", ""), "target"),
                "expression": _texto(asignacion.get("expression", ""), "expression"),
            }
        )
    return _operador(op_id, "derive", {"assignments": normal}, evidence)


def unir(
    op_id: str,
    join_type: str,
    by: list[str],
    sources: list[str],
    evidence=None,
) -> Operator:
    """Unir: JOIN de SQL con tipo explícito. Requiere dos fuentes y una llave."""
    if join_type not in TIPOS_UNION:
        raise ValueError(f"join_type debe ser {TIPOS_UNION}, no '{join_type}'")
    params = {
        "join_type": join_type,
        "by": [n.lower() for n in _lista(by, "by")],
        "sources": _lista(sources, "sources", minimo=2),
    }
    return _operador(op_id, "join", params, evidence)


def combinar(
    op_id: str,
    join_type: str,
    by: list[str],
    sources: list[str],
    evidence=None,
) -> Operator:
    """Combinar (MERGE): emparejamiento por llave. Mismo tipo que `unir`, con `by` y sin `keys`.

    La semántica fila con fila la aplica el intérprete; el emisor no lo traduce a tMap (hito 132m).
    """
    return unir(op_id, join_type, by, sources, evidence)


def agregar(
    op_id: str,
    group_by: list[str],
    aggregations: list[dict[str, str]],
    evidence=None,
) -> Operator:
    """Agregar: GROUP BY con agregados (expression y alias por cada uno)."""
    if not aggregations:
        raise ValueError("aggregations necesita al menos un agregado")
    normal = [
        {
            "expression": _texto(a.get("expression", ""), "expression"),
            "alias": _texto(a.get("alias", ""), "alias"),
        }
        for a in aggregations
    ]
    params = {
        "group_by": [g.lower() for g in _lista(group_by, "group_by", minimo=0)],
        "aggregations": normal,
    }
    return _operador(op_id, "aggregate", params, evidence)


def ordenar(op_id: str, by: list[str], descending: bool = False, evidence=None) -> Operator:
    """Ordenar: clave de orden (PROC SORT BY y ORDER BY)."""
    params = {"by": [n.lower() for n in _lista(by, "by")], "descending": bool(descending)}
    return _operador(op_id, "sort", params, evidence)


def deduplicar(op_id: str, by: list[str], keep: str = "first", evidence=None) -> Operator:
    """Deduplicar: una fila por clave (NODUP, NODUPKEY, DISTINCT sobre una clave)."""
    if keep not in MODOS_DEDUP:
        raise ValueError(f"keep debe ser {MODOS_DEDUP}, no '{keep}'")
    params = {"by": [n.lower() for n in _lista(by, "by")], "keep": keep}
    return _operador(op_id, "dedup", params, evidence)


def concatenar(op_id: str, sources: list[str], evidence=None) -> Operator:
    """Concatenar: SET de varias tablas o UNION ALL."""
    return _operador(
        op_id, "union", {"sources": _lista(sources, "sources", minimo=2)}, evidence
    )


def pivotar(
    op_id: str, by: list[str], var: str, evidence=None
) -> Operator:
    """Pivotar (PROC TRANSPOSE): operador nuevo, sin lowering todavía; queda como hueco."""
    params = {"by": [n.lower() for n in _lista(by, "by", minimo=0)], "var": _texto(var, "var")}
    return _operador(
        op_id,
        "pivot",
        params,
        evidence,
        status="hueco",
        notes=["PROC TRANSPOSE sin traducción: pendiente"],
    )


def iterar(op_id: str, template: str, instancias: list[dict], evidence=None) -> Operator:
    """Iterar: una plantilla repetida con sus instancias de contexto (pasada 7)."""
    if not instancias:
        raise ValueError("instancias necesita al menos una instancia")
    params = {"template": _texto(template, "template"), "instancias": list(instancias)}
    return _operador(op_id, "iterate", params, evidence)


def controlar(op_id: str, reason: str, evidence=None) -> Operator:
    """Controlar: control de fila o de grupo (RETAIN, FIRST./LAST., CALL SYMPUT).

    Es el kind stateful_row.
    """
    return _operador(op_id, "stateful_row", {"reason": _texto(reason, "reason")}, evidence)


__all__ = [
    "agregar",
    "calcular",
    "combinar",
    "concatenar",
    "controlar",
    "deduplicar",
    "escribir",
    "filtrar",
    "iterar",
    "leer",
    "leer_archivo",
    "ordenar",
    "pivotar",
    "proyectar",
    "renombrar",
    "unir",
]
