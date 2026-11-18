"""Contrato de formatos discretos de usuario para el plan D1."""

from dataclasses import dataclass

from sgm.formatos.usuario import normalize_user_put


@dataclass(frozen=True)
class FormatoUsuario:
    nombre: str
    rangos: tuple[tuple[str, str], ...]
    otro: str | None = None


def uses_user_formats(params: dict, names: set[str]) -> bool:
    """Busca usos de PUT entre las expresiones del operador, incluidas las condicionales."""
    for key, value in params.items():
        if key in {"expression", "condition", "conditional", "otherwise", "sql"} and isinstance(
            value, str,
        ):
            if normalize_user_put(value, names) != value:
                return True
        elif isinstance(value, dict) and uses_user_formats(value, names):
            return True
        elif isinstance(value, list) and any(
            uses_user_formats(item, names) for item in value if isinstance(item, dict)
        ):
            return True
    return False
