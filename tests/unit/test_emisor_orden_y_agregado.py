"""`ORDER BY`, `DISTINCT` y `GROUP BY` de `PROC SQL` llegan al Job como `tSortRow`, `tUniqRow` y
`tAggregateRow`, con el criterio que el SAS dice y con el faltante tratado como SAS.

Se migra un programa pequeño con su muestra y se mira el nodo que sale, no el texto del `.item`.
"""

from __future__ import annotations

from pathlib import Path

from sgm.cli_migrar import migrar
from sgm.talend_item.modelo import Nodo, Tabla
from sgm.talend_item.validador import validar_job

CLIENTES = "id,ciudad,saldo\n1,Cali,100\n2,Cali,\n3,Bogota,50\n"


def _migrar(tmp_path: Path, consulta: str):
    muestra = tmp_path / "muestra"
    muestra.mkdir()
    (muestra / "clientes.csv").write_text(CLIENTES, encoding="utf-8")
    programa = tmp_path / "p.sas"
    programa.write_text(
        "PROC IMPORT DATAFILE='.../clientes.csv' OUT=WORK.clientes DBMS=CSV REPLACE;\n"
        "  GETNAMES=YES;\nRUN;\n"
        f"PROC SQL;\n  CREATE TABLE WORK.salida AS\n  {consulta};\nQUIT;\n"
        "PROC EXPORT DATA=WORK.salida OUTFILE='.../salida.csv' DBMS=CSV REPLACE;\nRUN;\n",
        encoding="utf-8",
    )
    return migrar(programa, tmp_path / "out", muestra=muestra)


def _nodo(resultado, componente: str) -> Nodo:
    encontrados = [n for job in resultado.jobs for n in job.nodos if n.componente == componente]
    assert len(encontrados) == 1, [n.componente for job in resultado.jobs for n in job.nodos]
    return encontrados[0]


def _tabla(nodo: Nodo, nombre: str) -> tuple[tuple[str, str], ...]:
    return next(p.celdas for p in nodo.parametros if isinstance(p, Tabla) and p.nombre == nombre)


def _reales(resultado) -> list:
    return [p for p in resultado.pendientes if p.codigo != "P-TIPO-DESCONOCIDO"]


def _validos(resultado) -> None:
    for job in resultado.jobs:
        assert validar_job(job) == []


def test_order_by_descendente_es_un_criterio_por_columna(tmp_path):
    resultado = _migrar(tmp_path, "SELECT id, saldo FROM WORK.clientes ORDER BY saldo DESC, id")

    orden = _nodo(resultado, "tSortRow")

    # `saldo` no tiene tipo demostrado (el programa no opera con ella): se ordena como texto y el
    # `P-TIPO-DESCONOCIDO` ya lo avisa. Con un catálogo o una operación numérica sería `num`.
    assert _reales(resultado) == []
    assert _tabla(orden, "CRITERIA") == (
        ("COLNAME", "saldo"), ("SORT", "alpha"), ("ORDER", "desc"),
        ("COLNAME", "id"), ("SORT", "alpha"), ("ORDER", "asc"),
    )  # fmt: skip
    _validos(resultado)


def test_order_by_de_una_columna_que_no_existe_deja_el_nodo_pendiente(tmp_path):
    resultado = _migrar(tmp_path, "SELECT id FROM WORK.clientes ORDER BY sin_esa_columna")

    assert [n for job in resultado.jobs for n in job.nodos if n.componente == "tSortRow"] == []
    assert "P-ORDEN-COLUMNA-DESCONOCIDA" in {p.codigo for p in resultado.pendientes}


def test_distinct_usa_todas_las_columnas_del_select_como_llave(tmp_path):
    resultado = _migrar(tmp_path, "SELECT DISTINCT ciudad FROM WORK.clientes")

    unicos = _nodo(resultado, "tUniqRow")

    assert _reales(resultado) == []
    llaves = [v for c, v in _tabla(unicos, "UNIQUE_KEY") if c == "KEY_ATTRIBUTE"]
    assert llaves == ["true"]
    _validos(resultado)


def test_group_by_con_conteo_suma_y_minimo(tmp_path):
    resultado = _migrar(
        tmp_path,
        "SELECT ciudad, COUNT(*) AS n, COUNT(saldo) AS con_saldo, SUM(saldo) AS total"
        " FROM WORK.clientes GROUP BY ciudad",
    )

    agregado = _nodo(resultado, "tAggregateRow")

    assert _reales(resultado) == []
    assert _tabla(agregado, "GROUPBYS") == (("OUTPUT_COLUMN", "ciudad"), ("INPUT_COLUMN", "ciudad"))
    operaciones = _tabla(agregado, "OPERATIONS")
    # COUNT(*) cuenta filas (no ignora nulos); COUNT(col) y SUM ignoran el faltante, como SAS.
    assert operaciones == (
        ("OUTPUT_COLUMN", "n"), ("FUNCTION", "count"),
        ("INPUT_COLUMN", "id"), ("IGNORE_NULL", "false"),
        ("OUTPUT_COLUMN", "con_saldo"), ("FUNCTION", "count"),
        ("INPUT_COLUMN", "saldo"), ("IGNORE_NULL", "true"),
        ("OUTPUT_COLUMN", "total"), ("FUNCTION", "sum"),
        ("INPUT_COLUMN", "saldo"), ("IGNORE_NULL", "true"),
    )  # fmt: skip
    salida = agregado.metadatas[0].columnas if agregado.metadatas else agregado.columnas
    assert [(c.nombre, c.tipo) for c in salida] == [
        ("ciudad", "id_String"), ("n", "id_Long"), ("con_saldo", "id_Long"), ("total", "id_Double"),
    ]  # fmt: skip
    _validos(resultado)


def test_un_agregado_sin_group_by_no_tiene_tabla_de_grupos(tmp_path):
    resultado = _migrar(tmp_path, "SELECT MAX(saldo) AS mayor FROM WORK.clientes")

    agregado = _nodo(resultado, "tAggregateRow")

    assert not any(
        isinstance(p, Tabla) and p.nombre == "GROUPBYS" and p.celdas for p in agregado.parametros
    )
    assert _tabla(agregado, "OPERATIONS")[1] == ("FUNCTION", "max")


def test_una_expresion_sobre_agregados_agrega_cada_llamada_y_calcula_detras(tmp_path):
    resultado = _migrar(tmp_path, "SELECT COUNT(*) - COUNT(saldo) AS sin_saldo FROM WORK.clientes")

    agregado = _nodo(resultado, "tAggregateRow")
    llamadas = [v for c, v in _tabla(agregado, "OPERATIONS") if c == "OUTPUT_COLUMN"]

    assert _reales(resultado) == []
    assert llamadas == ["agg_1", "agg_2"]  # cada llamada se agrega por su cuenta
    assert any(n.componente == "tMap" for job in resultado.jobs for n in job.nodos)  # la resta
    _validos(resultado)


def test_una_subconsulta_escalar_como_agregado_queda_pendiente(tmp_path):
    resultado = _migrar(
        tmp_path, "SELECT (SELECT COUNT(*) FROM WORK.clientes) AS n FROM WORK.clientes"
    )

    assert [n for job in resultado.jobs for n in job.nodos if n.componente == "tAggregateRow"] == []
    assert "P-AGREGADO-SIN-TRADUCIR" in {p.codigo for p in resultado.pendientes}
