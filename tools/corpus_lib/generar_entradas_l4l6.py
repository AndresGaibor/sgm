"""Genera los casos L4 a L6: `caso.yaml`, `entradas/`, `esperado/` (capa B) y el expandido de L5.

El `programa.sas` de cada caso se escribe a mano. Este script es reproducible: dos ejecuciones dan
los mismos bytes. Desde la carpeta `tools/`:

    uv run python -m corpus_lib.generar_entradas_l4l6

Reglas: L4 usa `corpus_semantica_funciones.evaluar` (capa B); L6 usa `referencia_datastep`
(capa B); L5 escribe `programa_expandido.sas` con `expansor_macros.expandir`, y su esperado lo
calcula el oráculo SQL con `oraculo L5` (capa A). Los casos con `pendiente` no tienen esperado.
"""

from __future__ import annotations

from pathlib import Path

import yaml
from corpus_semantica_funciones import FALTANTE, Faltante, evaluar

from .csv_tabla import Tabla, escribir_csv
from .especificaciones_l4 import ESPECIFICACIONES_L4
from .especificaciones_l4b import ESPECIFICACIONES_L4B
from .especificaciones_l5 import ESPECIFICACIONES_L5
from .especificaciones_l6 import ESPECIFICACIONES_L6
from .expansor_macros import expandir

REPO = Path(__file__).resolve().parents[2]
CORPUS = REPO / "tests" / "corpus"
TOLERANCIA_EXACTA = 0.000001


def _celda(valor: object) -> object:
    """Valor de una celda de salida: el faltante de SAS sale como None y un lógico como 1 o 0."""
    if isinstance(valor, Faltante):
        return None
    if isinstance(valor, bool):
        return int(valor)
    return valor


def calcular_l4(spec: dict) -> Tabla:
    """Aplica las asignaciones del DATA step a cada fila, en orden, con la capa B."""
    _nombre, columnas, filas, numericas = spec["entrada"]
    cols = list(columnas)
    registros = [dict(zip(cols, fila, strict=True)) for fila in filas]
    for variable, columna, pasos, _sas in spec["asignaciones"]:
        for registro in registros:
            valor = registro[columna]
            if valor is None:
                valor = FALTANTE if columna in numericas else ""
            for paso in pasos:
                valor = evaluar(paso[0], valor, *paso[1:])
            registro[variable] = _celda(valor)
        if variable not in cols:
            cols.append(variable)
    return Tabla(cols, [tuple(registro[c] for c in cols) for registro in registros])


def calcular_l6(spec: dict) -> Tabla:
    """Ejecuta la función de referencia de MERGE/FIRST./RETAIN/SORT y proyecta las columnas."""
    entradas = {
        nombre: [dict(zip(cols, fila, strict=True)) for fila in filas]
        for nombre, (cols, filas) in spec["entradas"].items()
    }
    salida = spec["calculo"](entradas)
    columnas = spec["columnas"]
    return Tabla(list(columnas), [tuple(_celda(fila[c]) for c in columnas) for fila in salida])


def _entradas(nivel: str, spec: dict) -> dict[str, tuple[list[str], list[tuple]]]:
    if nivel == "L4":
        nombre, columnas, filas, _numericas = spec["entrada"]
        return {nombre: (list(columnas), [tuple(fila) for fila in filas])}
    return {
        nombre: (list(cols), [tuple(fila) for fila in filas])
        for nombre, (cols, filas) in spec["entradas"].items()
    }


def _estado(spec: dict) -> tuple[str, str | None]:
    if "pendiente" in spec:
        return "pendiente", spec["pendiente"]
    if spec.get("pendiente_revision"):
        return "pendiente_revision", "Regla sin fuente oficial consultada; ver razonamiento."
    return "traducible", None


def _caso_yaml(nivel: str, spec: dict) -> dict:
    estado, motivo = _estado(spec)
    capa = "C" if estado == "pendiente" else ("A" if nivel == "L5" else "B")
    datos: dict = {
        "nivel": nivel,
        "construcciones": spec["construcciones"],
        "capa": capa,
        "tolerancia": 0 if nivel == "L5" else TOLERANCIA_EXACTA,
        "orden_relevante": nivel != "L5",
        "estado": estado,
        "salidas": spec["salida"] if "salida" in spec else spec["salidas"],
        "razonamiento": spec["razonamiento"],
        "fuentes_url": spec["fuentes"],
        "invariantes": spec["invariantes"],
    }
    if isinstance(datos["salidas"], str):
        datos["salidas"] = [datos["salidas"]]
    if motivo is not None:
        datos["motivo"] = motivo
    return datos


def _valores_into(spec: dict, entradas: dict[str, tuple[list[str], list[tuple]]]) -> dict:
    """Valor de cada macrovariable de `into`: la celda de la primera fila de la columna."""
    valores: dict[str, str] = {}
    for variable, (tabla, columna) in spec.get("into", {}).items():
        columnas, filas = entradas[tabla]
        valores[variable] = str(filas[0][columnas.index(columna)])
    return valores


def _escribir(directorio: Path, nombre: str, columnas: list[str], filas: list[tuple]) -> None:
    escribir_csv(directorio / "entradas" / f"{nombre}.csv", Tabla(columnas, filas))


def generar_caso(nivel: str, nombre: str, spec: dict, corpus: Path = CORPUS) -> list[Path]:
    """Escribe los archivos generados de un caso y devuelve sus rutas."""
    directorio = corpus / nivel / nombre
    escritos: list[Path] = []
    entradas = _entradas(nivel, spec)
    for tabla, (columnas, filas) in entradas.items():
        _escribir(directorio, tabla, columnas, filas)
        escritos.append(directorio / "entradas" / f"{tabla}.csv")
    ruta_yaml = directorio / "caso.yaml"
    ruta_yaml.write_text(
        yaml.safe_dump(_caso_yaml(nivel, spec), allow_unicode=True, sort_keys=False, width=1000),
        encoding="utf-8",
    )
    escritos.append(ruta_yaml)
    estado, _ = _estado(spec)
    if nivel == "L4" and estado != "pendiente":
        ruta = directorio / "esperado" / f"{spec['salida']}.csv"
        escribir_csv(ruta, calcular_l4(spec))
        escritos.append(ruta)
    if nivel == "L6":
        ruta = directorio / "esperado" / f"{spec['salida']}.csv"
        escribir_csv(ruta, calcular_l6(spec))
        escritos.append(ruta)
    if nivel == "L5":
        fuente = (directorio / "programa.sas").read_text(encoding="utf-8")
        ruta = directorio / "programa_expandido.sas"
        texto = expandir(fuente, _valores_into(spec, entradas))
        ruta.write_text(texto, encoding="utf-8", newline="\n")
        escritos.append(ruta)
    return escritos


ESPECIFICACIONES = {
    "L4": {**ESPECIFICACIONES_L4, **ESPECIFICACIONES_L4B},
    "L5": ESPECIFICACIONES_L5,
    "L6": ESPECIFICACIONES_L6,
}


def generar_todo(corpus: Path = CORPUS) -> list[Path]:
    """Escribe todos los casos L4 a L6 y devuelve los archivos escritos."""
    escritos: list[Path] = []
    for nivel, especificaciones in ESPECIFICACIONES.items():
        for nombre, spec in especificaciones.items():
            escritos.extend(generar_caso(nivel, nombre, spec, corpus))
    return escritos


def main() -> int:
    escritos = generar_todo()
    print(f"{len(escritos)} archivos generados en {CORPUS}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
