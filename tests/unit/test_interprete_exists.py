"""EXISTS y NOT EXISTS correlacionados de una igualdad en el intérprete (plan C, C-9).

Con llaves presentes se resuelven como pertenencia. Con un faltante en alguna llave se rechazan: la
guía no dice si un faltante es igual a otro (lrcon, p. 154).
"""

from __future__ import annotations

import pytest

from sgm.cli_migrar import ResultadoMigrar, _plan
from sgm.migrar.interprete import ejecutar_plan
from sgm.migrar.interprete_base import NoSoportadoEnInterprete

VENTAS = [{"id": "1", "monto": "10"}, {"id": "2", "monto": "30"}, {"id": "3", "monto": "20"}]
PAGOS = [{"id": "2", "cliente": "x"}, {"id": "9", "cliente": "y"}]


def _ejecutar(programa: str, tmp_path, ventas=VENTAS, pagos=PAGOS):
    plan = _plan(programa, "programa", ResultadoMigrar(carpeta=tmp_path))
    return ejecutar_plan(
        plan,
        {"ventas": [dict(f) for f in ventas], "pagos": [dict(f) for f in pagos]},
    )


def test_exists_deja_las_filas_con_pareja(tmp_path):
    programa = (
        "PROC SQL;\n"
        "  CREATE TABLE WORK.con_pago AS SELECT v.id, v.monto FROM WORK.ventas v "
        "WHERE EXISTS (SELECT 1 FROM WORK.pagos p WHERE p.id = v.id);\n"
        "QUIT;\n"
    )
    assert [f["id"] for f in _ejecutar(programa, tmp_path)["con_pago"]] == ["2"]


def test_not_exists_deja_las_filas_sin_pareja(tmp_path):
    programa = (
        "PROC SQL;\n"
        "  CREATE TABLE WORK.sin_pago AS SELECT v.id FROM WORK.ventas v "
        "WHERE NOT EXISTS (SELECT 1 FROM WORK.pagos p WHERE p.id = v.id);\n"
        "QUIT;\n"
    )
    assert [f["id"] for f in _ejecutar(programa, tmp_path)["sin_pago"]] == ["1", "3"]


def test_faltante_en_la_llave_externa_se_rechaza(tmp_path):
    programa = (
        "PROC SQL;\n"
        "  CREATE TABLE WORK.con_pago AS SELECT v.id FROM WORK.ventas v "
        "WHERE EXISTS (SELECT 1 FROM WORK.pagos p WHERE p.id = v.id);\n"
        "QUIT;\n"
    )
    ventas = [{"id": "", "monto": "10"}, {"id": "2", "monto": "30"}]
    with pytest.raises(NoSoportadoEnInterprete):
        _ejecutar(programa, tmp_path, ventas=ventas)


def test_faltante_en_la_llave_interna_se_rechaza(tmp_path):
    programa = (
        "PROC SQL;\n"
        "  CREATE TABLE WORK.con_pago AS SELECT v.id FROM WORK.ventas v "
        "WHERE EXISTS (SELECT 1 FROM WORK.pagos p WHERE p.id = v.id);\n"
        "QUIT;\n"
    )
    pagos = [{"id": "", "cliente": "z"}]
    with pytest.raises(NoSoportadoEnInterprete):
        _ejecutar(programa, tmp_path, pagos=pagos)


def test_el_emisor_sigue_dejando_el_exists_pendiente(tmp_path):
    from sgm.talend_item.desde_plan import plan_a_jobs

    programa = (
        "PROC SQL;\n"
        "  CREATE TABLE WORK.con_pago AS SELECT v.id FROM WORK.ventas v "
        "WHERE EXISTS (SELECT 1 FROM WORK.pagos p WHERE p.id = v.id);\n"
        "QUIT;\n"
    )
    plan = _plan(programa, "programa", ResultadoMigrar(carpeta=tmp_path))

    resultado = plan_a_jobs(plan, {})

    # El EXISTS no tiene componente verificado: el pendiente lo dice y el Job no traduce el filtro.
    assert resultado.pendientes, "el EXISTS debe quedar pendiente, no traducido en silencio"
