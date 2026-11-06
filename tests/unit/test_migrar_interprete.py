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
from sgm.ir.models import Plan
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


def _plan(texto: str) -> Plan:
    return compile_file(analyze_program({"p.sas": texto}), "p.sas", project_base()).plan


def _caso(nombre: str) -> Plan:
    texto = (CORPUS / nombre / "programa.sas").read_text(encoding="utf-8")
    return _plan(texto)


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


def test_un_operador_no_soportado_no_se_salta():
    """Un `sort` sin implementar detiene la ejecución con su nombre, no devuelve filas sin ordenar."""
    plan = _caso("l2_14_inner_join_where_orden")

    with pytest.raises(NoSoportadoEnInterprete) as error:
        ejecutar_plan(plan, {"clientes": [], "ventas": []})

    assert error.value.kind == "sort"
    assert str(error.value).startswith("sort")

