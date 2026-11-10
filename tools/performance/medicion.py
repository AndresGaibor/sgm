"""Mide el tiempo y la memoria residente de un comando y sus procesos descendientes."""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from .windows_processes import WindowsProcessTreeMemory

POLL_INTERVAL_SECONDS = 0.05

class _ProcessPeakMemory:
    """Mide el máximo residente observado para el árbol del proceso migrador."""

    def __init__(self, pid: int) -> None:
        self.metric: str
        self._pid = pid
        self._peak_bytes = 0
        self._windows = None
        if os.name == "nt":
            self._windows = WindowsProcessTreeMemory(pid)
            self.metric = self._windows.metric
        elif sys.platform.startswith("linux"):
            self.metric = "PeakProcessTreeVmRSS"
        else:
            raise RuntimeError("la medición de memoria solo admite Windows y Linux")

    @staticmethod
    def _linux_process_tree(root_pid: int) -> set[int]:
        parents: dict[int, int] = {}
        for stat_path in Path("/proc").glob("[0-9]*/stat"):
            try:
                stat = stat_path.read_text(encoding="ascii")
                fields = stat[stat.rfind(")") + 2 :].split()
                parents[int(stat_path.parent.name)] = int(fields[1])
            except (FileNotFoundError, IndexError, ValueError):
                continue

        process_ids = {root_pid}
        while True:
            descendants = {
                pid for pid, parent_pid in parents.items() if parent_pid in process_ids
            }
            expanded = process_ids | descendants
            if expanded == process_ids:
                return process_ids
            process_ids = expanded

    def read(self) -> int:
        if self._windows is not None:
            return self._windows.read()

        process_ids = self._linux_process_tree(self._pid)
        total_bytes = 0
        for pid in process_ids:
            try:
                status = Path(f"/proc/{pid}/status").read_text(encoding="ascii")
            except FileNotFoundError:
                continue
            for line in status.splitlines():
                if line.startswith("VmRSS:"):
                    total_bytes += int(line.split()[1]) * 1024
                    break
        self._peak_bytes = max(self._peak_bytes, total_bytes)
        return self._peak_bytes

    def terminate_windows_tree(self) -> set[int]:
        if self._windows is not None:
            return self._windows.terminate_windows_tree()
        return set()

    def close(self) -> None:
        if self._windows is not None:
            self._windows.close()


def measure_command(
    command: list[str], cwd: Path, timeout_seconds: float
) -> dict[str, int | float | bool | str | None]:
    """Ejecuta un hijo y captura duración, salida y máximo residente del sistema."""
    if not command:
        raise ValueError("el comando no puede estar vacío")
    if timeout_seconds <= 0:
        raise ValueError("timeout_seconds debe ser positivo")

    started = time.perf_counter()
    popen_options: dict[str, Any] = {}
    if os.name != "nt":
        popen_options["start_new_session"] = True
    process = subprocess.Popen(
        command,
        cwd=cwd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        **popen_options,
    )
    monitor: _ProcessPeakMemory | None = None
    peak_memory_bytes = 0
    timed_out = False
    try:
        monitor = _ProcessPeakMemory(process.pid)
        while process.poll() is None:
            peak_memory_bytes = max(peak_memory_bytes, monitor.read())
            elapsed = time.perf_counter() - started
            if elapsed >= timeout_seconds:
                timed_out = True
                _terminate_process_tree(process, monitor)
                break
            time.sleep(POLL_INTERVAL_SECONDS)
        exit_code = process.wait()
        peak_memory_bytes = max(peak_memory_bytes, monitor.read())
        memory_metric = monitor.metric
    finally:
        if process.poll() is None:
            _terminate_process_tree(process, monitor)
            process.wait()
        if monitor is not None:
            monitor.close()

    return {
        "elapsed_seconds": round(time.perf_counter() - started, 3),
        "exit_code": exit_code,
        "timed_out": timed_out,
        "peak_memory_bytes": peak_memory_bytes,
        "memory_metric": memory_metric,
    }


def _terminate_process_tree(
    process: subprocess.Popen[Any], monitor: _ProcessPeakMemory | None
) -> None:
    """Termina el comando y sus descendientes para evitar procesos huérfanos."""
    if process.poll() is not None:
        return
    if os.name == "nt":
        remaining = (
            monitor.terminate_windows_tree() if monitor is not None else {process.pid}
        )
        if process.poll() is None:
            remaining.add(process.pid)
        if not remaining:
            return
        for pid in remaining:
            subprocess.run(
                ["taskkill", "/PID", str(pid), "/T", "/F"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
        if process.poll() is None:
            process.kill()
        return

    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
