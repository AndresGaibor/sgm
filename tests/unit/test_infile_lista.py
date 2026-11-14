from __future__ import annotations

import pytest

from sgm.compile import compile_file, project_base
from sgm.frontend.datastep_io import input_fields
from sgm.frontend.program import analyze_program
from sgm.ir.models import Column
from sgm.migrar.esquemas import esquemas_de_entrada
from sgm.migrar.interprete_errores import NoSoportadoEnInterprete
from sgm.migrar.interprete_infile import leer_lista
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


def test_colon_informat_es_lista_y_preserva_tipo_y_longitud():
    parsed = input_fields("input id nombre :$12. saldo;")

    assert parsed["mode"] == "list"
    assert parsed["names"] == ["id", "nombre", "saldo"]
    assert parsed["types"] == {"id": "numerico", "nombre": "caracter", "saldo": "numerico"}
    assert parsed["lengths"] == {"nombre": 12}
    assert parsed["informats"] == {"nombre": "$12."}


def test_informat_no_reconocido_y_lista_de_variables_no_se_confunden_con_lista_simple():
    assert input_fields("input valor : formato_no_catalogado.")["mode"] == "unknown"
    assert input_fields("input valor1-valor4")["mode"] == "unknown"


def test_dsd_lee_delimitador_entre_comillas_y_missover_no_toma_la_siguiente_linea():
    rows = leer_lista(
        ['id;nombre;saldo', '1;"Perez; Ana";100.5', '2;Luis;;', '4;Mara'],
        [("id", None), ("nombre", "$12."), ("saldo", None)],
        ";",
        dsd=True,
        missover=True,
        firstobs=2,
    )

    assert rows == [
        {"id": "1", "nombre": "Perez; Ana", "saldo": "100.5"},
        {"id": "2", "nombre": "Luis", "saldo": None},
        {"id": "4", "nombre": "Mara", "saldo": None},
    ]


def test_dsd_distingue_separadores_vacios_y_sin_dsd_los_colapsa():
    variables = [("a", None), ("b", None), ("c", None)]

    assert leer_lista(["a;;c"], variables, ";", dsd=True, missover=True) == [
        {"a": "a", "b": None, "c": "c"}
    ]
    assert leer_lista(["a;;c"], variables, ";", dsd=False, missover=True) == [
        {"a": "a", "b": "c", "c": None}
    ]


def test_flowover_implicito_se_deja_como_pendiente_del_interprete():
    with pytest.raises(NoSoportadoEnInterprete) as error:
        leer_lista(["4;Mara"], [("id", None), ("nombre", None), ("saldo", None)], ";", False, False)

    assert error.value.detalle == "P-INFILE-FLOWOVER"


def test_emisor_configura_cabecera_dsd_y_esquema_para_infile():
    plan = _plan(
        "data work.clientes;\n"
        "infile '/datos/clientes.txt' dlm=';' dsd missover firstobs=2;\n"
        "input id nombre :$12. saldo;\n"
        "run;"
    )
    result = nodo_lectura(
        _op(plan),
        [Column("id", "Double"), Column("nombre", "String", 12), Column("saldo", "Double")],
        "tFileInputDelimited_1",
        0,
        0,
    )

    assert result.pendientes == []
    assert result.nodo is not None
    params = _parametros(result.nodo)
    assert params["HEADER"] == "1"
    assert params["FIELDSEPARATOR"] == '";"'
    assert params["CSV_OPTION"] == "true"
    assert params["TEXT_ENCLOSURE"] == '"""'
    assert result.columnas[1].longitud == 12


def test_emisor_deja_csv_desactivado_sin_dsd():
    plan = _plan(
        "data work.entrada;\n"
        "infile '/datos/entrada.txt' dlm=';' missover;\n"
        "input id valor;\n"
        "run;"
    )
    result = nodo_lectura(
        _op(plan),
        [Column("id", "Double"), Column("valor", "Double")],
        "tFileInputDelimited_1",
        0,
        0,
    )

    assert result.nodo is not None
    assert _parametros(result.nodo)["CSV_OPTION"] == "false"


def test_migracion_completa_emite_infile_y_no_deja_pendientes_genericos():
    plan = _plan(
        "data work.clientes;\n"
        "infile '/datos/clientes.txt' dlm=';' dsd missover firstobs=2;\n"
        "input id nombre :$12. saldo;\n"
        "run;"
    )
    schemas, _ = esquemas_de_entrada(plan, {}, None)

    migrated = plan_a_jobs(plan, schemas)

    assert len(migrated.jobs) == 1
    assert any(node.componente == "tFileInputDelimited" for node in migrated.jobs[0].nodos)
    assert not {
        "P-INFILE-SIN-EQUIVALENCIA",
        "P-FORMATO-SIN-SOPORTE",
        "P-TIPO-DESCONOCIDO",
    } & {pending.codigo for pending in migrated.pendientes}


@pytest.mark.parametrize(
    ("option", "code"),
    [
        ("", "P-INFILE-FLOWOVER"),
        ("flowover", "P-INFILE-FLOWOVER"),
        ("truncover", "P-INFILE-TRUNCOVER-LISTA"),
        ("missover flowover", "P-INFILE-OPCIONES-CONFLICTO"),
    ],
)
def test_no_emite_lectores_con_fin_de_registro_no_demostrado(option, code):
    plan = _plan(
        "data work.entrada;\n"
        f"infile '/datos/entrada.txt' dlm=';' {option};\n"
        "input id valor;\n"
        "run;"
    )
    result = nodo_lectura(
        _op(plan),
        [Column("id", "Double"), Column("valor", "Double")],
        "tFileInputDelimited_1",
        0,
        0,
    )

    assert result.nodo is None
    assert [pending.codigo for pending in result.pendientes] == [code]

    schemas, _ = esquemas_de_entrada(plan, {}, None)
    migrated = plan_a_jobs(plan, schemas)

    assert migrated.jobs == []
    assert code in {pending.codigo for pending in migrated.pendientes}


def test_input_list_declara_tipos_sas_sin_pendiente_desconocido():
    plan = _plan(
        "data work.clientes;\n"
        "infile '/datos/clientes.txt' dlm=';' dsd missover firstobs=2;\n"
        "input id nombre :$12. saldo;\n"
        "run;"
    )
    op = _op(plan)

    assert op.params["input_mode"] == "list"
    assert op.params["input_types"] == {"id": "numerico", "nombre": "caracter", "saldo": "numerico"}
    assert op.params["input_lengths"] == {"nombre": 12}
    assert op.params["input_informats"] == {"nombre": "$12."}

    schemas, pending = esquemas_de_entrada(plan, {}, None)

    assert [(column.name, column.type, column.length) for column in schemas["work.clientes"]] == [
        ("id", "Double", None),
        ("nombre", "String", 12),
        ("saldo", "Double", None),
    ]
    assert not any(item.codigo == "P-TIPO-DESCONOCIDO" for item in pending)


def test_dsd_usa_coma_si_sas_no_declara_otro_delimitador():
    plan = _plan(
        "data work.entrada;\n"
        "infile '/datos/entrada.csv' dsd missover;\n"
        "input id texto :$8.;\n"
        "run;"
    )
    op = _op(plan)

    assert op.params["delimiter"] == ","
    result = nodo_lectura(
        op,
        [Column("id", "Double"), Column("texto", "String", 8)],
        "tFileInputDelimited_1",
        0,
        0,
    )

    assert result.nodo is not None
    assert _parametros(result.nodo)["FIELDSEPARATOR"] == '","'
