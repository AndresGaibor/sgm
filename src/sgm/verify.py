"""Comparación de salidas para la validación extremo a extremo (fase 5.8).

Compara dos exportaciones CSV (la de SAS y la de Talend) con tres chequeos: conteo de filas,
suma de cada columna numérica y huella del contenido (sin importar el orden de las filas).
No demuestra equivalencia por sí mismo: solo dice si los datos de prueba coinciden.
"""

from __future__ import annotations

import csv
import hashlib
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Informe:
    filas: tuple[int, int]
    columnas_iguales: bool
    sumas: dict[str, tuple[float, float]] = field(default_factory=dict)
    huella: tuple[str, str] = ("", "")

    @property
    def coincide(self) -> bool:
        return (
            self.filas[0] == self.filas[1]
            and self.columnas_iguales
            and all(a == b for a, b in self.sumas.values())
            and self.huella[0] == self.huella[1]
        )

    def texto(self) -> str:
        lineas = [
            f"Filas: SAS {self.filas[0]}, Talend {self.filas[1]}",
            f"Columnas iguales: {'sí' if self.columnas_iguales else 'no'}",
        ]
        for col, (a, b) in sorted(self.sumas.items()):
            lineas.append(f"Suma de {col}: SAS {a}, Talend {b}")
        lineas.append(f"Huella: {'igual' if self.huella[0] == self.huella[1] else 'distinta'}")
        lineas.append("RESULTADO: " + ("coinciden" if self.coincide else "no coinciden"))
        return "\n".join(lineas) + "\n"


def _leer(ruta: Path) -> tuple[list[str], list[list[str]]]:
    """Cabecera y filas de un CSV; el separador es `;` si la cabecera lo usa, si no `,`."""
    texto = ruta.read_text(encoding="utf-8-sig")
    primera = texto.splitlines()[0] if texto.strip() else ""
    separador = ";" if primera.count(";") > primera.count(",") else ","
    filas = [fila for fila in csv.reader(texto.splitlines(), delimiter=separador) if fila]
    if not filas:
        return [], []
    cabecera, cuerpo = filas[0], filas[1:]
    return [c.strip() for c in cabecera], [[c.strip() for c in fila] for fila in cuerpo]


def _numero(texto: str) -> float | None:
    try:
        return float(texto.replace(",", "."))
    except ValueError:
        return None


def _huella(filas: list[list[str]]) -> str:
    digest = hashlib.sha256()
    for linea in sorted("\x1f".join(fila) for fila in filas):
        digest.update(linea.encode("utf-8") + b"\n")
    return digest.hexdigest()


def comparar(sas: Path, talend: Path) -> Informe:
    """Compara dos CSV de datos de prueba. Lanza `ValueError` si los encabezados no coinciden."""
    cab_a, filas_a = _leer(sas)
    cab_b, filas_b = _leer(talend)
    informe = Informe(
        filas=(len(filas_a), len(filas_b)),
        columnas_iguales=cab_a == cab_b,
        huella=(_huella(filas_a), _huella(filas_b)),
    )
    if not informe.columnas_iguales:
        return informe
    for i, col in enumerate(cab_a):
        valores_a = [_numero(f[i]) for f in filas_a if i < len(f)]
        valores_b = [_numero(f[i]) for f in filas_b if i < len(f)]
        if valores_a and all(v is not None for v in valores_a) and all(
            v is not None for v in valores_b
        ):
            informe.sumas[col] = (round(sum(valores_a), 6), round(sum(valores_b), 6))
    return informe


def comparar_command(
    sas: Path,
    talend: Path,
) -> None:
    """Compara la exportación de SAS con la de Talend: filas, sumas y huella (fase 5.8)."""
    import typer

    if not sas.exists() or not talend.exists():
        raise typer.BadParameter("uno de los archivos no existe")
    informe = comparar(sas, talend)
    typer.echo(informe.texto())
    if not informe.coincide:
        raise typer.Exit(code=1)
