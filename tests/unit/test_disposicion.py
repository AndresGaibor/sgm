"""Disposición de nodos en el lienzo: columnas por profundidad, filas por orden, sin superposición.

Las pruebas construyen Jobs pequeños a mano, con nodos en (0, 0), para que lo que se mire sea solo
la disposición y no el emisor. La última prueba del validador comprueba que la superposición se
reporta con el mensaje en castellano y que un Job ya dispuesto no recibe ningún aviso.
"""

from __future__ import annotations

from dataclasses import replace

from sgm.talend_item.disposicion import disponer
from sgm.talend_item.modelo import Conexion, Job, Nodo
from sgm.talend_item.validador import validar_job


def _nodo(unico: str) -> Nodo:
    return Nodo(componente="tLogRow", version="0.102", unico=unico)


def _conexion(origen: str, destino: str) -> Conexion:
    return Conexion(origen, destino)


def _posiciones(job: Job) -> dict[str, tuple[int, int]]:
    return {nodo.unico: (nodo.x, nodo.y) for nodo in job.nodos}


def test_cadena_lineal_una_columna_por_paso():
    job = Job(
        "cadena",
        nodos=[_nodo("A"), _nodo("B"), _nodo("C")],
        conexiones=[_conexion("A", "B"), _conexion("B", "C")],
    )

    dispuesto = disponer(job)

    assert _posiciones(dispuesto) == {"A": (0, 0), "B": (200, 0), "C": (400, 0)}


def test_bifurcacion_y_union_en_columnas_correctas():
    # A se bifurca en B y C; D recibe de B y C. D cae en la columna 2 (camino más largo).
    job = Job(
        "rombo",
        nodos=[_nodo("A"), _nodo("B"), _nodo("C"), _nodo("D")],
        conexiones=[
            _conexion("A", "B"),
            _conexion("A", "C"),
            _conexion("B", "D"),
            _conexion("C", "D"),
        ],
    )

    dispuesto = disponer(job)

    assert _posiciones(dispuesto) == {
        "A": (0, 0),
        "B": (200, 0),
        "C": (200, 96),
        "D": (400, 0),
    }


def test_union_toma_el_camino_mas_largo():
    # A -> B -> C -> D y además A -> D: D debe quedar después de C, no junto a A.
    job = Job(
        "largo",
        nodos=[_nodo("A"), _nodo("B"), _nodo("C"), _nodo("D")],
        conexiones=[
            _conexion("A", "B"),
            _conexion("B", "C"),
            _conexion("C", "D"),
            _conexion("A", "D"),
        ],
    )

    dispuesto = disponer(job)

    assert _posiciones(dispuesto)["D"] == (600, 0)


def test_ciclo_no_cuelga_y_todos_quedan_distintos():
    job = Job(
        "ciclo",
        nodos=[_nodo("A"), _nodo("B"), _nodo("C")],
        conexiones=[_conexion("A", "B"), _conexion("B", "C"), _conexion("C", "A")],
    )

    dispuesto = disponer(job)

    posiciones = _posiciones(dispuesto)
    assert len(set(posiciones.values())) == 3
    assert posiciones["A"] == (0, 0)


def test_nodo_aislado_queda_en_la_primera_columna():
    job = Job(
        "aislado",
        nodos=[_nodo("A"), _nodo("B"), _nodo("Z")],
        conexiones=[_conexion("A", "B")],
    )

    dispuesto = disponer(job)

    assert _posiciones(dispuesto)["Z"] == (0, 96)


def test_filas_siguen_el_orden_de_aparicion_en_job_nodos():
    # B y C están en la misma columna; B aparece antes en job.nodos, así que ocupa la fila 0.
    job = Job(
        "filas",
        nodos=[_nodo("A"), _nodo("B"), _nodo("C")],
        conexiones=[_conexion("A", "B"), _conexion("A", "C")],
    )

    dispuesto = disponer(job)

    assert _posiciones(dispuesto)["B"] == (200, 0)
    assert _posiciones(dispuesto)["C"] == (200, 96)


def test_determinismo_dos_corridas_iguales():
    job = Job(
        "det",
        nodos=[_nodo("A"), _nodo("B"), _nodo("C"), _nodo("D")],
        conexiones=[
            _conexion("A", "C"),
            _conexion("B", "C"),
            _conexion("C", "D"),
            _conexion("D", "A"),
        ],
    )

    assert disponer(job) == disponer(job)


def test_no_muta_el_job_de_entrada():
    original = Job(
        "inmutable",
        nodos=[_nodo("A"), _nodo("B")],
        conexiones=[_conexion("A", "B")],
    )
    antes = [replace(nodo) for nodo in original.nodos]

    dispuesto = disponer(original)

    assert dispuesto is not original
    assert [(n.x, n.y) for n in original.nodos] == [(n.x, n.y) for n in antes]
    assert _posiciones(original) == {"A": (0, 0), "B": (0, 0)}
    assert _posiciones(dispuesto) == {"A": (0, 0), "B": (200, 0)}


def test_validador_reporta_dos_nodos_en_la_misma_posicion():
    job = Job("encimados", nodos=[_nodo("A"), _nodo("B")])

    problemas = validar_job(job)

    assert any("los nodos A y B están en la misma posición" in problema for problema in problemas)


def test_validador_no_reporta_nada_sobre_un_job_dispuesto():
    job = Job(
        "limpio",
        nodos=[_nodo("A"), _nodo("B"), _nodo("C")],
        conexiones=[_conexion("A", "B"), _conexion("A", "C")],
    )

    problemas = validar_job(disponer(job))

    assert not [problema for problema in problemas if "misma posición" in problema]
