"""Compilación de muchos Jobs del corpus en una sola llamada a Studio.

Studio guarda en memoria cada Job por su identificador: compilar dos veces el mismo nombre da el
resultado viejo. Por eso cada corrida copia los Jobs a `process/` con un sufijo nuevo, compila todo
de una vez y borra lo copiado pase lo que pase. Los Jobs que ya estaban en el proyecto no se tocan.
"""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

from validar_en_studio import renombrar

from corpus_lib.studio_validar import _EXTENSIONES, _copiar_jobs, _proyecto_tecnico
from sgm.backend_talend.base import BackendTalend, ResultadoLote


def compilar_en_lote(
    carpetas: list[Path], proyecto: Path, backend: BackendTalend, sufijo: str
) -> ResultadoLote:
    """Copia los Jobs a `process/` con `sufijo`, compila en una llamada y limpia siempre.

    Cada carpeta de `carpetas` trae un Job (`.item` y, si existe, `.properties`). Devuelve lo que
    diga el backend; si el backend falla, la excepción se propaga con `process/` ya limpio.
    """
    proceso = Path(proyecto) / "process"
    proceso.mkdir(parents=True, exist_ok=True)
    tecnico = _proyecto_tecnico(Path(proyecto))
    copiados: list[Path] = []
    temporales: list[Path] = []
    try:
        nombres: list[str] = []
        for posicion, carpeta in enumerate(carpetas):
            temporal = Path(tempfile.mkdtemp(prefix="lote-"))
            temporales.append(temporal)
            _copiar_jobs(Path(carpeta), temporal)
            # El sufijo lleva la posición: dos programas distintos pueden producir Jobs con el
            # mismo nombre —`programa.sas` en dos carpetas da `job_programa` dos veces— y sin la
            # posición la segunda copia pisa a la primera y Studio solo ve un Job.
            nombres.extend(renombrar(temporal, f"{sufijo}{posicion:02d}", tecnico).values())
            for archivo in sorted(temporal.iterdir()):
                if archivo.suffix in _EXTENSIONES and archivo.is_file():
                    destino = proceso / archivo.name
                    shutil.copyfile(archivo, destino)
                    copiados.append(destino)
        # Studio tiene el repositorio en memoria: los `.item` recién copiados no existen para él
        # hasta que se refresca, y compilar sin refrescar da «el job no existe en el repositorio».
        backend.refrescar()
        return backend.compilar_lote(nombres)
    finally:
        for archivo in copiados:
            archivo.unlink(missing_ok=True)
        for temporal in temporales:
            shutil.rmtree(temporal, ignore_errors=True)


__all__ = ["compilar_en_lote"]
