"""Hito 95 / R1-12: la rama de duplicados se emite con su forma de SAS (sin Studio).

La validación en Studio está en `tools/prueba_duplicados.py`. Estas pruebas miran la forma del
Job: llaves recortadas en el `tMap`, `tUniqRow` sensible a mayúsculas, dos salidas CSV con
cabecera y `context.sufijo`, y los nombres de conexión sin repetir.
"""

from __future__ import annotations

import pytest

from sgm.proceso.reglas_duplicados import ReglaDuplicados
from sgm.talend_item.flujos_duplicados import (
    ENTRADA,
    TMAP,
    UNICOS,
    componentes,
    job_duplicados,
)
from sgm.talend_item.modelo import Columna

COLUMNAS = [Columna("CLAVE"), Columna("SALDO")]
REGLA = ReglaDuplicados(entrada="ENTRADA", salida="VECTORES", llaves=("CLAVE",), equals=True)


def _nodo(nodos, unico):
    return next(n for n in nodos if n.unico == unico)


def _tabla_unique_key(nodo) -> list[tuple[str, str]]:
    parametro = next(p for p in nodo.parametros if not isinstance(p, tuple))
    return list(parametro.celdas)


def test_la_llave_se_recorta_en_el_tmap_y_el_resto_pasa_igual():
    nodos, _ = componentes(REGLA, COLUMNAS, "tReplicate_1")
    salida = _nodo(nodos, TMAP).metadatas[0]
    assert salida.nombre == "dup_fila"
    assert "replaceAll" in _nodo(nodos, TMAP).datos
    assert f"{ENTRADA}.SALDO" in _nodo(nodos, TMAP).datos


def test_tunique_marca_solo_la_llave_como_clave_y_sensible_a_mayusculas():
    nodos, _ = componentes(REGLA, COLUMNAS, "tReplicate_1")
    celdas = _tabla_unique_key(_nodo(nodos, UNICOS))
    assert ("SCHEMA_COLUMN", "CLAVE") in celdas
    assert ("SCHEMA_COLUMN", "SALDO") in celdas
    indice = celdas.index(("SCHEMA_COLUMN", "CLAVE"))
    assert celdas[indice + 1] == ("KEY_ATTRIBUTE", "true")
    assert celdas[indice + 2] == ("CASE_SENSITIVE", "true")
    indice_saldo = celdas.index(("SCHEMA_COLUMN", "SALDO"))
    assert celdas[indice_saldo + 1] == ("KEY_ATTRIBUTE", "false")


def test_hay_dos_csv_con_cabecera_y_sufijo():
    nodos, conexiones = componentes(REGLA, COLUMNAS, "tReplicate_1")
    csv = [n for n in nodos if n.componente == "tFileOutputDelimited"]
    assert len(csv) == 2
    for nodo in csv:
        valores = {f[1]: f[2] for f in nodo.parametros if isinstance(f, tuple)}
        assert valores.get("INCLUDEHEADER") == "true"
        assert "context.sufijo" in valores["FILENAME"]
    rutas = {c.conector: c.nombre for c in conexiones if c.conector != "FLOW"}
    assert rutas == {"UNIQUE": "dup_unica", "DUPLICATE": "dup_repetida"}


def test_los_nombres_de_conexion_no_chocan_con_otras_ramas():
    _, conexiones = componentes(REGLA, COLUMNAS, "tReplicate_1")
    nombres = [c.nombre for c in conexiones]
    prefijos_ajenos = ("cta_", "saldo_", "ubic_", "valido", "fila_", "row")
    assert not [n for n in nombres if n.startswith(prefijos_ajenos)]


def test_el_job_propio_lee_el_csv_de_contexto_con_cabecera():
    job = job_duplicados(REGLA, COLUMNAS, ",")
    lectura = next(n for n in job.nodos if n.componente == "tFileInputDelimited")
    valores = {f[1]: f[2] for f in lectura.parametros if isinstance(f, tuple)}
    assert valores["FILENAME"] == "context.ruta_origen"
    assert valores["HEADER"] == "1"
    nombres = {p.nombre for p in job.contextos["Default"]}
    assert nombres == {"ruta_origen", "ruta_resultados", "sufijo"}


def test_sin_equals_no_se_emite():
    regla = ReglaDuplicados(entrada="E", salida="S", llaves=("CLAVE",), equals=False)
    with pytest.raises(ValueError, match="EQUALS"):
        componentes(regla, COLUMNAS, "tReplicate_1")


def test_una_llave_fuera_del_esquema_falla():
    regla = ReglaDuplicados(entrada="E", salida="S", llaves=("NRO_DOC",), equals=True)
    with pytest.raises(ValueError, match="NRO_DOC"):
        componentes(regla, COLUMNAS, "tReplicate_1")
