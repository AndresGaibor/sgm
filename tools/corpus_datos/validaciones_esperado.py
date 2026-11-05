"""Calcula y escribe `esperado/` de los casos L8 de validaciones, por construcción.

Cada caso tiene su función en los módulos `validaciones_esp_*`. Las tablas WORK se escriben como
`esperado/<TABLA>.csv`, con cabecera y el formato del oráculo (`csv_tabla`). Los archivos de
PROC EXPORT se escriben en `esperado/archivos/<ARCHIVO>.csv`: sin cabecera (`PUTNAMES=NO`), con
separador `;` y sin comillas, como exporta `DBMS=DLM`.
"""

from __future__ import annotations

import sys
from pathlib import Path

_CARPETA = Path(__file__).resolve().parent
for _ruta in (_CARPETA.parent, _CARPETA):
    if str(_ruta) not in sys.path:
        sys.path.insert(0, str(_ruta))

from corpus_lib.csv_tabla import celda_texto, escribir_csv  # noqa: E402
from validaciones_esp_cascada import v07, v08  # noqa: E402
from validaciones_esp_cuenta import v04  # noqa: E402
from validaciones_esp_documento import v01, v02  # noqa: E402
from validaciones_esp_normaliza import v06  # noqa: E402
from validaciones_esp_saldo import v05  # noqa: E402
from validaciones_esp_ubicacion import v03  # noqa: E402
from validaciones_modelo import Esperado  # noqa: E402

# Cada caso y la función que calcula su esperado. Todas reciben (spec, excel); las que no usan
# homologación lo ignoran, para que el generador tenga una sola forma de llamarlas.
CALCULOS = {
    "v01_tipo_doc": lambda spec, excel: v01(spec, excel),
    "v02_vacios_ceros": lambda spec, excel: v02(spec),
    "v03_pais_dane": lambda spec, excel: v03(spec, excel),
    "v04_tipo_cta_gmf": lambda spec, excel: v04(spec, excel),
    "v05_codex_saldos": lambda spec, excel: v05(spec),
    "v06_normalizacion": lambda spec, excel: v06(spec),
    "v07_cadena_completa": lambda spec, excel: v07(spec, excel),
    "v08_nequi_cadena": lambda spec, excel: v08(spec, excel),
}


def calcular(caso: str, spec: dict, excel: dict) -> Esperado:
    """Esperado por construcción del caso (sin leer el SQL del programa)."""
    return CALCULOS[caso](spec, excel)


def _linea_dlm(fila: tuple) -> str:
    return ";".join(celda_texto(valor) for valor in fila)


def escribir(carpeta: Path, esp: Esperado) -> list[Path]:
    """Escribe las tablas y los archivos del esperado en `carpeta`; devuelve las rutas."""
    carpeta.mkdir(parents=True, exist_ok=True)
    escritos: list[Path] = []
    for nombre, tabla in esp.tablas.items():
        ruta = carpeta / f"{nombre}.csv"
        escribir_csv(ruta, tabla)
        escritos.append(ruta)
    carpeta_archivos = carpeta / "archivos"
    carpeta_archivos.mkdir(parents=True, exist_ok=True)
    for nombre, tabla in esp.archivos.items():
        ruta = carpeta_archivos / f"{nombre}.csv"
        ruta.write_text("".join(_linea_dlm(f) + "\n" for f in tabla.filas), encoding="utf-8")
        escritos.append(ruta)
    return escritos
