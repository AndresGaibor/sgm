"""Backend de Talend que llama a la CLI de `talend-mcp`.

La CLI se invoca como `bun run cli --project <proyecto> --json tools call <tool> --input <json>
--yes`, con `cwd` en la carpeta de `talend-mcp`. El ejecutor se inyecta: así se prueba el mapeo de
respuestas y la forma de la línea de comandos sin Studio, sin `bun` y sin esperar minutos.

Un fallo de la CLI nunca sale como traza: o es `BackendNoDisponible` con el motivo, o es
`ValueError` cuando lo que se pidió está prohibido (un secreto en la línea de comandos).
"""

from __future__ import annotations

import json
import subprocess
from collections.abc import Callable
from pathlib import Path

from sgm.backend_talend.archivos import ArchivosBackend
from sgm.backend_talend.base import BackendNoDisponible, ResultadoLote, Veredicto
from sgm.backend_talend.comun import (
    PARALELISMO,
    TOOL_LOTE,
    TOOL_REFRESCO,
    TOOL_VERIFICAR,
    resultado_lote,
    sin_secretos,
    veredicto,
)

# Argumentos, tiempo máximo; devuelve (código de salida, salida estándar).
Ejecutor = Callable[[list[str], float], tuple[int, str]]


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
        fecha: str | None = None,
    ) -> None:
        self.talend_dir = Path(talend_dir)
        self.proyecto = Path(proyecto)
        self.tiempo_max = tiempo_max
        self.ejecutor = ejecutor or ejecutor_subprocess(self.talend_dir)
        self.fecha = fecha

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

    def llamar(self, tool: str, entrada: dict, tiempo_max: float | None = None) -> dict:
        """Llama a una herramienta y devuelve su `data`, o lanza `BackendNoDisponible`.

        `tiempo_max` permite un corte más corto que el del backend (la comprobación de salud usa
        diez segundos para no colgar el ciclo de desarrollo).
        """
        limite = self.tiempo_max if tiempo_max is None else tiempo_max
        codigo, salida = self.ejecutor(self._comando(tool, entrada), limite)
        try:
            respuesta = json.loads(salida)
        except (TypeError, ValueError) as error:
            raise BackendNoDisponible(
                f"respuesta no válida de la CLI de talend-mcp al llamar {tool}: "
                f"{str(salida)[:200]!r}"
            ) from error
        if not isinstance(respuesta, dict):
            raise BackendNoDisponible(f"respuesta no válida de la CLI de talend-mcp: {tool}")
        datos = respuesta.get("data")
        # `ok: false` con `error` es un fallo del puente; `ok: false` con `data` es un resultado
        # negativo (un Job que no compila), que el llamador decide cómo tratar.
        if respuesta.get("error") or (respuesta.get("ok") is False and not isinstance(datos, dict)):
            motivo = respuesta.get("error") or respuesta.get("message") or f"código {codigo}"
            raise BackendNoDisponible(f"la CLI de talend-mcp falló en {tool}: {motivo}")
        if codigo != 0:
            raise BackendNoDisponible(f"la CLI de talend-mcp falló en {tool}: código {codigo}")
        return datos if isinstance(datos, dict) else respuesta

    def refrescar(self) -> None:
        """Pide a Studio que relea el workspace: sin eso, un `.item` copiado a mano no existe."""
        self.llamar(TOOL_REFRESCO, {})

    def compilar_lote(self, nombres: list[str]) -> ResultadoLote:
        """Compila los Jobs en una llamada; la respuesta real trae un mapa `result.jobs`."""
        datos = self.llamar(TOOL_LOTE, {"jobs": list(nombres), "parallelism": PARALELISMO})
        return resultado_lote(datos, list(nombres))

    def verificar(self, nombre: str, contexto: dict[str, str]) -> Veredicto:
        """Compila el Job y devuelve su veredicto, sin ejecutarlo.

        `talend_job_verify` no acepta contexto: el de esta llamada se valida (para que ningún
        secreto llegue a la CLI) y se guarda para cuando el Job se ejecute con `run: true`.
        """
        sin_secretos(contexto)
        datos = self.llamar(TOOL_VERIFICAR, {"job": nombre, "run": False})
        return veredicto(datos)


__all__ = ["Ejecutor", "TalendCliBackend", "ejecutor_subprocess"]
