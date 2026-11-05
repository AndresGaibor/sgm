"""Conformidad del migrador contra el diseño manual.

Cada sección y cada fila de `diseno_manual.yaml` se compara con la salida de
`obtener_diseno(client_large.sas)`. Las secciones que el emisor ya produce (`SECCIONES_EMITIDAS`)
se evalúan de verdad; las demás son `xfail` estricto: cuando una pase, el informe la marca como
error hasta que se libere. No se borran ni se debilitan: se van liberando.

`DIFERENCIAS_CONOCIDAS` lista las filas emitidas donde el migrador discrepa del manual, con el
motivo. Son `xfail` estricto con ese motivo: si la diferencia desaparece, la prueba avisa.
"""

from __future__ import annotations

from functools import lru_cache

import pytest

from sgm.conformidad.estado import DIFERENCIAS_CONOCIDAS
from sgm.conformidad.referencia import Fila
from tests.conformidad.cargador import RAIZ, cargar_secciones, todas_las_filas
from tests.conformidad.interfaz import SECCIONES_EMITIDAS, diferencias_fila, obtener_diseno

PROGRAMA = RAIZ / "tests" / "fixtures" / "sas" / "client" / "client_large.sas"
SECCIONES = cargar_secciones()



def _marca_seccion(codigo: str):
    if codigo in SECCIONES_EMITIDAS:
        return []
    return [
        pytest.mark.xfail(strict=True, reason="el emisor de esta sección del diseño aún no existe")
    ]


def _param_seccion(codigo: str):
    return pytest.param(codigo, id=codigo, marks=_marca_seccion(codigo))


def _param_fila(fila: Fila):
    marcas = _marca_seccion(fila.seccion)
    if fila.id in DIFERENCIAS_CONOCIDAS:
        marcas = [pytest.mark.xfail(strict=True, reason=DIFERENCIAS_CONOCIDAS[fila.id])]
    return pytest.param(fila, id=f"{fila.seccion}:{fila.id}", marks=marcas)


@lru_cache(maxsize=1)
def _diseno():
    return obtener_diseno(PROGRAMA)


@pytest.mark.parametrize("codigo", [_param_seccion(c) for c in SECCIONES])
def test_seccion_presente_con_todas_sus_claves(codigo: str) -> None:
    obtenida = _diseno().get(codigo, {})
    faltan = [f.clave for f in SECCIONES[codigo].filas if f.clave not in obtenida]
    assert faltan == []


@pytest.mark.parametrize("fila", [_param_fila(f) for f in todas_las_filas(SECCIONES)])
def test_fila_conforme_con_el_diseno(fila: Fila) -> None:
    obtenida = _diseno().get(fila.seccion, {}).get(fila.clave)
    assert diferencias_fila(fila, obtenida) == []
