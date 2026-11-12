"""Rebanadas literales de programas con trazabilidad y ediciones declaradas."""

from __future__ import annotations

import hashlib
import re
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass(frozen=True)
class Rebanada:
    """Origen y huella del fragmento original, antes de las ediciones declaradas."""

    fuente: str
    rangos: tuple[tuple[int, int], ...]
    sha256: str
    prologo: str = ""
    sustituciones: tuple[tuple[str, str], ...] = ()


def rebanar(texto: str, rangos: Sequence[tuple[int, int]]) -> str:
    """Extrae líneas 1-based inclusivas y deja una línea vacía entre los rangos."""
    lines = texto.splitlines(keepends=True)
    fragments = []
    for start, end in rangos:
        if start < 1 or end < start or end > len(lines):
            raise ValueError(
                f"rango inválido ({start}, {end}): la fuente tiene {len(lines)} líneas"
            )
        fragments.append("".join(lines[start - 1:end]))
    result = ""
    for fragment in fragments:
        if result:
            result += "\n" if result.endswith(("\n", "\r")) else "\n\n"
        result += fragment
    return result


def huella(texto_rebanado: str) -> str:
    """SHA-256 del texto original seleccionado, codificado en UTF-8."""
    return hashlib.sha256(texto_rebanado.encode("utf-8")).hexdigest()


def armar(rebanada: Rebanada, texto_fuente: str) -> str:
    """Aplica sustituciones únicas y antepone el prólogo en una línea independiente."""
    text = rebanar(texto_fuente, rebanada.rangos)
    for old, new in rebanada.sustituciones:
        if not old or text.count(old) != 1:
            raise ValueError(f"sustitución {old!r}: debe aparecer exactamente una vez")
        text = text.replace(old, new, 1)
    prefix = rebanada.prologo
    if prefix and not prefix.endswith(("\n", "\r")):
        prefix += "\n"
    return prefix + text


def verificar(rebanada: Rebanada, raiz: Path) -> list[str]:
    """Verifica únicamente fuentes relativas contenidas en la raíz, incluso tras symlinks."""
    source_path = Path(rebanada.fuente)
    if source_path.anchor or ".." in source_path.parts:
        return [f"{rebanada.fuente}: la fuente debe ser una ruta relativa sin '..'"]
    try:
        path = (raiz / source_path).resolve()
        if not path.is_relative_to(raiz.resolve()):
            return [f"{rebanada.fuente}: la fuente resuelta queda fuera de la raíz"]
        if not path.is_file():
            return [f"{rebanada.fuente}: la fuente no existe"]
        with path.open(encoding="utf-8", newline="") as source:
            actual = huella(rebanar(source.read(), rebanada.rangos))
    except (OSError, UnicodeError, ValueError, RuntimeError) as error:
        return [f"{rebanada.fuente}: no se pudo verificar: {error}"]
    if actual != rebanada.sha256:
        return [f"{rebanada.fuente}: huella distinta (esperada {rebanada.sha256}, actual {actual})"]
    return []


def escribir_rebanada(destino: Path, rebanada: Rebanada, texto_fuente: str) -> list[Path]:
    """Escribe programa y metadatos seguros; la huella siempre describe el original."""
    if huella(rebanar(texto_fuente, rebanada.rangos)) != rebanada.sha256:
        raise ValueError(f"{rebanada.fuente}: la huella no corresponde al fragmento original")
    text = armar(rebanada, texto_fuente)
    metadata = {
        "fuente": rebanada.fuente,
        "rangos": [list(span) for span in rebanada.rangos],
        "sha256": rebanada.sha256,
        "prologo": rebanada.prologo,
        "sustituciones": [list(pair) for pair in rebanada.sustituciones],
    }
    destino.mkdir(parents=True, exist_ok=True)
    program, manifest = destino / "programa.sas", destino / "rebanada.yaml"
    program.write_text(text, encoding="utf-8", newline="")
    manifest.write_text(
        yaml.safe_dump(metadata, allow_unicode=True, sort_keys=False),
        encoding="utf-8", newline="",
    )
    return [program, manifest]


def _pairs(value: object, field: str) -> list[tuple]:
    """Valida pares YAML sin aceptar textos como secuencias de dos caracteres."""
    if not isinstance(value, list):
        raise ValueError(f"'{field}' debe ser una lista de pares")
    if any(not isinstance(pair, list) or len(pair) != 2 for pair in value):
        raise ValueError(f"'{field}' debe contener pares de dos elementos")
    return [tuple(pair) for pair in value]


def _line_number(value: object) -> int:
    """Acepta enteros positivos o su escritura decimal sin pérdida de precisión."""
    if type(value) is int and value > 0:
        return value
    if isinstance(value, str) and re.fullmatch(r"[0-9]+", value) and int(value) > 0:
        return int(value)
    raise ValueError("'rangos' requiere números de línea enteros positivos")


def leer_rebanada(ruta: Path) -> Rebanada:
    """Carga YAML seguro, valida campos y convierte listas de pares a tuplas."""
    try:
        data = yaml.safe_load(ruta.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("se esperaba un mapa YAML")
        required = {"fuente", "rangos", "sha256"}
        allowed = required | {"prologo", "sustituciones"}
        if required - data.keys() or data.keys() - allowed:
            raise ValueError("faltan campos requeridos o hay campos desconocidos")
        source, digest = data["fuente"], data["sha256"]
        if not isinstance(source, str) or not source.strip():
            raise ValueError("'fuente' debe ser texto no vacío")
        if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise ValueError("'sha256' debe tener 64 dígitos hexadecimales en minúscula")
        spans = tuple(
            (_line_number(start), _line_number(end))
            for start, end in _pairs(data["rangos"], "rangos")
        )
        if any(start > end for start, end in spans):
            raise ValueError("'rangos' contiene un rango invertido")
        prefix = data.get("prologo", "")
        if not isinstance(prefix, str):
            raise ValueError("'prologo' debe ser texto")
        replacements = tuple(_pairs(data.get("sustituciones", []), "sustituciones"))
        if any(not isinstance(old, str) or not old or not isinstance(new, str)
               for old, new in replacements):
            raise ValueError("'sustituciones' requiere textos y un origen no vacío")
        return Rebanada(source, spans, digest, prefix, replacements)
    except (OSError, UnicodeError, yaml.YAMLError, ValueError) as error:
        raise ValueError(f"{ruta}: rebanada inválida: {error}") from None
