"""Interfaz del backend de Talend y los tipos que devuelve.

El núcleo de `sgm` escribe Jobs sin necesitar Talend: `ArchivosBackend` basta. Lo que sí necesita
Studio (compilar, ejecutar, verificar) vive detrás de esta interfaz y solo lo implementa
`TalendCliBackend`, que habla con la CLI de `talend-mcp`. Así el núcleo no depende de la CLI.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from sgm.talend_item.modelo import Job

# Niveles del veredicto de `talend_job_verify`, en el orden en que los escribe la herramienta.
NIVELES_VEREDICTO = ("ok", "ok_con_avisos", "error")


class BackendNoDisponible(RuntimeError):
    """El backend no puede hacer lo pedido: no hay CLI, no hay Studio o no hubo respuesta válida."""


@dataclass(frozen=True)
class ResultadoLote:
    """Compilación de varios Jobs en una sola llamada: los que compilan y los que no, con motivo."""

    compilan: tuple[str, ...]
    no_compilan: dict[str, str]


@dataclass(frozen=True)
class Veredicto:
    """Resultado de verificar un Job: su nivel y los hallazgos que lo justifican."""

    nivel: str
    hallazgos: tuple[str, ...]


class BackendTalend(Protocol):
    """Lo que el resto del producto puede pedirle a un backend de Talend."""

    def escribir(self, jobs: list[Job], carpeta: Path) -> list[Path]:
        """Escribe los Jobs en `carpeta` y devuelve las rutas escritas, en orden."""
        ...

    def compilar_lote(self, nombres: list[str]) -> ResultadoLote:
        """Compila los Jobs nombrados, ya copiados al proyecto, en una sola llamada."""
        ...

    def refrescar(self) -> None:
        """Hace que Studio vea los Jobs escritos por archivo en `process/`.

        Studio guarda el repositorio en memoria: un `.item` copiado a mano no existe para él hasta
        que se refresca el workspace, y la compilación falla con «el job no existe en el
        repositorio». Un backend que no habla con Studio no tiene nada que refrescar.
        """
        ...

    def verificar(self, nombre: str, contexto: dict[str, str]) -> Veredicto:
        """Verifica un Job ya compilado con un contexto dado."""
        ...
