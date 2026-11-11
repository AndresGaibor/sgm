"""Intérprete del plan: uniones, filtros y proyecciones con la semántica de SAS.

El intérprete es el anillo B: prueba que el plan calcula lo que el SAS dice sin abrir Studio. Por eso
las pruebas no miran el código sino las filas que salen, y las que importan son las de los faltantes,
que es donde Python y SAS no coinciden.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from sgm.compile import compile_file, project_base
from sgm.frontend.program import analyze_program
from sgm.ir.models import Edge, Graph, Operator, Plan
from sgm.migrar.interprete import NoSoportadoEnInterprete, ejecutar_plan

CORPUS = Path(__file__).resolve().parents[1] / "corpus" / "L2"

# `saldo < 500` con `saldo` faltante es verdadero en SAS y lanza una excepción en Java. Es el mismo
# programa que usa la prueba del emisor para el filtro.
CON_SALDO = """PROC IMPORT DATAFILE='.../entradas/clientes.csv' OUT=WORK.CLIENTES DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

PROC SQL;
  CREATE TABLE WORK.morosos AS
  SELECT id_cliente, saldo FROM WORK.clientes
  WHERE saldo < 500;
QUIT;

PROC EXPORT DATA=WORK.morosos OUTFILE='.../salida/morosos.csv' DBMS=CSV REPLACE;
RUN;
"""


# Una subconsulta escalar como agregado: no es FUNCION(columna) y el intérprete no la adivina.
AGREGADO_COMPUESTO = (
    "PROC IMPORT DATAFILE='.../clientes.csv' OUT=WORK.CLIENTES DBMS=CSV REPLACE;"
    " GETNAMES=YES; RUN;"
    " PROC SQL; CREATE TABLE WORK.r AS"
    " SELECT (SELECT COUNT(*) FROM WORK.clientes) AS n FROM WORK.clientes; QUIT;"
)


def _plan(texto: str) -> Plan:
    return compile_file(analyze_program({"p.sas": texto}), "p.sas", project_base()).plan


def _caso(nombre: str) -> Plan:
    texto = (CORPUS / nombre / "programa.sas").read_text(encoding="utf-8")
    return _plan(texto)


def _ejecutar_in(condicion: str, entradas: dict[str, list[dict]]) -> list[dict]:
    plan = _plan(
        "PROC SQL; CREATE TABLE WORK.resultado AS SELECT c.id FROM WORK.clientes c "
        f"WHERE {condicion}; QUIT;"
    )
    return ejecutar_plan(plan, entradas)["resultado"]


def test_inner_join_descarta_sin_pareja():
    plan = _caso("l2_01_inner_join_clientes_ventas")
    entradas = {
        "clientes": [
            {"id_cliente": "1", "nombre": "Ana", "ciudad": "Norte"},
            {"id_cliente": "2", "nombre": "Beto", "ciudad": "Sur"},
        ],
        "ventas": [{"id_venta": "10", "id_cliente": "1", "monto": "500"}],
    }

    filas = ejecutar_plan(plan, entradas)["ventas_con_nombre"]

    assert filas == [{"id_venta": "10", "nombre": "Ana", "monto": "500"}]


def test_left_join_deja_faltantes():
    plan = _caso("l2_02_left_join_con_faltantes")
    entradas = {
        "clientes": [
            {"id_cliente": "1", "nombre": "Ana", "ciudad": "Norte"},
            {"id_cliente": "2", "nombre": "Beto", "ciudad": "Sur"},
        ],
        "ventas": [{"id_venta": "10", "id_cliente": "1", "monto": "500"}],
    }

    filas = ejecutar_plan(plan, entradas)["clientes_con_ventas"]

    assert len(filas) == 2
    sin_venta = next(fila for fila in filas if fila["nombre"] == "Beto")
    assert sin_venta["id_venta"] is None
    assert sin_venta["monto"] is None


def test_llave_con_blancos_finales_empareja():
    """En SAS `'AB'` y `'AB   '` son iguales: los blancos finales no cuentan al comparar."""
    plan = _caso("l2_01_inner_join_clientes_ventas")
    entradas = {
        "clientes": [{"id_cliente": "7 ", "nombre": "Ana", "ciudad": "Norte"}],
        "ventas": [{"id_venta": "10", "id_cliente": "7", "monto": "500"}],
    }

    filas = ejecutar_plan(plan, entradas)["ventas_con_nombre"]

    assert filas == [{"id_venta": "10", "nombre": "Ana", "monto": "500"}]


def test_filtro_menor_que_con_faltante_es_verdadero():
    """Un faltante numérico es menor que cualquier número, así que `saldo < 500` es verdadero."""
    plan = _plan(CON_SALDO)
    entradas = {
        "clientes": [
            {"id_cliente": "1", "saldo": "400"},
            {"id_cliente": "2", "saldo": ""},
            {"id_cliente": "3", "saldo": "900"},
        ]
    }

    filas = ejecutar_plan(plan, entradas)["morosos"]

    assert [fila["id_cliente"] for fila in filas] == ["1", "2"]


def test_comparacion_de_caracter_sas_trata_blanco_como_faltante_y_conserva_iniciales():
    texto = """PROC IMPORT DATAFILE='.../entrada.csv' OUT=WORK.clientes DBMS=CSV REPLACE;
      GETNAMES=YES;
    RUN;

    PROC SQL;
      CREATE TABLE WORK.menores AS
      SELECT id FROM WORK.clientes WHERE nombre < 'A';
    QUIT;

    PROC EXPORT DATA=WORK.menores OUTFILE='.../salida.csv' DBMS=CSV REPLACE;
    RUN;
    """
    plan = _plan(texto)
    entradas = {
        "clientes": [
            {"id": "1", "nombre": ""},
            {"id": "2", "nombre": " A"},
            {"id": "3", "nombre": "A"},
        ]
    }

    filas = ejecutar_plan(plan, entradas)["menores"]

    assert [fila["id"] for fila in filas] == ["1", "2"]


def test_data_step_asigna_columna_y_conserva_las_que_vienen_de_set():
    texto = """DATA WORK.con_totales;
      SET WORK.ventas;
      total = monto * 2;
    RUN;
    """
    plan = _plan(texto)

    filas = ejecutar_plan(plan, {"ventas": [{"id_venta": "7", "monto": "12.5"}]})

    assert filas["con_totales"] == [{"id_venta": "7", "monto": "12.5", "total": "25"}]


def test_data_step_if_then_else_asigna_una_de_dos_expresiones():
    texto = """DATA WORK.clasificados;
      SET WORK.saldos;
      IF saldo >= 0 THEN estado = 'positivo';
      ELSE estado = 'negativo';
    RUN;
    """
    plan = _plan(texto)
    entradas = {
        "saldos": [
            {"id": "1", "saldo": "5"},
            {"id": "2", "saldo": "-3"},
            {"id": "3", "saldo": ""},
        ]
    }

    filas = ejecutar_plan(plan, entradas)["clasificados"]

    assert filas == [
        {"id": "1", "saldo": "5", "estado": "positivo"},
        {"id": "2", "saldo": "-3", "estado": "negativo"},
        {"id": "3", "saldo": "", "estado": "negativo"},
    ]


def test_data_step_keep_proyecta_solo_las_columnas_declaradas():
    plan = _plan("DATA WORK.publicas; SET WORK.privadas; KEEP id saldo; RUN;")
    entradas = {"privadas": [{"id": "1", "saldo": "25", "secreto": "x"}]}

    filas = ejecutar_plan(plan, entradas)["publicas"]

    assert filas == [{"id": "1", "saldo": "25"}]


def test_data_step_drop_elimina_solo_las_columnas_declaradas():
    plan = _plan("DATA WORK.publicas; SET WORK.privadas; DROP secreto; RUN;")
    entradas = {"privadas": [{"id": "1", "saldo": "25", "secreto": "x"}]}

    filas = ejecutar_plan(plan, entradas)["publicas"]

    assert filas == [{"id": "1", "saldo": "25"}]


def test_data_step_rename_cambia_nombres_solo_en_la_salida():
    """RENAME del DATA step cambia los nombres de salida; las expresiones usan el nombre viejo."""
    plan = _plan("DATA WORK.publicas; SET WORK.privadas; RENAME saldo=balance; RUN;")
    entradas = {"privadas": [{"id": "1", "saldo": "25"}]}

    filas = ejecutar_plan(plan, entradas)["publicas"]

    assert filas == [{"id": "1", "balance": "25"}]


def test_set_where_optiona_filtra_filas_antes_del_resto_del_data_step():
    plan = _plan(
        "DATA WORK.activos; SET WORK.clientes(WHERE=(estado = 'ACTIVO')); RUN;"
    )
    entradas = {
        "clientes": [
            {"id_cliente": "1", "estado": "ACTIVO"},
            {"id_cliente": "2", "estado": "INACTIVO"},
        ]
    }

    filas = ejecutar_plan(plan, entradas)["activos"]

    assert filas == [{"id_cliente": "1", "estado": "ACTIVO"}]


def test_subsetting_if_conserva_no_cero_y_descarta_cero_o_faltante():
    plan = _plan("DATA WORK.seleccionados; SET WORK.valores; IF cantidad; RUN;")
    entradas = {
        "valores": [
            {"id": "1", "cantidad": "2"},
            {"id": "2", "cantidad": "0"},
            {"id": "3", "cantidad": ""},
            {"id": "4", "cantidad": "-1"},
        ]
    }

    filas = ejecutar_plan(plan, entradas)["seleccionados"]

    assert [fila["id"] for fila in filas] == ["1", "4"]


@pytest.mark.parametrize(
    ("programa", "entradas"),
    [
        # Una expresión sobre agregados no es FUNCION(columna): el intérprete no la adivina.
        (AGREGADO_COMPUESTO, {"clientes": []}),
        (
            "PROC SQL; CREATE TABLE resumen AS SELECT STD(valor) AS desviacion "
            "FROM WORK.valores; QUIT;",
            {"valores": []},
        ),
    ],
)
def test_un_operador_no_soportado_no_se_salta(programa, entradas):
    """Un paso sin implementar detiene la ejecución con su nombre, no devuelve filas sin calcular."""
    plan = _plan(programa)
    with pytest.raises(NoSoportadoEnInterprete) as error:
        ejecutar_plan(plan, entradas)

    assert error.value.kind == "aggregate"
    assert str(error.value).startswith("aggregate")


def test_agregados_por_grupo_cuentan_omisiones_y_conservan_faltantes_sas():
    plan = _plan(
        "PROC SQL;\n"
        "CREATE TABLE WORK.resumen AS\n"
        "SELECT categoria, COUNT(*) AS filas, COUNT(valor) AS no_faltantes,\n"
        "SUM(valor) AS suma, SUM(valor + 1) AS suma_mas_uno, AVG(valor) AS promedio,\n"
        "MIN(valor) AS minimo, MAX(valor) AS maximo\n"
        "FROM WORK.entrada\n"
        "GROUP BY categoria;\n"
        "QUIT;"
    )
    entradas = {
        "entrada": [
            {"categoria": "A", "valor": "1"},
            {"categoria": "A", "valor": ""},
            {"categoria": "A", "valor": "5"},
            {"categoria": "B", "valor": ""},
            {"categoria": "B", "valor": None},
            {"categoria": "", "valor": "2"},
            {"categoria": None, "valor": "4"},
        ]
    }

    filas = ejecutar_plan(plan, entradas)["resumen"]

    assert filas == [
        {
            "categoria": "A",
            "filas": "3",
            "no_faltantes": "2",
            "suma": "6",
            "suma_mas_uno": "8",
            "promedio": "3",
            "minimo": "1",
            "maximo": "5",
        },
        {
            "categoria": "B",
            "filas": "2",
            "no_faltantes": "0",
            "suma": None,
            "suma_mas_uno": None,
            "promedio": None,
            "minimo": None,
            "maximo": None,
        },
        {
            "categoria": "",
            "filas": "2",
            "no_faltantes": "2",
            "suma": "6",
            "suma_mas_uno": "8",
            "promedio": "3",
            "minimo": "2",
            "maximo": "4",
        },
    ]


def test_group_by_solo_publica_las_columnas_que_solicita_el_select():
    plan = _plan(
        "PROC SQL; CREATE TABLE WORK.resumen AS SELECT COUNT(*) AS n "
        "FROM WORK.entrada GROUP BY categoria; QUIT;"
    )

    filas = ejecutar_plan(
        plan,
        {"entrada": [{"categoria": "A"}, {"categoria": "A"}, {"categoria": "B"}]},
    )["resumen"]

    assert filas == [{"n": "2"}, {"n": "1"}]


def test_group_by_respeta_el_orden_de_columnas_del_select():
    plan = _plan(
        "PROC SQL; CREATE TABLE WORK.resumen AS "
        "SELECT COUNT(*) AS n, categoria AS cat FROM WORK.entrada "
        "GROUP BY categoria; QUIT;"
    )

    filas = ejecutar_plan(plan, {"entrada": [{"categoria": "A"}]})["resumen"]

    assert list(filas[0]) == ["n", "cat"]


def test_group_by_rechaza_select_star_con_agregado():
    plan = _plan(
        "PROC SQL; CREATE TABLE WORK.resumen AS SELECT *, COUNT(*) AS n "
        "FROM WORK.entrada GROUP BY categoria; QUIT;"
    )

    with pytest.raises(NoSoportadoEnInterprete, match="aggregate.*columnas sin agregar"):
        ejecutar_plan(plan, {"entrada": [{"categoria": "A", "detalle": "x"}]})


def test_group_by_conserva_alias_de_columna_seleccionada_y_agregado_tras_join():
    plan = _plan(
        "PROC SQL; CREATE TABLE WORK.resumen AS "
        "SELECT a.categoria AS cat, COUNT(*) AS n "
        "FROM WORK.entrada AS a INNER JOIN WORK.otra AS b "
        "ON a.categoria = b.categoria GROUP BY a.categoria; QUIT;"
    )

    filas = ejecutar_plan(
        plan,
        {
            "entrada": [{"categoria": "A"}, {"categoria": "A"}],
            "otra": [{"categoria": "A"}],
        },
    )["resumen"]

    assert filas == [{"cat": "A", "n": "2"}]


def test_group_by_order_by_columna_agrupada_con_alias_usa_el_alias_de_salida():
    plan = _plan(
        "PROC SQL; CREATE TABLE WORK.resumen AS "
        "SELECT categoria AS cat, COUNT(*) AS n FROM WORK.entrada "
        "GROUP BY categoria ORDER BY categoria; QUIT;"
    )

    filas = ejecutar_plan(
        plan, {"entrada": [{"categoria": "B"}, {"categoria": "A"}]}
    )["resumen"]

    assert filas == [{"cat": "A", "n": "1"}, {"cat": "B", "n": "1"}]


def test_group_by_order_by_no_seleccionado_rechaza_remezcla_sas():
    plan = _plan(
        "PROC SQL; CREATE TABLE WORK.resumen AS SELECT COUNT(*) AS n "
        "FROM WORK.entrada GROUP BY categoria ORDER BY categoria; QUIT;"
    )

    with pytest.raises(NoSoportadoEnInterprete, match="aggregate.*columnas sin agregar"):
        ejecutar_plan(plan, {"entrada": [{"categoria": "A"}, {"categoria": "B"}]})


def test_group_by_rechaza_columna_seleccionada_que_requiere_remezcla():
    plan = _plan(
        "PROC SQL; CREATE TABLE WORK.resumen AS "
        "SELECT categoria, detalle, COUNT(*) AS n FROM WORK.entrada "
        "GROUP BY categoria; QUIT;"
    )

    with pytest.raises(NoSoportadoEnInterprete, match="aggregate.*columnas sin agregar"):
        ejecutar_plan(
            plan,
            {"entrada": [{"categoria": "A", "detalle": "x"}, {"categoria": "A", "detalle": "y"}]},
        )


def test_agregados_globales_sin_filas_devuelven_una_fila_resumen():
    plan = _plan(
        "PROC SQL; CREATE TABLE WORK.resumen AS SELECT COUNT(*) AS filas "
        "FROM WORK.entrada; QUIT;"
    )

    filas = ejecutar_plan(plan, {"entrada": []})["resumen"]

    assert filas == [{"filas": "0"}]


def test_agregado_como_paso_de_map_se_ejecuta_y_publica_su_salida():
    grafo = Graph()
    fuente = Operator("fuente", "read", {"dataset": "WORK.entrada"})
    mapa = Operator(
        "mapa",
        "map",
        {
            "steps": [
                {
                    "kind": "aggregate",
                    "params": {
                        "group_by": ["categoria"],
                        "aggregations": [{"expression": "COUNT(*)", "alias": "filas"}],
                    },
                }
            ],
            "outputs": ["WORK.resumen"],
        },
    )
    destino = Operator("destino", "write", {"dataset": "WORK.resumen"})
    for operador in (fuente, mapa, destino):
        grafo.add_operator(operador)
    grafo.add_edge(Edge("fuente", "mapa", "(interno)"))
    grafo.add_edge(Edge("mapa", "destino", "WORK.resumen"))

    filas = ejecutar_plan(
        Plan("prueba", graph=grafo),
        {"entrada": [{"categoria": "A"}, {"categoria": "A"}, {"categoria": "B"}]},
    )["resumen"]

    assert filas == [
        {"categoria": "A", "filas": "2"},
        {"categoria": "B", "filas": "1"},
    ]


def test_agregados_globales_suman_todas_las_filas_no_faltantes():
    plan = _plan(
        "PROC SQL; CREATE TABLE WORK.resumen AS SELECT COUNT(*) AS filas, "
        "SUM(valor) AS suma, AVG(valor) AS promedio, MIN(valor) AS minimo, "
        "MAX(valor) AS maximo FROM WORK.entrada; QUIT;"
    )

    filas = ejecutar_plan(
        plan, {"entrada": [{"valor": "2"}, {"valor": ""}, {"valor": "4"}]}
    )["resumen"]

    assert filas == [
        {"filas": "3", "suma": "6", "promedio": "3", "minimo": "2", "maximo": "4"}
    ]


def test_count_distinct_ignora_faltantes_y_cuenta_un_valor_una_vez():
    plan = _plan(
        "PROC SQL; CREATE TABLE WORK.resumen AS "
        "SELECT COUNT(DISTINCT canal) AS canales FROM WORK.entrada; QUIT;"
    )

    filas = ejecutar_plan(
        plan,
        {
            "entrada": [
                {"canal": "web"},
                {"canal": "web"},
                {"canal": ""},
                {"canal": None},
                {"canal": "sucursal"},
            ]
        },
    )["resumen"]

    assert filas == [{"canales": "2"}]


def test_mean_de_un_argumento_es_agregado_de_promedio_por_grupo():
    plan = _plan(
        "PROC SQL; CREATE TABLE WORK.resumen AS "
        "SELECT categoria, MEAN(a) AS promedio FROM WORK.entrada "
        "GROUP BY categoria; QUIT;"
    )

    filas = ejecutar_plan(
        plan,
        {
            "entrada": [
                {"categoria": "A", "a": "2"},
                {"categoria": "A", "a": "4"},
                {"categoria": "B", "a": ""},
            ]
        },
    )["resumen"]

    assert filas == [
        {"categoria": "A", "promedio": "3"},
        {"categoria": "B", "promedio": None},
    ]


def test_proc_sql_multiargumento_ejecuta_funciones_numericas_por_fila():
    plan = _plan(
        "PROC SQL; CREATE TABLE WORK.resumen AS "
        "SELECT SUM(a, MAX(b, c)) AS suma, MIN(a, b) AS minimo, MAX(a, b) AS maximo, "
        "MEAN(a, b) AS promedio FROM WORK.entrada; QUIT;"
    )
    proyeccion = next(op for op in plan.graph.operators() if op.kind == "derive")
    assert proyeccion.status == "parcial"
    assert [item["expression"] for item in proyeccion.params["assignments"]] == [
        "SGM_ROW_SUM(a, SGM_ROW_MAX(b, c))",
        "SGM_ROW_MIN(a, b)",
        "SGM_ROW_MAX(a, b)",
        "SGM_ROW_MEAN(a, b)",
    ]

    filas = ejecutar_plan(
        plan,
        {
            "entrada": [
                {"a": "2", "b": "6", "c": "3"},
                {"a": "", "b": "5", "c": "7"},
                {"a": "", "b": "", "c": ""},
            ]
        },
    )["resumen"]

    assert filas == [
        {"suma": "8", "minimo": "2", "maximo": "6", "promedio": "4"},
        {"suma": "7", "minimo": "5", "maximo": "5", "promedio": "5"},
        {"suma": None, "minimo": None, "maximo": None, "promedio": None},
    ]


def test_proc_sql_avg_con_varios_argumentos_no_se_interpreta_como_agregado():
    plan = _plan(
        "PROC SQL; CREATE TABLE WORK.resumen AS "
        "SELECT AVG(a, b) AS promedio FROM WORK.entrada; QUIT;"
    )

    assert any(
        operador.kind == "unsupported" and operador.params.get("reason") == "PARSE_ERROR"
        for operador in plan.graph.operators()
    )


def test_proc_sql_sum_multiargumento_rechaza_valor_no_numerico():
    plan = _plan(
        "PROC SQL; CREATE TABLE WORK.resumen AS "
        "SELECT SUM(a, b) AS suma FROM WORK.entrada; QUIT;"
    )

    with pytest.raises(NoSoportadoEnInterprete, match="SUM requiere argumentos numéricos"):
        ejecutar_plan(plan, {"entrada": [{"a": "texto", "b": "2"}]})


def test_proc_sql_no_reescribe_columna_con_nombre_interno_de_funcion():
    plan = _plan(
        "PROC SQL; CREATE TABLE WORK.salida AS "
        "SELECT sgm_sum AS valor FROM WORK.entrada; QUIT;"
    )
    proyeccion = next(op for op in plan.graph.operators() if op.kind == "derive")

    assert proyeccion.params["assignments"] == [
        {"target": "valor", "expression": "sgm_sum", "origin": "columna"}
    ]


def test_group_by_sin_filas_no_produce_grupos():
    plan = _plan(
        "PROC SQL; CREATE TABLE WORK.resumen AS SELECT categoria, COUNT(*) AS filas "
        "FROM WORK.entrada GROUP BY categoria; QUIT;"
    )

    assert ejecutar_plan(plan, {"entrada": []})["resumen"] == []


def test_agregados_agrupan_por_varias_columnas():
    plan = _plan(
        "PROC SQL; CREATE TABLE WORK.resumen AS SELECT region, categoria, COUNT(*) AS filas "
        "FROM WORK.entrada GROUP BY region, categoria; QUIT;"
    )
    entradas = {
        "entrada": [
            {"region": "Norte", "categoria": "A"},
            {"region": "Norte", "categoria": "A"},
            {"region": "Norte", "categoria": "B"},
            {"region": "Sur", "categoria": "A"},
        ]
    }

    assert ejecutar_plan(plan, entradas)["resumen"] == [
        {"region": "Norte", "categoria": "A", "filas": "2"},
        {"region": "Norte", "categoria": "B", "filas": "1"},
        {"region": "Sur", "categoria": "A", "filas": "1"},
    ]


def test_agregado_no_adivina_tipo_de_clave_de_grupo_numerica_en_texto():
    plan = _plan(
        "PROC SQL; CREATE TABLE WORK.resumen AS SELECT codigo, COUNT(*) AS filas "
        "FROM WORK.entrada GROUP BY codigo; QUIT;"
    )

    with pytest.raises(NoSoportadoEnInterprete, match="tipo.*ambiguo"):
        ejecutar_plan(plan, {"entrada": [{"codigo": "01"}, {"codigo": "1"}]})


def test_in_subconsulta_sin_coincidencias_devuelve_cero_filas():
    filas = _ejecutar_in(
        "c.id IN (SELECT v.id FROM work.ventas v WHERE v.id > 99)",
        {"clientes": [{"id": "1"}, {"id": "2"}], "ventas": [{"id": "3"}]},
    )

    assert filas == []


def test_not_in_subconsulta_sin_coincidencias_conserva_las_filas():
    filas = _ejecutar_in(
        "c.id NOT IN (SELECT v.id FROM work.ventas v WHERE v.id > 99)",
        {"clientes": [{"id": "1"}, {"id": "2"}], "ventas": [{"id": "3"}]},
    )

    assert filas == [{"id": "1"}, {"id": "2"}]


def test_in_subconsulta_con_duplicados_no_duplica_filas():
    filas = _ejecutar_in(
        "c.id IN (SELECT v.id FROM work.ventas v)",
        {"clientes": [{"id": "1"}, {"id": "2"}], "ventas": [{"id": "1"}, {"id": "1"}]},
    )

    assert filas == [{"id": "1"}]


def test_in_subconsulta_correlacionada_se_rechaza():
    with pytest.raises(NoSoportadoEnInterprete, match="correlacionada"):
        _ejecutar_in(
            "c.id IN (SELECT v.id FROM work.ventas v WHERE v.id = c.id)",
            {"clientes": [{"id": "1"}], "ventas": [{"id": "1"}]},
        )


@pytest.mark.parametrize(
    ("filas", "ventas"),
    [
        ([{"id": ""}], [{"id": "1"}]),
        ([{"id": "1"}], [{"id": ""}]),
    ],
)
def test_in_subconsulta_con_faltantes_se_rechaza(filas, ventas):
    with pytest.raises(NoSoportadoEnInterprete, match="faltante"):
        _ejecutar_in("c.id IN (SELECT v.id FROM work.ventas v)", {"clientes": filas, "ventas": ventas})


def test_in_subconsulta_de_varias_columnas_se_rechaza():
    with pytest.raises(NoSoportadoEnInterprete, match="una sola columna"):
        _ejecutar_in(
            "c.id IN (SELECT v.id, v.canal FROM work.ventas v)",
            {"clientes": [{"id": "1"}], "ventas": [{"id": "1", "canal": "WEB"}]},
        )


def test_in_subconsulta_con_fuente_no_verificable_se_rechaza():
    with pytest.raises(NoSoportadoEnInterprete, match="fuente.*disponible"):
        _ejecutar_in("c.id IN (SELECT v.id FROM work.ventas v)", {"clientes": [{"id": "1"}]})


def test_in_subconsulta_con_agregado_se_rechaza():
    with pytest.raises(NoSoportadoEnInterprete, match="no soportada"):
        _ejecutar_in(
            "c.id IN (SELECT MAX(v.id) FROM work.ventas v)",
            {"clientes": [{"id": "1"}], "ventas": [{"id": "1"}]},
        )


def test_in_subconsulta_con_varias_fuentes_se_rechaza():
    with pytest.raises(NoSoportadoEnInterprete, match="una sola fuente"):
        _ejecutar_in(
            "c.id IN (SELECT v.id FROM work.ventas v, work.clientes x)",
            {
                "clientes": [{"id": "1"}],
                "ventas": [{"id": "1"}],
            },
        )


def test_select_alias_star_en_join_proyecta_solo_el_lado_seleccionado():
    plan = _plan(
        "PROC SQL; CREATE TABLE WORK.homologados AS SELECT t.* "
        "FROM WORK.operaciones t INNER JOIN WORK.homologacion h "
        "ON t.tipo_doc = h.CNAME; QUIT;"
    )

    filas = ejecutar_plan(
        plan,
        {
            "operaciones": [
                {"id": "1", "tipo_doc": "CC", "monto": "100"},
                {"id": "2", "tipo_doc": "NIT", "monto": "200"},
            ],
            "homologacion": [
                {"CNAME": "CC", "descripcion": "Cédula"},
            ],
        },
    )["homologados"]

    assert filas == [{"id": "1", "tipo_doc": "CC", "monto": "100"}]


def test_output_data_step_distribuye_filas_a_todos_los_destinos_explicitos():
    plan = _plan(
        "DATA WORK.primera WORK.segunda WORK.no_implicita;\n"
        "SET WORK.entrada;\n"
        "OUTPUT WORK.primera WORK.segunda;\n"
        "RUN;"
    )

    tablas = ejecutar_plan(plan, {"entrada": [{"id": "1"}, {"id": "2"}]})

    esperadas = [{"id": "1"}, {"id": "2"}]
    assert tablas["primera"] == esperadas
    assert tablas["segunda"] == esperadas
    assert "no_implicita" not in tablas


def test_output_condicional_multiple_respeta_rama_else():
    plan = _plan(
        "DATA WORK.uno WORK.dos WORK.otros;\n"
        "SET WORK.entrada;\n"
        "IF valor = 1 THEN OUTPUT WORK.uno WORK.dos;\n"
        "ELSE OUTPUT WORK.otros;\n"
        "RUN;"
    )

    tablas = ejecutar_plan(
        plan,
        {"entrada": [{"valor": "1"}, {"valor": "2"}, {"valor": "1"}]},
    )

    assert tablas["uno"] == [{"valor": "1"}, {"valor": "1"}]
    assert tablas["dos"] == [{"valor": "1"}, {"valor": "1"}]
    assert tablas["otros"] == [{"valor": "2"}]


def test_output_sin_destinos_explicitamente_usa_todas_las_salidas_data():
    plan = _plan(
        "DATA WORK.primera WORK.segunda;\n"
        "SET WORK.entrada;\n"
        "OUTPUT;\n"
        "RUN;"
    )

    tablas = ejecutar_plan(plan, {"entrada": [{"id": "1"}, {"id": "2"}]})

    esperadas = [{"id": "1"}, {"id": "2"}]
    assert tablas["primera"] == esperadas
    assert tablas["segunda"] == esperadas


def test_output_condicional_sin_destino_escribe_a_todos_los_datasets_de_data():
    plan = _plan(
        "DATA WORK.primera WORK.segunda;\n"
        "SET WORK.entrada;\n"
        "IF valor=1 THEN OUTPUT;\n"
        "RUN;"
    )

    tablas = ejecutar_plan(plan, {"entrada": [{"valor": "1"}, {"valor": "2"}]})

    esperadas = [{"valor": "1"}]
    assert tablas["primera"] == esperadas
    assert tablas["segunda"] == esperadas


def test_output_contiguos_a_destinos_distintos_distribuyen_cada_observacion():
    plan = _plan(
        "DATA WORK.primera WORK.segunda;\n"
        "SET WORK.entrada;\n"
        "OUTPUT WORK.primera;\n"
        "OUTPUT WORK.segunda;\n"
        "RUN;"
    )

    tablas = ejecutar_plan(plan, {"entrada": [{"id": "1"}, {"id": "2"}]})

    esperadas = [{"id": "1"}, {"id": "2"}]
    assert tablas["primera"] == esperadas
    assert tablas["segunda"] == esperadas


def test_output_repetido_a_mismo_destino_no_finge_el_numero_de_filas():
    plan = _plan(
        "DATA WORK.salida;\n"
        "SET WORK.entrada;\n"
        "OUTPUT WORK.salida;\n"
        "OUTPUT WORK.salida;\n"
        "RUN;"
    )

    with pytest.raises(NoSoportadoEnInterprete, match="unsupported"):
        ejecutar_plan(plan, {"entrada": [{"id": "1"}]})


def test_output_condicional_no_terminal_escribe_y_continua_con_todas_las_filas():
    plan = _plan(
        "DATA WORK.temprano WORK.tarde WORK.final;\n"
        "SET WORK.entrada;\n"
        "IF valor=1 THEN OUTPUT WORK.temprano;\n"
        "ELSE OUTPUT WORK.tarde;\n"
        "valor=valor+10;\n"
        "OUTPUT WORK.final;\n"
        "RUN;"
    )

    tablas = ejecutar_plan(plan, {"entrada": [{"valor": "1"}, {"valor": "2"}]})

    assert tablas["temprano"] == [{"valor": "1"}]
    assert tablas["tarde"] == [{"valor": "2"}]
    assert tablas["final"] == [{"valor": "11"}, {"valor": "12"}]


def test_output_if_sin_else_escribe_solo_si_se_cumple_la_condicion():
    plan = _plan(
        "DATA WORK.coinciden;\n"
        "SET WORK.entrada;\n"
        "IF valor = 1 THEN OUTPUT WORK.coinciden;\n"
        "RUN;"
    )

    tablas = ejecutar_plan(
        plan,
        {"entrada": [{"valor": "1"}, {"valor": "0"}, {"valor": "1"}]},
    )

    assert tablas["coinciden"] == [{"valor": "1"}, {"valor": "1"}]


def test_output_else_if_encadenado_distribuye_por_primera_condicion_cumplida():
    plan = _plan(
        "DATA WORK.uno WORK.dos WORK.otros;\n"
        "SET WORK.entrada;\n"
        "IF valor >= 1 THEN OUTPUT WORK.uno;\n"
        "ELSE IF valor >= 2 THEN OUTPUT WORK.dos;\n"
        "ELSE OUTPUT WORK.otros;\n"
        "RUN;"
    )

    tablas = ejecutar_plan(
        plan,
        {"entrada": [{"valor": "1"}, {"valor": "2"}, {"valor": "0"}]},
    )

    assert tablas["uno"] == [{"valor": "1"}, {"valor": "2"}]
    assert tablas["dos"] == []
    assert tablas["otros"] == [{"valor": "0"}]


def test_in_subconsulta_usa_version_previa_a_una_sobreescritura_futura():
    plan = _plan(
        "PROC SQL;\n"
        "CREATE TABLE WORK.lookup AS SELECT id FROM WORK.version_inicial;\n"
        "QUIT;\n"
        "PROC SQL;\n"
        "CREATE TABLE WORK.resultado AS SELECT c.id FROM WORK.clientes c "
        "WHERE c.id IN (SELECT l.id FROM WORK.lookup l);\n"
        "QUIT;\n"
        "PROC SQL;\n"
        "CREATE TABLE WORK.lookup AS SELECT id FROM WORK.version_futura;\n"
        "QUIT;\n"
    )

    filas = ejecutar_plan(
        plan,
        {
            "version_inicial": [{"id": "10"}],
            "version_futura": [{"id": "20"}],
            "clientes": [{"id": "10"}, {"id": "20"}],
        },
    )["resultado"]

    assert filas == [{"id": "10"}]


def test_select_alias_star_sin_esquema_en_lado_vacio_de_left_join_se_rechaza():
    plan = _plan(
        "PROC SQL; CREATE TABLE WORK.homologados AS SELECT h.* "
        "FROM WORK.operaciones o LEFT JOIN WORK.homologacion h "
        "ON o.tipo_doc = h.tipo_doc; QUIT;"
    )

    with pytest.raises(NoSoportadoEnInterprete, match="esquema.*verificable"):
        ejecutar_plan(
            plan,
            {"operaciones": [{"tipo_doc": "CC"}], "homologacion": []},
        )


def test_data_step_if_then_do_else_aplica_ambas_ramas():
    plan = _plan(
        "DATA WORK.clientes_revisados;\n"
        "  SET WORK.clientes;\n"
        "  LENGTH revision $ 2;\n"
        "  IF saldo < 0 THEN DO;\n"
        "    revision = 'SI';\n"
        "    saldo = 0;\n"
        "  END;\n"
        "  ELSE revision = 'NO';\n"
        "RUN;"
    )
    entradas = {
        "clientes": [
            {"id": "1", "saldo": "-5"},
            {"id": "2", "saldo": "7"},
            {"id": "3", "saldo": ""},
        ]
    }

    filas = ejecutar_plan(plan, entradas)["clientes_revisados"]

    assert filas == [
        {"id": "1", "saldo": "0", "revision": "SI"},
        {"id": "2", "saldo": "7", "revision": "NO"},
        {"id": "3", "saldo": "0", "revision": "SI"},
    ]
