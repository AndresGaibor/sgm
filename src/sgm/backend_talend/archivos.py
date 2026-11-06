"""Backend de archivos: escribe los Jobs en disco y no habla con Talend.

Es el backend por omisión de `sgm migrar`: deja los `.item` y `.properties` listos para abrirlos en
Studio, sin necesitar que Studio esté corriendo. Compilar y ejecutar quedan fuera de su alcance y
se piden con `BackendNoDisponible`, nunca con una traza.
"""

from __future__ import annotations

from pathlib import Path

from sgm.backend_talend.base import BackendNoDisponible, ResultadoLote, Veredicto
from sgm.talend_item.escritura import escribir_job
from sgm.talend_item.modelo import Job

_SIN_STUDIO = "el backend de archivos no compila ni ejecuta"


class ArchivosBackend:
    """Cumple `BackendTalend` escribiendo con `talend_item.escritura.escribir_job`."""

    # Fecha que se escribe en los `.properties`. `None` es el reloj; `sgm migrar` pasa la fecha de
    # modificación del programa para que dos corridas den los mismos bytes. Es atributo de clase y
    # no solo de instancia porque `TalendCliBackend` no llama a este `__init__`.
    fecha: str | None = None

    def __init__(self, fecha: str | None = None) -> None:
        self.fecha = fecha

    def escribir(self, jobs: list[Job], carpeta: Path) -> list[Path]:
        rutas: list[Path] = []
        for job in jobs:
            rutas.extend(escribir_job(job, carpeta, fecha=self.fecha))
        return rutas

    def compilar_lote(self, nombres: list[str]) -> ResultadoLote:
        raise BackendNoDisponible(_SIN_STUDIO)

    def refrescar(self) -> None:
        """No hay nada que refrescar: sin Studio, el repositorio es el propio disco."""

    def verificar(self, nombre: str, contexto: dict[str, str]) -> Veredicto:
        raise BackendNoDisponible(_SIN_STUDIO)


__all__ = ["ArchivosBackend"]
