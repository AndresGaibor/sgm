"""Pruebas sin Docker de los contenedores de pruebas (tools/contenedores).

Comprueban la forma de los compose, que los nombres empiecen por sgmtest_, que no haya
secretos reales y que el cargador genere el SQL correcto sin conectarse a ninguna base.
Las pruebas con Docker son comandos manuales (ver los README), no van aquí.
"""

import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parents[2]
CONTENEDORES = REPO / "tools" / "contenedores"
sys.path.insert(0, str(CONTENEDORES))

from fuentes_sas import tablas_base  # noqa: E402
from sql_carga import sentencias_desde_csv, sentencias_ficticias  # noqa: E402

COMPOSE = {
    "impala": CONTENEDORES / "impala" / "docker-compose.yml",
    "postgres": CONTENEDORES / "postgres" / "docker-compose.yml",
}
PROGRAMA_GRANDE = REPO / "tests" / "fixtures" / "sas" / "client" / "client_large.sas"
# Única contraseña permitida en los compose: la de un contenedor desechable de prueba.
CLAVES_DE_PRUEBA = {"sgmtest_pw_local"}


def _cargar(nombre: str) -> dict:
    return yaml.safe_load(COMPOSE[nombre].read_text(encoding="utf-8"))


@pytest.mark.parametrize("nombre", sorted(COMPOSE))
def test_compose_es_yaml_valido_con_servicios(nombre):
    datos = _cargar(nombre)
    assert datos["services"], "el compose no define servicios"


@pytest.mark.parametrize("nombre", sorted(COMPOSE))
def test_todos_los_nombres_empiezan_por_sgmtest(nombre):
    datos = _cargar(nombre)
    assert datos["name"].startswith("sgmtest_")
    for servicio in datos["services"].values():
        if "container_name" in servicio:
            assert servicio["container_name"].startswith("sgmtest_")
    for red in (datos.get("networks") or {}).values():
        assert red["name"].startswith("sgmtest_")
    for volumen in (datos.get("volumes") or {}):
        assert volumen.startswith("sgmtest_")


@pytest.mark.parametrize("nombre", sorted(COMPOSE))
def test_sin_secretos_reales_en_los_compose(nombre):
    texto = COMPOSE[nombre].read_text(encoding="utf-8")
    contrasenas = re.findall(r"PASSWORD[A-Z_]*:\s*(\S+)", texto)
    for valor in contrasenas:
        assert valor in CLAVES_DE_PRUEBA, f"contraseña no permitida en {nombre}: {valor}"


def test_impala_publica_hiveserver2_solo_en_loopback():
    servicios = _cargar("impala")["services"]
    puertos = servicios["impalad"]["ports"]
    assert puertos == ["127.0.0.1:21050:21050"]


def test_impala_limita_la_memoria_de_cada_servicio():
    servicios = _cargar("impala")["services"]
    assert {s: servicios[s]["mem_limit"] for s in servicios} == {
        "hms": "1g",
        "statestored": "256m",
        "catalogd": "1g",
        "impalad": "2500m",
    }


def test_hive_site_del_impala_es_xml_y_apunta_al_hms():
    raiz = ET.parse(CONTENEDORES / "impala" / "quickstart_conf" / "hive-site.xml").getroot()
    valores = {p.findtext("name"): p.findtext("value") for p in raiz.findall("property")}
    assert valores["hive.metastore.uris"] == "thrift://hms:9083"


def test_scripts_de_arranque_usan_solo_nombres_sgmtest():
    for ruta in (CONTENEDORES / "impala").glob("arrancar.*"):
        texto = ruta.read_text(encoding="utf-8")
        for nombre in re.findall(r"sgmtest_\w+", texto):
            assert nombre.startswith("sgmtest_")
        assert "docker" in texto


def test_sql_de_programa_grande_sin_conectarse():
    tablas, omitidas = tablas_base(PROGRAMA_GRANDE)
    nombres = {f"{t.biblioteca}.{t.tabla}" for t in tablas}
    assert nombres == {
        "resultados_vspc_clientes.master_customer_data",
        "s_canales.sai_scilibramd_sciffimgfr",
        "proceso_vspc_finanzas.mcdq",
    }
    assert omitidas == []
    for tabla in tablas:
        sql = "\n".join(sentencias_ficticias(tabla, filas=3))
        assert f"CREATE TABLE {tabla.biblioteca}.{tabla.tabla}" in sql
        assert sql.count("STRING") == len(tabla.columnas)
        assert sql.count("'SIM_") == 3 * len(tabla.columnas)


def test_columna_usada_por_el_programa_aparece_en_el_create():
    tablas, _ = tablas_base(PROGRAMA_GRANDE)
    maestra = next(t for t in tablas if t.tabla == "master_customer_data")
    assert "cod_tipo_doc" in maestra.columnas
    sql = "\n".join(sentencias_ficticias(maestra, filas=1))
    assert "`cod_tipo_doc` STRING" in sql


def test_csv_se_carga_con_su_cabecera_y_escapa_comillas(tmp_path):
    csv = tmp_path / "entrada.csv"
    csv.write_text("id,nombre\n1,SIM_o'brien\n2,SIM_dos\n", encoding="utf-8")
    sql = "\n".join(sentencias_desde_csv("default", "sgmtest_csv", csv))
    assert "`id` STRING" in sql and "`nombre` STRING" in sql
    assert "'SIM_o''brien'" in sql
    assert sql.count("(") >= 3
