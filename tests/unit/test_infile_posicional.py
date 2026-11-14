from __future__ import annotations

import pytest

from sgm.compile import compile_file, project_base
from sgm.formatos.informat_archivo import leer_campo
from sgm.frontend.datastep_io import input_fields
from sgm.frontend.program import analyze_program
from sgm.ir.models import Column
from sgm.migrar.esquemas import esquemas_de_entrada
from sgm.migrar.interprete_errores import NoSoportadoEnInterprete
from sgm.migrar.interprete_posicional import leer_columnas
from sgm.talend_item.desde_plan import plan_a_jobs
from sgm.talend_item.desde_plan_nodos import nodo_lectura


def _plan(text: str):
    analysis = analyze_program({"p.sas": text})
    return compile_file(analysis, "p.sas", project_base()).plan


def _op(plan):
    return next(op for op in plan.graph.operators() if op.kind == "read_file")


def _parametros(nodo) -> dict[str, str | None]:
    return {
        parametro[1]: parametro[2]
        for parametro in nodo.parametros
        if isinstance(parametro, tuple)
    }


def test_input_posicional_conserva_inicio_ancho_tipo_e_informat():
    parsed = input_fields("input @1 cuenta $5. @6 sucursal 3. @9 monto 8.2;")

    assert parsed["mode"] == "column"
    assert parsed["names"] == ["cuenta", "sucursal", "monto"]
    assert parsed["fields"] == [
        {"name": "cuenta", "start": 1, "width": 5, "informat": "$5."},
        {"name": "sucursal", "start": 6, "width": 3, "informat": "3."},
        {"name": "monto", "start": 9, "width": 8, "informat": "8.2"},
    ]


def test_input_posicional_por_rangos_conserva_columnas_inclusivas():
    parsed = input_fields("input codigo $ 1-5 zona 6-8 importe 9-16;")

    assert parsed["mode"] == "column"
    assert parsed["fields"] == [
        {"name": "codigo", "start": 1, "width": 5, "informat": "$5."},
        {"name": "zona", "start": 6, "width": 3, "informat": "3."},
        {"name": "importe", "start": 9, "width": 8, "informat": "8."},
    ]


def test_input_posicional_con_control_no_soportado_no_se_degrada_a_esquema_vacio():
    parsed = input_fields("input @1 codigo $5. +2 monto 8.2;")

    assert parsed["mode"] == "unknown"


@pytest.mark.parametrize(
    ("texto", "informat", "esperado"),
    [
        ("  1234.5", "8.2", "1234.5"),
        ("     750", "8.2", "7.5"),
        ("010", "3.", "10"),
        ("   ", "8.2", None),
    ],
)
def test_informat_archivo_convierte_decimal_explicito_omitido_y_faltante(texto, informat, esperado):
    assert leer_campo(texto, informat) == esperado


def test_informat_no_integrado_no_se_convierte_por_su_nombre():
    with pytest.raises(NoSoportadoEnInterprete) as error:
        leer_campo("   123,45", "comma8.2")

    assert error.value.detalle == "P-INFORMAT-SIN-SOPORTE"


def test_truncover_conserva_fila_corta_y_no_activa_flowover():
    campos = [("monto", 9, 8, "8.2")]

    assert leer_columnas(["C0003003"], campos, truncover=True) == [{"monto": None}]
    with pytest.raises(NoSoportadoEnInterprete) as error:
        leer_columnas(["C0003003"], campos, truncover=False)
    assert error.value.detalle == "P-INFILE-FLOWOVER"


def test_input_posicional_baja_posiciones_y_tipos_demostrados_a_la_ir():
    plan = _plan(
        "data work.mov;\n"
        "infile '/datos/mov.txt' truncover;\n"
        "input @1 cuenta $5. @6 sucursal 3. @9 monto 8.2;\n"
        "run;"
    )
    op = _op(plan)

    assert op.params["input_positions"] == [
        {"name": "cuenta", "start": 1, "width": 5, "informat": "$5."},
        {"name": "sucursal", "start": 6, "width": 3, "informat": "3."},
        {"name": "monto", "start": 9, "width": 8, "informat": "8.2"},
    ]
    schemas, pending = esquemas_de_entrada(plan, {}, None)
    assert [(column.name, column.type, column.length) for column in schemas["work.mov"]] == [
        ("cuenta", "String", 5),
        ("sucursal", "Double", None),
        ("monto", "BigDecimal", None),
    ]
    assert not any(item.codigo == "P-TIPO-DESCONOCIDO" for item in pending)


def test_component_posicional_permanece_pendiente_sin_plantilla_real():
    plan = _plan(
        "data work.mov;\n"
        "infile '/datos/mov.txt' truncover;\n"
        "input @1 cuenta $5. @6 sucursal 3. @9 monto 8.2;\n"
        "run;"
    )
    result = nodo_lectura(
        _op(plan),
        [Column("cuenta", "String", 5), Column("sucursal", "Double"), Column("monto", "BigDecimal")],
        "tFileInputPositional_1",
        0,
        0,
    )

    assert result.nodo is None
    assert [pending.codigo for pending in result.pendientes] == ["P-COMPONENTE-SIN-PLANTILLA"]


def test_salida_work_no_duplica_pendiente_del_lector_posicional():
    plan = _plan(
        "data work.mov;\n"
        "infile '/datos/mov.txt' truncover;\n"
        "input @1 cuenta $5. @6 sucursal 3. @9 monto 8.2;\n"
        "run;"
    )
    schemas, _ = esquemas_de_entrada(plan, {}, None)

    migrated = plan_a_jobs(plan, schemas)

    assert migrated.jobs == []
    assert [pending.codigo for pending in migrated.pendientes] == ["P-COMPONENTE-SIN-PLANTILLA"]
