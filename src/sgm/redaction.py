"""Enmascara credenciales del texto fuente antes de que entre en cualquier modelo derivado.

Se aplica al leer los archivos (parser, análisis Grid): ningún JSON, plan ni informe contiene el
valor original. Conserva longitud de líneas y números de línea. La copia fuente importada no se toca.
"""

import re

MASK = "***"
_VALUE = r"""("[^"\n]*"|'[^'\n]*'|[^\s;,)\n"']+)"""
_SECRET_OPT = re.compile(
    rf"(?i)\b(password|passwd|pwd|pw|pass|dbpass|dbpwd|authdomain_secret|token|secret|sas_?pass)\b(\s*=\s*){_VALUE}"
)
# sentencias SAS que llevan credenciales
_SAS_STMT = re.compile(r"(?is)\b(?:libname|connect\s+to|filename|options|%sysexec|x)\b[^;]*")
# `proc pwencode in='clave'` lleva la clave en texto claro; `in=&macrovariable` no es un secreto
_PWENCODE = re.compile(rf"(?is)(\bproc\s+pwencode\b[^;]*?\bin\s*=\s*)(?![\"']?&){_VALUE}")
_LET = re.compile(r"(?i)(%let\s+\w*(?:pass|pwd|secret|token|apikey|api_key|key)\w*\s*=)([^;]*)")
# genérico (shell, .env, .cfg): cualquier NOMBRE=valor cuyo nombre sugiera un secreto, y -password valor
_NAME_VALUE = re.compile(
    rf"(?i)\b(\w*(?:password|passwd|pwd|secret|token|apikey|api_key)\w*)(\s*=\s*){_VALUE}"
)
_FLAG = re.compile(r"(?i)(\s-{1,2}(?:password|passwd|pw|pwd|token)\s+)(\S+)")


def _sub_opt(m: re.Match[str]) -> str:
    return f"{m.group(1)}{m.group(2)}{MASK}"


def redact_sas(text: str) -> str:
    text = _SAS_STMT.sub(lambda m: _SECRET_OPT.sub(_sub_opt, m.group(0)), text)
    text = _PWENCODE.sub(lambda m: f"{m.group(1)}{MASK}", text)
    return _LET.sub(lambda m: f"{m.group(1)} {MASK}", text)


def redact_other(text: str) -> str:
    text = _NAME_VALUE.sub(_sub_opt, text)
    return _FLAG.sub(lambda m: f"{m.group(1)}{MASK}", text)


def redact(text: str, path: str) -> str:
    """Enmascara credenciales de cualquier texto, sin fiarse de la extensión.

    Un programa SAS puede llegar como `.txt` (pasa en los lotes del cliente), así que se aplican
    ambos redactores: el de sentencias SAS y el genérico. `path` se conserva por compatibilidad.
    """
    del path
    return redact_other(redact_sas(text))
