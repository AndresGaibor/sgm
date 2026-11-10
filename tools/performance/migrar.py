"""Mide tiempo y memoria de `sgm migrar` en las entradas de MG-P12-01."""

from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    __package__ = "tools.performance"

from .medicion import measure_command

WALL_TIME_LIMIT_SECONDS = 120.0
PEAK_MEMORY_LIMIT_BYTES = 1_000_000_000
PROCESS_TIMEOUT_SECONDS = 600.0
EXPECTED_FOLDER_PROGRAMS = 189


def select_sas_files(source: Path, exclude: Path | None = None) -> list[Path]:
    """Lista `.sas` recursivamente, con orden estable y una exclusión opcional."""
    excluded = exclude.resolve() if exclude is not None else None
    files = [
        path
        for path in source.rglob("*")
        if path.is_file() and path.suffix.casefold() == ".sas"
        and (excluded is None or path.resolve() != excluded)
    ]
    return sorted(
        files,
        key=lambda path: (
            path.relative_to(source).as_posix().casefold(),
            path.relative_to(source).as_posix(),
        ),
    )


def stage_sas_files(files: list[Path], source: Path, destination: Path) -> int:
    """Copia las fuentes conservando rutas relativas; el tiempo de copia no se mide."""
    for source_file in files:
        target = destination / source_file.relative_to(source)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_file, target)
    return len(files)


def meets_limits(
    measurement: dict[str, int | float | bool | str | None],
    actual_packages: int,
    expected_packages: int,
) -> bool:
    """Acepta solo una corrida completa y estrictamente bajo ambos límites."""
    return (
        measurement["exit_code"] == 0
        and measurement["timed_out"] is False
        and float(measurement["elapsed_seconds"]) < WALL_TIME_LIMIT_SECONDS
        and int(measurement["peak_memory_bytes"]) < PEAK_MEMORY_LIMIT_BYTES
        and actual_packages == expected_packages
    )


def _package_count(output: Path) -> tuple[int, int]:
    files = [path for path in output.rglob("*") if path.is_file()]
    packages = sum(path.name == "trace.json" for path in files)
    output_bytes = sum(path.stat().st_size for path in files)
    return packages, output_bytes


def _measure_scenario(
    name: str,
    source: Path,
    source_files: int,
    source_bytes: int,
    expected_packages: int,
    output: Path,
    project_root: Path,
) -> dict[str, Any]:
    result = measure_command(
        [sys.executable, "-m", "sgm.cli", "migrar", str(source), "--out", str(output)],
        cwd=project_root,
        timeout_seconds=PROCESS_TIMEOUT_SECONDS,
    )
    actual_packages, output_bytes = _package_count(output)
    return {
        "source": name,
        "source_files": source_files,
        "source_bytes": source_bytes,
        **result,
        "expected_packages": expected_packages,
        "actual_packages": actual_packages,
        "output_bytes": output_bytes,
        "passed": meets_limits(result, actual_packages, expected_packages),
    }


def run_benchmarks(project_root: Path, report_path: Path) -> dict[str, Any]:
    """Mide `client_large.sas` y los otros 189 fixtures en un árbol temporal."""
    fixture_root = project_root / "tests" / "fixtures" / "sas"
    large_source = fixture_root / "client" / "client_large.sas"
    if not large_source.is_file():
        raise FileNotFoundError(f"no existe el caso de estrés esperado: {large_source.name}")
    folder_files = select_sas_files(fixture_root, exclude=large_source)
    if len(folder_files) != EXPECTED_FOLDER_PROGRAMS:
        raise ValueError(
            f"se esperaban {EXPECTED_FOLDER_PROGRAMS} fuentes de carpeta y se encontraron "
            f"{len(folder_files)}; revisar el conjunto de medición"
        )

    with tempfile.TemporaryDirectory(prefix="sgm-p12-01-") as temporary:
        temporary_root = Path(temporary)
        staged_source = temporary_root / "programas"
        staged_count = stage_sas_files(folder_files, fixture_root, staged_source)
        if staged_count != EXPECTED_FOLDER_PROGRAMS:
            raise RuntimeError("el número de fuentes preparadas no coincide con el seleccionado")

        large_output = temporary_root / "salida-large"
        folder_output = temporary_root / "salida-carpeta"
        large_case = _measure_scenario(
            "tests/fixtures/sas/client/client_large.sas",
            large_source,
            1,
            large_source.stat().st_size,
            1,
            large_output,
            project_root,
        )
        folder_case = _measure_scenario(
            "tests/fixtures/sas/ (client_large.sas excluido)",
            staged_source,
            staged_count,
            sum(path.stat().st_size for path in folder_files),
            EXPECTED_FOLDER_PROGRAMS,
            folder_output,
            project_root,
        )

    report = {
        "task": "MG-P12-01",
        "measured_at_utc": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "environment": {
            "os": platform.system(),
            "os_release": platform.release(),
            "architecture": platform.machine(),
            "python": platform.python_version(),
            "cpu_count": os.cpu_count(),
        },
        "limits": {
            "elapsed_seconds_strictly_less_than": WALL_TIME_LIMIT_SECONDS,
            "peak_memory_bytes_strictly_less_than": PEAK_MEMORY_LIMIT_BYTES,
            "process_timeout_seconds": PROCESS_TIMEOUT_SECONDS,
        },
        "scenarios": {"large_program": large_case, "folder_189": folder_case},
        "passed": large_case["passed"] and folder_case["passed"],
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Mide MG-P12-01 sin guardar salidas de Job.")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("metrics/performance/mg-p12-01.json"),
        help="Ruta del reporte JSON de la medición.",
    )
    arguments = parser.parse_args()
    project_root = Path(__file__).resolve().parents[2]
    report = run_benchmarks(project_root, arguments.output)
    for name, result in report["scenarios"].items():
        print(
            f"{name}: {result['elapsed_seconds']:.3f} s, "
            f"{result['peak_memory_bytes']} bytes, "
            f"{result['actual_packages']}/{result['expected_packages']} paquetes"
        )
    print(f"Resultado: {'aprobado' if report['passed'] else 'fuera de límites'}")
    print(f"Reporte: {arguments.output}")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
