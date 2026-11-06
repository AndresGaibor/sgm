"""sgm v2: compilador de programas SAS a guías de migración a Talend."""

from importlib.metadata import PackageNotFoundError, version

# Fuente única: la versión de `pyproject.toml`, leída del paquete instalado.
# Sin instalar (p. ej. ejecutando desde el árbol fuente sin `uv sync`) queda el respaldo.
VERSION_SIN_INSTALAR = "0+desconocida"


def _version_instalada() -> str:
    """Devuelve la versión del paquete `sgm` instalado, o el respaldo si no está instalado."""
    try:
        return version("sgm")
    except PackageNotFoundError:
        return VERSION_SIN_INSTALAR


__version__ = _version_instalada()
