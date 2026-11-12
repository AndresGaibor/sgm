"""PROC genéricos a operadores. Sin regla: `unsupported` con PROC_NO_SOPORTADO."""

from __future__ import annotations

import re

from sgm.frontend.steps import Proc
from sgm.ir import operadores
from sgm.ir.builder import Builder, qualify
from sgm.ir.models import Evidence, Operator
from sgm.ir.pasos import op_validado
from sgm.ir.proc_rules import declared, lower_declared, names_of

_names = names_of

REPORT_PROCS = frozenset({"print", "report", "contents"})

# Opciones que el PROC IMPORT y el PROC EXPORT escriben como sentencia del cuerpo (`GETNAMES=YES;`)
# o en la cabecera. Se leen del texto y no se suponen: el valor que falta queda en `None`.
_OPCION = re.compile(
    r"(?i)\b(dbms|delimiter|getnames|sheet|guessingrows)\s*=\s*('[^']*'|\"[^\"]*\"|[^\s;]+)"
)


def _sin_comillas(valor: str) -> str:
    return valor.strip().strip("'\"")


def _opciones(step: Proc) -> dict[str, str]:
    """Opciones de archivo del paso, tal como las escribe el SAS (cabecera y cuerpo)."""
    texto = " ".join([step.text, *step.body])
    return {m.group(1).lower(): m.group(2) for m in _OPCION.finditer(texto)}


def _dbms(opciones: dict[str, str]) -> str | None:
    valor = opciones.get("dbms")
    return _sin_comillas(valor).lower() if valor else None


def _entero(valor: str | None) -> int | str | None:
    """Convierte el límite literal y conserva MAX o una expresión sin evaluar."""
    texto = _sin_comillas(valor) if valor else ""
    return int(texto) if texto.isdigit() else texto or None


def _getnames(opciones: dict[str, str]) -> bool:
    """`GETNAMES=YES` es el valor por omisión de SAS (`proc`, p. 1387)."""
    valor = opciones.get("getnames")
    return True if valor is None else _sin_comillas(valor).upper() != "NO"


def _read_file(step: Proc, ev: Evidence, b: Builder, out: str | None) -> None:
    """`PROC IMPORT`: archivo de entrada con su formato, separador, cabecera y hoja."""
    opciones = _opciones(step)
    params = {
        "datafile": step.options.get("datafile"),
        "outputs": [qualify(out)] if out else [],
        "dbms": _dbms(opciones),
        "delimiter": _sin_comillas(opciones["delimiter"]) if "delimiter" in opciones else None,
        "getnames": _getnames(opciones),
        "sheet": _sin_comillas(opciones["sheet"]) if "sheet" in opciones else None,
        "guessingrows": _entero(opciones.get("guessingrows")),
    }
    b.op("read_file", params, ev)


def _write_file(step: Proc, ev: Evidence, b: Builder, data: str | None) -> None:
    """`PROC EXPORT`: archivo de salida con su formato y separador."""
    opciones = _opciones(step)
    params = {
        "inputs": [qualify(data)] if data else [],
        "outfile": step.options.get("outfile"),
        "dbms": _dbms(opciones),
        "delimiter": _sin_comillas(opciones["delimiter"]) if "delimiter" in opciones else None,
    }
    if "sheet" in opciones:
        params["sheet"] = _sin_comillas(opciones["sheet"])
    b.op("write_file", params, ev)


def _report(step: Proc, ev: Evidence, b: Builder, data: str | None) -> None:
    """Reporte impreso de un dataset. Su destino lo decide la política `reports` (pasada 2)."""
    statement = "; ".join([step.text, *step.body])
    params = {
        "statement": statement,
        "procedure": step.name,
        "reason": "REPORTE",
        "inputs": [qualify(data)] if data else [],
    }
    b.op(
        "unsupported",
        params,
        ev,
        status="hueco",
        notes=["reporte impreso: lo decide la política reports de env/project.json"],
    )


def lower_proc(step: Proc, ev: Evidence, b: Builder) -> None:
    name = step.name
    data = step.options.get("data")
    out = step.options.get("out")
    if name in REPORT_PROCS and not out:  # con OUT= produce un dataset que otros pasos leen
        _report(step, ev, b, data)
    elif name == "sort":
        _sort(step, ev, b, data, out)
    elif (spec := declared(name)) is not None:  # append, means, summary, freq: en YAML (F1.4)
        if not lower_declared(spec, step, ev, b, data, out):
            _unsupported(step, ev, b, spec["fallback"]["note"])
    elif name == "import":
        _read_file(step, ev, b, out)
    elif name == "export":
        _write_file(step, ev, b, data)
    else:
        _unsupported(step, ev, b, f"PROC {name.upper()} sin regla de migración")


def _sort(step: Proc, ev: Evidence, b: Builder, data: str | None, out: str | None) -> None:
    by, descending, error = _sort_keys(step.clauses.get("by"))
    flags = set(step.flags)
    nodupkey = "nodupkey" in flags
    noduprec = bool(flags & {"nodup", "noduprec", "noduprecs"})
    dupout = step.options.get("dupout")
    opciones_desconocidas = sorted(set(step.options) - {"data", "out", "dupout"})
    banderas_admitidas = {"nodupkey", "nodup", "noduprec", "noduprecs", "equals", "noequals"}
    banderas_desconocidas = sorted(flags - banderas_admitidas)
    sentencias_desconocidas = [
        sentencia
        for sentencia in step.body
        if sentencia and sentencia.split(None, 1)[0].lower() != "by"
    ]
    if error:
        _unsupported(step, ev, b, error)
        return
    if opciones_desconocidas or banderas_desconocidas or sentencias_desconocidas:
        desconocidos = sorted(
            [*opciones_desconocidas, *banderas_desconocidas]
            + [sentencia.split(None, 1)[0].lower() for sentencia in sentencias_desconocidas]
        )
        detalle = ", ".join(desconocidos)
        nota = f"PROC SORT contiene opciones o sentencias aún no traducidas: {detalle}"
        _unsupported(step, ev, b, nota)
        return
    if {"equals", "noequals"} <= flags:
        _unsupported(step, ev, b, "PROC SORT combina EQUALS y NOEQUALS")
        return
    if nodupkey and noduprec:
        _unsupported(
            step,
            ev,
            b,
            "PROC SORT combina NODUPKEY con NODUPREC; la combinación no está verificada",
        )
        return
    if dupout and not nodupkey:
        _unsupported(step, ev, b, "DUPOUT= solo se admite junto con NODUPKEY")
        return
    salidas = [qualify(nombre).lower() for nombre in (dupout, out) if nombre]
    dupout_reemplaza_entrada = bool(
        dupout and data and qualify(dupout).lower() == qualify(data).lower()
    )
    if len(salidas) != len(set(salidas)) or dupout_reemplaza_entrada:
        _unsupported(step, ev, b, "DUPOUT= no puede compartir dataset con DATA= u OUT=")
        return
    es_by_all = by == ["_all_"]
    if noduprec and not es_by_all:
        notas = ["NODUPREC solo elimina duplicados adyacentes; sin BY _ALL_ no se demuestra "
            "que todos queden juntos"]
        b.op(
            "sort",
            {**_sort_params(by, descending, flags, data),
                "outputs": [qualify(out or data)] if (out or data) else []},
            ev,
            status="parcial",
            notes=notas,
        )
        return
    nodup = nodupkey or noduprec
    sort_status = "soportado" if by else "parcial"
    sort_notes = [] if by else ["PROC SORT sin BY: no se puede deducir la clave"]
    params_sort = _sort_params(by, descending, flags, data)
    sort = op_validado(
        b,
        lambda: operadores.ordenar(
            "_",
            by,
            descending,
            compacto=True,
            inputs=[qualify(data)] if data else [],
            equals=False if "noequals" in flags else None,
            evidence=[ev],
        ),
        "sort",
        params_sort,
        ev,
        status=sort_status,
        notes=sort_notes,
    )
    current: Operator = sort
    if nodup:
        notas = [] if by else ["NODUPKEY sin clave: deduplicación parcial"]
        dedup_status = "soportado" if by else "parcial"
        if nodupkey and by:
            dedup_status = "parcial"
            notas.append(
                "EQUALS conserva empates en orden de entrada; la estabilidad de tSortRow "
                "no está verificada para identificar la misma fila"
            )
        if nodupkey and "noequals" in flags:
            dedup_status = "parcial"
            notas.append(
                "NOEQUALS permite cambiar qué observación queda por cada clave duplicada"
            )
        dup = [qualify(dupout)] if dupout else None
        params = {"by": by, "keep": "first"}
        if dup is not None:
            params["duplicate_outputs"] = dup
        dedup = op_validado(
            b,
            lambda: operadores.deduplicar("_", by, "first", duplicate_outputs=dup, evidence=[ev]),
            "dedup",
            params,
            ev,
            status=dedup_status,
            notes=notas,
        )
        b.link(sort, dedup)
        current = dedup
    target = out or data
    if target:
        current.params["outputs"] = [qualify(target)]
        b.refresh(current)


def _sort_params(
    by: list[str], descending: list[bool], flags: set[str], data: str | None
) -> dict[str, object]:
    """Guarda solo opciones no predeterminadas para mantener estables las firmas del plan."""
    params: dict[str, object] = {
        "by": by,
        "inputs": [qualify(data)] if data else [],
    }
    if any(descending):
        params["descending"] = descending
    if "noequals" in flags:
        params["equals"] = False
    return params


def _sort_keys(clause: str | None) -> tuple[list[str], list[bool], str | None]:
    """Lee BY y aplica DESCENDING solo a la variable que le sigue, como en SAS."""
    if not clause:
        return [], [], None
    match = re.match(r"(?is)^\s*by\b(.*?);?\s*$", clause)
    if not match:
        return [], [], "PROC SORT recibió una cláusula BY que no se pudo interpretar"
    tokens = match.group(1).split()
    nombres: list[str] = []
    descendentes: list[bool] = []
    pendiente_descendente = False
    for token in tokens:
        limpio = token.rstrip(";")
        if limpio.lower() == "descending":
            if pendiente_descendente:
                return [], [], "PROC SORT contiene DESCENDING sin variable asociada"
            pendiente_descendente = True
            continue
        if not re.fullmatch(r"(?i)[a-z_][a-z0-9_]*", limpio):
            return [], [], f"PROC SORT BY contiene un nombre no admitido: {limpio}"
        if pendiente_descendente and limpio.lower() == "_all_":
            return [], [], "DESCENDING _ALL_ no está verificado para PROC SORT"
        nombres.append(limpio.lower())
        descendentes.append(pendiente_descendente)
        pendiente_descendente = False
    if pendiente_descendente:
        return [], [], "PROC SORT contiene DESCENDING sin variable asociada"
    return nombres, descendentes, None


def _unsupported(step: Proc, ev: Evidence, b: Builder, note: str) -> None:
    statement = "; ".join([step.text, *step.body])
    b.op(
        "unsupported",
        {"statement": statement, "procedure": step.name, "reason": "PROC_NO_SOPORTADO"},
        ev,
        status="hueco",
        notes=[note],
    )
