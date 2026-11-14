"""Bajada conservadora de SUBSTR cuando aparece como pseudovariable."""

from sgm.frontend.datastep import DataStep, classify_statement
from sgm.ir.builder import Builder
from sgm.ir.lower_data import lower_data
from sgm.ir.lower_data_substr import reescribir_substr_izquierda
from sgm.ir.models import Evidence, Graph
from sgm.migrar.interprete import _proyectar


def test_pseudovariable_substr_se_clasifica_como_asignacion():
    sentencia = classify_statement("substr(a, 2, 3) = 'XY'", 7)
    assert sentencia.kind == "assign"
    assert sentencia.fields == {"target": "substr(a, 2, 3)", "expression": "'XY'"}


def test_reescribe_substr_con_longitud_explicita_y_relleno():
    assert reescribir_substr_izquierda("substr(a, 2, 3)", "'XY'") == (
        "a",
        "substrn(a,1,2-1) || substrn('XY' || repeat(' ',3),1,3) || substr(a,2+3)",
    )


def test_reescribe_substr_sin_longitud_usando_el_ancho_del_valor():
    assert reescribir_substr_izquierda("substr(a, 4)", "'Z'") == (
        "a",
        "substrn(a,1,4-1) || substrn('Z',1,lengthc('Z')) || substr(a,4+lengthc('Z'))",
    )


def test_asignacion_comun_no_se_interpreta_como_pseudovariable():
    assert reescribir_substr_izquierda("a", "1") is None


def test_pseudovariable_fuera_del_subconjunto_se_marca_como_hueco():
    sentencia = classify_statement("substr(a) = 'XY'", 2)
    paso = DataStep(
        outputs=["salida"],
        statements=[classify_statement("set entrada", 1), sentencia],
        line=1,
        end_line=2,
        text="data salida; set entrada; substr(a)='XY'; run;",
    )
    builder = Builder(Graph())

    lower_data(paso, Evidence("programa.sas", 1, 2, None), builder)

    derivacion = next(op for op in builder.created if op.kind == "derive")
    assert derivacion.status == "hueco"
    assert derivacion.notes == [
        "Pendiente: P-DATASTEP-SUBSTR-IZQ; la pseudovariable no se puede reescribir"
    ]


def test_lower_data_reemplaza_el_destino_pseudovariable_por_la_variable():
    sentencia = classify_statement("substr(a, 2, 3) = 'XY'", 2)
    paso = DataStep(
        outputs=["salida"],
        statements=[classify_statement("set entrada", 1), sentencia],
        line=1,
        end_line=2,
        text="data salida; set entrada; substr(a,2,3)='XY'; run;",
    )
    builder = Builder(Graph())

    lower_data(paso, Evidence("programa.sas", 1, 2, None), builder)

    derivacion = next(op for op in builder.created if op.kind == "derive")
    assert derivacion.params["assignments"] == [
        {
            "target": "a",
            "expression": "substrn(a,1,2-1) || substrn('XY' || repeat(' ',3),1,3) || substr(a,2+3)",
        }
    ]


def test_asignacion_data_step_actualiza_el_nombre_existente_sin_distinguir_mayusculas():
    assert _proyectar(
        [{"codigo": "ABCDEF"}],
        [{"target": "CODIGO", "expression": "'AXY EF'"}],
        aditivo=True,
    ) == [{"codigo": "AXY EF"}]
