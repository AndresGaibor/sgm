"""Pruebas del arnés de medición MG-P12-01, sin ejecutar el corpus grande."""

from __future__ import annotations

import sys
import time

from tools.performance.migrar import (
    measure_command,
    meets_limits,
    select_sas_files,
    stage_sas_files,
)


def test_select_sas_files_orders_paths_and_excludes_one_source(tmp_path):
    source = tmp_path / "source"
    nested = source / "nested"
    nested.mkdir(parents=True)
    first = source / "B.SAS"
    second = nested / "a.sas"
    excluded = source / "large.sas"
    for path in (first, second, excluded):
        path.write_text("data x; run;", encoding="utf-8")

    selected = select_sas_files(source, exclude=excluded)

    assert selected == [first, second]


def test_stage_sas_files_preserves_relative_paths(tmp_path):
    source = tmp_path / "source"
    program = source / "nested" / "program.sas"
    program.parent.mkdir(parents=True)
    program.write_text("data x; run;", encoding="utf-8")
    destination = tmp_path / "staged"

    count = stage_sas_files([program], source, destination)

    assert count == 1
    assert (destination / "nested" / "program.sas").read_text(encoding="utf-8") == "data x; run;"


def test_measure_command_captures_wall_time_and_child_peak_memory(tmp_path):
    code = (
        "import time; data = bytearray(32_000_000); "
        "[data.__setitem__(i, 1) for i in range(0, len(data), 4096)]; time.sleep(0.2)"
    )
    command = [sys.executable, "-c", code]

    result = measure_command(command, cwd=tmp_path, timeout_seconds=5.0)

    assert result["exit_code"] == 0
    assert result["timed_out"] is False
    assert 0 < result["elapsed_seconds"] < 5.0
    assert result["peak_memory_bytes"] >= 32_000_000
    assert result["memory_metric"]


def test_measure_command_kills_descendants_when_timeout_expires(tmp_path):
    marker = tmp_path / "child-survived.txt"
    child_script = tmp_path / "child.py"
    child_script.write_text(
        "import time; from pathlib import Path; time.sleep(1.2); "
        f"Path({str(marker)!r}).write_text('survived', encoding='utf-8')",
        encoding="utf-8",
    )
    parent_code = (
        "import subprocess, sys, time; "
        "subprocess.Popen([sys.executable, sys.argv[1]]); time.sleep(10)"
    )

    result = measure_command(
        [sys.executable, "-c", parent_code, str(child_script)],
        cwd=tmp_path,
        timeout_seconds=0.8,
    )
    time.sleep(1.5)

    assert result["timed_out"] is True
    assert result["exit_code"] != 0
    assert not marker.exists()


def test_meets_limits_uses_strict_time_memory_and_package_counts():
    measurement = {
        "exit_code": 0,
        "timed_out": False,
        "elapsed_seconds": 119.999,
        "peak_memory_bytes": 999_999_999,
    }

    assert meets_limits(measurement, actual_packages=189, expected_packages=189)
    assert not meets_limits({**measurement, "elapsed_seconds": 120.0}, 189, 189)
    assert not meets_limits({**measurement, "peak_memory_bytes": 1_000_000_000}, 189, 189)
    assert not meets_limits(measurement, actual_packages=188, expected_packages=189)
