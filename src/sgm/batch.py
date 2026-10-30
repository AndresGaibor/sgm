"""Compilación por lotes: orden por inclusiones, paralelismo por programa y aislamiento de errores.

El análisis del proyecto (macros, expansión) se hace una vez, en el proceso principal, porque las
macros se comparten entre archivos. Después cada programa se compila en su propio proceso
(`ProcessPoolExecutor`). Si un programa falla, no detiene a los demás: su error queda en el
inventario como `PARSE_ERROR` del archivo.
"""

from __future__ import annotations

import re
from concurrent.futures import ProcessPoolExecutor

from sgm.catalog.config import Env
from sgm.compile import Compiled, compile_file, project_base
from sgm.frontend.macro_index import PathIndex, resolve_path
from sgm.frontend.program import ProgramAnalysis, analyze_program
from sgm.ir.models import Evidence, Gap, Plan
from sgm.redaction import redact

INCLUDE = re.compile(r"""(?i)%include\s+['"]([^'"]+)['"]""")


def include_order(files: dict[str, str]) -> list[str]:
    """Archivos que otros incluyen primero (sus macros se necesitan antes), luego el resto por
    nombre."""
    index = PathIndex(files)
    included: set[str] = set()
    for text in files.values():
        for raw in INCLUDE.findall(text):
            match = resolve_path(raw, index)
            if match.status == "resolved" and match.file is not None:
                included.add(match.file)
    return sorted(files, key=lambda name: (name not in included, name))


def _failed(program: str, error: Exception) -> Compiled:
    """Programa que no se pudo compilar: plan vacío y un hueco `PARSE_ERROR` del archivo."""
    plan = Plan(program=program)
    plan.gaps.append(
        Gap(
            signature=f"PARSE_ERROR:{program}:{type(error).__name__}",
            reason="PARSE_ERROR",
            evidence=[Evidence(file=program, line_start=1, line_end=1, label=None)],
        )
    )
    return Compiled(plan, [])


def _compile_one(analysis: ProgramAnalysis, program: str, base: dict) -> Compiled:
    try:
        return compile_file(analysis, program, base)
    except Exception as error:  # un archivo que falla no detiene a los demás
        return _failed(program, error)


def compile_batch(
    files: dict[str, str],
    library_engines: dict[str, str] | None = None,
    workers: int = 1,
    env: Env | None = None,
) -> tuple[dict[str, Compiled], ProgramAnalysis]:
    """Compila todos los programas. `workers` > 1 reparte los programas entre procesos.

    `env` es `env/` ya cargado (motores, políticas, externos). Sin él, valores por defecto.
    """
    clean = {path: redact(text, path) for path, text in files.items()}
    base = project_base(library_engines, env)
    externals = {path: redact(text, path) for path, text in base["external_files"].items()}
    analysis = analyze_program(clean, externals)
    order = include_order(clean)
    if workers <= 1:
        compiled = {program: _compile_one(analysis, program, base) for program in order}
    else:
        with ProcessPoolExecutor(max_workers=workers) as pool:
            futures = {
                program: pool.submit(_compile_one, analysis, program, base) for program in order
            }
            compiled = {program: future.result() for program, future in futures.items()}
    return {program: compiled[program] for program in sorted(compiled)}, analysis
