"""Cola de validaciones de Studio que no se pudieron ejecutar.

Una validación que no se pudo hacer (bridge caído, diálogo modal, Studio ocupado) no se cuenta como
pasada ni se pierde: queda en `out/studio-pendientes.json` con su motivo y el número de intentos, y
`corpus_studio.py pendientes` la reintenta. La escritura es atómica (archivo temporal y
`os.replace`), así un corte a mitad del lote no deja la cola a medias.

El reintento recompila con un sufijo nuevo porque Studio guarda en memoria cada Job por su
identificador: reutilizar el nombre devuelve el resultado viejo (ver `studio_validar.sufijo_nuevo`).
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path

RUTA_POR_OMISION = Path("out") / "studio-pendientes.json"
MOTIVO_REINTENTO = "FALLO_EN_REINTENTO"


@dataclass(frozen=True)
class Pendiente:
    """Un caso que quedó sin validar: cuál, por qué y cuántas veces se intentó."""

    caso: str
    motivo: str
    intentos: int = 1


def _normalizar(datos: object) -> list[Pendiente]:
    """Entradas válidas de la lista guardada; lo que no tenga caso se descarta."""
    if not isinstance(datos, list):
        return []
    pendientes: list[Pendiente] = []
    for item in datos:
        if not isinstance(item, dict):
            continue
        caso = str(item.get("caso") or "").strip()
        if not caso:
            continue
        try:
            intentos = int(item.get("intentos") or 1)
        except (TypeError, ValueError):
            intentos = 1
        motivo = str(item.get("motivo") or "sin motivo")
        pendientes.append(Pendiente(caso, motivo, max(intentos, 1)))
    return pendientes


def leer(ruta: Path) -> list[Pendiente]:
    """Pendientes guardados; lista vacía si el archivo no existe o no se puede leer."""
    try:
        texto = Path(ruta).read_text(encoding="utf-8")
    except OSError:
        return []
    try:
        datos = json.loads(texto)
    except ValueError:
        return []
    return _normalizar(datos)


def _escribir(ruta: Path, pendientes: list[Pendiente]) -> None:
    """Escribe la cola completa de una vez: temporal en la misma carpeta y reemplazo."""
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    temporal = ruta.with_name(f"{ruta.name}.tmp")
    filas = [asdict(pendiente) for pendiente in pendientes]
    texto = json.dumps(filas, ensure_ascii=False, indent=2)
    temporal.write_text(texto + "\n", encoding="utf-8")
    os.replace(temporal, ruta)


def encolar(ruta: Path, pendiente: Pendiente) -> None:
    """Agrega el caso, o le suma un intento y actualiza el motivo si ya estaba."""
    pendientes = leer(ruta)
    for posicion, guardado in enumerate(pendientes):
        if guardado.caso == pendiente.caso:
            pendientes[posicion] = Pendiente(
                pendiente.caso, pendiente.motivo, guardado.intentos + 1
            )
            _escribir(ruta, pendientes)
            return
    pendientes.append(Pendiente(pendiente.caso, pendiente.motivo, max(pendiente.intentos, 1)))
    _escribir(ruta, pendientes)


def vaciar(ruta: Path, resueltos: set[str]) -> None:
    """Quita de la cola los casos resueltos; el resto conserva su orden e intentos."""
    pendientes = leer(ruta)
    quedan = [pendiente for pendiente in pendientes if pendiente.caso not in resueltos]
    if len(quedan) != len(pendientes) or ruta.exists():
        _escribir(ruta, quedan)


__all__ = ["MOTIVO_REINTENTO", "RUTA_POR_OMISION", "Pendiente", "encolar", "leer", "vaciar"]
