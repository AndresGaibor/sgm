"""Manifiestos y escritura reproducible de datos para rebanadas."""

import csv

import pytest

from sgm.ir.models import Column
from tools.datos_sinteticos.manifiesto import (
    Manifiesto,
    TablaDeDatos,
    generar_entradas,
    leer_manifiesto,
)
from tools.datos_sinteticos.requisitos import Requisitos, requisitos_de_rebanada


def test_generar_entradas_fijas_y_ficha_son_reproducibles(tmp_path):
    from tools.datos_sinteticos.ficha import leer_ficha

    req = requisitos_de_rebanada(
        "proc sql; select z.k from work.z z where z.k in ('1','2'); quit;"
    )
    manifest = Manifiesto(semilla=37, tablas={"work.z": TablaDeDatos(3, {"k": "7"})})
    schemas = {"work.z": [Column("k", "String", source="derived")]}
    first = tmp_path / "first"
    second = tmp_path / "second"
    paths = generar_entradas(req, schemas, manifest, first)
    again = generar_entradas(req, schemas, manifest, second)

    csv_path = first / "WORK.z.csv"
    ficha_path = first / "WORK.z.ficha.yaml"
    assert csv_path in paths and ficha_path in paths
    with csv_path.open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    assert [row["k"] for row in rows] == ["7", "7", "7"]
    ficha = leer_ficha(ficha_path)
    assert ficha.tabla == "work.z"
    assert ficha.origen == "sintetico" and ficha.semilla == 37
    assert ficha.columnas == {"k": "String"}
    assert csv_path.with_suffix(".ficha.yaml") == ficha_path
    assert {p.name.lower(): p.read_bytes() for p in paths} == {
        p.name.lower(): p.read_bytes() for p in again
    }


def test_generar_entradas_aplica_valores_fijos_por_fila(tmp_path):
    req = requisitos_de_rebanada(
        "proc sql; select t.year, t.month, t.day from lib.t t; quit;"
    )
    manifest = Manifiesto(
        semilla=37,
        tablas={
            "lib.t": TablaDeDatos(
                4,
                {"year": "2026"},
                ("year", "month", "day"),
                (
                    {"month": "9", "day": "2026-09-26"},
                    {"month": "9", "day": "2026-09-27"},
                    {"month": "9", "day": "2026-09-28"},
                    {"month": "8", "day": "2026-08-31"},
                ),
            )
        },
    )
    generar_entradas(
        req,
        {"lib.t": [Column(name, "String", source="fixture") for name in ("year", "month", "day")]},
        manifest,
        tmp_path,
    )

    with (tmp_path / "lib.t.csv").open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))

    assert [(row["month"], row["day"]) for row in rows] == [
        ("9", "2026-09-26"),
        ("9", "2026-09-27"),
        ("9", "2026-09-28"),
        ("8", "2026-08-31"),
    ]
    assert {row["year"] for row in rows} == {"2026"}


def test_generar_entradas_usa_esquema_de_tabla_base(tmp_path):
    req = requisitos_de_rebanada(
        "proc sql; create table work.y as select t.id from lib.t t; quit;"
    )
    assert req.tablas_base == {"lib.t": ["id"]}
    manifest = Manifiesto(semilla=8, tablas={"lib.t": TablaDeDatos(2)})
    paths = generar_entradas(
        req, {"lib.t": [Column("id", "Integer")]}, manifest, tmp_path
    )
    assert tmp_path / "lib.t.csv" in paths
    with (tmp_path / "lib.t.csv").open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == 2 and all(1 <= int(row["id"]) <= 1000 for row in rows)


def test_incluye_columnas_de_filtro_en_tabla_de_entrada(tmp_path):
    req = requisitos_de_rebanada(
        "proc sql; select t.id from lib.t t where status='A'; quit;"
    )
    manifest = Manifiesto(semilla=8, tablas={"lib.t": TablaDeDatos(2)})
    paths = generar_entradas(
        req,
        {"lib.t": [Column("id", "Integer"), Column("status", "String")]},
        manifest,
        tmp_path,
    )
    with (tmp_path / "lib.t.csv").open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    assert set(rows[0]) == {"id", "status"}
    assert paths


def test_columnas_no_demostradas_se_exigen_en_manifiesto(tmp_path):
    req = requisitos_de_rebanada("proc sql; select * from work.z; quit;")
    manifest = Manifiesto(semilla=1, tablas={"work.z": TablaDeDatos(1)})
    with pytest.raises(ValueError, match=r"work\.z.*columnas"):
        generar_entradas(req, {}, manifest, tmp_path)


def test_falta_tabla_en_manifiesto_falla_sin_escribir_parcialmente(tmp_path):
    req = requisitos_de_rebanada("proc sql; select z.k from work.z z; quit;")
    manifest = Manifiesto(semilla=1, tablas={})
    with pytest.raises(ValueError, match=r"work\.z"):
        generar_entradas(req, {}, manifest, tmp_path)
    assert list(tmp_path.iterdir()) == []


def test_lector_manifiesto_valida_semilla_y_columnas(tmp_path):
    path = tmp_path / "datos.yaml"
    path.write_text(
        "semilla: 2026\ntablas:\n  work.z:\n    filas: 2\n    columnas: [k]\n",
        encoding="utf-8",
    )
    assert leer_manifiesto(path) == Manifiesto(2026, {"work.z": TablaDeDatos(2, {}, ("k",))})
    path.write_text("semilla: 1\ntablas:\n  work.z:\n    filas: -1\n", encoding="utf-8")
    with pytest.raises(ValueError, match=r"work\.z"):
        leer_manifiesto(path)


@pytest.mark.parametrize(
    ("filas", "declaracion", "mensaje"),
    [
        (1, "fijos_por_fila: [{k: 1}]", "mapear columnas a textos"),
        (1, "fijos_por_fila: [{k: 'a'}, {k: 'b'}]", "lista de hasta 1 filas"),
    ],
)
def test_lector_manifiesto_valida_fijos_por_fila(tmp_path, filas, declaracion, mensaje):
    path = tmp_path / "datos.yaml"
    path.write_text(
        f"semilla: 1\ntablas:\n  work.z:\n    filas: {filas}\n"
        f"    columnas: [k]\n    {declaracion}\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match=mensaje):
        leer_manifiesto(path)


def test_nombres_de_tabla_no_pueden_salir_del_directorio_destino(tmp_path):
    req = Requisitos(tablas_work_externas={"work../escape": ["k"]})
    manifest = Manifiesto(1, {"work../escape": TablaDeDatos(1, {}, ("k",))})
    with pytest.raises(ValueError):
        generar_entradas(req, {}, manifest, tmp_path)
    assert list(tmp_path.iterdir()) == []
