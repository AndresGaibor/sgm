"""Conformidad del migrador contra el diseño manual: empieza en rojo (xfail estricto).

Cada sección y cada fila de `diseno_manual.yaml` se compara con la salida de
`obtener_diseno(client_large.sas)`. Mientras el emisor de las 8 secciones no exista, todas
fallan con `NotImplementedError`; `strict=True` hace que, cuando una pase, el informe la marque
como error hasta que se quite el `xfail`. No se borran ni se debilitan: se van liberando.
"""

from __future__ import annotations

from functools import lru_cache

import pytest

from tests.conformidad.cargador import RAIZ, Fila, cargar_secciones, todas_las_filas
from tests.conformidad.interfaz import diferencias_fila, obtener_diseno

PROGRAMA = RAIZ / "tests" / "fixtures" / "sas" / "client" / "client_large.sas"
SECCIONES = cargar_secciones()

pendiente_emisor = pytest.mark.xfail(
    strict=True,
    raises=NotImplementedError,
    reason="Fase 0: el emisor de las 8 secciones del diseño aún no existe",
)


@lru_cache(maxsize=1)
def _diseno():
    return obtener_diseno(PROGRAMA)


@pendiente_emisor
@pytest.mark.parametrize("codigo", list(SECCIONES), ids=list(SECCIONES))
def test_seccion_presente_con_todas_sus_claves(codigo: str) -> None:
    obtenida = _diseno().get(codigo, {})
    faltan = [f.clave for f in SECCIONES[codigo].filas if f.clave not in obtenida]
    assert faltan == []


@pendiente_emisor
@pytest.mark.parametrize(
    "fila",
    todas_las_filas(SECCIONES),
    ids=[f"{f.seccion}:{f.id}" for f in todas_las_filas(SECCIONES)],
)
def test_fila_conforme_con_el_diseno(fila: Fila) -> None:
    obtenida = _diseno().get(fila.seccion, {}).get(fila.clave)
    assert diferencias_fila(fila, obtenida) == []
