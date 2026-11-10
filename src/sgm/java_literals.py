"""Emite literales Java sin insertar controles ni romper la sintaxis del código."""

from __future__ import annotations

import unicodedata

_ESCAPES = {
    '"': '\\"',
    "\\": "\\\\",
    "\b": "\\b",
    "\f": "\\f",
    "\n": "\\n",
    "\r": "\\r",
    "\t": "\\t",
}


def literal_java(text: str) -> str:
    """Devuelve una cadena Java delimitada con comillas y caracteres especiales escapados."""
    partes: list[str] = []
    for caracter in text:
        if caracter in _ESCAPES:
            partes.append(_ESCAPES[caracter])
        elif unicodedata.category(caracter) == "Cc" and ord(caracter) <= 0xFF:
            partes.append(f"\\{ord(caracter):03o}")
        elif 32 <= ord(caracter) < 127:
            partes.append(caracter)
        else:
            unidades = caracter.encode("utf-16-be")
            partes.extend(
                f"\\u{int.from_bytes(unidades[i : i + 2], 'big'):04x}"
                for i in range(0, len(unidades), 2)
            )
    return '"' + "".join(partes) + '"'


def literal_nombre_archivo(text: str) -> str:
    """Valida un segmento de nombre y devuelve un literal Java seguro."""
    if (
        not text
        or text in {".", ".."}
        or any(caracter in text for caracter in "/\\:")
        or text.endswith((" ", "."))
        or any(unicodedata.category(caracter) == "Cc" for caracter in text)
    ):
        raise ValueError("segmento de nombre de archivo inválido")
    return literal_java(text)


__all__ = ["literal_java", "literal_nombre_archivo"]
