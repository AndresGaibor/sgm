"""Ámbito de formatos por ejecución; nunca comparte declaraciones entre planes."""

from contextlib import contextmanager
from contextvars import ContextVar

from sqlglot import exp

from sgm.formatos.usuario import normalize_user_put
from sgm.ir.formatos_usuario import FormatoUsuario
from sgm.ir.types_code import expression_type
from sgm.migrar.interprete_errores import NoSoportadoEnInterprete

_FORMATS: ContextVar[dict[str, FormatoUsuario] | None] = ContextVar("user_formats", default=None)
_TYPES: ContextVar[dict[str, str | None] | None] = ContextVar("user_format_types", default=None)


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


@contextmanager
def user_format_types(types: dict[str, str | None]):
    token = _TYPES.set(types)
    try:
        yield
    finally:
        _TYPES.reset(token)


def input_types() -> dict[str, str | None] | None:
    return _TYPES.get()


def sas_type(expression: exp.Expression) -> str | None:
    while isinstance(expression, exp.Paren):
        expression = expression.this
    if isinstance(expression, exp.Column):
        return (input_types() or {}).get(expression.name.casefold())
    if isinstance(expression, exp.Anonymous) and expression.name.casefold() in {"put", "sgm_put"}:
        return "String"
    inferred = expression_type(expression.sql())
    return inferred.type if inferred else None


def apply_user_format(value: object, name: str, source_type: str | None) -> str:
    """OTHER incluye el faltante carácter, sin inventar el tipo de None (proc.pdf, p.1181)."""
    fmt = (_FORMATS.get() or {}).get(name.casefold())
    if fmt is None:
        raise NoSoportadoEnInterprete("PUT", f"formato no declarado: {name}")
    if source_type != "String":
        reason = (
            "tipo SAS sin demostrar" if source_type is None else "tipo SAS distinto de carácter"
        )
        raise NoSoportadoEnInterprete(
            "PUT", f"Pendiente: P-FORMATO-TIPO; {reason} para {name} (proc.pdf, p. 1181)",
        )
    if value is None:
        value = ""
    if not isinstance(value, str):
        raise NoSoportadoEnInterprete("PUT", "el formato de carácter requiere un valor de carácter")
    for key, label in fmt.rangos:
        if value == key:
            return label
    if fmt.otro is not None:
        return fmt.otro
    raise NoSoportadoEnInterprete("PUT", f"valor no enumerado sin OTHER en {name}")
