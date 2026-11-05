"""Cruce del esperado por construcción con el oráculo SQL, caso a caso.

Para cada caso corre el programa con `validaciones_sas.ejecutar` (PROC SQL en SQLite; DATA step con
la capa B) y compara cada tabla WORK y cada archivo de PROC EXPORT con lo que dio `calcular`. Una
tabla que el oráculo no puede calcular queda en `no_verificadas` con su motivo; no cuenta como
verificada ni como diferencia.

Uso (desde la raíz del repositorio):

    uv run python tools/corpus_datos/validaciones_cruce.py
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path

_CARPETA = Path(__file__).resolve().parent
for _ruta in (_CARPETA.parent, _CARPETA):
    if str(_ruta) not in sys.path:
        sys.path.insert(0, str(_ruta))

from corpus_lib.csv_tabla import Tabla, celda_texto  # noqa: E402
from validaciones import CASOS, EXCEL  # noqa: E402
from validaciones_esperado import calcular  # noqa: E402
from validaciones_sas import ejecutar  # noqa: E402

REPO = _CARPETA.parents[1]
CORPUS_L8 = REPO / "tests" / "corpus" / "L8" / "validaciones"


@dataclass
class Informe:
    """Resultado del cruce de un caso."""

    caso: str
    verificadas: list[str] = field(default_factory=list)
    diferencias: dict[str, list[str]] = field(default_factory=dict)
    no_verificadas: dict[str, str] = field(default_factory=dict)


def _canon(fila: tuple) -> tuple[str, ...]:
    return tuple(celda_texto(valor) for valor in fila)


def _comparar(esperada: Tabla, obtenida: Tabla, con_cabecera: bool = True) -> list[str]:
    """Diferencias entre dos tablas: columnas (si hay cabecera) y el multiconjunto de filas."""
    diferencias: list[str] = []
    if con_cabecera and list(esperada.columnas) != list(obtenida.columnas):
        return [f"columnas: esperado {esperada.columnas}, obtenido {obtenida.columnas}"]
    esp = sorted(_canon(f) for f in esperada.filas)
    obt = sorted(_canon(f) for f in obtenida.filas)
    if len(esp) != len(obt):
        diferencias.append(f"filas: esperado {len(esp)}, obtenido {len(obt)}")
    for a, b in list(zip(esp, obt, strict=False))[:5]:
        if a != b:
            diferencias.append(f"fila esperada {a} frente a obtenida {b}")
    return diferencias


def cruzar(caso: str, carpeta: Path | None = None) -> Informe:
    """Corre el programa del caso y compara su esperado por construcción con lo que obtiene."""
    carpeta = carpeta or CORPUS_L8 / caso
    esperado = calcular(caso, CASOS[caso], EXCEL)
    programa = (carpeta / "programa.sas").read_text(encoding="utf-8")
    corrida = ejecutar(programa, carpeta / "entradas")
    informe = Informe(caso)
    for nombre, esp in esperado.tablas.items():
        if nombre not in corrida.tablas:
            motivo = corrida.no_verificadas.get(nombre, "el programa no produce esta tabla")
            informe.no_verificadas[nombre] = motivo
            continue
        dif = _comparar(esp, corrida.tablas[nombre])
        if dif:
            informe.diferencias[nombre] = dif
        else:
            informe.verificadas.append(nombre)
    for archivo, esp in esperado.archivos.items():
        tabla = corrida.exportes.get(archivo)
        if tabla is None:
            informe.no_verificadas[f"archivo {archivo}"] = "sin PROC EXPORT en el programa"
        elif tabla not in corrida.tablas:
            motivo = corrida.no_verificadas.get(tabla, "tabla no producida")
            informe.no_verificadas[f"archivo {archivo}"] = f"depende de {tabla}: {motivo}"
        else:
            dif = _comparar(esp, corrida.tablas[tabla], con_cabecera=False)
            if dif:
                informe.diferencias[f"archivo {archivo}"] = dif
            else:
                informe.verificadas.append(f"archivo {archivo}")
    return informe


def main() -> int:
    for caso in CASOS:
        informe = cruzar(caso)
        print(f"{caso}: verificadas {len(informe.verificadas)}, "
              f"no verificadas {len(informe.no_verificadas)}, "
              f"diferencias {len(informe.diferencias)}")  # fmt: skip
        for nombre, dif in informe.diferencias.items():
            print(f"  DIFIERE {nombre}: {dif[:2]}")
        for nombre, motivo in informe.no_verificadas.items():
            print(f"  NO VERIFICADA {nombre}: {motivo[:120]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
