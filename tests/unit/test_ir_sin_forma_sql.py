"""Guardia de B-6: el lowering de SQL construye sus operadores por los constructores.

`filter`, `derive`, `join`, `union` y `aggregate` no se añaden con `.op("...")` ni con `.step("...")`
literal, salvo las excepciones listadas con su motivo. Los parámetros de `join` salen de
`ir/operadores.py` y, si el constructor rechaza los datos, el contador de `ir/pasos.py` lo cuenta.
"""

from __future__ import annotations

import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
IR = RAIZ / "src" / "sgm" / "ir"
ARCHIVOS = [
    "lower_sql_flow.py",
    "lower_sql_agregados.py",
    "lower_sql_cruces.py",
    "lower_sql_texto.py",
]
PROHIBIDOS = {"filter", "derive", "join", "union", "aggregate", "select", "rename", "sort", "dedup"}
# Excepciones contadas por archivo y tipo, con su motivo. Ningún otro caso se permite.
#   lower_sql_flow.py: derive "sin entradas" (`SELECT` sin FROM, `calcular` exige asignaciones);
#     derive con lista vacía de columnas (`SELECT *` sobre un cruce); join de la rama de SELECT,
#     con los parámetros de `unir` y el enlace de las dos entradas.
#   lower_sql_cruces.py: join del cruce `IN` / `NOT IN`, con los parámetros de `unir`.
EXCEPCIONES = {
    "lower_sql_flow.py": {"derive": 2, "join": 1},
    "lower_sql_cruces.py": {"join": 1},
}
_LLAMADA = re.compile(r"\.(?:op|step)\(\s*\"([a-z_]+)\"")


def _kinds(ruta: Path) -> list[str]:
    return _LLAMADA.findall(ruta.read_text(encoding="utf-8"))


def test_los_operadores_sql_directos_son_solo_las_excepciones_listadas() -> None:
    for nombre in ARCHIVOS:
        kinds = _kinds(IR / nombre)
        for kind in PROHIBIDOS:
            n = kinds.count(kind)
            permitido = EXCEPCIONES.get(nombre, {}).get(kind, 0)
            assert n == permitido, f"{nombre}: {n} {kind} directos (permitidos: {permitido})"
