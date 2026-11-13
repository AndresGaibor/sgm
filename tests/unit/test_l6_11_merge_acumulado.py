"""l6_11 (B-11, paso 4): el MERGE por zona con la sentencia suma coincide con el esperado a mano.

El caso queda `pendiente` (la sentencia suma no tiene estado por fila en el traductor, B-13 y B-14), así que no
tiene `esperado/`. Esta prueba fija el resultado con la regla en la mano: `lrcon`, p. 598 (MERGE por grupo);
`lestmtsref`, p. 360 (la sentencia suma retiene el valor y cuenta el faltante como cero); `IF FIRST.ZONA THEN
ACUM=0` reinicia el acumulado por grupo.
"""

from __future__ import annotations

from pathlib import Path

from sgm.compile import compile_file, project_base
from sgm.frontend.program import analyze_program
from sgm.migrar.interprete import ejecutar_plan

CASO = Path("tests/corpus/L6/l6_11_merge_mas_acumulado")
ESPERADO = [("N", "Norte", "10", 10.0), ("N", "Norte", "15", 25.0), ("S", "Sur", "7", 7.0)]


def _csv(ruta: Path) -> list[dict]:
    lineas = ruta.read_text(encoding="utf-8").splitlines()
    cab = lineas[0].split(",")
    return [dict(zip(cab, linea.split(","), strict=True)) for linea in lineas[1:]]


def test_merge_con_suma_coincide_con_la_regla_a_mano():
    programa = (CASO / "programa.sas").read_text(encoding="utf-8")
    plan = compile_file(analyze_program({"p.sas": programa}), "p.sas", project_base()).plan
    salida = ejecutar_plan(
        plan,
        {"zonas": _csv(CASO / "entradas" / "ZONAS.csv"), "ventas": _csv(CASO / "entradas" / "VENTAS.csv")},
    )["ventas_zona"]
    filas = [{k.lower(): v for k, v in f.items()} for f in salida]
    assert [(f["zona"], f["nombre"], f["monto"], float(f["acum"])) for f in filas] == ESPERADO
    assert sum(float(f["acum"]) for f in filas) == 42
