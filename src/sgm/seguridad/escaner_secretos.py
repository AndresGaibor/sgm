"""Escáner de secretos: busca contraseñas, tokens y claves en texto, archivos y carpetas.

Un hallazgo guarda el archivo, la línea, el tipo y el valor ENMASCARADO. El valor completo se usa
solo en memoria y nunca sale de este módulo. Las reglas viven en `reglas_texto` y `reglas_xml`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from sgm.seguridad.enmascarado import enmascarar, es_marcador
from sgm.seguridad.lista_blanca import valor_permitido_en_texto
from sgm.seguridad.reglas_texto import REGLAS_TEXTO
from sgm.seguridad.reglas_xml import hallazgos_xml

# Carpetas que no son artefactos: control de versiones, cachés y entornos locales.
CARPETAS_IGNORADAS = frozenset({".git", "__pycache__", ".venv", ".pytest_cache", "node_modules"})
_BYTES_BINARIOS = b"\x00"


@dataclass(frozen=True, order=True)
class Hallazgo:
    archivo: str
    linea: int
    tipo: str
    valor: str  # siempre enmascarado


@dataclass(frozen=True)
class Escaneo:
    revisados: int
    hallazgos: tuple[Hallazgo, ...] = field(default_factory=tuple)


def _linea_de(texto: str, posicion: int) -> int:
    return texto.count("\n", 0, posicion) + 1


def _hallazgos_de_texto(texto: str, archivo: str) -> list[Hallazgo]:
    encontrados: list[Hallazgo] = []
    for hallazgo in hallazgos_xml(texto):
        encontrados.append(
            Hallazgo(archivo, hallazgo.linea, hallazgo.tipo, enmascarar(hallazgo.valor))
        )
    for regla in REGLAS_TEXTO:
        for m in regla.patron.finditer(texto):
            valor = m.group("valor") if "valor" in m.re.groupindex else m.group(0)
            if es_marcador(valor) or valor_permitido_en_texto(valor):
                continue
            linea = _linea_de(texto, m.start())
            encontrados.append(Hallazgo(archivo, linea, regla.tipo, enmascarar(valor)))
    return _sin_duplicados(encontrados)


def _sin_duplicados(hallazgos: list[Hallazgo]) -> list[Hallazgo]:
    """Una misma línea y un mismo valor enmascarado cuentan una vez (la primera regla gana)."""
    vistos: set[tuple[str, int, str]] = set()
    unicos: list[Hallazgo] = []
    for h in hallazgos:
        clave = (h.archivo, h.linea, h.valor)
        if clave not in vistos:
            vistos.add(clave)
            unicos.append(h)
    return sorted(unicos)


def escanear_texto(texto: str, archivo: str = "<texto>") -> list[Hallazgo]:
    """Hallazgos de un texto, ordenados por línea y tipo. `archivo` solo etiqueta el resultado."""
    return _hallazgos_de_texto(texto, archivo)


def escanear_archivo(ruta: Path, raiz: Path | None = None) -> list[Hallazgo] | None:
    """Hallazgos de un archivo de texto. Devuelve None si es binario (no se revisa)."""
    datos = ruta.read_bytes()
    if _BYTES_BINARIOS in datos[:8192]:
        return None
    etiqueta = ruta.relative_to(raiz).as_posix() if raiz else ruta.name
    return _hallazgos_de_texto(datos.decode("utf-8", errors="replace"), etiqueta)


def _archivos(ruta: Path) -> list[Path]:
    """Archivos bajo `ruta` en orden alfabético, sin las carpetas ignoradas."""
    encontrados = []
    for hijo in sorted(ruta.rglob("*")):
        if not hijo.is_file():
            continue
        if any(parte in CARPETAS_IGNORADAS for parte in hijo.relative_to(ruta).parts):
            continue
        encontrados.append(hijo)
    return encontrados


def escanear_ruta(ruta: Path) -> Escaneo:
    """Escanea un archivo o una carpeta entera. Los hallazgos salen ordenados y deterministas."""
    if ruta.is_file():
        resultado = escanear_archivo(ruta)
        return Escaneo(revisados=0 if resultado is None else 1, hallazgos=tuple(resultado or ()))
    revisados = 0
    hallazgos: list[Hallazgo] = []
    for archivo in _archivos(ruta):
        resultado = escanear_archivo(archivo, raiz=ruta)
        if resultado is None:
            continue
        revisados += 1
        hallazgos.extend(resultado)
    return Escaneo(revisados=revisados, hallazgos=tuple(sorted(hallazgos)))
