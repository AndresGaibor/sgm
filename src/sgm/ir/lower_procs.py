"""PROC genéricos a operadores. Sin regla: `unsupported` con PROC_NO_SOPORTADO."""

from __future__ import annotations

import re

from sgm.frontend.steps import Proc
from sgm.ir.builder import Builder, qualify
from sgm.ir.lower_procs_append import lower_append
from sgm.ir.lower_procs_common import unsupported as _unsupported
from sgm.ir.lower_procs_limpieza import lower_limpieza
from sgm.ir.lower_procs_sort import lower_sort
from sgm.ir.models import Evidence
from sgm.ir.proc_rules import declared, lower_declared, names_of

_names = names_of

REPORT_PROCS = frozenset({"print", "report", "tabulate", "contents"})
P_WORK_INTROSPECCION = "P-WORK-INTROSPECCION"
P_APPEND_MISMA_TABLA = "P-APPEND-MISMA-TABLA"
P_APPEND_OPCION_NO_SOPORTADA = "P-APPEND-OPCION-NO-SOPORTADA"

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


def _work_all(data: str | None) -> bool:
    """`WORK._ALL_` depende del estado de la sesión y no de una tabla de entrada fija."""
    return bool(data and re.fullmatch(r"\s*work\s*\.\s*_all_\s*", data, re.IGNORECASE))


def _same_dataset(left: str | None, right: str | None) -> bool:
    """Compara referencias SAS con biblioteca implícita y sin distinguir mayúsculas."""
    return bool(left and right and qualify(left).casefold() == qualify(right).casefold())


def _append_limitation(step: Proc) -> str | None:
    """Devuelve un motivo si APPEND trae modificadores que la regla no modela."""
    opciones = sorted(set(step.options) - {"base", "data"})
    banderas = sorted(set(step.flags))
    opciones_dataset = sorted(
        opcion for opcion in ("base", "data") if "(" in str(step.options.get(opcion, ""))
    )
    referencias_dinamicas = sorted(
        opcion
        for opcion in ("base", "data")
        if re.search(r"[&%]", str(step.options.get(opcion, "")))
    )
    sentencias = sorted(
        {
            sentencia.split(None, 1)[0].lower()
            for sentencia in step.body
            if sentencia.strip()
        }
    )
    detalle = []
    if opciones:
        detalle.append("opciones: " + ", ".join(opciones))
    if banderas:
        detalle.append("banderas: " + ", ".join(banderas))
    if opciones_dataset:
        detalle.append("opciones de dataset en: " + ", ".join(opciones_dataset))
    if referencias_dinamicas:
        detalle.append("referencias dinámicas en: " + ", ".join(referencias_dinamicas))
    if sentencias:
        detalle.append("sentencias: " + ", ".join(sentencias))
    if not detalle:
        return None
    return (
        "Pendiente: P-APPEND-OPCION-NO-SOPORTADA; PROC APPEND contiene "
        + "; ".join(detalle)
        + "; la sintaxis se documenta en proc.pdf, p. 162"
    )


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
    if name == "contents" and out and _work_all(data):
        _unsupported(
            step,
            ev,
            b,
            "Pendiente: P-WORK-INTROSPECCION; la salida enumera los miembros actuales de WORK, "
            "que dependen del estado de la sesión SAS y no de datos aportados al migrador",
            pending_code=P_WORK_INTROSPECCION,
        )
    elif name in {"delete", "datasets", "copy"}:
        lower_limpieza(step, ev, b)
    elif name in REPORT_PROCS and not out:  # con OUT= produce un dataset que otros pasos leen
        _report(step, ev, b, data)
    elif name == "append":
        if _same_dataset(step.options.get("base"), data):
            _unsupported(
                step,
                ev,
                b,
                "Pendiente: P-APPEND-MISMA-TABLA; la semántica de APPEND cuando BASE= y DATA= "
                "identifican la misma tabla no está demostrada por la referencia SAS disponible",
                pending_code=P_APPEND_MISMA_TABLA,
            )
        elif limite := _append_limitation(step):
            _unsupported(step, ev, b, limite, pending_code=P_APPEND_OPCION_NO_SOPORTADA)
        elif (spec := declared(name)) is None or not lower_append(step, ev, b, spec):
            _unsupported(step, ev, b, "PROC APPEND sin BASE= y DATA=")
    elif name == "sort":
        lower_sort(step, ev, b)
    elif (spec := declared(name)) is not None:  # append, means, summary, freq: en YAML (F1.4)
        if not lower_declared(spec, step, ev, b, data, out):
            _unsupported(step, ev, b, spec["fallback"]["note"])
    elif name == "import":
        _read_file(step, ev, b, out)
    elif name == "export":
        _write_file(step, ev, b, data)
    else:
        _unsupported(step, ev, b, f"PROC {name.upper()} sin regla de migración")
