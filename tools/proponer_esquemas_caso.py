"""Propone el bloque `esquemas` de un caso desde el migrador (B-4, MG-P1-02).

Imprime el bloque para que una persona lo revise. No escribe `caso.yaml`: cada tipo se contrasta con
el SAS y con `entradas/*.csv` antes de pegarlo. Lo que no tiene prueba sale como `pendiente` con su
motivo; nunca como `String` por omisión.

Uso: uv run python tools/proponer_esquemas_caso.py <carpeta-del-caso>
"""

from __future__ import annotations

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
from sgm.migrar.tipos_import import tipos_de_archivo  # noqa: E402

MOTIVO_SIN_TIPO = "sin tipo demostrado en el programa ni en la muestra de entradas"


def _plan(programa: Path) -> Plan:
    texto = programa.read_text(encoding="utf-8")
    analisis = analyze_program({"programa.sas": texto})
    return compile_file(analisis, "programa.sas", project_base()).plan


def _entrada_de(columna: TipoColumna) -> dict[str, Any]:
    if columna.tipo == NUMERICO and columna.linea:
        return {"tipo": "Double", "linea": columna.linea}
    if columna.tipo == CARACTER and columna.linea:
        entrada: dict[str, Any] = {"tipo": "String", "linea": columna.linea}
        if columna.largo:
            entrada["longitud"] = columna.largo
        return entrada
    return {"tipo": "pendiente", "motivo": MOTIVO_SIN_TIPO}


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
        cabecera = []
        if ruta.is_file():
            primera = ruta.read_text(encoding="utf-8-sig", errors="replace").splitlines()[:1]
            linea_cabecera = primera[0] if primera else ""
            separador = op.params.get("delimiter") or (";" if ";" in linea_cabecera else ",")
            partes = linea_cabecera.split(separador)
            cabecera = [c.strip().strip("'\"") for c in partes if c.strip()]
        demostrados = (
            tipos_de_archivo(ruta, op.params.get("delimiter"), cabecera) if cabecera else {}
        )
        linea = op.evidence[0].line_start if op.evidence else None
        columnas: dict[str, Any] = {}
        for nombre_col in cabecera:
            tipo = demostrados.get(nombre_col)
            if tipo is not None and linea:
                cadena = tipo.tipo_sas == "caracter"
                tipo_salida = "String" if cadena else "Double"
                columnas[nombre_col] = {"tipo": tipo_salida, "linea": linea}
            else:
                columnas[nombre_col] = {"tipo": "pendiente", "motivo": MOTIVO_SIN_TIPO}
        if columnas:
            bloque[tabla] = columnas
    return leidas


def bloque_del_caso(caso: Path) -> dict[str, dict[str, Any]]:
    plan = _plan(caso / "programa.sas")
    bloque: dict[str, dict[str, Any]] = {}
    leidas = _lecturas(caso, plan, bloque)
    resultado = propagar_tipos(plan)
    for conjunto, columnas in resultado.tablas.items():
        if conjunto in leidas or not columnas:
            continue
        bloque[conjunto.upper()] = {nombre: _entrada_de(col) for nombre, col in columnas.items()}
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
