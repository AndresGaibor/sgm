"""Lectura controlada de archivos delimitados para el esperado del anillo B."""

from __future__ import annotations

import csv
import re
from typing import TYPE_CHECKING

from sgm.ir.models import Plan
from sgm.migrar.ficha import leer_ficha
from sgm.migrar.interprete_infile import leer_lista
from sgm.migrar.interprete_posicional import leer_columnas
from sgm.migrar.lector_xlsx import leer_xlsx
from tools.datos_sinteticos.ficha import validar_ficha

if TYPE_CHECKING:
    from .caso import Caso

_IDENTIFICADOR = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\Z")


def _tabla(nombre: object) -> str:
    return str(nombre or "").strip().casefold().split(".")[-1]


def _relevantes(plan: Plan, salidas: tuple[str, ...]) -> set[str]:
    """Recorre hacia atrás desde salidas declaradas para excluir imports sin uso."""
    esperadas = {_tabla(nombre) for nombre in salidas}
    objetivos = set()
    for operator in plan.graph.operators():
        params = operator.params
        producidas = list(params.get("outputs") or [])
        if operator.kind == "write":
            producidas.append(params.get("dataset", ""))
        consumidas = params.get("inputs") or [] if operator.kind == "write_file" else []
        if any(_tabla(nombre) in esperadas for nombre in [*producidas, *consumidas]):
            objetivos.add(operator.id)

    relevantes = set()
    pendientes = list(objetivos)
    while pendientes:
        actual = pendientes.pop()
        if actual in relevantes:
            continue
        relevantes.add(actual)
        pendientes.extend(plan.graph.predecessors(actual))
    return relevantes


def _nombre_fuente(datafile: object) -> str:
    """Extrae un nombre simple; nunca usa la ruta SAS para leer fuera del caso."""
    literal = str(datafile or "").strip()
    if len(literal) >= 2 and literal[0] == literal[-1] and literal[0] in "'\"":
        literal = literal[1:-1]
    partes = re.split(r"[\\/]", literal)
    if ".." in partes or not partes or not partes[-1]:
        raise ValueError("DATAFILE no identifica un archivo local del caso")
    nombre = partes[-1]
    if not re.fullmatch(r"[A-Za-z0-9_][A-Za-z0-9_.-]*\.[A-Za-z0-9]{1,10}", nombre):
        raise ValueError("DATAFILE tiene un nombre de archivo no permitido")
    return nombre


def _leer_dlm(
    operator: object, caso: Caso
) -> tuple[str, list[str], list[dict[str, str]]]:
    params = operator.params
    dbms = str(params.get("dbms") or "").casefold()
    separator = params.get("delimiter") or ("," if dbms == "csv" else None)
    if dbms not in {"csv", "dlm"}:
        raise ValueError(f"PROC IMPORT DBMS={dbms or '(sin DBMS)'} no es texto delimitado")
    if not isinstance(separator, str) or len(separator) != 1 or separator in '\r\n"':
        raise ValueError("PROC IMPORT DBMS=DLM requiere DELIMITER explícito de un carácter")
    has_header = params.get("getnames")
    if not isinstance(has_header, bool):
        raise ValueError("PROC IMPORT DBMS=DLM no tiene GETNAMES resuelto")
    name = _nombre_fuente(params.get("datafile"))
    case_root = caso.directorio.resolve()
    root = caso.entradas.resolve()
    if root == case_root or not root.is_relative_to(case_root):
        raise ValueError("raíz de entradas fuera de la carpeta del caso")
    path = (root / name).resolve()
    if not path.is_relative_to(root) or not path.is_file():
        raise ValueError(f"no existe el archivo DATAFILE del caso: {name}")
    ficha_path = path.with_suffix(".ficha.yaml").resolve()
    if not ficha_path.is_relative_to(root):
        raise ValueError(f"la ficha del archivo sale de entradas/: {name}")
    if not ficha_path.is_file():
        raise ValueError(f"falta la ficha de procedencia del archivo: {name}")
    ficha = leer_ficha(ficha_path)
    errores = validar_ficha(ficha, path)
    if errores:
        raise ValueError(f"{name}: ficha inválida: {'; '.join(errores)}")
    if ficha.tabla != f"archivo:{name}" or ficha.cabecera is not has_header:
        raise ValueError(f"{name}: la ficha no coincide con GETNAMES del programa")
    if ficha.delimitador != separator:
        raise ValueError(f"{name}: la ficha no coincide con DELIMITER del programa")

    try:
        with path.open(encoding="utf-8-sig", newline="") as stream:
            rows = list(csv.reader(stream, delimiter=separator, strict=True))
    except (OSError, UnicodeError, csv.Error) as error:
        raise ValueError(f"{name}: archivo delimitado inválido") from error
    if not rows:
        raise ValueError(f"{name}: archivo sin filas; no se puede demostrar el esquema")
    datarow = params.get("datarow")
    if datarow is None:
        datarow = 2 if has_header else 1
    if isinstance(datarow, bool) or not isinstance(datarow, int):
        raise ValueError(f"{name}: DATAROW no es un entero literal")
    if datarow < (2 if has_header else 1):
        raise ValueError(f"{name}: DATAROW no es válido con GETNAMES; proc.pdf, p. 1385")
    first_data = datarow - 1
    if has_header:
        columns, values = rows[0], rows[first_data:]
        if any(not _IDENTIFICADOR.fullmatch(column) for column in columns):
            raise ValueError(f"{name}: GETNAMES requiere nombres de columna simples en este anillo")
    else:
        values = rows[first_data:]
        if not values:
            raise ValueError(f"{name}: DATAROW no encuentra una fila para demostrar el ancho")
        columns = [f"VAR{index}" for index in range(1, len(values[0]) + 1)]
    if not columns or any(len(row) != len(columns) for row in values):
        raise ValueError(f"{name}: cantidad de campos inconsistente")
    if list(ficha.columnas) != columns:
        raise ValueError(f"{name}: las columnas no coinciden con la ficha")
    return (
        _tabla((params.get("outputs") or [""])[0]),
        columns,
        [dict(zip(columns, row, strict=True)) for row in values],
    )


def _leer_xlsx(operator: object, caso: Caso) -> tuple[str, list[str], list[dict[str, str]]]:
    """Lee solo la hoja declarada por PROC IMPORT desde entradas del caso."""
    params = operator.params
    getnames = params.get("getnames")
    if not isinstance(getnames, bool):
        raise ValueError("PROC IMPORT DBMS=XLSX no tiene GETNAMES resuelto")
    name = _nombre_fuente(params.get("datafile"))
    case_root = caso.directorio.resolve()
    root = caso.entradas.resolve()
    if root == case_root or not root.is_relative_to(case_root):
        raise ValueError("raíz de entradas fuera de la carpeta del caso")
    path = (root / name).resolve()
    if not path.is_relative_to(root) or not path.is_file():
        raise ValueError(f"no existe el archivo DATAFILE del caso: {name}")
    columns, rows = leer_xlsx(path, params.get("sheet"), getnames=getnames)
    if any(not _IDENTIFICADOR.fullmatch(column) for column in columns):
        raise ValueError(f"{name}: los nombres de columna Excel no son identificadores portables")
    return (
        _tabla((params.get("outputs") or [""])[0]),
        columns,
        [dict(zip(columns, row, strict=True)) for row in rows],
    )


def _leer_infile(
    operator: object, caso: Caso
) -> tuple[str, list[str], list[dict[str, str | None]]]:
    """Carga INFILE únicamente desde `entradas/` y ejecuta el INPUT de lista literal."""
    params = operator.params
    input_mode = params.get("input_mode")
    if input_mode not in {"list", "column"}:
        raise ValueError("el esperado del anillo B no interpreta esta forma de INPUT")
    name = _nombre_fuente(params.get("datafile"))
    case_root = caso.directorio.resolve()
    root = caso.entradas.resolve()
    if root == case_root or not root.is_relative_to(case_root):
        raise ValueError("raíz de entradas fuera de la carpeta del caso")
    path = (root / name).resolve()
    if not path.is_relative_to(root) or not path.is_file():
        raise ValueError(f"no existe el archivo INFILE del caso: {name}")
    try:
        with path.open(encoding="utf-8-sig") as stream:
            lines = stream.read().splitlines()
    except (OSError, UnicodeError) as error:
        raise ValueError(f"{name}: no se pudo leer el archivo INFILE") from error
    options = params.get("infile_options") or {}
    names = [str(column) for column in params.get("input_names") or []]
    if input_mode == "column":
        positions = params.get("input_positions") or []
        if not positions:
            raise ValueError(f"{name}: INPUT posicional no conserva columnas literales")
        campos = [
            (
                str(field["name"]),
                int(field["start"]),
                int(field["width"]),
                str(field["informat"]),
            )
            for field in positions
        ]
        truncover = bool((params.get("infile_options") or {}).get("truncover"))
        filas = leer_columnas(lines, campos, truncover)
        return _tabla((params.get("outputs") or [""])[0]), names, filas

    delimiter = params.get("delimiter")
    if not isinstance(delimiter, str):
        raise ValueError(f"{name}: INFILE no tiene DLM literal")
    informats = {
        str(column).casefold(): str(informat)
        for column, informat in (params.get("input_informats") or {}).items()
    }
    rows = leer_lista(
        lines,
        [(column, informats.get(column.casefold())) for column in names],
        delimiter,
        bool(options.get("dsd")),
        bool(options.get("missover")),
        firstobs=params.get("firstobs", 1),
        truncover=bool(options.get("truncover")),
    )
    return _tabla((params.get("outputs") or [""])[0]), names, rows


def entradas_de_archivos(
    plan: Plan, caso: Caso, salidas: tuple[str, ...] | list[str] | None = None
) -> tuple[dict[str, list[dict[str, str | None]]], dict[str, list[str]]]:
    """Carga únicamente imports necesarios para las salidas y soportados por este anillo."""
    relevantes = _relevantes(plan, caso.salidas if salidas is None else tuple(salidas))
    entradas = {}
    columnas = {}
    for operator in plan.graph.operators():
        if operator.kind != "read_file" or operator.id not in relevantes:
            continue
        if operator.params.get("infile_statement") and operator.params.get("input_statement"):
            name, names, rows = _leer_infile(operator, caso)
            if name in entradas:
                raise ValueError(f"{name}: más de una lectura produce la misma tabla")
            entradas[name] = rows
            columnas[name] = names
            continue
        dbms = str(operator.params.get("dbms") or "").casefold()
        if dbms == "xls":
            raise ValueError("DBMS=XLS no se ejecuta en el intérprete: P-XLS-SIN-EJECUCION")
        if dbms not in {"csv", "dlm", "xlsx"}:
            raise ValueError(
                f"{_tabla((operator.params.get('outputs') or [''])[0])}: "
                f"DBMS={dbms or '(sin DBMS)'} no está soportado en el esperado del anillo B"
            )
        name, names, rows = (
            _leer_xlsx(operator, caso) if dbms == "xlsx" else _leer_dlm(operator, caso)
        )
        if name in entradas:
            raise ValueError(f"{name}: más de un PROC IMPORT produce la misma tabla")
        entradas[name] = rows
        columnas[name] = names
    return entradas, columnas
