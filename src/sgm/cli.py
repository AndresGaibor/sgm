"""CLI de sgm."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Annotated

import typer

from sgm import cache, generadores, trinquete
from sgm import diagnostics as diagnostics_mod
from sgm import explain as explain_mod
from sgm import intake as intake_mod
from sgm import lineage as lineage_mod
from sgm import metrics as metrics_mod
from sgm import rules_validate as rules_validate_mod
from sgm.batch import compile_batch
from sgm.catalog import describe as describe_mod
from sgm.cli_util import _collect, _env
from sgm.emit.guide_md import render_guide
from sgm.emit.plan_json import metadatos_de_salida, plan_to_dict
from sgm.facts.cli import facts_command, mapa_command
from sgm.ingest.importer import ImportError_
from sgm.store import gaps as gap_store
from sgm.store import overrides as override_store
from sgm.store.db import Store
from sgm.verify import comparar_command

app = typer.Typer(
    help="sgm: compila programas SAS a guías de migración Talend.", no_args_is_help=True
)
from sgm.cli_conformidad import conformidad_command  # noqa: E402
from sgm.cli_decisiones import decisions_app, gaps_app  # noqa: E402
from sgm.cli_diseno import diseno_command  # noqa: E402
from sgm.cli_flow import flujo_command  # noqa: E402
from sgm.cli_proceso import proceso_command  # noqa: E402
from sgm.cli_secretos import secretos_command  # noqa: E402
from sgm.cli_talend import talend_command  # noqa: E402

rules_app = typer.Typer(help="Reglas, casos y configuración.", no_args_is_help=True)
case_app = typer.Typer(help="Casos de prueba declarativos.", no_args_is_help=True)
app.add_typer(decisions_app, name="decisions")
app.add_typer(gaps_app, name="gaps")
app.add_typer(rules_app, name="rules")
app.add_typer(case_app, name="case")
app.command("facts")(facts_command)
app.command("mapa")(mapa_command)
app.command("comparar")(comparar_command)
app.command("diseno")(diseno_command)
app.command("proceso")(proceso_command)
app.command("talend")(talend_command)
app.command("flujo")(flujo_command)
app.command("conformidad")(conformidad_command)
app.command("secretos")(secretos_command)


@app.callback()
def main() -> None:
    """Punto de entrada: cada subcomando es una operación de sgm."""


def _project_name(source: Path) -> str:
    return source.stem if source.is_file() else source.name


def _write_outputs(out: Path, compiled: dict) -> list[str]:
    """Escribe guía y plan de cada programa. Devuelve los nombres escritos."""
    names: list[str] = []
    for program, result in compiled.items():
        stem = Path(program).with_suffix("").as_posix().replace("/", "__")
        guide = f"{stem}.guide.md"
        plan = f"{stem}.plan.json"
        (out / guide).write_text(render_guide(result.plan), encoding="utf-8")
        payload = {"metadatos": metadatos_de_salida(), **plan_to_dict(result.plan)}
        (out / plan).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        names += [guide, plan]
    return names


@app.command()
def compile(
    source: Annotated[Path, typer.Argument(help="Archivo .sas o carpeta con programas.")],
    out: Annotated[Path, typer.Option("--out", help="Carpeta de salida.")] = Path("out"),
    workers: Annotated[int, typer.Option("--workers", help="Programas en paralelo.")] = 1,
    no_cache: Annotated[bool, typer.Option("--no-cache", help="No usar la caché.")] = False,
) -> None:
    """Escribe `<programa>.guide.md` y `<programa>.plan.json` por cada programa."""
    if not source.exists():
        raise typer.BadParameter(f"no existe: {source}")
    files = _collect(source)
    if not files:
        typer.echo("No hay programas SAS en la fuente.")
        raise typer.Exit(code=1)
    out.mkdir(parents=True, exist_ok=True)
    key = cache.project_key(files)
    if not no_cache:
        restored = cache.restore(out, key)
        if restored:
            typer.echo(f"Caché: {len(restored)} archivos recuperados sin recalcular.")
            return
    compiled, _ = compile_batch(files, workers=workers, env=_env())
    project = _project_name(source)
    with Store() as store:
        sueltos = override_store.joins_sueltos(store, compiled)
        if sueltos:
            # Una decisión deja un join suelto: se compila otra vez sin fundirlo en el tMap.
            compiled, _ = compile_batch(files, workers=workers, env=_env(), no_fusionar=sueltos)
        for result in compiled.values():
            override_store.apply(result.plan, store, project)
        gap_store.save(store, gap_store.inventory([r.plan for r in compiled.values()]))
    names = _write_outputs(out, compiled)
    for program, result in compiled.items():
        typer.echo(
            f"{program}: {len(result.plan.graph)} operadores, "
            f"{len(result.plan.gaps)} firmas con hueco"
        )
    cache.save(out, key, names)
    typer.echo(f"Salida en {out}")


@app.command()
def metrics(
    source: Annotated[Path, typer.Argument(help="Archivo .sas o carpeta con programas.")],
    out: Annotated[Path, typer.Option("--out", help="Carpeta de salida.")] = Path("out"),
    check: Annotated[
        bool, typer.Option("--check", help="Falla si una métrica empeora frente a la línea base.")
    ] = False,
    baseline: Annotated[Path, typer.Option("--baseline", help="Archivo de la línea base.")] = Path(
        "metrics"
    )
    / "baseline.json",
    write_baseline: Annotated[
        bool, typer.Option("--write-baseline", help="Guarda estas cifras como línea base.")
    ] = False,
    razon: Annotated[
        str, typer.Option("--razon", help="Motivo escrito al cambiar la línea base.")
    ] = "",
) -> None:
    """Imprime las métricas y las guarda en `out/metrics.json` y `out/diagnostico.md`."""
    files = _collect(source)
    if not files:
        typer.echo("No hay programas SAS en la fuente.")
        raise typer.Exit(code=1)
    started = time.perf_counter()
    compiled, analysis = compile_batch(files, env=_env())
    report = metrics_mod.compute(compiled, files, analysis)
    report["total"]["tiempo_compilacion_s"] = round(time.perf_counter() - started, 1)
    if write_baseline:
        if not razon:
            raise typer.BadParameter("cambiar la línea base exige --razon")
        baseline.parent.mkdir(parents=True, exist_ok=True)
        saved = {"razon": razon, "total": report["total"]}
        baseline.write_text(json.dumps(saved, ensure_ascii=False, indent=2), encoding="utf-8")
        typer.echo(f"Línea base guardada en {baseline}")
    if check:
        problems = trinquete.check(report, json.loads(baseline.read_text(encoding="utf-8")))
        if problems:
            typer.echo("Trinquete: una métrica empeora:")
            for problem in problems:
                typer.echo(f"  - {problem}")
            raise typer.Exit(code=1)
        typer.echo("Trinquete: ninguna métrica empeora frente a la línea base.")
    out.mkdir(parents=True, exist_ok=True)
    (out / "metrics.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (out / "diagnostico.md").write_text(
        diagnostics_mod.render(diagnostics_mod.build(compiled), report), encoding="utf-8"
    )
    total = report["total"]
    typer.echo(
        f"Programas {total['programas']}, pasos SAS {total['pasos_sas']}, "
        f"nodos SAS {total['nodos_sas']}, componentes {total['componentes']}, "
        f"pasos por componente {total['pasos_por_componente']}, "
        f"nodos por componente {total['nodos_por_componente']}, tJava {total['pct_tjava']} %"
    )
    typer.echo(f"Métricas en {out / 'metrics.json'} y diagnóstico en {out / 'diagnostico.md'}")


@app.command()
def lineage(
    source: Annotated[Path, typer.Argument(help="Archivo .sas o carpeta con programas.")],
) -> None:
    """Propone oleadas de ejecución según las tablas permanentes que escribe y lee cada programa."""
    files = _collect(source)
    if not files:
        typer.echo("No hay programas SAS en la fuente.")
        raise typer.Exit(code=1)
    compiled, _ = compile_batch(files, env=_env())
    for number, wave in enumerate(lineage_mod.waves(compiled), 1):
        typer.echo(f"Oleada {number}: " + ", ".join(wave))


env_app = typer.Typer(help="Entorno: esquemas de las bases.", no_args_is_help=True)
app.add_typer(env_app, name="env")


@env_app.command("import-describe")
def env_import_describe(
    archivo: Annotated[Path, typer.Argument(help="Salida de texto de DESCRIBE de Impala.")],
    schema: Annotated[str, typer.Option("--schema", help="Nombre del esquema, en minúsculas.")],
) -> None:
    """Escribe env/schemas/<esquema>.json con las tablas de la salida de DESCRIBE."""
    try:
        ruta, tablas = describe_mod.importar(archivo, schema)
    except (ValueError, FileNotFoundError) as error:
        raise typer.BadParameter(str(error)) from error
    typer.echo(f"Esquema escrito: {ruta} ({len(tablas)} tablas)")
    for tabla, columnas in sorted(tablas.items()):
        sin_tipo = sum(1 for c in columnas if c.type is None)
        typer.echo(f"  {tabla}: {len(columnas)} columnas, {sin_tipo} sin tipo traducible")


@app.command()
def explain(
    ref: Annotated[str, typer.Argument(help="Archivo y línea, por ejemplo programa.sas:120.")],
) -> None:
    """Qué operadores, pasadas, huecos y notas tiene una línea del programa."""
    archivo, _, linea = ref.rpartition(":")
    if not archivo or not linea.isdigit():
        raise typer.BadParameter("usa archivo:línea, por ejemplo programa.sas:120")
    try:
        typer.echo(explain_mod.explicar(Path(archivo), int(linea), env=_env()))
    except (FileNotFoundError, ValueError) as error:
        raise typer.BadParameter(str(error)) from error


@app.command()
def intake(
    source: Annotated[Path, typer.Argument(help="Carpeta, ZIP o archivo SAS a importar.")],
) -> None:
    """Importa un lote a corpus/inbox: UTF-8, sin secretos, compilado y con sus huecos."""
    try:
        resultado = intake_mod.intake(source, env=_env())
    except (ImportError_, FileNotFoundError) as error:
        raise typer.BadParameter(str(error)) from error
    typer.echo(
        f"Lote: {resultado.carpeta}\n"
        f"  archivos={resultado.archivos} omitidos={resultado.omitidos} "
        f"programas={resultado.programas}\n"
        f"  líneas con secretos redactadas={resultado.lineas_redactadas}\n"
        f"  codificaciones convertidas a UTF-8={resultado.codificaciones or 'ninguna'}\n"
        f"  huecos registrados={resultado.huecos}"
    )


@case_app.command("new")
def case_new(
    from_gap: Annotated[str, typer.Option("--from-gap", help="Firma del hueco.")],
    fuente: Annotated[
        Path, typer.Option("--fuente", help="Programa o carpeta donde está el hueco.")
    ],
) -> None:
    """Crea tests/cases/<firma>/ con el fragmento anonimizado del hueco y su estado actual."""
    try:
        carpeta = generadores.crear_caso(from_gap, fuente)
    except (ValueError, FileExistsError, FileNotFoundError) as error:
        raise typer.BadParameter(str(error)) from error
    typer.echo(f"Caso creado: {carpeta}")


@rules_app.command("new")
def rules_new(
    tipo: Annotated[str, typer.Argument(help="proc, statement, function, intrinsic o mapping.")],
    from_gap: Annotated[str, typer.Option("--from-gap", help="Firma del hueco.")],
    fuente: Annotated[
        Path | None,
        typer.Option("--fuente", help="Programa o carpeta; hace falta si el caso no existe."),
    ] = None,
) -> None:
    """Crea el archivo de reglas prellenado (status parcial) y apunta a su caso."""
    try:
        destino = generadores.crear_regla(tipo, from_gap, fuente)
    except (ValueError, FileExistsError, FileNotFoundError) as error:
        raise typer.BadParameter(str(error)) from error
    typer.echo(f"Regla creada: {destino}. Complétala y corre `sgm rules validate`.")


@rules_app.command("validate")
def rules_validate() -> None:
    """Valida reglas, casos y configuración contra sus esquemas. Sale con 1 si hay errores."""
    problems = rules_validate_mod.validate()
    for problem in problems:
        typer.echo(str(problem))
    if problems:
        typer.echo(f"{len(problems)} problemas.")
        raise typer.Exit(code=1)
    typer.echo("Reglas, casos y configuración válidos.")


if __name__ == "__main__":
    app()
