from __future__ import annotations

import csv
from pathlib import Path

import pytest

from sgm.compile import compile_file, project_base
from sgm.frontend.datastep import classify_statement
from sgm.frontend.datastep_io import file_fields, put_fields
from sgm.frontend.program import analyze_program
from sgm.ir.models import Evidence, Operator
from sgm.migrar.esquemas import esquemas_de_entrada
from sgm.migrar.interprete import ejecutar_plan
from sgm.migrar.interprete_errores import NoSoportadoEnInterprete
from sgm.migrar.interprete_file_put import escribir_archivos_plan, escribir_lista
from sgm.talend_item.desde_plan import plan_a_jobs
from sgm.talend_item.desde_plan_nodos import nodo_escritura
from sgm.talend_item.modelo import Columna


def _plan(text: str):
    analysis = analyze_program({"p.sas": text})
    return compile_file(analysis, "p.sas", project_base()).plan


def _parametros(nodo) -> dict[str, str | None]:
    return {
        parametro[1]: parametro[2]
        for parametro in nodo.parametros
        if isinstance(parametro, tuple)
    }


def test_file_y_put_lista_reconocen_delimitador_y_variables():
    file = file_fields("file '/salida/ventas.txt' dsd dlm='|'")
    put = put_fields("put id nombre monto")

    assert file == {
        "destino": "'/salida/ventas.txt'",
        "es_ruta": True,
        "fileref": None,
        "es_fileref": False,
        "opciones": {"dsd": True, "dlm": "|"},
        "no_reconocidas": [],
    }
    assert put == {"modo": "lista", "variables": ["id", "nombre", "monto"], "raw": "put id nombre monto"}


def test_file_y_put_no_inventan_soporte_para_rutas_o_formatos_dinamicos():
    file = file_fields("file salida dsd dlm=separador")
    first_character = file_fields("file 'C:/salida.txt' dsd dlm='||'")
    put = put_fields("put id comma10.2")

    assert file["es_ruta"] is False
    assert file["no_reconocidas"] == ["dlm"]
    assert first_character["opciones"]["dlm"] == "|"
    assert first_character["no_reconocidas"] == []
    assert put["modo"] == "formateado"


def test_clasificador_conserva_campos_file_y_put():
    assert classify_statement("file 'a.txt' dsd dlm='|'", 1).fields["opciones"]["dlm"] == "|"
    assert classify_statement("put id nombre", 2).fields["variables"] == ["id", "nombre"]


def test_escribir_lista_comilla_delimitadores_y_duplica_comillas():
    assert escribir_lista(
        [{"id": "2", "nombre": 'Lu|"is', "monto": "3"}],
        ["id", "nombre", "monto"],
        "|",
        True,
    ) == ['2|"Lu|""is"|3']


def test_escribir_lista_deja_formato_numerico_sin_equivalencia_como_pendiente():
    with pytest.raises(NoSoportadoEnInterprete) as error:
        escribir_lista([{"id": 2}], ["id"], "|", True)

    assert error.value.detalle == "P-PUT-NUMERIC-FORMAT"


def test_emisor_bloquea_formato_numerico_por_defecto_no_validado():
    operador = Operator(
        id="op00001",
        kind="write_file",
        params={
            "outfile": "'/salida.txt'",
            "dbms": "dlm",
            "file_format": "delimited",
            "delimiter": "|",
            "variables": ["id"],
            "dsd": True,
            "putnames": False,
        },
        signature="write_file",
        evidence=[Evidence("p.sas", 4, 4, None)],
    )
    resultado = nodo_escritura(operador, [Columna("id", "id_Double")], "out_1", 0, 0)

    assert resultado.nodo is None
    assert [pendiente.codigo for pendiente in resultado.pendientes] == [
        "P-PUT-NUMERIC-FORMAT"
    ]


def test_emisor_bloquea_proyeccion_que_romperia_el_esquema_del_flujo():
    operador = Operator(
        id="op00001",
        kind="write_file",
        params={
            "outfile": "'/salida.txt'",
            "dbms": "dlm",
            "file_format": "delimited",
            "delimiter": "|",
            "variables": ["id", "nombre", "monto"],
            "dsd": True,
            "putnames": False,
        },
        signature="write_file",
        evidence=[Evidence("p.sas", 4, 4, None)],
    )
    columnas = [
        Columna("id", "id_String"),
        Columna("nombre", "id_String"),
        Columna("monto", "id_String"),
        Columna("extra", "id_String"),
    ]

    resultado = nodo_escritura(operador, columnas, "out_1", 0, 0)

    assert resultado.nodo is None
    assert [pendiente.codigo for pendiente in resultado.pendientes] == [
        "P-FILE-PUT-PROJECTION-SIN-SOPORTE"
    ]


def test_escribir_lista_sin_dsd_no_supone_escape_de_delimitador():
    with pytest.raises(NoSoportadoEnInterprete) as error:
        escribir_lista([{"nombre": "Luis|Jr"}], ["nombre"], "|", False)

    assert error.value.detalle == "P-FILE-DSD-COMILLAS"


def test_escribir_lista_deja_faltantes_dsd_como_pendiente_documental():
    with pytest.raises(NoSoportadoEnInterprete) as error:
        escribir_lista(
            [{"id": "3", "nombre": "Mara", "monto": None}],
            ["id", "nombre", "monto"],
            "|",
            True,
        )

    assert error.value.detalle == "P-FILE-DSD-MISSING"


def test_data_null_file_put_baja_a_escritura_delimitada_sin_dataset_null():
    plan = _plan(
        "data _null_;\n"
        "set work.ventas;\n"
        "file '/salida/ventas.txt' dsd dlm='|';\n"
        "put id nombre monto;\n"
        "run;"
    )
    escritura = next(op for op in plan.graph.operators() if op.kind == "write_file")

    assert escritura.params["outfile"] == "'/salida/ventas.txt'"
    assert escritura.params["inputs"] == ["WORK.ventas"]
    assert escritura.params["delimiter"] == "|"
    assert escritura.params["dsd"] is True
    assert escritura.params["variables"] == ["id", "nombre", "monto"]
    assert "_NULL_" not in str(escritura.params)


def test_data_null_con_transformacion_no_ignora_la_asignacion():
    plan = _plan(
        "data _null_; set work.ventas; id = id + 1; "
        "file '/salida/ventas.txt' dsd dlm='|'; put id; run;"
    )

    assert not any(op.kind == "write_file" for op in plan.graph.operators())


def test_emisor_configura_salida_lista_dsd_sin_cabecera():
    case = Path(__file__).resolve().parents[1] / "corpus" / "L0" / "l0_24_file_put_lista_dsd"
    plan = _plan((case / "programa.sas").read_text(encoding="utf-8"))
    esquemas, pendientes = esquemas_de_entrada(plan, {}, case / "entradas")
    resultado = plan_a_jobs(plan, esquemas)
    nodo = next(
        nodo
        for job in resultado.jobs
        for nodo in job.nodos
        if nodo.componente == "tFileOutputDelimited"
    )
    parametros = _parametros(nodo)

    assert not pendientes
    assert [pendiente.codigo for pendiente in resultado.pendientes] == [
        "P-FILE-DSD-MISSING"
    ]
    assert parametros["FIELDSEPARATOR"] == '"|"'
    assert parametros["INCLUDEHEADER"] == "false"
    assert parametros["CSV_OPTION"] == "true"
    assert [columna.nombre for columna in nodo.metadatas[0].columnas] == [
        "id",
        "nombre",
        "monto",
    ]


def test_corpus_de_file_put_compara_el_archivo_delimitado():
    case = Path(__file__).resolve().parents[1] / "corpus" / "L0" / "l0_24_file_put_lista_dsd"
    with (case / "entradas" / "ventas.csv").open(encoding="utf-8", newline="") as archivo:
        filas = list(csv.DictReader(archivo))
    plan = _plan((case / "programa.sas").read_text(encoding="utf-8"))
    tablas = ejecutar_plan(plan, {"ventas": filas})
    archivos = escribir_archivos_plan(plan, tablas)

    assert list(archivos.values())[0] == (
        case / "esperado" / "ventas.txt"
    ).read_text(encoding="utf-8").splitlines()
