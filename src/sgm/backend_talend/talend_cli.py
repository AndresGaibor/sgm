"""Backend de Talend que llama a la CLI de `talend-mcp`.

La CLI se invoca como `bun run cli --project <proyecto> --json tools call <tool> --input <json>
--yes`, con `cwd` en la carpeta de `talend-mcp`. El ejecutor se inyecta: así se prueba el mapeo de
respuestas y la forma de la línea de comandos sin Studio, sin `bun` y sin esperar minutos.

Un fallo de la CLI nunca sale como traza: o es `BackendNoDisponible` con el motivo, o es
`ValueError` cuando lo que se pidió está prohibido (un secreto en la línea de comandos).
"""

from __future__ import annotations

import json
import re
import subprocess
from collections.abc import Callable
from pathlib import Path

from sgm.backend_talend.archivos import ArchivosBackend
from sgm.backend_talend.base import BackendNoDisponible, ResultadoLote, Veredicto

# Argumentos, tiempo máximo; devuelve (código de salida, salida estándar).
Ejecutor = Callable[[list[str], float], tuple[int, str]]

_TOOL_LOTE = "talend_job_build_batch"
_TOOL_VERIFICAR = "talend_job_verify"
_PARALELISMO = 4
# Un nombre de variable de contexto que huela a credencial no se manda: la CLI no debe verla.
_SECRETO = re.compile(r"(pass|pwd|secret|token|clave)", re.IGNORECASE)


def _sin_secretos(contexto: dict[str, str]) -> None:
    """Rechaza un contexto con credenciales antes de armar la línea de comandos."""
    culpables = sorted(nombre for nombre in contexto if _SECRETO.search(nombre))
    if culpables:
        raise ValueError(f"el contexto lleva secretos y no se pueden pasar por la CLI: {culpables}")


def ejecutor_subprocess(talend_dir: Path) -> Ejecutor:
    """Ejecutor real: `subprocess.run` en la carpeta de `talend-mcp`."""

    def ejecutar(comando: list[str], tiempo_max: float) -> tuple[int, str]:
        if not talend_dir.is_dir():
            raise BackendNoDisponible(f"no se encontró la carpeta de talend-mcp: {talend_dir}")
        try:
            resultado = subprocess.run(
                comando,
                cwd=talend_dir,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=tiempo_max,
                check=False,
            )
        except FileNotFoundError as error:
            raise BackendNoDisponible(
                f"no se encontró el ejecutable {comando[0]}; instala bun y talend-mcp"
            ) from error
        except subprocess.TimeoutExpired as error:
            raise BackendNoDisponible(
                f"la CLI de talend-mcp no respondió en {tiempo_max:.0f} s"
            ) from error
        return resultado.returncode, resultado.stdout

    return ejecutar


class TalendCliBackend(ArchivosBackend):
    """Escribe como el backend de archivos y además compila y verifica con la CLI."""

    def __init__(
        self,
        talend_dir: Path,
        proyecto: Path,
        ejecutor: Ejecutor | None = None,
        tiempo_max: float = 120.0,
    ) -> None:
        self.talend_dir = Path(talend_dir)
        self.proyecto = Path(proyecto)
        self.tiempo_max = tiempo_max
        self.ejecutor = ejecutor or ejecutor_subprocess(self.talend_dir)

    def _comando(self, tool: str, entrada: dict) -> list[str]:
        return [
            "bun",
            "run",
            "cli",
            "--project",
            str(self.proyecto),
            "--json",
            "tools",
            "call",
            tool,
            "--input",
            json.dumps(entrada, ensure_ascii=False),
            "--yes",
        ]

    def _llamar(self, tool: str, entrada: dict) -> dict:
        """Llama a una herramienta y devuelve su `data`, o lanza `BackendNoDisponible`."""
        codigo, salida = self.ejecutor(self._comando(tool, entrada), self.tiempo_max)
        try:
            respuesta = json.loads(salida)
        except (TypeError, ValueError) as error:
            raise BackendNoDisponible(
                f"respuesta no válida de la CLI de talend-mcp al llamar {tool}: "
                f"{str(salida)[:200]!r}"
            ) from error
        if not isinstance(respuesta, dict):
            raise BackendNoDisponible(f"respuesta no válida de la CLI de talend-mcp: {tool}")
        if respuesta.get("ok") is False or codigo != 0:
            motivo = respuesta.get("error") or respuesta.get("message") or f"código {codigo}"
            raise BackendNoDisponible(f"la CLI de talend-mcp falló en {tool}: {motivo}")
        datos = respuesta.get("data")
        return datos if isinstance(datos, dict) else respuesta

    def compilar_lote(self, nombres: list[str]) -> ResultadoLote:
        datos = self._llamar(_TOOL_LOTE, {"jobs": list(nombres), "parallelism": _PARALELISMO})
        fallos = {
            str(item.get("job")): str(item.get("error") or "sin motivo")
            for item in datos.get("noCompilan") or []
        }
        return ResultadoLote(
            compilan=tuple(str(nombre) for nombre in datos.get("compilan") or []),
            no_compilan=fallos,
        )

    def verificar(self, nombre: str, contexto: dict[str, str]) -> Veredicto:
        _sin_secretos(contexto)
        datos = self._llamar(_TOOL_VERIFICAR, {"job": nombre, "context": dict(contexto)})
        nivel = str(datos.get("verdict") or datos.get("nivel") or "error")
        hallazgos = tuple(str(h) for h in datos.get("findings") or datos.get("hallazgos") or [])
        return Veredicto(nivel, hallazgos)


__all__ = ["Ejecutor", "TalendCliBackend", "ejecutor_subprocess"]
