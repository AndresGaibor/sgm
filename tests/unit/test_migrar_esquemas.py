"""Esquemas de las tablas de entrada sin ningún YAML.

Prioridad por tabla: catálogo del entorno, cabecera del archivo de muestra, columnas que el programa
usa aguas abajo. Lo que no se demuestra se queda en `String` —el tipo por omisión documentado— con su
pendiente `P-TIPO-DESCONOCIDO`: nunca se inventa un `Integer` ni una fecha.
"""

from __future__ import annotations

from pathlib import Path

from sgm.compile import compile_file, project_base
from sgm.frontend.program import analyze_program
from sgm.ir.models import Column, Plan
from sgm.migrar.esquemas import esquemas_de_entrada

CORPUS = Path(__file__).resolve().parents[1] / "corpus" / "L2"
RAIZ = Path(__file__).resolve().parents[1] / "corpus"


def _plan(caso: str) -> Plan:
    texto = (CORPUS / caso / "programa.sas").read_text(encoding="utf-8")
    analysis = analyze_program({"p.sas": texto})
    return compile_file(analysis, "p.sas", project_base()).plan


def _plan_de(nivel: str, caso: str) -> Plan:
    texto = (RAIZ / nivel / caso / "programa.sas").read_text(encoding="utf-8")
    analysis = analyze_program({"p.sas": texto})
    return compile_file(analysis, "p.sas", project_base()).plan


def _nombres(columnas: list[Column]) -> list[str]:
    return [columna.name for columna in columnas]


def test_catalogo_tiene_prioridad():
    plan = _plan("l2_01_inner_join_clientes_ventas")
    catalogo = {
        "work.clientes": [
            Column("id_cliente", "Integer", source="catalog"),
            Column("nombre", "String", source="catalog"),
        ],
        "work.ventas": [Column("id_venta", "Long", source="catalog")],
    }

    esquemas, pendientes = esquemas_de_entrada(plan, catalogo, muestra=None)

    assert esquemas["work.clientes"] == catalogo["work.clientes"]
    assert esquemas["work.ventas"] == catalogo["work.ventas"]
    assert pendientes == []


def test_cabecera_de_la_muestra(tmp_path):
    (tmp_path / "clientes.csv").write_text("id;nombre\n1;Ana\n", encoding="utf-8")
    plan = _plan("l2_01_inner_join_clientes_ventas")

    esquemas, pendientes = esquemas_de_entrada(plan, {}, muestra=tmp_path)

    assert _nombres(esquemas["work.clientes"]) == ["id", "nombre"]
    assert {columna.source for columna in esquemas["work.clientes"]} == {"file_header"}
    # la muestra demuestra los tipos: id numérico y nombre carácter (PROC IMPORT, GUESSINGROWS)
    assert {c.name: c.type for c in esquemas["work.clientes"]} == {"id": "Double", "nombre": "String"}
    # queda solo el de work.ventas, que no tiene archivo: antes había uno por cada tabla
    assert [p.codigo for p in pendientes] == ["P-TIPO-DESCONOCIDO"]
    assert "work.ventas" in pendientes[0].mensaje


def test_columnas_usadas_aguas_abajo():
    plan = _plan("l2_01_inner_join_clientes_ventas")

    esquemas, _ = esquemas_de_entrada(plan, {}, muestra=None)

    assert {"id_venta", "monto", "id_cliente"} <= set(_nombres(esquemas["work.ventas"]))
    assert {"nombre", "id_cliente"} <= set(_nombres(esquemas["work.clientes"]))


def test_sin_tipo_demostrado_publica_pendiente():
    plan = _plan("l2_01_inner_join_clientes_ventas")

    _, pendientes = esquemas_de_entrada(plan, {}, muestra=None)

    assert [p.codigo for p in pendientes] == ["P-TIPO-DESCONOCIDO", "P-TIPO-DESCONOCIDO"]
    assert all(p.linea is not None for p in pendientes)
    assert "work.clientes" in pendientes[0].mensaje


def test_no_inventa_tipos():
    """Sin catálogo, el único tipo es el `String` por omisión, y cada tabla lleva su pendiente."""
    plan = _plan("l2_01_inner_join_clientes_ventas")

    esquemas, pendientes = esquemas_de_entrada(plan, {}, muestra=None)

    tipos = {columna.type for columnas in esquemas.values() for columna in columnas}
    assert tipos <= {"String"}
    assert len(pendientes) == len(esquemas)


def test_select_sin_calificar_da_las_columnas():
    """`select id_cliente, nombre, saldo from work.clientes` no califica, pero hay una sola tabla."""
    plan = _plan_de("L1", "l1_01_select_columnas")

    esquemas, _ = esquemas_de_entrada(plan, {}, muestra=None)

    assert _nombres(esquemas["work.clientes"]) == ["id_cliente", "nombre", "saldo"]


def test_expresion_da_las_columnas_que_usa():
    plan = _plan_de("L1", "l1_05_aritmetica_faltantes")

    esquemas, _ = esquemas_de_entrada(plan, {}, muestra=None)

    assert {"monto", "cantidad"} <= set(_nombres(esquemas["work.ventas"]))


def test_keep_da_las_columnas_que_conserva():
    plan = _plan_de("L0", "l0_03_keep")

    esquemas, _ = esquemas_de_entrada(plan, {}, muestra=None)

    assert _nombres(esquemas["work.clientes"]) == ["id_cliente", "nombre", "saldo"]


def test_dos_tablas_no_se_atribuyen_las_columnas_sueltas():
    """Con dos tablas en juego, `id_cliente` puede ser de cualquiera: no se atribuye a ciegas."""
    plan = _plan("l2_01_inner_join_clientes_ventas")

    esquemas, _ = esquemas_de_entrada(plan, {}, muestra=None)

    assert "id_cliente" in _nombres(esquemas["work.clientes"])
    assert "id_cliente" in _nombres(esquemas["work.ventas"])
    assert "monto" not in _nombres(esquemas["work.clientes"])




def test_la_aritmetica_demuestra_el_tipo_numerico():
    """`precio * stock` no deja dudas: en SAS solo se multiplican números.

    Sin catálogo, esas dos columnas salían `String` y el Job no compilaba en Studio
    (`bad operand types for binary operator '*'`). El programa demuestra el tipo; no se adivina.
    """
    plan = _plan_de("L0", "l0_06_asignacion")
    esquemas, _ = esquemas_de_entrada(plan, {}, muestra=None)

    tipos = {columna.name: columna.type for columnas in esquemas.values() for columna in columnas}
    assert tipos["precio"] == "Double"
    assert tipos["stock"] == "Double"


def test_coalesce_con_un_numero_demuestra_el_tipo():
    """`coalesce(monto, 0)` mezcla la columna con un número: la columna es numérica."""
    plan = _plan_de("L2", "l2_09_coalesce_tras_left_join")
    esquemas, _ = esquemas_de_entrada(plan, {}, muestra=None)

    tipos = {columna.name: columna.type for columnas in esquemas.values() for columna in columnas}
    assert tipos["monto"] == "Double"


def test_agregado_sql_demuestra_el_tipo_numerico_de_su_columna():
    texto = (
        "PROC IMPORT DATAFILE='entrada.csv' OUT=WORK.clientes DBMS=CSV REPLACE; "
        "GETNAMES=YES; RUN; "
        "PROC SQL; CREATE TABLE WORK.resumen AS "
        "SELECT SUM(saldo) AS total FROM WORK.clientes; QUIT;"
    )
    plan = compile_file(analyze_program({"p.sas": texto}), "p.sas", project_base()).plan

    esquemas, pendientes = esquemas_de_entrada(plan, {}, muestra=None)

    columnas = {columna.name: columna.type for columna in esquemas["work.clientes"]}
    assert columnas["saldo"] == "Double"
    assert not any("saldo" in pendiente.mensaje for pendiente in pendientes)


def test_el_pendiente_cuenta_solo_las_columnas_sin_tipo():
    plan = _plan_de("L0", "l0_06_asignacion")
    _, pendientes = esquemas_de_entrada(plan, {}, muestra=None)

    mensajes = [p.mensaje for p in pendientes]
    assert all("de" in mensaje for mensaje in mensajes), mensajes
    assert not any(": 0 de" in mensaje for mensaje in mensajes), mensajes
