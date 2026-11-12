"""Propone el bloque `esquemas` de un caso desde el migrador (B-4, MG-P1-02).

Imprime el bloque para que una persona lo revise. No escribe `caso.yaml`: cada tipo se contrasta con
el SAS y con `entradas/*.csv` antes de pegarlo. Lo que no tiene prueba sale como `pendiente` con su
motivo; nunca como `String` por omisión.

Uso: uv run python tools/proponer_esquemas_caso.py <carpeta-del-caso>
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any

import yaml

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "tools"))

from corpus_lib import esquemas_caso  # noqa: E402

from sgm.compile import compile_file, project_base  # noqa: E402
from sgm.frontend.program import analyze_program  # noqa: E402
from sgm.ir.models import Plan  # noqa: E402
from sgm.migrar.esquemas_propagacion import CARACTER, NUMERICO, TipoColumna, propagar_tipos  # noqa: E402
from sgm.migrar.tipos_import import filas_del_archivo, tipos_de_archivo  # noqa: E402

MOTIVO_SIN_TIPO = "sin tipo demostrado en el programa ni en la muestra de entradas"


def _plan(programa: Path) -> Plan:
    texto = programa.read_text(encoding="utf-8")
    analisis = analyze_program({"programa.sas": texto})
    return compile_file(analisis, "programa.sas", project_base()).plan


def _linea_de_declaracion(nombre: str, lineas: list[str], hasta: int) -> int | None:
    """Línea (1-based) de la última declaración `LENGTH` o `FORMAT` de `nombre` antes de `hasta`."""
    patron = re.compile(r'\b' + re.escape(nombre) + r'\b', re.IGNORECASE)
    for indice in range(min(hasta, len(lineas)) - 1, -1, -1):
        texto = lineas[indice]
        if ("LENGTH" in texto.upper() or "FORMAT" in texto.upper()) and patron.search(texto):
            return indice + 1
    return None


def _entrada_de(columna: TipoColumna, lineas: list[str]) -> dict[str, Any]:
    """Solo `LENGTH` o `FORMAT` demuestran un tipo en este contrato (no la aritmética ni un
    informato de `INPUT`)."""
    declarado = columna.fuente == "declarado"
    util = columna.tipo in (NUMERICO, CARACTER)
    if not columna.linea or not declarado or not util:
        return {"tipo": "pendiente", "motivo": MOTIVO_SIN_TIPO}
    linea = _linea_de_declaracion(columna.nombre, lineas, columna.linea)
    if linea is None:
        return {"tipo": "pendiente", "motivo": MOTIVO_SIN_TIPO}
    if columna.tipo == CARACTER:
        entrada: dict[str, Any] = {"tipo": "String", "linea": linea}
        if columna.largo:
            entrada["longitud"] = columna.largo
        return entrada
    return {"tipo": "Double", "linea": linea}


def _lecturas(caso: Path, plan: Plan, bloque: dict[str, dict[str, Any]]) -> set[str]:
    """Tablas de los `read_file`: tipo por la muestra de `entradas/`; el resto, pendiente."""
    leidas: set[str] = set()
    for op in plan.graph.operators():
        if op.kind != "read_file":
            continue
        salidas = op.params.get("outputs") or []
        if not salidas:
            continue
        tabla = str(salidas[0]).upper()
        leidas.add(tabla.lower())
        nombre = Path(str(op.params.get("datafile") or "").strip("'\"").replace("\\", "/")).name
        ruta = caso / "entradas" / nombre
        getnames = op.params.get("getnames") is not False
        delimiter = op.params.get("delimiter")
        cabecera = filas_del_archivo(ruta, delimiter, getnames)[0] if ruta.is_file() else []
        demostrados = (
            tipos_de_archivo(ruta, delimiter, cabecera, getnames=getnames) if cabecera else {}
        )
        linea = op.evidence[0].line_start if op.evidence else None
        columnas: dict[str, Any] = {}
        for nombre_col in cabecera:
            tipo = demostrados.get(nombre_col)
            if tipo is not None and linea:
                cadena = tipo.tipo_sas == "caracter"
                tipo_salida = "String" if cadena else "Double"
                columnas[nombre_col] = {"tipo": tipo_salida, "linea": linea, "fuente": "muestra"}
            else:
                columnas[nombre_col] = {"tipo": "pendiente", "motivo": MOTIVO_SIN_TIPO}
        if columnas:
            bloque[tabla] = columnas
    return leidas


def bloque_del_caso(caso: Path) -> dict[str, dict[str, Any]]:
    plan = _plan(caso / "programa.sas")
    lineas = (caso / "programa.sas").read_text(encoding="utf-8").splitlines()
    bloque: dict[str, dict[str, Any]] = {}
    leidas = _lecturas(caso, plan, bloque)
    resultado = propagar_tipos(plan)
    for conjunto, columnas in resultado.tablas.items():
        if conjunto in leidas or not columnas:
            continue
        bloque[conjunto.upper()] = {
            nombre: _entrada_de(col, lineas) for nombre, col in columnas.items()
        }
    return bloque


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print("uso: proponer_esquemas_caso.py <carpeta-del-caso>", file=sys.stderr)
        return 2
    bloque = bloque_del_caso(Path(argv[0]))
    if not bloque:
        print("el programa no declara tablas con columnas", file=sys.stderr)
        return 1
    esquemas_caso.validar(bloque)
    print(yaml.safe_dump({"esquemas": bloque}, allow_unicode=True, sort_keys=False))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
