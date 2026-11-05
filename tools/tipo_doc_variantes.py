"""Variantes de `v01_tipo_doc` para medir la comparación texto frente a número (hito 85).

El caso planta 95 filas CTE (88 válidas, 7 con `TD99`) y 65 AHO (60 y 5), con códigos **de texto**
`TD01`..`TD04` en el CSV y en el Excel de homologación. Aquí solo se cambia la representación de
los códigos; la verdad plantada y los esperados siguen saliendo de `esperado/` del corpus.

    texto     TD01..TD04 / TD99 contra TD01..TD04   (el caso original)
    numerico  1..4 / 99          contra 1..4
    ceros     01..04 / 99        contra 01..04      (el `01` frente a `1` de T10)

Con `--excel-sin-ceros` el Excel queda en `1..4` aunque el CSV lleve `01..04`. El esperado de
cada combinación se declara en `coincide()` y se comprueba ejecutando en Studio, nunca se calcula
a partir de la salida del propio Job.
"""

from __future__ import annotations

import re
import shutil
from pathlib import Path

from simular_insumos import escribir_xlsx

REPO = Path(__file__).resolve().parents[1]
CASO = REPO / "tests" / "corpus" / "L8" / "validaciones" / "v01_tipo_doc"
PRODUCTOS = ("CTE", "AHO")
VARIANTES = ("texto", "numerico", "ceros")
EXCEL = "Homologacion_tpo_dto.xlsx"
COL_TIPO_DOC = 8  # VAR9, base 0, en el CSV de 23 columnas
VALIDOS = ("TD01", "TD02", "TD03", "TD04")
CODIGOS = {
    "TD01": ("TD01", "1", "01"),
    "TD02": ("TD02", "2", "02"),
    "TD03": ("TD03", "3", "03"),
    "TD04": ("TD04", "4", "04"),
    "TD99": ("TD99", "99", "99"),
}
_TOTALES = re.compile(r"^\s*(\d+)\|[^\s|]+\s*$", re.MULTILINE)


def codigo(valor: str, variante: str) -> str:
    """Representación de un código del corpus en la variante pedida."""
    if variante not in VARIANTES or valor not in CODIGOS:
        raise ValueError(f"código o variante desconocidos: {valor!r}, {variante!r}")
    return CODIGOS[valor][VARIANTES.index(variante)]


def coincide(variante: str, sin_normalizar: bool, excel_plano: bool) -> bool:
    """Si esa combinación debe reproducir la verdad plantada de `v01`.

    Medido en Studio en el hito 85: `input(..., 8.)` vuelve `1` un `01`, y el Excel conserva su
    texto. Casan solo las formas que dejan los DOS lados de la unión con la misma escritura.
    """
    if variante == "texto":
        return sin_normalizar
    if variante == "numerico":
        return True
    if variante == "ceros":
        return not sin_normalizar if excel_plano else sin_normalizar
    raise ValueError(f"variante desconocida: {variante!r}")


def preparar_entradas(trabajo: Path, variante: str, excel_plano: bool = False) -> None:
    """Copia las entradas de `v01` cambiando solo la columna `TIPO_DOC` y el Excel."""
    entradas = trabajo / "entradas"
    salida = trabajo / "salida"
    entradas.mkdir(parents=True, exist_ok=True)
    salida.mkdir(parents=True, exist_ok=True)
    for archivo in salida.glob("*.csv"):
        archivo.unlink()
    for producto in PRODUCTOS:
        origen = CASO / "entradas" / f"DETALLE_{producto}.csv"
        filas = []
        for linea in origen.read_text(encoding="utf-8").splitlines():
            if not linea.strip():
                continue
            campos = linea.split(";")
            campos[COL_TIPO_DOC] = codigo(campos[COL_TIPO_DOC], variante)
            filas.append(";".join(campos))
        (entradas / origen.name).write_text("\n".join(filas) + "\n", encoding="utf-8")
    destino = entradas / EXCEL
    if variante == "texto":
        shutil.copyfile(CASO / "entradas" / EXCEL, destino)
    else:
        columna = (
            [CODIGOS[v][1] for v in VALIDOS]
            if excel_plano
            else [codigo(v, variante) for v in VALIDOS]
        )
        escribir_xlsx(destino, ["CNAME"], [[valor] for valor in columna])


def _filas(nombre: str) -> int:
    texto = (CASO / "esperado" / nombre).read_text(encoding="utf-8")
    return len([linea for linea in texto.splitlines() if linea.strip()]) - 1


def esperado_corpus(producto: str) -> dict[str, int]:
    """Conteos plantados en `v01`, leídos de `esperado/` (fuente independiente)."""
    return {
        "origen": _filas(f"SABANA_{producto}.csv"),
        "validos": _filas(f"TIPO_DOC_VALIDO_{producto}.csv"),
        "rechazados": _filas(f"TIPO_DOC_INVALIDO_{producto}.csv"),
    }


def expectativa(
    variante: str, sin_normalizar: bool, excel_plano: bool, corpus: dict[str, int]
) -> tuple[dict, str]:
    """Conteos que se esperan para esa combinación y por qué."""
    if coincide(variante, sin_normalizar, excel_plano):
        return dict(corpus), "coincide con la verdad plantada en v01"
    if variante == "texto":
        motivo = "input(..., 8.) deja faltante un código de texto: todo se rechaza"
    elif not sin_normalizar:
        motivo = "el 01 del CSV llega como 1 y el Excel conserva 01: todo se rechaza"
    else:
        motivo = "comparación de texto pura: 01 no casa con 1, todo se rechaza"
    return {"origen": corpus["origen"], "validos": 0, "rechazados": corpus["origen"]}, motivo


def medir(stdout: str, salida: Path, producto: str) -> dict[str, int]:
    """Conteos observados: los dos `tLogRow` y las líneas del archivo de rechazos."""
    totales = [int(m.group(1)) for m in _TOTALES.finditer(stdout)]
    archivo = salida / f"doc_incorrectos_{producto}.csv"
    lineas = archivo.read_text(encoding="utf-8").splitlines() if archivo.is_file() else []
    return {
        "origen": totales[0] if totales else -1,
        "validos": totales[1] if len(totales) > 1 else 0,
        "rechazados": max(0, len([linea for linea in lineas if linea.strip()]) - 1),
    }


def informe(producto: str, corpus: dict, esperado: dict, obtenido: dict, motivo: str) -> bool:
    """Imprime la comparación y dice si cuadra y si se cumple el invariante de R1-03."""
    cuadra = esperado == obtenido
    invariante = obtenido["origen"] == obtenido["validos"] + obtenido["rechazados"]
    print(f"{producto}: v01 planta {corpus}; combinación esperada {esperado}; obtenido {obtenido}")
    print(
        f"  invariante origen=válidos+rechazados: {'sí' if invariante else 'NO'}; "
        f"{'OK' if cuadra else 'DIFERENCIA'} ({motivo})"
    )
    return cuadra and invariante
