"""Guardia de B-5: los lowering de DATA step y de PROC construyen sus operadores por los constructores.

Ningún `filter`, `select`, `rename`, `sort`, `dedup`, `read_file` ni `write_file` se añade con
`Builder.op` directamente, salvo las excepciones listadas con su motivo.
"""

from __future__ import annotations

import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
IR = RAIZ / "src" / "sgm" / "ir"
ARCHIVOS = ["lower_data.py", "lower_data_asignaciones.py", "lower_data_recorrido.py", "lower_procs.py"]
PROHIBIDOS = {"filter", "select", "rename", "sort", "dedup", "read_file", "write_file"}
# Excepciones contadas por archivo y tipo, con su motivo. Ningún otro caso se permite.
#   lower_data.py: read_file de INFILE/INPUT (sus parámetros `reason` y `multiple_io_statements` no
#     caben en `leer_archivo`); derive de "sin entradas" (el propio lowering lo crea vacío).
#   lower_data_asignaciones.py: derive condicional (`conditional`), sin constructor.
#   lower_data_recorrido.py: derive pendientes que reciben asignaciones después.
EXCEPCIONES = {
    "lower_data.py": {"read_file": 1, "derive": 1},
    "lower_data_asignaciones.py": {"derive": 1},
    "lower_data_recorrido.py": {"derive": 2},
}
_LLAMADA = re.compile(r"\.op\(\s*\"([a-z_]+)\"")


def _kinds(ruta: Path) -> list[str]:
    return _LLAMADA.findall(ruta.read_text(encoding="utf-8"))


def test_los_operadores_directos_son_solo_las_excepciones_listadas() -> None:
    for nombre in ARCHIVOS:
        kinds = _kinds(IR / nombre)
        for kind in PROHIBIDOS | {"derive"}:
            n = kinds.count(kind)
            permitido = EXCEPCIONES.get(nombre, {}).get(kind, 0)
            assert n == permitido, f"{nombre}: {n} {kind} con Builder.op (permitidos: {permitido})"
