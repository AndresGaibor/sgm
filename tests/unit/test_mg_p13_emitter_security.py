"""Regresiones de seguridad del emisor con nombres y valores ficticios."""

from __future__ import annotations

import pytest

from sgm.compile import compile_project
from sgm.expressions.expressions import translate
from sgm.ir.models import Column, Operator
from sgm.talend_item.arquitectura import Arquitectura, PeriodoDecl
from sgm.talend_item.desde_plan import plan_a_jobs
from sgm.talend_item.desde_plan_expresiones import expresion, resolver_filas
from sgm.talend_item.desde_plan_map import Fuente, construir
from sgm.talend_item.desde_plan_nodos import nodo_lectura
from sgm.talend_item.desde_plan_nodos_escritura import nodo_escritura
from sgm.talend_item.jobs_conciliacion import job_conciliacion
from sgm.talend_item.jobs_diseno import java
from sgm.talend_item.jobs_producto import job_producto
from sgm.talend_item.jobs_totales import job_totales
from sgm.talend_item.modelo import Columna
from sgm.talend_item.normalizacion import literal_java
from sgm.talend_item.tmap import EntradaMap, SalidaMap, tmap

_PAYLOAD_JAVA = "x);System.exit(1);//"
def test_name_literal_con_codigo_java_queda_pendiente():
    java_generado, motivo = expresion(
        f"'{_PAYLOAD_JAVA}'n",
        {"row1": {"x"}},
        {"row1.x": "id_String"},
    )

    assert java_generado is None
    assert "name literal" in motivo.lower()
    assert "System.exit" not in motivo


def test_resolvedor_rechaza_codigo_java_fuera_de_un_literal():
    java_generado, motivo = resolver_filas(
        "input_row.x);System.exit(1);//",
        {"row1": {"x"}},
    )

    assert java_generado is None
    assert "expresión Java" in motivo


def test_resolvedor_rechaza_escape_unicode_que_java_convierte_en_separador():
    java_generado, motivo = resolver_filas(
        r"input_row.x\u003bSystem.exit(1)\u003b\u002f\u002f",
        {"row1": {"x"}},
    )

    assert java_generado is None
    assert "expresión Java" in motivo


def test_tmap_rechaza_identificadores_java_hostiles_en_sus_esquemas():
    with pytest.raises(ValueError, match="esquema"):
        tmap(
            "tMap_1",
            [EntradaMap("row1", [Columna("x;System.exit(1);//")])],
            [SalidaMap("out1", [Columna("x")], {"x": "row1.x"})],
        )


def test_tmap_rechaza_codigo_java_en_expresiones_publicas():
    with pytest.raises(ValueError, match="expresión Java"):
        tmap(
            "tMap_1",
            [EntradaMap("row1", [Columna("x")])],
            [SalidaMap("out1", [Columna("x")], {"x": "row1.x;System.exit(1);//"})],
        )


@pytest.mark.parametrize(
    "paso",
    [
        {"kind": "derive", "params": {"assignments": [{"target": "x;System.exit(1);//", "expression": "1"}]}},
        {"kind": "rename", "params": {"pairs": [["x", "x;System.exit(1);//"]]}},
    ],
)
def test_map_deja_pendiente_un_destino_de_columna_no_portable(paso):
    resultado = construir(
        Operator(id="mapa", kind="map", params={"steps": [paso]}),
        [Fuente("origen", "tabla", [Columna("x")])],
        "tMap_1",
        0,
        0,
    )

    assert resultado.nodo is None
    assert resultado.columnas == []
    assert any("portables" in pendiente.mensaje for pendiente in resultado.pendientes)


def test_map_deja_pendiente_un_esquema_de_entrada_no_portable():
    resultado = construir(
        Operator(
            id="mapa",
            kind="map",
            params={
                "steps": [
                    {
                        "kind": "derive",
                        "params": {"assignments": [{"target": "y", "expression": "1"}]},
                    }
                ]
            },
        ),
        [Fuente("origen", "tabla", [Columna("x;System.exit(1);//")])],
        "tMap_1",
        0,
        0,
    )

    assert resultado.nodo is None
    assert resultado.columnas == []
    assert any("portables" in pendiente.mensaje for pendiente in resultado.pendientes)


def test_pipeline_completo_no_emite_esquema_hostil_aun_con_fuente_del_catalogo():
    fuente = (
        "proc import datafile='entrada.csv' out=work.t dbms=csv; getnames=yes; run; "
        "data work.o; set work.t; y=1; run; "
        "proc export data=work.o outfile='salida.csv' dbms=csv; run;"
    )
    compiled, _ = compile_project({"caso.sas": fuente})
    plan = compiled["caso.sas"].plan
    resultado = plan_a_jobs(
        plan,
        {"work.t": [Column("x;System.exit(1);//", "String")]},
    )
    textos = [
        nodo.datos + repr(nodo.parametros)
        for job in resultado.jobs
        for nodo in job.nodos
    ]

    assert all("System.exit" not in texto for texto in textos)
    assert any("P-ESQUEMA-NO-PORTABLE" in pendiente.codigo for pendiente in resultado.pendientes)


def test_job_producto_rechaza_nombres_de_columna_hostiles():
    arq = Arquitectura("P", ("DEV",), "padre", "producto", "totales", "conc", "fin")

    with pytest.raises(ValueError, match="columna"):
        job_producto(arq, ("x;System.exit(1);//",))


def test_job_totales_escapa_el_prefijo_del_nombre_de_archivo():
    prefijo = 'x" + System.getProperty("os.name") + "'
    periodo = PeriodoDecl(
        "fecha", (("AÑO", "anio"), ("MES", "mes"), ("DIA", "dia"))
    )
    arq = Arquitectura(
        "P", ("DEV",), "padre", "producto", "totales", "conc", "fin",
        periodo=periodo, archivo_totales=prefijo,
    )
    job = job_totales(arq, ("CTE",))
    salida = next(n for n in job.nodos if n.unico == "tFileOutputDelimited_1")
    filename = next(p[2] for p in salida.parametros if isinstance(p, tuple) and p[1] == "FILENAME")

    assert filename == (
        f"context.ruta_resultados + {java(prefijo + '_')} + "
        "context.anio + context.mes + context.dia + " + java(".csv")
    )


def test_job_conciliacion_escapa_producto_en_nombre_de_archivo():
    producto = 'x" + System.getProperty("os.name") + "'
    periodo = PeriodoDecl(
        "fecha", (("AÑO", "anio"), ("MES", "mes"), ("DIA", "dia"))
    )
    arq = Arquitectura(
        "P", ("DEV",), "padre", "producto", "totales", "conc", "fin",
        periodo=periodo, archivo_totales="totales",
    )
    job = job_conciliacion(arq, (producto,))
    entrada = next(n for n in job.nodos if n.unico == "tFileInputDelimited_o1")
    filename = next(p[2] for p in entrada.parametros if isinstance(p, tuple) and p[1] == "FILENAME")

    assert filename == (
        f"context.ruta_resultados + {java('totales_origen_' + producto + '.csv')}"
    )


def test_job_totales_rechaza_producto_que_intenta_salir_de_la_carpeta():
    periodo = PeriodoDecl(
        "fecha", (("AÑO", "anio"), ("MES", "mes"), ("DIA", "dia"))
    )
    arq = Arquitectura(
        "P", ("DEV",), "padre", "producto", "totales", "conc", "fin",
        periodo=periodo, archivo_totales="totales",
    )

    with pytest.raises(ValueError, match="nombre de archivo"):
        job_totales(arq, ("../externo",))


def test_lectura_y_escritura_publicas_escapan_las_rutas_literales():
    ruta = 'x" + System.getProperty("os.name") + ".csv'
    lectura = nodo_lectura(
        Operator("read", "read_file", {"datafile": f"'{ruta}'", "dbms": "csv"}),
        [Column("x", "String")],
        "tFileInputDelimited_1",
        0,
        0,
    ).nodo
    escritura = nodo_escritura(
        Operator("write", "write_file", {"outfile": f"'{ruta}'", "dbms": "csv"}),
        [Columna("x")],
        "tFileOutputDelimited_1",
        0,
        0,
    ).nodo

    for nodo in (lectura, escritura):
        filename = next(p[2] for p in nodo.parametros if isinstance(p, tuple) and p[1] == "FILENAME")
        assert filename == java(ruta)


def test_resolvedor_permite_metodo_java_generado_despues_de_la_columna():
    resultado, motivo = resolver_filas("input_row.x.trim()", {"row1": {"x"}})

    assert motivo is None
    assert resultado == "row1.x.trim()"


def test_resolvedor_permite_backslash_unicode_doble_dentro_de_literal_java():
    expresion_java = r'"[\\u0009]"'
    resultado, motivo = resolver_filas(expresion_java, {})

    assert motivo is None
    assert resultado == expresion_java


def test_literal_java_del_emisor_escapa_controles():
    assert java("línea\r\tfin") == '"l\\u00ednea\\r\\tfin"'
    assert java("a\nb") == '"a\\nb"'
    assert literal_java("\b\f") == '"\\b\\f"'


def test_literal_java_de_expresion_escapa_saltos_de_linea():
    resultado = translate("'primera\r\nsegunda'").talend

    assert "\r" not in resultado and "\n" not in resultado
    assert "\\r\\n" in resultado


def test_resolvedor_conserva_separadores_dentro_de_literales():
    resultado, motivo = resolver_filas(
        '"input_row.x; // conservado" + input_row.x',
        {"row1": {"x"}},
    )

    assert motivo is None
    assert resultado == '"input_row.x; // conservado" + row1.x'


@pytest.mark.parametrize(
    "filas",
    [
        {"row1": {"x;System.exit(1)//"}},
        {"row1;System.exit(1)//": {"x"}},
    ],
)
def test_resolvedor_rechaza_identificadores_hostiles_en_el_esquema(filas):
    resultado, motivo = resolver_filas("input_row.x", filas)

    assert resultado is None
    assert "esquema de entrada" in motivo
