"""Ámbito de formatos por ejecución; nunca comparte declaraciones entre planes."""

from contextlib import contextmanager
from contextvars import ContextVar

from sgm.formatos.usuario import normalize_user_put
from sgm.ir.formatos_usuario import FormatoUsuario
from sgm.migrar.interprete_errores import NoSoportadoEnInterprete

_FORMATS: ContextVar[dict[str, FormatoUsuario] | None] = ContextVar("user_formats", default=None)


@contextmanager
def user_formats(formats: list[FormatoUsuario]):
    """Instala el registro solo durante esta ejecución y lo restaura incluso si falla."""
    token = _FORMATS.set({fmt.nombre.casefold(): fmt for fmt in formats})
    try:
        yield
    finally:
        _FORMATS.reset(token)


def normalize(text: str) -> str:
    return normalize_user_put(text, _FORMATS.get() or {})


def apply_user_format(value: object, name: str) -> str:
    """OTHER incluye el faltante carácter, sin inventar el tipo de None (proc.pdf, p.1181)."""
    fmt = (_FORMATS.get() or {}).get(name.casefold())
    if fmt is None:
        raise NoSoportadoEnInterprete("PUT", f"formato no declarado: {name}")
    if value is None:
        raise NoSoportadoEnInterprete("PUT", "Pendiente: tipo del valor faltante sin demostrar")
    if not isinstance(value, str):
        raise NoSoportadoEnInterprete("PUT", "el formato de carácter requiere un valor de carácter")
    for key, label in fmt.rangos:
        if value == key:
            return label
    if fmt.otro is not None:
        return fmt.otro
    raise NoSoportadoEnInterprete("PUT", f"valor no enumerado sin OTHER en {name}")
