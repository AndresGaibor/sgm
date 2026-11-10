"""Publica el paquete de `sgm migrar` solo después de revisar sus artefactos."""

from __future__ import annotations

import shutil
import tempfile
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from sgm.seguridad import escaner_secretos
from sgm.seguridad.escaner_secretos import Hallazgo


@dataclass(frozen=True)
class ResultadoCompuerta:
    """Estado seguro para informar al llamador; nunca guarda texto sospechoso."""

    publicado: bool
    hallazgos: tuple[Hallazgo, ...] = field(default_factory=tuple)
    motivo: str | None = None
    archivos: tuple[Path, ...] = field(default_factory=tuple)


def _contiene_enlaces(ruta: Path) -> bool:
    """Evita que el escaneo o la publicación sigan rutas fuera del paquete."""
    return _es_enlace(ruta) or (ruta.is_dir() and any(_es_enlace(hijo) for hijo in ruta.rglob("*")))


def _es_enlace(ruta: Path) -> bool:
    """Reconoce symlinks y junctions de Windows, que también salen del árbol esperado."""
    return ruta.is_symlink() or ruta.is_junction()


def _escanear(ruta: Path) -> tuple[Hallazgo, ...] | str:
    """Devuelve hallazgos o un motivo genérico que no propaga errores con datos sensibles."""
    try:
        return escaner_secretos.escanear_ruta(ruta).hallazgos
    except Exception as error:  # noqa: BLE001 — el texto del error podría incluir contenido leído
        return f"no se pudo completar la revisión de seguridad ({type(error).__name__})"


def _archivos(ruta: Path) -> list[Path]:
    return sorted((hijo for hijo in ruta.rglob("*") if hijo.is_file()), key=lambda p: p.as_posix())


def _publicar(candidato: Path, destino: Path) -> tuple[Path, ...]:
    """Copia archivos revisados sin quitar archivos manuales del paquete destino."""
    publicados: list[Path] = []
    for archivo in _archivos(candidato):
        relativo = archivo.relative_to(candidato)
        final = destino / relativo
        final.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(archivo, final)
        publicados.append(final)
    return tuple(publicados)


def publicar_con_revision(destino: Path, generar: Callable[[Path], None]) -> ResultadoCompuerta:
    """Genera, escanea y publica un paquete o bloquea cualquier salida dudosa.

    Se clona la salida anterior al staging y se genera encima: así la revisión cubre también los
    archivos existentes, los archivos extra se conservan y una salida con hallazgos queda intacta.
    """
    destino = Path(destino)
    if _contiene_enlaces(destino):
        return ResultadoCompuerta(False, motivo="la ruta de salida contiene un enlace simbólico")
    if destino.exists() and not destino.is_dir():
        return ResultadoCompuerta(False, motivo="la ruta de salida existente no es una carpeta")

    if destino.is_dir():
        previos = _escanear(destino)
        if isinstance(previos, str):
            return ResultadoCompuerta(False, motivo=previos)
        if previos:
            return ResultadoCompuerta(False, hallazgos=previos)

    try:
        destino.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix=".sgm-migrar-", dir=destino.parent) as temporal:
            candidato = Path(temporal) / destino.name
            if destino.is_dir():
                shutil.copytree(destino, candidato, dirs_exist_ok=True)
            else:
                candidato.mkdir()

            generar(candidato)
            if _contiene_enlaces(candidato):
                return ResultadoCompuerta(
                    False, motivo="el paquete generado contiene un enlace simbólico"
                )

            hallazgos = _escanear(candidato)
            if isinstance(hallazgos, str):
                return ResultadoCompuerta(False, motivo=hallazgos)
            if hallazgos:
                return ResultadoCompuerta(False, hallazgos=hallazgos)
            if _contiene_enlaces(destino):
                return ResultadoCompuerta(
                    False, motivo="la ruta de salida contiene un enlace simbólico"
                )

            try:
                publicados = _publicar(candidato, destino)
            except Exception as error:  # noqa: BLE001 — no revelar una ruta o contenido del sistema
                return ResultadoCompuerta(
                    False,
                    motivo=f"no se pudo publicar el paquete revisado ({type(error).__name__})",
                )
            return ResultadoCompuerta(True, archivos=publicados)
    except Exception as error:  # noqa: BLE001 — falla cerrada y sin propagar datos del error
        return ResultadoCompuerta(
            False,
            motivo=f"no se pudo completar la revisión de seguridad ({type(error).__name__})",
        )


__all__ = ["ResultadoCompuerta", "publicar_con_revision"]
