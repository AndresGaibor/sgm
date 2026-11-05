"""Formato de caso del corpus: lectura y validación de `caso.yaml` y búsqueda de casos.

Un caso vive en `tests/corpus/<nivel>/<caso>/` con `programa.sas`, `entradas/`, `esperado/` y
`caso.yaml`.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import yaml

CAPAS = ("A", "B", "C")
ESTADOS = ("traducible", "parcial", "pendiente", "pendiente_revision")
CAMPOS = frozenset(
    {
        "nivel", "construcciones", "capa", "tolerancia", "orden_relevante", "estado", "motivo",
        "salidas", "razonamiento",
    }
)
_NIVEL = re.compile(r"L\d+$")
_IDENTIFICADOR = re.compile(r"[A-Za-z_]\w*$")


@dataclass(frozen=True)
class Caso:
    """Un caso del corpus, con los datos de su `caso.yaml` ya validados."""

    nombre: str
    directorio: Path
    nivel: str
    construcciones: tuple[str, ...]
    capa: str
    tolerancia: float
    orden_relevante: bool
    estado: str
    motivo: str | None
    salidas: tuple[str, ...]
    razonamiento: str | None

    @property
    def programa(self) -> Path:
        return self.directorio / "programa.sas"

    @property
    def entradas(self) -> Path:
        return self.directorio / "entradas"

    @property
    def esperado(self) -> Path:
        return self.directorio / "esperado"


def cargar_caso(directorio: Path) -> Caso:
    """Lee y valida `caso.yaml`. Un campo desconocido o un valor fuera de rango es un error."""
    ruta = directorio / "caso.yaml"
    datos = yaml.safe_load(ruta.read_text(encoding="utf-8"))
    if not isinstance(datos, dict):
        raise ValueError(f"{ruta}: se esperaba un mapa YAML")
    desconocidos = sorted(set(datos) - CAMPOS)
    if desconocidos:
        raise ValueError(f"{ruta}: campos no reconocidos {desconocidos}")

    def error(mensaje: str) -> ValueError:
        return ValueError(f"{ruta}: {mensaje}")

    nivel = datos.get("nivel")
    if nivel != directorio.parent.name:
        raise error(f"'nivel' debe ser '{directorio.parent.name}', no '{nivel}'")
    construcciones = datos.get("construcciones")
    if not isinstance(construcciones, list) or not construcciones:
        raise error("'construcciones' debe ser una lista no vacía")
    if not all(isinstance(item, str) and item.strip() for item in construcciones):
        raise error("cada construcción debe ser un texto no vacío")
    capa = datos.get("capa")
    if capa not in CAPAS:
        raise error(f"'capa' debe ser una de {CAPAS}, no '{capa}'")
    tolerancia = datos.get("tolerancia", 0)
    if isinstance(tolerancia, bool) or not isinstance(tolerancia, (int, float)) or tolerancia < 0:
        raise error("'tolerancia' debe ser un número mayor o igual que 0")
    orden_relevante = datos.get("orden_relevante", True)
    if not isinstance(orden_relevante, bool):
        raise error("'orden_relevante' debe ser true o false")
    estado = datos.get("estado")
    if estado not in ESTADOS:
        raise error(f"'estado' debe ser uno de {ESTADOS}, no '{estado}'")
    motivo = datos.get("motivo")
    if motivo is not None and not isinstance(motivo, str):
        raise error("'motivo' debe ser texto")
    if estado != "traducible" and not motivo:
        raise error(f"con estado '{estado}' hace falta 'motivo'")
    salidas = datos.get("salidas", [])
    if not isinstance(salidas, list) or not all(
        isinstance(item, str) and _IDENTIFICADOR.match(item) for item in salidas
    ):
        raise error("'salidas' debe ser una lista de nombres de tabla")
    if capa in ("A", "C") and not salidas:
        raise error(f"la capa {capa} necesita 'salidas' (tablas WORK que se comparan)")
    razonamiento = datos.get("razonamiento")
    if razonamiento is not None and not isinstance(razonamiento, str):
        raise error("'razonamiento' debe ser texto")
    return Caso(
        nombre=directorio.name,
        directorio=directorio,
        nivel=nivel,
        construcciones=tuple(construcciones),
        capa=capa,
        tolerancia=float(tolerancia),
        orden_relevante=orden_relevante,
        estado=estado,
        motivo=motivo,
        salidas=tuple(salidas),
        razonamiento=razonamiento,
    )


def niveles(corpus: Path) -> list[Path]:
    """Carpetas de nivel (L0, L1, ...) ordenadas por número."""
    if not corpus.is_dir():
        raise ValueError(f"no existe la carpeta del corpus: {corpus}")
    carpetas = [p for p in corpus.iterdir() if p.is_dir() and _NIVEL.match(p.name)]
    return sorted(carpetas, key=lambda p: int(p.name[1:]))


def casos_de_nivel(corpus: Path, nivel: str) -> list[Caso]:
    """Casos de un nivel, en orden por nombre. Una carpeta sin caso.yaml se ignora."""
    carpeta = corpus / nivel
    if not carpeta.is_dir():
        raise ValueError(f"no existe el nivel '{nivel}' en {corpus}")
    return [
        cargar_caso(p)
        for p in sorted(carpeta.iterdir())
        if p.is_dir() and (p / "caso.yaml").is_file()
    ]


def todos_los_casos(corpus: Path) -> list[Caso]:
    """Todos los casos del corpus, nivel a nivel."""
    casos: list[Caso] = []
    for carpeta in niveles(corpus):
        casos.extend(casos_de_nivel(corpus, carpeta.name))
    return casos


def resolver(corpus: Path, objetivo: str) -> list[Caso]:
    """Interpreta el argumento de `oraculo`: 'todos', un nivel (L1) o un caso por su nombre."""
    if objetivo == "todos":
        return todos_los_casos(corpus)
    if _NIVEL.match(objetivo) and (corpus / objetivo).is_dir():
        return casos_de_nivel(corpus, objetivo)
    encontrados = [caso for caso in todos_los_casos(corpus) if caso.nombre == objetivo]
    if not encontrados:
        raise ValueError(f"no existe el caso ni el nivel '{objetivo}' en {corpus}")
    if len(encontrados) > 1:
        raise ValueError(f"el nombre '{objetivo}' aparece en más de un nivel")
    return encontrados
