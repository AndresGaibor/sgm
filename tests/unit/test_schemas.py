"""Pruebas de la pasada 9: esquemas desde el entorno y su propagación. Los datos son de ejemplo."""

import json

from sgm.catalog.schemas import load_schemas
from sgm.compile import compile_project


def _plan(text: str):
    compiled, _ = compile_project({"p.sas": text})
    return compiled["p.sas"].plan


def _last_with_schema(plan):
    ops = [o for o in plan.graph.operators() if o.schema is not None]
    return max(ops, key=lambda o: o.id)


def test_lectura_de_tabla_de_entorno_asigna_su_esquema():
    plan = _plan("data d; set ejemplo_lz.clientes; run;")
    names = {c.name: c.type for c in _last_with_schema(plan).schema}
    assert names["cliente_id"] == "Integer" and names["fecha_alta"] == "Date"


def test_keep_reduce_las_columnas_y_rename_las_renombra():
    plan = _plan(
        "data d; set ejemplo_lz.clientes; keep cliente_id nombre; rename nombre = nombre_cliente; run;"
    )
    assert [c.name for c in _last_with_schema(plan).schema] == ["cliente_id", "nombre_cliente"]


def test_derive_sin_tipo_genera_hueco_tipo_desconocido():
    plan = _plan("data d; set ejemplo_lz.clientes; z = saldo * 2; run;")
    columna = next(c for c in _last_with_schema(plan).schema if c.name == "z")
    assert columna.type is None and columna.source == "unknown"
    assert any(g.reason == "TIPO_DESCONOCIDO" for g in plan.gaps)


def test_merge_une_los_esquemas_sin_duplicar_columnas():
    plan = _plan(
        "data j; merge ejemplo_lz.clientes(in=a) ejemplo_lz.cuentas(in=b); by cliente_id; run;"
    )
    nombres = [c.name for c in _last_with_schema(plan).schema]
    assert nombres.count("cliente_id") == 1
    assert "cuenta_id" in nombres and "nombre" in nombres


def test_dataset_sin_esquema_no_inventa_columnas():
    plan = _plan("data d; set otra_lib.desconocida; run;")
    assert all(o.schema is None for o in plan.graph.operators() if o.kind == "read")


def test_load_schemas_marca_sin_tipo_como_desconocido(tmp_path):
    archivo = tmp_path / "schemas.json"
    archivo.write_text(
        json.dumps({"ejemplo_lz.x": [{"name": "a"}, {"name": "b", "type": "String"}]})
    )
    columnas = load_schemas(archivo)["ejemplo_lz.x"]
    assert [c.type for c in columnas] == [None, "String"]
