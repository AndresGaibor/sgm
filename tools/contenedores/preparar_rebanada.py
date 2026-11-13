"""Genera fixtures deterministas y SQL opcional de carga por caso."""

from __future__ import annotations

import argparse
import csv
import io
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sgm.compile import compile_file, project_base  # noqa: E402
from sgm.frontend.program import analyze_program  # noqa: E402
from sgm.ir.models import Column  # noqa: E402
from sgm.migrar.esquemas_programa import (  # noqa: E402
    esquemas_desde_programa,
    numeric_columns_by_input,
)
from tools.contenedores.cargar_tablas import ejecutar_sql  # noqa: E402
from tools.contenedores.sql_carga import (  # noqa: E402
    sentencias_tipadas,
    sql_completo,
    sql_conteos,
)
from tools.datos_sinteticos.manifiesto import (  # noqa: E402
    Manifiesto,
    generar_entradas,
    leer_manifiesto,
)
from tools.datos_sinteticos.requisitos import Requisitos, requisitos_de_rebanada  # noqa: E402

CONTAINER = "sgmtest_impalad"


@dataclass(frozen=True)
class _Context:
    requirements: Requisitos
    manifest: Manifiesto
    schemas: dict[str, list[Column]]


def _input_schemas(
    text: str, name: str, requirements: Requisitos, manifest: Manifiesto
) -> dict[str, list[Column]]:
    """Completa esquemas externos con columnas usadas y tipos demostrados por sus operaciones."""
    filename = f"{name}.sas"
    plan = compile_file(analyze_program({filename: text}), filename, project_base()).plan
    inferred, _ = esquemas_desde_programa(text, name)
    numeric_columns = numeric_columns_by_input(plan)
    result: dict[str, list[Column]] = {}
    for tables in (requirements.tablas_work_externas, requirements.tablas_base):
        for table, demonstrated in tables.items():
            names = list(demonstrated)
            declared = manifest.tablas.get(table.casefold())
            seen = {column.casefold() for column in names}
            if declared is not None:
                for column in declared.columnas:
                    if column.casefold() not in seen:
                        names.append(column)
                        seen.add(column.casefold())
            existing = {column.name.casefold(): column for column in inferred.get(table, [])}
            columns = []
            for column in names:
                current = existing.get(column.casefold())
                is_numeric = column.casefold() in numeric_columns.get(table.casefold(), set())
                if current is not None and current.type is not None and current.source != "unknown":
                    columns.append(current)
                elif is_numeric:
                    columns.append(Column(column, "Double", source="derived"))
                elif current is not None:
                    columns.append(current)
                else:
                    columns.append(Column(column, None, source="unknown"))
            result[table.casefold()] = columns
    return result


def _read_context(case: Path) -> _Context:
    case_dir = case.resolve()
    program_path = case_dir / "programa.sas"
    manifest_path = case_dir / "datos.yaml"
    if not program_path.is_file():
        raise ValueError(f"falta el programa SAS: {program_path}")
    if not manifest_path.is_file():
        raise ValueError(f"falta el manifiesto de datos: {manifest_path}")
    try:
        text = program_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        raise ValueError(f"no se pudo leer el programa SAS: {program_path}") from error
    manifest = leer_manifiesto(manifest_path)
    requirements = requisitos_de_rebanada(text, case_dir.name)
    schemas = _input_schemas(text, case_dir.name, requirements, manifest)
    return _Context(requirements, manifest, schemas)


def _read_csv_rows(path: Path, table: str) -> tuple[list[str], list[list[str]]]:
    try:
        with path.open(encoding="utf-8", newline="") as stream:
            reader = csv.reader(stream, strict=True)
            header = next(reader, None)
            if not header:
                raise ValueError(f"{table}: el CSV no tiene cabecera")
            rows = list(reader)
    except (OSError, UnicodeError, csv.Error) as error:
        raise ValueError(f"{table}: no se pudo leer el CSV generado") from error
    if any(len(row) != len(header) for row in rows):
        raise ValueError(f"{table}: fila CSV con cantidad de columnas incorrecta")
    return header, rows


def _build_load_sql(context: _Context) -> str:
    tables = context.requirements.tablas_base
    if not tables:
        return ""
    base_requirements = Requisitos(
        tablas_base=tables,
        exigidos={
            table: values
            for table, values in context.requirements.exigidos.items()
            if table in tables
        },
    )
    missing = [table for table in tables if table not in context.manifest.tablas]
    if missing:
        raise ValueError(f"{missing[0]}: falta en datos.yaml")
    base_manifest = Manifiesto(
        context.manifest.semilla,
        {table: context.manifest.tablas[table] for table in tables},
    )
    blocks: list[list[str]] = []
    with tempfile.TemporaryDirectory(prefix="sgm_rebanada_") as temporary:
        destination = Path(temporary)
        generar_entradas(
            base_requirements,
            {table: context.schemas[table] for table in tables},
            base_manifest,
            destination,
        )
        for name in tables:
            library, table = name.split(".", 1)
            csv_path = destination / f"{library}.{table}.csv"
            header, rows = _read_csv_rows(csv_path, name)
            columns = context.schemas.get(name.casefold(), [])
            by_name = {column.name.casefold(): column for column in columns}
            ordered_columns = [
                by_name.get(column.casefold(), Column(column, None)) for column in header
            ]
            if len(ordered_columns) != len(columns):
                raise ValueError(f"{name}: columnas del CSV no coinciden con su esquema")
            blocks.append(sentencias_tipadas(library, table, ordered_columns, rows))
    return sql_completo(blocks)


def sql_de_carga(caso: Path) -> str:
    """Construye SQL tipado de tablas base sin modificar el caso ni ejecutarlo."""
    return _build_load_sql(_read_context(caso))


def _execute(sql: str, action: str) -> str:
    try:
        result = ejecutar_sql(sql)
    except (OSError, RuntimeError) as error:
        raise RuntimeError(
            f"No se pudo {action}; verifica que el contenedor {CONTAINER} esté disponible: {error}"
        ) from error
    detail = (result.stderr or "").strip() or (result.stdout or "").strip()
    if result.returncode != 0 or "Could not execute" in (result.stdout or ""):
        raise RuntimeError(
            f"No se pudo {action}; verifica el contenedor {CONTAINER}: "
            f"{detail or 'impala-shell terminó con error'}"
        )
    return result.stdout or ""


def _table_count(stdout: str, table: str) -> int | None:
    for line in stdout.splitlines():
        text = line.strip()
        if text.startswith("|") and text.endswith("|"):
            cells = [cell.strip() for cell in text.strip("|").split("|")]
        else:
            try:
                cells = (
                    [cell.strip() for cell in next(csv.reader(io.StringIO(text)))]
                    if "," in text
                    else []
                )
            except csv.Error:
                cells = []
        if (
            len(cells) == 2
            and cells[0].casefold() == table.casefold()
            and cells[1].isdigit()
        ):
            return int(cells[1])
    return None


def _load(context: _Context) -> None:
    sql = _build_load_sql(context)
    if not sql:
        return
    _execute(sql, "crear y cargar las tablas")
    tables = list(context.requirements.tablas_base)
    counts = _execute(
        sql_conteos([tuple(name.split(".", 1)) for name in tables]),
        "verificar los conteos",
    )
    for name in tables:
        found = _table_count(counts, name)
        expected = context.manifest.tablas[name].filas
        if found != expected:
            actual = "sin resultado" if found is None else str(found)
            raise RuntimeError(
                f"Conteo no coincide para {name}: {actual}; se esperaban {expected}"
            )


def preparar(caso: Path, cargar: bool = False) -> list[Path]:
    """Genera las entradas del caso y, opcionalmente, las carga y verifica en Impala."""
    case_dir = caso.resolve()
    context = _read_context(case_dir)
    paths = generar_entradas(
        context.requirements,
        context.schemas,
        context.manifest,
        case_dir / "entradas",
    )
    csv_paths = [path for path in paths if path.suffix.casefold() == ".csv"]
    if cargar:
        _load(context)
    return csv_paths


def main(argv: list[str] | None = None) -> int:
    """Ejecuta `uv run python tools/contenedores/preparar_rebanada.py <caso> [--cargar]`."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("caso", type=Path, help="carpeta con programa.sas y datos.yaml")
    parser.add_argument("--cargar", action="store_true", help="carga y verifica las tablas base")
    args = parser.parse_args(argv)
    try:
        paths = preparar(args.caso, cargar=args.cargar)
    except (OSError, RuntimeError, ValueError) as error:
        print(str(error), file=sys.stderr)
        return 1
    print(f"Entradas preparadas: {len(paths)}")
    for path in paths:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
