"""Una prueba por tipo de conexión que el emisor sabe escribir (MG-P9-05).

Cada prueba arma un Job mínimo, lo escribe con `render_item` y compara la conexión del XML con la
que guardó Studio. Hoy el único Job real de Studio en `tests/fixtures/talend/` es `hijo_0.1.item`, y
en él solo viaja una conexión de fila (FLOW). Por eso los demás tipos son `xfail` estricto: la
prueba falla en el paso de la referencia de Studio, con el motivo escrito en el decorador. Cuando se
apruebe y copie un Job real a `tests/fixtures/talend/`, la prueba compara de verdad y el `xfail` se
quita.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from sgm.talend_item.componentes import fixed_flow_input, log_row
from sgm.talend_item.conexiones import (
    al_terminar_componente,
    al_terminar_subjob,
    iterar,
    lookup,
    si,
)
from sgm.talend_item.item import render_item
from sgm.talend_item.modelo import Columna, Conexion, Job, Nodo

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "talend"
RUTA_JAVA = r"C:\Talend\8.0.1\studio\configuration\lib\java"
COLUMNAS = [Columna("id", "id_Integer"), Columna("ciudad", "id_String")]
FILAS = [["1", '"Bogota"']]


def _nodos(origen: str, destino: str) -> list[Nodo]:
    return [
        fixed_flow_input(origen, COLUMNAS, FILAS, 120, 120, RUTA_JAVA),
        log_row(destino, COLUMNAS, 320, 120, RUTA_JAVA),
    ]


def _escribir(
    conexion: Conexion, origen: str = "tFixedFlowInput_1", destino: str = "tLogRow_1"
) -> ET.Element:
    """Escribe el Job con una sola conexión y devuelve su elemento `<connection>`."""
    job = Job("MCP_Conexion_Tipos", nodos=_nodos(origen, destino), conexiones=[conexion])
    (elemento,) = ET.fromstring(render_item(job)).findall("connection")
    return elemento


def _parametros(elemento: ET.Element) -> list[ET.Element]:
    return elemento.findall("elementParameter")


def _conexion_de_studio(conector: str) -> ET.Element:
    """Primera conexión con ese `connectorName` en los Jobs guardados por Studio de tests/fixtures."""
    for ruta in sorted(FIXTURES.glob("*.item")):
        for elemento in ET.fromstring(ruta.read_text(encoding="utf-8")).findall("connection"):
            if elemento.get("connectorName") == conector:
                return elemento
    raise AssertionError(
        f"no hay en tests/fixtures ningún Job guardado por Studio con una conexión {conector}"
    )


def _comparar_con_studio(conector: str, elemento: ET.Element) -> None:
    """Connector, lineStyle, etiqueta y parámetros iguales a los del Job de Studio."""
    referencia = _conexion_de_studio(conector)
    for atributo in ("connectorName", "lineStyle", "label"):
        assert elemento.get(atributo) == referencia.get(atributo), atributo
    firmas = [(p.get("field"), p.get("name"), p.get("show")) for p in _parametros(elemento)]
    firmas_ref = [(p.get("field"), p.get("name"), p.get("show")) for p in _parametros(referencia)]
    assert firmas == firmas_ref
    # El valor de UNIQUE_NAME depende del ordinal de la conexión en el Job, no del tipo.
    valores = [(p.get("name"), p.get("value")) for p in _parametros(elemento) if p.get("name") != "UNIQUE_NAME"]
    valores_ref = [(p.get("name"), p.get("value")) for p in _parametros(referencia) if p.get("name") != "UNIQUE_NAME"]
    assert valores == valores_ref


def _motivo(conector: str, detalle: str) -> str:
    return f"sin Job de Studio con {conector} en tests/fixtures: {detalle}"


def test_fila_main_flow_coincide_con_el_job_real():
    """Main (fila): FLOW con lineStyle 0. Es el único tipo con Job real en tests/fixtures."""
    elemento = _escribir(
        Conexion("tFixedFlowInput_2", "tLogRow_2"),
        origen="tFixedFlowInput_2",
        destino="tLogRow_2",
    )
    _comparar_con_studio("FLOW", elemento)
    assert (elemento.get("source"), elemento.get("target")) == ("tFixedFlowInput_2", "tLogRow_2")


@pytest.mark.xfail(
    strict=True,
    raises=AssertionError,
    reason=_motivo(
        "SUBJOB_OK",
        "el lineStyle 1 viene de docs/guia-validacion-studio.md §4 y de un Job de talend-mcp "
        "fuera de este repo; falta copiar un fixture aprobado",
    ),
)
def test_on_subjob_ok_se_escribe_como_studio():
    elemento = _escribir(al_terminar_subjob("tFixedFlowInput_1", "tLogRow_1"))
    _comparar_con_studio("SUBJOB_OK", elemento)


@pytest.mark.xfail(
    strict=True,
    raises=AssertionError,
    reason=_motivo(
        "COMPONENT_OK",
        "el lineStyle 3 viene de un Job de talend-mcp fuera de este repo; falta copiar un fixture "
        "aprobado",
    ),
)
def test_on_component_ok_se_escribe_como_studio():
    elemento = _escribir(al_terminar_componente("tFixedFlowInput_1", "tLogRow_1"))
    _comparar_con_studio("COMPONENT_OK", elemento)


@pytest.mark.xfail(
    strict=True,
    raises=AssertionError,
    reason=_motivo(
        "RUN_IF",
        "el lineStyle 6 y el parámetro CONDITION vienen de un Job de talend-mcp fuera de este "
        "repo; falta copiar un fixture aprobado",
    ),
)
def test_run_if_se_escribe_como_studio():
    elemento = _escribir(si("tFixedFlowInput_1", "tLogRow_1", "true"))
    _comparar_con_studio("RUN_IF", elemento)


@pytest.mark.xfail(
    strict=True,
    raises=AssertionError,
    reason=(
        "no existe función en conexiones.py para OnSubjobError, y no hay Job de Studio con "
        "SUBJOB_ERROR en el repo: docs/guia-validacion-studio.md §4 lo deja pendiente (tarea R2-05). "
        "docs/studio-internals de talend-mcp dice lineStyle 4, pero ningún .item de su workspace lo "
        "contiene"
    ),
)
def test_on_subjob_error_tiene_referencia_de_studio():
    # Sin función ni lineStyle verificado no se construye la conexión: se empieza por la referencia.
    _conexion_de_studio("SUBJOB_ERROR")


@pytest.mark.xfail(
    strict=True,
    raises=AssertionError,
    reason=_motivo(
        "ITERATE",
        "el lineStyle 7 y los parámetros de iteración vienen de un Job de talend-mcp fuera de este "
        "repo; falta copiar un fixture aprobado",
    ),
)
def test_iterate_se_escribe_como_studio():
    elemento = _escribir(iterar("tFixedFlowInput_1", "tLogRow_1"))
    _comparar_con_studio("ITERATE", elemento)


@pytest.mark.xfail(
    strict=True,
    raises=AssertionError,
    reason=_motivo(
        "LOOKUP",
        "el lineStyle 8 sale de bytecode, no de un Job; ningún Job disponible (repo ni talend-mcp) "
        "tiene una conexión LOOKUP",
    ),
)
def test_lookup_se_escribe_como_studio():
    elemento = _escribir(lookup("tFixedFlowInput_1", "tLogRow_1", "row2"))
    _comparar_con_studio("LOOKUP", elemento)


@pytest.mark.xfail(
    strict=True,
    raises=AssertionError,
    reason=_motivo(
        "REJECT",
        "tmap.py y jobs_producto.py la escriben con el lineStyle por defecto (0) sin ningún Job que "
        "lo confirme",
    ),
)
def test_reject_se_escribe_como_studio():
    elemento = _escribir(Conexion("tFixedFlowInput_1", "tLogRow_1", "rechazados", "REJECT"))
    _comparar_con_studio("REJECT", elemento)


@pytest.mark.xfail(
    strict=True,
    raises=AssertionError,
    reason=_motivo(
        "FILTER",
        "no hay emisor que la use (el filtro va por expressionFilter de tMap); talend-mcp tiene un "
        "FILTER de tFilterRow con lineStyle 0 pero con metaname=FILTER, y el emisor pone el origen",
    ),
)
def test_filter_se_escribe_como_studio():
    elemento = _escribir(Conexion("tFixedFlowInput_1", "tLogRow_1", "row1", "FILTER"))
    _comparar_con_studio("FILTER", elemento)


@pytest.mark.xfail(
    strict=True,
    raises=AssertionError,
    reason=(
        "ORDER no es un tipo de conexión: no está en rules/talend/components.json ni en Studio. El "
        "ORDER que existe es un parámetro de tSortRow (asc/desc). Falta aclarar qué se quiso probar "
        "y un Job de Studio que muestre cómo se fija el orden de ejecución de los subjobs"
    ),
)
def test_el_orden_de_ejecucion_con_order():
    raise AssertionError("ORDER no tiene forma de escribirse ni referencia de Studio")
