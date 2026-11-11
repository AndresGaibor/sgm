"""Emisor del Job de Talend desde el plan: lectura, `tMap` y escritura, sin ningún YAML.

Las pruebas usan los casos `L2` del corpus tal como los compila el pipeline: si el plan cambia, el
Job cambia con él y la prueba lo dice. Los dos puntos que el plan marca como foco de revisión están
aquí: el faltante de un filtro (en SAS es menor que cualquier número) y un operador que lanza una
excepción (no se lleva el resto del Job).
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from sgm.compile import compile_file, project_base
from sgm.frontend.program import analyze_program
from sgm.ir.models import Column, Plan
from sgm.migrar.esquemas import esquemas_de_entrada
from sgm.talend_item import desde_plan_map
from sgm.talend_item.desde_plan import plan_a_jobs
from sgm.talend_item.desde_plan_expresiones import expresion
from sgm.talend_item.modelo import Job
from sgm.talend_item.validador import validar_job

CORPUS = Path(__file__).resolve().parents[1] / "corpus" / "L2"
RAIZ = Path(__file__).resolve().parents[1] / "corpus"

# `WHERE saldo < 500` no está en el corpus L1, que solo compara contra un literal con `>=`. El
# programa es el mínimo que ejercita la comparación de orden con un faltante posible.
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


def _plan(texto: str) -> Plan:
    return compile_file(analyze_program({"p.sas": texto}), "p.sas", project_base()).plan


def _caso(nombre: str) -> Plan:
    return _plan((CORPUS / nombre / "programa.sas").read_text(encoding="utf-8"))


def _job(plan: Plan, esquemas: dict[str, list[Column]] | None = None) -> Job:
    if esquemas is None:
        esquemas, _ = esquemas_de_entrada(plan, {}, None)
    return plan_a_jobs(plan, esquemas).jobs[0]


def _componentes(job: Job) -> list[str]:
    return [nodo.componente for nodo in job.nodos]


def _tmap(job: Job) -> str:
    return next(nodo.datos for nodo in job.nodos if nodo.componente == "tMap")


def test_un_job_con_cuatro_nodos():
    """Dos lecturas, el `tMap` y la escritura: los `read`/`write` internos no son nodos aparte."""
    job = _job(_caso("l2_01_inner_join_clientes_ventas"))

    assert sorted(_componentes(job)) == [
        "tFileInputDelimited",
        "tFileInputDelimited",
        "tFileOutputDelimited",
        "tMap",
    ]


def test_conexiones_principal_lookup_y_salida():
    job = _job(_caso("l2_01_inner_join_clientes_ventas"))

    flujo = [c for c in job.conexiones if c.estilo == 0]
    lookups = [c for c in job.conexiones if c.estilo == 8]
    assert len(job.conexiones) == 3
    assert len(flujo) == 2  # la principal entra y la salida sale
    assert len(lookups) == 1
    assert lookups[0].conector == "LOOKUP"
    assert lookups[0].destino == "tMap_1"


def test_inner_join_activa_union_interna():
    job = _job(_caso("l2_01_inner_join_clientes_ventas"))

    assert 'name="row2"' in _tmap(job)
    assert 'innerJoin="true"' in _tmap(job)


def test_left_join_no_activa_union_interna():
    job = _job(_caso("l2_02_left_join_con_faltantes"))

    assert 'innerJoin="true"' not in _tmap(job)
    assert 'expression="row1.id_cliente"' in _tmap(job)  # la llave sigue declarada


def test_un_lookup_de_sql_trae_todas_las_parejas():
    """Un cliente con cuatro ventas sale cuatro veces: `UNIQUE_MATCH` solo daría la primera."""
    for caso in ("l2_01_inner_join_clientes_ventas", "l2_02_left_join_con_faltantes"):
        datos = _tmap(_job(_caso(caso)))

        assert 'name="row2" matchingMode="ALL_ROWS"' in datos, caso


def test_traza_apunta_a_las_lineas_del_sas():
    plan = _caso("l2_01_inner_join_clientes_ventas")

    traza = plan_a_jobs(plan, esquemas_de_entrada(plan, {}, None)[0]).traza

    assert traza["tMap_1"] == [15, 16, 17, 18, 19, 20, 21]
    assert 16 in traza["tMap_1"]  # la línea del CREATE TABLE


def _filtro_de(job: Job) -> str:
    linea = next(x for x in _tmap(job).splitlines() if "expressionFilter" in x)
    return linea.split('expressionFilter="')[1].split('"')[0]


def test_filtro_con_faltante_es_nulo_seguro():
    """`saldo < 500` es verdadero con `saldo` faltante, como en SAS; en Java un nulo no compara."""
    plan = _plan(CON_SALDO)
    esquema = {"work.clientes": [Column("id_cliente", "Integer"), Column("saldo", "Integer")]}

    job = _job(plan, esquema)
    filtro = _filtro_de(job)

    assert "row1.saldo == null" in filtro
    assert filtro.index("row1.saldo == null") < filtro.index("row1.saldo &lt; 500")


def test_filtro_sobre_texto_comprueba_que_sea_numero():
    """Sin tipo demostrado la columna es texto: el filtro no puede comparar texto con un número."""
    plan = _plan(CON_SALDO)

    job = _job(plan, {"work.clientes": [Column("id_cliente"), Column("saldo")]})
    filtro = _filtro_de(job)

    assert "row1.saldo == null" in filtro
    assert "matches(" in filtro
    assert "Double.parseDouble(row1.saldo)" in filtro


@pytest.mark.parametrize("operador", ["<", "<=", ">", ">="])
def test_comparacion_entre_columnas_numericas_cubre_faltantes(operador):
    java, motivo = expresion(
        f"saldo_actual {operador} saldo_anterior",
        {"row1": {"saldo_actual", "saldo_anterior"}},
        {"row1.saldo_actual": "id_Double", "row1.saldo_anterior": "id_Double"},
    )

    assert motivo is None
    assert java is not None
    assert "== null" in java
    assert "!= null" in java
    assert f"row1.saldo_actual {operador} row1.saldo_anterior" in java
    assert ".compareTo(" not in java


def test_comparacion_de_orden_entre_columnas_sin_tipo_queda_pendiente():
    java, motivo = expresion(
        "saldo_actual < saldo_anterior",
        {"row1": {"saldo_actual", "saldo_anterior"}},
        {},
    )

    assert java is None
    assert motivo is not None
    assert "semántica de faltante" in motivo


def test_data_step_emite_asignacion_aditiva_en_tmap():
    plan = _plan(
        "PROC IMPORT DATAFILE='entrada.csv' OUT=WORK.ventas DBMS=CSV REPLACE;\n"
        "GETNAMES=YES;\nRUN;\n"
        "DATA con_totales;\nSET ventas;\ntotal = monto * 2;\nRUN;"
    )
    esquema = {"work.ventas": [Column("id_venta", "String"), Column("monto", "Double")]}

    job = _job(plan, esquema)
    datos = _tmap(job)

    assert 'name="id_venta" type="id_String"' in datos
    assert 'name="monto" type="id_Double"' in datos
    assert 'name="total"' in datos
    assert 'expression="(row1.monto * 2)" type="id_Double"' in datos
    assert "row1.monto" in datos and "* 2" in datos


def test_data_step_if_then_else_emite_ternario_en_tmap():
    plan = _plan(
        "PROC IMPORT DATAFILE='entrada.csv' OUT=WORK.saldos DBMS=CSV REPLACE;\n"
        "GETNAMES=YES;\nRUN;\n"
        "DATA clasificados;\nSET saldos;\n"
        "IF saldo >= 0 THEN estado = 'positivo';\n"
        "ELSE estado = 'negativo';\nRUN;"
    )
    esquema = {"work.saldos": [Column("id", "String"), Column("saldo", "Double")]}
    resultado = plan_a_jobs(plan, esquema)
    assert not resultado.pendientes, resultado.pendientes
    job = resultado.jobs[0]
    datos = _tmap(job)

    assert "outputTables" in datos, datos
    assert 'name="estado"' in datos
    assert 'expression="' in datos
    assert "row1.saldo != null" in datos
    assert ' ? &quot;positivo&quot; : &quot;negativo&quot;' in datos


def test_data_step_else_if_encadenado_emite_ternarios_en_orden():
    plan = _plan(
        "PROC IMPORT DATAFILE='entrada.csv' OUT=WORK.saldos DBMS=CSV REPLACE;\n"
        "GETNAMES=YES;\nRUN;\n"
        "DATA clasificados;\nSET saldos;\n"
        "IF saldo >= 2000 THEN nivel = 'ALTO';\n"
        "ELSE IF saldo >= 500 THEN nivel = 'MEDIO';\n"
        "ELSE nivel = 'BAJO';\nRUN;"
    )
    esquema = {"work.saldos": [Column("id", "String"), Column("saldo", "Double")]}

    resultado = plan_a_jobs(plan, esquema)

    assert not resultado.pendientes, resultado.pendientes
    datos = _tmap(resultado.jobs[0])
    assert "2000" in datos and "500" in datos, datos
    assert datos.index("2000") < datos.index("500")
    assert all(f"&quot;{valor}&quot;" in datos for valor in ("ALTO", "MEDIO", "BAJO"))


def test_output_explicito_sin_condicion_se_emite_como_una_salida_tmap():
    plan = _plan(
        "PROC IMPORT DATAFILE='entrada.csv' OUT=WORK.entrada DBMS=CSV REPLACE;\n"
        "GETNAMES=YES;\nRUN;\n"
        "DATA salida;\nSET entrada;\nOUTPUT salida;\nRUN;"
    )
    esquema = {"work.entrada": [Column("id", "String")]}

    resultado = plan_a_jobs(plan, esquema)

    assert not [p for p in resultado.pendientes if p.codigo == "P-OPERADOR-SIN-SOPORTE"]
    assert 'name="out1"' in _tmap(resultado.jobs[0])


def test_output_no_declarado_no_emite_escritura_parcial():
    plan = _plan(
        "PROC IMPORT DATAFILE='entrada.csv' OUT=WORK.entrada DBMS=CSV REPLACE;\n"
        "GETNAMES=YES;\nRUN;\n"
        "DATA WORK.declarada;\n"
        "SET WORK.entrada;\n"
        "OUTPUT WORK.no_declarada;\n"
        "RUN;"
    )
    esquema = {"work.entrada": [Column("id", "String")]}

    resultado = plan_a_jobs(plan, esquema)

    assert any(p.codigo == "P-OPERADOR-SIN-SOPORTE" for p in resultado.pendientes)
    assert not any(
        nodo.componente == "tFileOutputDelimited" for job in resultado.jobs for nodo in job.nodos
    )


def test_output_condicional_no_terminal_emite_salidas_y_continuacion():
    plan = _plan(
        "PROC IMPORT DATAFILE='entrada.csv' OUT=WORK.entrada DBMS=CSV REPLACE;\n"
        "GETNAMES=YES;\nRUN;\n"
        "DATA WORK.temprano WORK.tarde WORK.final;\n"
        "SET WORK.entrada;\n"
        "IF valor=1 THEN OUTPUT WORK.temprano;\n"
        "ELSE OUTPUT WORK.tarde;\n"
        "valor=valor+10;\n"
        "OUTPUT WORK.final;\n"
        "RUN;\n"
        "PROC EXPORT DATA=WORK.temprano OUTFILE='temprano.csv' DBMS=CSV REPLACE; RUN;\n"
        "PROC EXPORT DATA=WORK.tarde OUTFILE='tarde.csv' DBMS=CSV REPLACE; RUN;\n"
        "PROC EXPORT DATA=WORK.final OUTFILE='final.csv' DBMS=CSV REPLACE; RUN;"
    )
    esquema = {"work.entrada": [Column("valor", "Long")]}

    resultado = plan_a_jobs(plan, esquema)

    assert not [p for p in resultado.pendientes if p.codigo == "P-OPERADOR-SIN-SOPORTE"]
    job = resultado.jobs[0]
    assert sum(nodo.componente == "tFileOutputDelimited" for nodo in job.nodos) == 3
    assert validar_job(job) == []


def test_output_con_destino_repetido_en_sentencias_distintas_queda_pendiente():
    plan = _plan(
        "DATA primera segunda tercera;\n"
        "SET entrada;\n"
        "OUTPUT primera segunda;\n"
        "OUTPUT segunda tercera;\n"
        "RUN;"
    )

    (pendiente,) = [
        operador for operador in plan.graph.operators() if operador.kind == "unsupported"
    ]
    assert pendiente.params["reason_detail"] == "OUTPUT_DESTINO_REPETIDO"
    assert not [operador for operador in plan.graph.operators() if operador.kind == "split"]


def test_output_con_varios_destinos_emite_un_tmap_con_todas_las_salidas():
    plan = _plan(
        "PROC IMPORT DATAFILE='entrada.csv' OUT=WORK.entrada DBMS=CSV REPLACE;\n"
        "GETNAMES=YES;\nRUN;\n"
        "DATA WORK.primera WORK.segunda;\n"
        "SET WORK.entrada;\n"
        "OUTPUT WORK.primera WORK.segunda;\n"
        "RUN;\n"
        "PROC EXPORT DATA=WORK.primera OUTFILE='primera.csv' DBMS=CSV REPLACE;\nRUN;\n"
        "PROC EXPORT DATA=WORK.segunda OUTFILE='segunda.csv' DBMS=CSV REPLACE;\nRUN;"
    )
    esquema = {"work.entrada": [Column("id", "String")]}

    resultado = plan_a_jobs(plan, esquema)

    assert not [p for p in resultado.pendientes if p.codigo == "P-OPERADOR-SIN-SOPORTE"]
    assert len(resultado.jobs) == 1
    tmap = _tmap(resultado.jobs[0])
    assert 'name="out1"' in tmap
    assert 'name="out2"' in tmap
    assert 'name="id" expression="row1.id"' in tmap
    assert sum(nodo.componente == "tFileOutputDelimited" for nodo in resultado.jobs[0].nodos) == 2
    assert {conexion.nombre for conexion in resultado.jobs[0].conexiones} >= {"out1", "out2"}


def test_varias_sentencias_output_contiguas_distintas_se_emiten_como_tmap():
    plan = _plan(
        "PROC IMPORT DATAFILE='entrada.csv' OUT=WORK.entrada DBMS=CSV REPLACE;\n"
        "GETNAMES=YES;\nRUN;\n"
        "DATA WORK.primera WORK.segunda;\n"
        "SET WORK.entrada;\n"
        "OUTPUT WORK.primera;\n"
        "OUTPUT WORK.segunda;\n"
        "RUN;"
    )
    esquema = {"work.entrada": [Column("id", "String")]}

    resultado = plan_a_jobs(plan, esquema)

    assert not [p for p in resultado.pendientes if p.codigo == "P-OPERADOR-SIN-SOPORTE"]
    assert all(f'name="out{indice}"' in _tmap(resultado.jobs[0]) for indice in (1, 2))


def test_output_repetido_al_mismo_destino_sigue_pendiente():
    plan = _plan(
        "PROC IMPORT DATAFILE='entrada.csv' OUT=WORK.entrada DBMS=CSV REPLACE;\n"
        "GETNAMES=YES;\nRUN;\n"
        "DATA WORK.primera;\n"
        "SET WORK.entrada;\n"
        "OUTPUT WORK.primera;\n"
        "OUTPUT WORK.primera;\n"
        "RUN;"
    )
    esquema = {"work.entrada": [Column("id", "String")]}

    resultado = plan_a_jobs(plan, esquema)

    assert any(
        pendiente.codigo == "P-OPERADOR-SIN-SOPORTE"
        and "OUTPUT escribe más de una vez" in pendiente.mensaje
        for pendiente in resultado.pendientes
    )


def test_output_if_else_emite_ramas_filtradas_en_un_tmap():
    plan = _plan(
        "PROC IMPORT DATAFILE='entrada.csv' OUT=WORK.entrada DBMS=CSV REPLACE;\n"
        "GETNAMES=YES;\nRUN;\n"
        "DATA WORK.uno WORK.dos WORK.otros;\n"
        "SET WORK.entrada;\n"
        "IF valor = 1 THEN OUTPUT WORK.uno WORK.dos;\n"
        "ELSE OUTPUT WORK.otros;\n"
        "RUN;"
    )
    esquema = {"work.entrada": [Column("valor", "Long")]}

    resultado = plan_a_jobs(plan, esquema)

    assert not [
        pendiente
        for pendiente in resultado.pendientes
        if pendiente.codigo in {"P-OPERADOR-SIN-SOPORTE", "P-FILTRO-SIN-TRADUCIR"}
    ]
    tmap = _tmap(resultado.jobs[0])
    assert all(f'name="out{indice}"' in tmap for indice in (1, 2, 3))
    assert "row1.valor" in tmap
    assert "activateExpressionFilter=\"true\"" in tmap


def test_output_if_sin_else_emite_una_salida_filtrada_en_tmap():
    plan = _plan(
        "PROC IMPORT DATAFILE='entrada.csv' OUT=WORK.entrada DBMS=CSV REPLACE;\n"
        "GETNAMES=YES;\nRUN;\n"
        "DATA WORK.coinciden;\n"
        "SET WORK.entrada;\n"
        "IF valor = 1 THEN OUTPUT WORK.coinciden;\n"
        "RUN;"
    )
    esquema = {"work.entrada": [Column("valor", "Long")]}

    resultado = plan_a_jobs(plan, esquema)

    assert not [
        pendiente
        for pendiente in resultado.pendientes
        if pendiente.codigo in {"P-OPERADOR-SIN-SOPORTE", "P-FILTRO-SIN-TRADUCIR"}
    ]
    tmap = _tmap(resultado.jobs[0])
    assert 'name="out1"' in tmap
    assert "activateExpressionFilter=\"true\"" in tmap
    assert "row1.valor" in tmap


def test_output_condicional_sin_destino_emite_todas_las_salidas_filtradas():
    plan = _plan(
        "PROC IMPORT DATAFILE='entrada.csv' OUT=WORK.entrada DBMS=CSV REPLACE;\n"
        "GETNAMES=YES;\nRUN;\n"
        "DATA WORK.primera WORK.segunda;\n"
        "SET WORK.entrada;\n"
        "IF valor=1 THEN OUTPUT;\n"
        "RUN;\n"
        "PROC EXPORT DATA=WORK.primera OUTFILE='primera.csv' DBMS=CSV REPLACE; RUN;\n"
        "PROC EXPORT DATA=WORK.segunda OUTFILE='segunda.csv' DBMS=CSV REPLACE; RUN;"
    )
    esquema = {"work.entrada": [Column("valor", "Long")]}

    resultado = plan_a_jobs(plan, esquema)

    assert not [p for p in resultado.pendientes if p.codigo == "P-OPERADOR-SIN-SOPORTE"]
    job = resultado.jobs[0]
    assert sum(nodo.componente == "tFileOutputDelimited" for nodo in job.nodos) == 2
    assert _tmap(job).count('activateExpressionFilter="true"') == 2
    assert validar_job(job) == []


def test_output_condicional_sin_destino_no_terminal_emite_ramas_y_continuacion():
    plan = _plan(
        "PROC IMPORT DATAFILE='entrada.csv' OUT=WORK.entrada DBMS=CSV REPLACE;\n"
        "GETNAMES=YES;\nRUN;\n"
        "DATA WORK.primera WORK.segunda;\n"
        "SET WORK.entrada;\n"
        "IF valor=1 THEN OUTPUT;\n"
        "valor=valor+10;\n"
        "RUN;\n"
        "PROC EXPORT DATA=WORK.primera OUTFILE='primera.csv' DBMS=CSV REPLACE; RUN;\n"
        "PROC EXPORT DATA=WORK.segunda OUTFILE='segunda.csv' DBMS=CSV REPLACE; RUN;"
    )
    esquema = {"work.entrada": [Column("valor", "Long")]}

    resultado = plan_a_jobs(plan, esquema)

    assert not [p for p in resultado.pendientes if p.codigo == "P-OPERADOR-SIN-SOPORTE"]
    job = resultado.jobs[0]
    assert sum(nodo.componente == "tFileOutputDelimited" for nodo in job.nodos) == 2
    assert validar_job(job) == []


def test_output_sin_destino_intermedio_emite_todas_las_salidas_sin_duplicar_filas():
    plan = _plan(
        "PROC IMPORT DATAFILE='entrada.csv' OUT=WORK.entrada DBMS=CSV REPLACE;\n"
        "GETNAMES=YES;\nRUN;\n"
        "DATA WORK.primera WORK.segunda;\n"
        "SET WORK.entrada;\n"
        "OUTPUT;\n"
        "valor=valor+10;\n"
        "RUN;\n"
        "PROC EXPORT DATA=WORK.primera OUTFILE='primera.csv' DBMS=CSV REPLACE; RUN;\n"
        "PROC EXPORT DATA=WORK.segunda OUTFILE='segunda.csv' DBMS=CSV REPLACE; RUN;"
    )
    esquema = {"work.entrada": [Column("valor", "Long")]}

    resultado = plan_a_jobs(plan, esquema)

    assert not [p for p in resultado.pendientes if p.codigo == "P-OPERADOR-SIN-SOPORTE"]
    job = resultado.jobs[0]
    assert sum(nodo.componente == "tFileOutputDelimited" for nodo in job.nodos) == 2
    assert validar_job(job) == []


def test_output_else_if_encadenado_emite_filtros_priorizados_en_tmap():
    plan = _plan(
        "PROC IMPORT DATAFILE='entrada.csv' OUT=WORK.entrada DBMS=CSV REPLACE;\n"
        "GETNAMES=YES;\nRUN;\n"
        "DATA WORK.uno WORK.dos WORK.otros;\n"
        "SET WORK.entrada;\n"
        "IF valor >= 1 THEN OUTPUT WORK.uno;\n"
        "ELSE IF valor >= 2 THEN OUTPUT WORK.dos;\n"
        "ELSE OUTPUT WORK.otros;\n"
        "RUN;"
    )
    esquema = {"work.entrada": [Column("valor", "Long")]}

    resultado = plan_a_jobs(plan, esquema)

    assert not [
        pendiente
        for pendiente in resultado.pendientes
        if pendiente.codigo in {"P-OPERADOR-SIN-SOPORTE", "P-FILTRO-SIN-TRADUCIR"}
    ]
    tmap = _tmap(resultado.jobs[0])
    assert all(f'name="out{indice}"' in tmap for indice in (1, 2, 3))
    assert tmap.count('activateExpressionFilter="true"') == 3


def test_output_sin_destinos_emite_todas_las_salidas_del_encabezado():
    plan = _plan(
        "PROC IMPORT DATAFILE='entrada.csv' OUT=WORK.entrada DBMS=CSV REPLACE;\n"
        "GETNAMES=YES;\nRUN;\n"
        "DATA WORK.primera WORK.segunda;\n"
        "SET WORK.entrada;\n"
        "OUTPUT;\n"
        "RUN;"
    )
    esquema = {"work.entrada": [Column("id", "String")]}

    resultado = plan_a_jobs(plan, esquema)

    assert not [
        pendiente
        for pendiente in resultado.pendientes
        if pendiente.codigo == "P-OPERADOR-SIN-SOPORTE"
    ]
    assert all(
        f'name="out{indice}"' in _tmap(resultado.jobs[0]) for indice in (1, 2)
    )


def test_l6_13_output_multiple_destinos_emite_el_mismo_enrutamiento_del_corpus():
    programa = (
        Path(__file__).resolve().parents[1]
        / "corpus"
        / "L6"
        / "l6_13_output_multiple_destinos"
        / "programa.sas"
    )
    plan = _plan(programa.read_text(encoding="utf-8"))
    esquema = {"work.registros": [Column("id", "String"), Column("valor", "Long")]}

    resultado = plan_a_jobs(plan, esquema)

    assert not [
        pendiente
        for pendiente in resultado.pendientes
        if pendiente.codigo in {"P-OPERADOR-SIN-SOPORTE", "P-FILTRO-SIN-TRADUCIR"}
    ]
    assert sum(nodo.componente == "tFileOutputDelimited" for nodo in resultado.jobs[0].nodos) == 3
    assert all(f'name="out{indice}"' in _tmap(resultado.jobs[0]) for indice in (1, 2, 3))


def test_l6_14_output_en_puntos_del_pdv_conserva_el_orden_y_dos_salidas():
    programa = (
        Path(__file__).resolve().parents[1]
        / "corpus"
        / "L6"
        / "l6_14_output_en_puntos_del_pdv"
        / "programa.sas"
    )
    plan = _plan(programa.read_text(encoding="utf-8"))
    esquema = {"work.registros": [Column("id", "String"), Column("valor", "Long")]}

    resultado = plan_a_jobs(plan, esquema)

    assert not [p for p in resultado.pendientes if p.codigo == "P-OPERADOR-SIN-SOPORTE"]
    job = resultado.jobs[0]
    mapas = [nodo.datos for nodo in job.nodos if nodo.componente == "tMap"]
    assert len(mapas) >= 3
    assert 'name="valor" expression="row1.valor"' in mapas[0]
    assert 'name="valor" expression="(row2.valor + 10)"' in mapas[1]
    assert sum(nodo.componente == "tFileOutputDelimited" for nodo in job.nodos) == 2
    assert any(nodo.componente == "tReplicate" for nodo in job.nodos)
    assert validar_job(job) == []


def test_asignacion_condicional_numerica_derivada_queda_pendiente_por_faltante_sas():
    plan = _plan(
        "PROC IMPORT DATAFILE='entrada.csv' OUT=WORK.productos DBMS=CSV REPLACE;\n"
        "GETNAMES=YES;\nRUN;\n"
        "DATA bandera;\nSET productos;\n"
        "valor = precio * stock;\nIF valor > 2000 THEN grande = 1;\n"
        "ELSE grande = 0;\nRUN;"
    )
    esquema = {
        "work.productos": [
            Column("codigo", "String"),
            Column("precio", "Double"),
            Column("stock", "Double"),
        ]
    }

    resultado = plan_a_jobs(plan, esquema)

    assert len(resultado.pendientes) == 1
    assert resultado.pendientes[0].codigo == "P-FILTRO-SIN-TRADUCIR"
    assert "primitivo" in resultado.pendientes[0].mensaje
    datos = _tmap(resultado.jobs[0])
    assert 'name="valor"' in datos
    assert 'name="grande"' not in datos


@pytest.mark.parametrize(
    ("seleccion", "esperadas", "excluidas"),
    [
        ("KEEP id saldo;", ("id", "saldo"), ("secreto",)),
        ("DROP secreto;", ("id", "saldo"), ("secreto",)),
    ],
)
def test_data_step_keep_drop_limita_esquema_de_salida(seleccion, esperadas, excluidas):
    plan = _plan(
        "PROC IMPORT DATAFILE='entrada.csv' OUT=WORK.privadas DBMS=CSV REPLACE;\n"
        "GETNAMES=YES;\nRUN;\n"
        f"DATA publicas;\nSET privadas;\ntotal = saldo * 2;\n{seleccion}\nRUN;"
    )
    esquema = {
        "work.privadas": [
            Column("id", "String"),
            Column("saldo", "Double"),
            Column("secreto", "String"),
        ]
    }

    job = _job(plan, esquema)
    datos = _tmap(job)
    salida = datos.partition("<outputTables")[2].partition("</outputTables>")[0]

    assert all(f'name="{nombre}"' in salida for nombre in esperadas)
    assert all(f'name="{nombre}"' not in salida for nombre in excluidas)


def test_data_step_rename_emite_nuevo_nombre_y_expresion_de_origen():
    plan = _plan(
        "PROC IMPORT DATAFILE='entrada.csv' OUT=WORK.privadas DBMS=CSV REPLACE;\n"
        "GETNAMES=YES;\nRUN;\n"
        "DATA publicas;\nSET privadas;\ntotal = saldo * 2;\nRENAME saldo=balance;\nRUN;"
    )
    esquema = {"work.privadas": [Column("id", "String"), Column("saldo", "Double")]}

    job = _job(plan, esquema)
    datos = _tmap(job)
    salida = datos.partition("<outputTables")[2].partition("</outputTables>")[0]

    assert 'name="balance"' in salida
    assert 'expression="row1.saldo"' in salida
    assert 'name="saldo"' not in salida


def test_set_where_option_emite_filtro_en_tmap():
    programa = (RAIZ / "L0" / "l0_02_where_opcion" / "programa.sas").read_text(
        encoding="utf-8"
    )
    plan = _plan(programa)
    esquema = {
        "work.clientes": [
            Column("id_cliente", "String"),
            Column("nombre", "String"),
            Column("ciudad", "String"),
            Column("saldo", "Double"),
            Column("estado", "String"),
        ]
    }

    job = _job(plan, esquema)
    datos = _tmap(job)

    assert "outputTables" in datos, datos
    assert "expressionFilter=" in datos
    assert "row1.estado" in datos
    assert "ACTIVO" in datos


def test_subsetting_if_emite_filtro_nulo_seguro_para_numeros():
    plan = _plan(
        "PROC IMPORT DATAFILE='entrada.csv' OUT=WORK.valores DBMS=CSV REPLACE;\n"
        "GETNAMES=YES;\nRUN;\n"
        "DATA seleccionados;\nSET valores;\nIF cantidad;\nRUN;"
    )
    esquema = {"work.valores": [Column("id", "String"), Column("cantidad", "Double")]}

    resultado = plan_a_jobs(plan, esquema)
    assert not resultado.pendientes, resultado.pendientes
    datos = _tmap(resultado.jobs[0])

    assert "expressionFilter=" in datos
    assert "row1.cantidad" in datos
    assert "null" in datos


@pytest.mark.parametrize(
    ("sentencia", "esperadas"),
    [
        ("KEEP id saldo;", ("id", "saldo")),
        ("DROP secreto;", ("id", "saldo")),
        ("RENAME saldo=balance;", ("id", "balance")),
    ],
)
def test_data_step_modificador_aislado_emite_tmap(sentencia, esperadas):
    plan = _plan(
        "PROC IMPORT DATAFILE='entrada.csv' OUT=WORK.privadas DBMS=CSV REPLACE;\n"
        "GETNAMES=YES;\nRUN;\n"
        f"DATA publicas;\nSET privadas;\n{sentencia}\nRUN;"
    )
    esquema = {
        "work.privadas": [
            Column("id", "String"),
            Column("saldo", "Double"),
            Column("secreto", "String"),
        ]
    }

    resultado = plan_a_jobs(plan, esquema)
    assert not resultado.pendientes, resultado.pendientes
    salida = _tmap(resultado.jobs[0]).partition("<outputTables")[2].partition(
        "</outputTables>"
    )[0]

    assert all(f'name="{nombre}"' in salida for nombre in esperadas)


@pytest.mark.skipif(shutil.which("javac") is None, reason="sin JDK para compilar la expresión")
def test_el_filtro_compila_con_javac(tmp_path):
    plan = _plan(CON_SALDO)
    esquema = {"work.clientes": [Column("id_cliente", "Integer"), Column("saldo", "Integer")]}
    filtro = _filtro_de(_job(plan, esquema)).replace("&lt;", "<").replace("&gt;", ">")

    clase = tmp_path / "Prueba.java"
    clase.write_text(
        "public class Prueba {\n"
        "  static class Row { Integer id_cliente; Integer saldo; }\n"
        f"  static boolean filtra(Row row1) {{ return {filtro}; }}\n"
        "  public static void main(String[] a) {\n"
        "    Row nula = new Row();\n"
        "    if (!filtra(nula)) throw new IllegalStateException(\"el faltante debe pasar\");\n"
        "  }\n"
        "}\n",
        encoding="utf-8",
    )
    compilado = subprocess.run(
        ["javac", "-d", str(tmp_path), str(clase)], capture_output=True, text=True
    )
    assert compilado.returncode == 0, compilado.stderr
    ejecutado = subprocess.run(
        ["java", "-cp", str(tmp_path), "Prueba"], capture_output=True, text=True
    )
    assert ejecutado.returncode == 0, ejecutado.stderr


def test_un_select_sin_calificar_arma_el_job_completo():
    """`select a, b from work.clientes`: la columna suelta se resuelve porque hay una sola tabla."""
    plan = _plan((RAIZ / "L1" / "l1_01_select_columnas" / "programa.sas").read_text(encoding="utf-8"))

    resultado = plan_a_jobs(plan, esquemas_de_entrada(plan, {}, None)[0])

    assert resultado.pendientes == []
    assert _componentes(resultado.jobs[0]) == ["tFileInputDelimited", "tMap"]
    assert 'expression="row1.saldo"' in _tmap(resultado.jobs[0])


def test_l2_07_emite_la_salida_not_in_como_rechazo_inner():
    plan = _caso("l2_07_not_in_subconsulta")
    esquemas, _ = esquemas_de_entrada(plan, {}, None)

    resultado = plan_a_jobs(plan, esquemas)
    rechazo = [
        nodo.datos
        for job in resultado.jobs
        for nodo in job.nodos
        if nodo.componente == "tMap" and 'rejectInnerJoin="true"' in nodo.datos
    ]

    assert resultado.pendientes == []
    assert len(rechazo) == 1
    assert 'innerJoin="true"' in rechazo[0]


def test_un_operador_que_falla_no_detiene_a_los_demas(monkeypatch):
    """Un `tMap` que revienta deja su pendiente y el Job conserva lectura y escritura.

    El fallo se provoca en `tmap` —el montaje del nodo— y no en `construir`: así se comprueba lo
    peor, que el nodo no se puede montar, y aun así el esquema de la salida se conoce porque lo
    demuestra el `SELECT`.
    """
    plan = _caso("l2_01_inner_join_clientes_ventas")

    def revienta(*args, **kwargs):
        raise RuntimeError("mapper sin salida")

    monkeypatch.setattr(desde_plan_map, "tmap", revienta)

    resultado = plan_a_jobs(plan, esquemas_de_entrada(plan, {}, None)[0])

    assert sorted(_componentes(resultado.jobs[0])) == [
        "tFileInputDelimited",
        "tFileInputDelimited",
        "tFileOutputDelimited",
    ]
    fallos = [p for p in resultado.pendientes if p.codigo == "P-FALLO-INTERNO"]
    assert len(fallos) == 1
    assert fallos[0].linea == 15
    assert "mapper sin salida" in fallos[0].mensaje


def test_la_misma_tabla_leida_dos_veces_se_lee_una_vez_y_se_reparte():
    """Dos `PROC SQL` sobre la misma tabla son una lectura y un `tReplicate`, no dos lecturas.

    En Talend cada salida de un nodo tiene nombre y dueño: dos conexiones desde el mismo componente
    no existen. Antes el Job leía el archivo una vez por consumidor; ahora lo lee una vez y reparte
    las filas, que es lo que hace una persona.
    """
    plan = _caso("l2_04_validacion_tipo_doc")

    job = _job(plan)

    lecturas = [nodo for nodo in job.nodos if nodo.componente == "tFileInputDelimited"]
    repartos = [nodo for nodo in job.nodos if nodo.componente == "tReplicate"]
    assert len(lecturas) == 2  # dos tablas
    assert len(repartos) == 2  # cada una con dos consumidores
    salidas = [(c.origen, c.nombre) for c in job.conexiones]
    assert len(salidas) == len(set(salidas))
    for nodo in lecturas:
        destinos = [c.destino for c in job.conexiones if c.origen == nodo.unico]
        assert len(destinos) == 1 and destinos[0].startswith("tReplicate")
    for nodo in repartos:
        assert sum(1 for c in job.conexiones if c.origen == nodo.unico) == 2
    assert validar_job(job) == []


def test_una_tabla_cuyas_ramas_se_vuelven_a_juntar_se_lee_una_vez_por_rama():
    """`l2_15` usa `operaciones` como fila principal de dos mapas, y el resultado del primero entra
    como consulta del segundo. Talend no admite que un flujo repartido vuelva al mismo componente:
    ahí no hay `tReplicate` y la tabla se lee una vez por rama."""
    job = _job(_caso("l2_15_validacion_en_cascada"))

    lecturas = [nodo for nodo in job.nodos if nodo.componente == "tFileInputDelimited"]
    assert len(lecturas) == 4  # tres tablas; `operaciones`, dos veces
    assert not [nodo for nodo in job.nodos if nodo.componente == "tReplicate"]
    assert validar_job(job) == []


def test_los_nombres_de_fila_y_de_salida_no_se_repiten_entre_los_tmap_del_job():
    """El nombre de una conexión es el de su clase en el Java generado: `row1` no puede estar en
    dos `tMap` del mismo Job."""
    job = _job(_caso("l2_07_not_in_subconsulta"))

    nombres = [c.nombre for c in job.conexiones]
    assert len(nombres) == len(set(nombres))
    assert [n.componente for n in job.nodos].count("tFileInputDelimited") == 2
    assert [n.componente for n in job.nodos].count("tUniqRow") == 1


def test_un_mapa_con_ramas_es_un_tmap_con_una_salida_filtrada_por_rama(tmp_path):
    """`l3_07`: dos `WHERE` distintos sobre la misma tabla. Un solo `tMap` con dos salidas, cada
    una con su condición y su propio consumidor."""
    from sgm.cli_migrar import migrar

    caso = CORPUS.parent / "L3" / "l3_07_total_origen_y_salida"
    resultado = migrar(caso / "programa.sas", tmp_path, muestra=caso / "entradas")
    (job,) = resultado.jobs

    (mapa,) = [nodo for nodo in job.nodos if nodo.componente == "tMap"]
    salidas = [c for c in job.conexiones if c.origen == mapa.unico]
    assert len(salidas) == 2
    assert len({c.destino for c in salidas}) == 2
    assert all(c.destino.startswith("tAggregateRow") for c in salidas)
    texto = next(tmp_path.rglob("*.item")).read_text(encoding="utf-8")
    assert texto.count("expressionFilter=") == 2
    assert validar_job(job) == []

def test_data_step_if_then_do_else_emite_asignaciones_y_conserva_columna():
    plan = _plan(
        "PROC IMPORT DATAFILE='entrada.csv' OUT=WORK.saldos DBMS=CSV REPLACE;\n"
        "GETNAMES=YES;\nRUN;\n"
        "DATA clasificados;\nSET saldos;\n"
        "IF saldo < 0 THEN DO;\n"
        "revision = 'SI';\nsaldo = 0;\nEND;\n"
        "ELSE revision = 'NO';\nRUN;"
    )
    esquema = {"work.saldos": [Column("id", "String"), Column("saldo", "Double")]}

    resultado = plan_a_jobs(plan, esquema)

    assert not resultado.pendientes, resultado.pendientes
    datos = _tmap(resultado.jobs[0])
    assert 'name="saldo"' in datos and 'name="revision"' in datos
    assert (
        '<mapperTableEntries name="saldo" '
        'expression="((row1.saldo == null || row1.saldo &lt; 0) ? 0 : row1.saldo)" '
        'type="id_Double" nullable="true"/>' in datos
    )
    assert '&quot;SI&quot;' in datos and '&quot;NO&quot;' in datos

def test_data_step_condicional_conserva_tipo_fuente_tras_asignacion_previa():
    plan = _plan(
        "PROC IMPORT DATAFILE='entrada.csv' OUT=WORK.saldos DBMS=CSV REPLACE;\n"
        "GETNAMES=YES;\nRUN;\n"
        "DATA clasificados;\nSET saldos;\n"
        "saldo = 0;\n"
        "IF bandera > 0 THEN DO;\nsaldo = 1;\nEND;\n"
        "ELSE saldo = saldo;\nRUN;"
    )
    esquema = {
        "work.saldos": [
            Column("id", "String"),
            Column("saldo", "Double"),
            Column("bandera", "Integer"),
        ]
    }

    resultado = plan_a_jobs(plan, esquema)

    assert not resultado.pendientes, resultado.pendientes
    datos = _tmap(resultado.jobs[0])
    salida_saldo = next(
        linea
        for linea in datos.splitlines()
        if '<mapperTableEntries name="saldo" expression=' in linea
    )
    assert 'type="id_Double"' in salida_saldo
