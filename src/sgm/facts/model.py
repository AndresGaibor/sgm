"""Hechos: lo que un archivo SAS afirma, sin interpretarlo (capa C2 de `docs/automatizacion`).

Un hecho tiene tipo de un catálogo cerrado, valor, alcance, fuente (archivo y líneas) y el
extractor que lo produjo. Ninguna regla de negocio ni de Talend entra aquí.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# Catálogo cerrado. Agregar un tipo es un cambio del catálogo: se documenta y se prueba.
# Los tres últimos se añadieron al catálogo propuesto porque el SAS real los necesita.
TIPOS: frozenset[str] = frozenset(
    {
        "tabla_leida",
        "tabla_escrita",
        "tabla_borrada",
        "ruta_literal",
        "servidor",
        "conexion_base",
        "credencial",
        "macro_definida",
        "macro_llamada",
        "variable_constante",
        "variable_dinamica",
        "rama_por_valor",
        "limite_de_bucle",
        "include_externo",
        "archivo_externo",
        "funcion_usada",
        "proc_usado",
        "desconocido",
        "biblioteca",
        "comando_sistema",
        "sentencia_global",
    }
)

ALCANCES: frozenset[str] = frozenset({"work", "permanente", "externo", "no_aplica"})
USOS: frozenset[str] = frozenset({"lectura", "escritura", "no_aplica"})

MASK = "***"


class FactError(ValueError):
    """Un hecho que no cumple el catálogo o sus rangos de líneas."""


@dataclass(frozen=True)
class Fact:
    """Un hecho con su fuente. `id` lo asigna `extract` en orden estable por archivo."""

    id: str
    tipo: str
    valor: str
    alcance: str
    archivo: str
    linea_inicio: int
    linea_fin: int
    extractor: str
    nodo: str | None = None
    detalle: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.tipo not in TIPOS:
            raise FactError(f"tipo fuera del catálogo: {self.tipo}")
        if self.alcance not in ALCANCES:
            raise FactError(f"alcance fuera del catálogo: {self.alcance}")
        if self.linea_inicio < 1 or self.linea_fin < self.linea_inicio:
            raise FactError(f"rango de líneas inválido: {self.linea_inicio}-{self.linea_fin}")

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "tipo": self.tipo,
            "valor": self.valor,
            "alcance": self.alcance,
            "fuente": {
                "archivo": self.archivo,
                "lineas": [self.linea_inicio, self.linea_fin],
            },
            "nodo": self.nodo,
            "extractor": self.extractor,
            "detalle": dict(sorted(self.detalle.items())),
        }


def alcance_de(nombre: str, libref_externo: set[str]) -> str:
    """Alcance de un conjunto de datos por su biblioteca.

    Sin biblioteca explícita, SAS usa WORK. Una biblioteca declarada por `libname` con motor
    cuenta como externa; cualquier otra biblioteca explícita es permanente.
    """
    if "." not in nombre:
        return "work"
    libref = nombre.split(".", 1)[0].strip().lower()
    if libref == "work":
        return "work"
    if libref in libref_externo:
        return "externo"
    return "permanente"
