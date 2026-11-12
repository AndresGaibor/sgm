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


def leer(
    op_id: str,
    dataset: str,
    in_flag: str | None = None,
    incluir_bandera: bool = False,
    evidence=None,
) -> Operator:
    """Leer: una tabla del programa.

    El lowering tiene dos formas: la de DATA step lleva la clave `in` (aunque valga None) y la de
    SQL no la lleva. `incluir_bandera=True` produce la de DATA step.
    """
    params: dict[str, Any] = {"dataset": _texto(dataset, "dataset")}
    if incluir_bandera or in_flag:
        params["in"] = in_flag or None
    return _operador(op_id, "read", params, evidence)


def leer_archivo(
    op_id: str,
    datafile: str,
    outputs: list[str],
    dbms: str | None = None,
    delimiter: str | None = None,
    getnames: bool | None = None,
    sheet: str | None = None,
    guessingrows: str | None = None,
    evidence=None,
) -> Operator:
    """Leer archivo: una fuente externa (PROC IMPORT, INFILE) que llena una o más tablas.

    Las opciones del lowering (`dbms`, `delimiter`, `getnames`, `sheet`, `guessingrows`) siempre
    aparecen en los parámetros, aunque valgan None, como en el lowering.
    """
    params = {
        "datafile": _texto(datafile, "datafile"),
        "outputs": _lista(outputs, "outputs"),
        "dbms": dbms,
        "delimiter": delimiter,
        "getnames": getnames,
        "sheet": sheet,
        "guessingrows": guessingrows,
    }
    return _operador(op_id, "read_file", params, evidence)


def escribir_archivo(
    op_id: str,
    inputs: list[str],
    outfile: str,
    dbms: str | None = None,
    delimiter: str | None = None,
    evidence=None,
) -> Operator:
    """Escribir archivo: PROC EXPORT o salida de archivo de una o más tablas."""
    params = {
        "inputs": _lista(inputs, "inputs"),
        "outfile": _texto(outfile, "outfile"),
        "dbms": dbms,
        "delimiter": delimiter,
    }
    return _operador(op_id, "write_file", params, evidence)


def escribir(op_id: str, dataset: str, evidence=None) -> Operator:
    """Escribir: una tabla de salida del programa."""
    return _operador(op_id, "write", {"dataset": _texto(dataset, "dataset")}, evidence)


def filtrar(
    op_id: str, expression: str, outputs: list[str] | None = None, evidence=None
) -> Operator:
    """Filtrar: conserva las filas que cumplen la expresión (WHERE, HAVING, subsetting IF).

    `outputs` solo aparece en los parámetros si se da, como en el lowering.
    """
    params: dict[str, Any] = {"expression": _texto(expression, "expression")}
    if outputs is not None:
        params["outputs"] = _lista(outputs, "outputs")
    return _operador(op_id, "filter", params, evidence)


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


def calcular(
    op_id: str,
    assignments: list[dict[str, Any]],
    outputs: list[str] | None = None,
    modo: str | None = None,
    declared: dict[str, Any] | None = None,
    evidence=None,
) -> Operator:
    """Calcular: asignaciones `target = expression` de columnas nuevas o modificadas.

    Cada asignación conserva sus claves extra (por ejemplo `origin`), como el lowering. `outputs`,
    `modo` (`agrega`) y `declared` (LENGTH, FORMAT) solo aparecen si se dan.
    """
    if not assignments:
        raise ValueError("assignments necesita al menos una asignación")
    normal: list[dict[str, Any]] = []
    for asignacion in assignments:
        copia = dict(asignacion)
        copia["target"] = _texto(asignacion.get("target", ""), "target")
        copia["expression"] = _texto(asignacion.get("expression", ""), "expression")
        normal.append(copia)
    params: dict[str, Any] = {"assignments": normal}
    if outputs is not None:
        params["outputs"] = _lista(outputs, "outputs")
    if modo is not None:
        params["modo"] = _texto(modo, "modo")
    if declared is not None:
        params["declared"] = dict(declared)
    return _operador(op_id, "derive", params, evidence)


def unir(
    op_id: str,
    join_type: str,
    keys: list[tuple[str, str]],
    sources: list[str],
    condition: str | None = None,
    evidence=None,
) -> Operator:
    """Unir: JOIN de SQL con tipo explícito. Misma forma que el lowering de `PROC SQL`.

    `keys` son pares (columna izquierda, columna derecha); `by` se deduce de la izquierda. Requiere
    al menos una llave, salvo `cross`. `sources` es la tabla base del FROM (puede venir vacía).
    """
    if join_type not in TIPOS_UNION + ("cross",):
        raise ValueError(f"join_type debe ser {TIPOS_UNION + ('cross',)}, no '{join_type}'")
    pares = []
    for par in keys:
        if len(par) != 2:
            raise ValueError(f"cada llave debe ser un par (izquierda, derecha): {par!r}")
        pares.append([_texto(par[0], "llave izquierda"), _texto(par[1], "llave derecha")])
    if not pares and join_type != "cross":
        raise ValueError("una unión necesita al menos una llave, salvo cross")
    params = {
        "by": [izquierda.split(".")[-1].lower() for izquierda, _ in pares],
        "keys": pares,
        "join_type": join_type,
        "sources": _lista(sources, "sources", minimo=0),
        "condition": condition,
    }
    return _operador(op_id, "join", params, evidence)


def combinar(
    op_id: str,
    join_type: str,
    by: list[str],
    sources: list[str],
    evidence=None,
) -> Operator:
    """Combinar (MERGE): emparejamiento por llave con `by` y sin `keys`, como lower_data.

    La semántica fila con fila la aplica el intérprete; el emisor no lo traduce a tMap (hito 132m).
    """
    if join_type not in TIPOS_UNION:
        raise ValueError(f"join_type debe ser {TIPOS_UNION}, no '{join_type}'")
    params = {
        "by": [n.lower() for n in _lista(by, "by")],
        "join_type": join_type,
        "sources": [s for s in _lista(sources, "sources", minimo=2)],
    }
    return _operador(op_id, "join", params, evidence)


def agregar(
    op_id: str,
    group_by: list[str],
    aggregations: list[dict[str, str]],
    outputs: list[str] | None = None,
    pendiente: list[str] | None = None,
    status: str = "soportado",
    evidence=None,
    group_outputs: list[dict[str, str]] | None = None,
    output_order: list[str] | None = None,
) -> Operator:
    """Agregar: GROUP BY con agregados (expression y alias por cada uno).

    `pendiente` lista las columnas sin agregar que SAS remezcla; si se da, el operador es `parcial`.
    """
    if not aggregations:
        raise ValueError("aggregations necesita al menos un agregado")
    normal = [
        {
            "expression": _texto(a.get("expression", ""), "expression"),
            "alias": _texto(a.get("alias", ""), "alias"),
        }
        for a in aggregations
    ]
    params: dict[str, Any] = {
        "group_by": [g.lower() for g in _lista(group_by, "group_by", minimo=0)],
        "aggregations": normal,
    }
    if outputs is not None:
        params["outputs"] = _lista(outputs, "outputs")
    if pendiente is not None:
        params["pendiente"] = _lista(pendiente, "pendiente")
    if group_outputs is not None:
        params["group_outputs"] = [
            {
                "expression": _texto(item.get("expression", ""), "expression"),
                "alias": _texto(item.get("alias", ""), "alias"),
            }
            for item in group_outputs
        ]
    if output_order is not None:
        params["output_order"] = _lista(output_order, "output_order")
    return _operador(op_id, "aggregate", params, evidence, status=status)


def ordenar(
    op_id: str,
    by: list[str],
    descending: bool | list[bool] = False,
    outputs: list[str] | None = None,
    evidence=None,
    *,
    compacto: bool = False,
    inputs: list[str] | None = None,
    equals: bool | None = None,
) -> Operator:
    """Ordenar: clave de orden (PROC SORT BY y ORDER BY).

    `descending` es un booleano para todas las claves o una lista por clave (como el lowering).
    Con `compacto` tiene la forma de `PROC SORT` en el lowering: `inputs` siempre, `descending` solo
    si alguna clave es descendente y `equals` solo si se da (`lower_procs._sort_params`).
    """
    claves = [n.lower() for n in _lista(by, "by")]
    if isinstance(descending, bool):
        indicadores = [descending] * len(claves)
    else:
        indicadores = [bool(d) for d in descending]
        if len(indicadores) != len(claves):
            raise ValueError("descending necesita un valor por cada clave de by")
    if compacto:
        params: dict[str, Any] = {"by": claves, "inputs": _lista(inputs or [], "inputs", minimo=0)}
        if any(indicadores):
            params["descending"] = indicadores
        if equals is not None:
            params["equals"] = bool(equals)
    else:
        params = {"by": claves, "descending": indicadores}
    if outputs is not None:
        params["outputs"] = _lista(outputs, "outputs")
    return _operador(op_id, "sort", params, evidence)


def deduplicar(
    op_id: str,
    by: list[str],
    keep: str = "first",
    outputs: list[str] | None = None,
    evidence=None,
    *,
    duplicate_outputs: list[str] | None = None,
) -> Operator:
    """Deduplicar: una fila por clave (NODUP, NODUPKEY, DISTINCT sobre una clave).

    `outputs` solo aparece en los parámetros si se da, como en el lowering de PROC SORT.
    `duplicate_outputs` (DUPOUT= de PROC SORT) solo aparece si se da.
    """
    if keep not in MODOS_DEDUP:
        raise ValueError(f"keep debe ser {MODOS_DEDUP}, no '{keep}'")
    params: dict[str, Any] = {"by": [n.lower() for n in _lista(by, "by")], "keep": keep}
    if outputs is not None:
        params["outputs"] = _lista(outputs, "outputs")
    if duplicate_outputs is not None:
        params["duplicate_outputs"] = _lista(duplicate_outputs, "duplicate_outputs", minimo=0)
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
