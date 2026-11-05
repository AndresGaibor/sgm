"""Reglas de secretos sobre el texto crudo: asignaciones, cadenas de conexión, tokens y claves.

Cada regla captura el valor en el grupo `valor`. Las reglas se aplican al texto completo, así que
una sentencia que ocupa varias líneas (`proc pwencode`, `libname ... password=`) también se ve.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# Valor de una asignación: entre comillas o hasta el próximo separador SAS/SQL/XML.
_VALOR = r"""("[^"\n]*"|'[^'\n]*'|[^\s;,)'"]+)"""


@dataclass(frozen=True)
class Regla:
    tipo: str
    patron: re.Pattern[str]


REGLAS_TEXTO: tuple[Regla, ...] = (
    Regla(
        "password_en_cadena",
        re.compile(rf"(?i)\b\w*?(?:pwd|passwd|password)\s*=\s*(?P<valor>{_VALOR})"),
    ),
    Regla(
        "secreto_en_cadena",
        re.compile(rf"(?i)\b\w*?(?:secret|token|apikey|api_key)\s*=\s*(?P<valor>{_VALOR})"),
    ),
    Regla(
        "pwencode_en_claro",
        re.compile(rf"(?is)\bproc\s+pwencode\b[^;]*?\bin\s*=\s*(?P<valor>{_VALOR})"),
    ),
    Regla("sas_cifrado", re.compile(r"(?i)\{sas\d{3}\}(?P<valor>[^\s\"';}]+)")),
    Regla(
        "token_bearer",
        re.compile(r"(?i)\bBearer\s+(?P<valor>[A-Za-z0-9\-._~+/]{8,}=*)"),
    ),
    Regla(
        "clave_privada",
        re.compile(r"-----BEGIN (?:[A-Z0-9]+ )*PRIVATE KEY-----"),
    ),
    Regla(
        "url_con_credenciales",
        re.compile(r"(?i)\b[a-z][a-z0-9+.\-]*://[^\s/:@'\"]+:(?P<valor>[^\s/@'\"]+)@"),
    ),
)
