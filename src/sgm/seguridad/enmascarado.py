"""Enmascaramiento de valores sospechosos: ningún hallazgo guarda ni muestra el valor completo."""

from __future__ import annotations

MASCARA = "***"
# Por debajo de esta longitud no se muestra ningún carácter: 2 de 4 ya revelan media clave.
LONGITUD_MINIMA_VISIBLE = 6
# Prefijos de valores que son referencias o marcadores, no secretos: contexto de Talend, macro SAS,
# variable de shell y marcador `<...>` de plantilla.
PREFIJOS_REFERENCIA = ("context.", "$", "&", "%", "<")


def enmascarar(valor: str) -> str:
    """Muestra los 2 primeros caracteres y `***`; los valores cortos solo muestran `***`."""
    if len(valor) < LONGITUD_MINIMA_VISIBLE:
        return MASCARA
    return valor[:2] + MASCARA


def sin_comillas(valor: str) -> str:
    """Quita un par de comillas simples o dobles que envuelven el valor."""
    texto = valor.strip()
    if len(texto) >= 2 and texto[0] == texto[-1] and texto[0] in "\"'":
        return texto[1:-1]
    return texto


def es_marcador(valor: str) -> bool:
    """Valor que no es un secreto: vacío, máscara `***` o `...` (texto de ejemplo), referencia."""
    texto = sin_comillas(valor)
    sin_acento = texto.strip("`")  # un ejemplo citado en Markdown: `...`
    return not texto or set(sin_acento) <= {"*", "."} or texto.startswith(PREFIJOS_REFERENCIA)
