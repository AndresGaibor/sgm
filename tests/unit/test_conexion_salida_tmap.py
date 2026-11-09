"""La conexión que sale de un `tMap` lleva el nombre de su `outputTables` (exigido por Studio).

Si no coincide, Studio no carga el Job («Error al cargar el trabajo», hito 149m).
"""

from __future__ import annotations

import re
from pathlib import Path

from sgm.cli_migrar import migrar

CORPUS = Path("tests/corpus/L1/l1_14_expresion_compuesta")


def test_la_conexion_del_tmap_hacia_el_orden_usa_el_nombre_de_su_salida(tmp_path: Path):
    resultado = migrar(CORPUS / "programa.sas", tmp_path / "out", muestra=CORPUS / "entradas")
    texto = next(tmp_path.rglob("*.item")).read_text(encoding="utf-8")
    salidas = set(re.findall(r'<outputTables[^>]*name="([^"]+)"', texto))
    conexiones = re.findall(r'<connection[^>]*label="([^"]+)"[^>]*metaname="(tMap_\d+)"', texto)
    assert salidas, "el tMap debe tener al menos una salida"
    for etiqueta, _ in conexiones:
        assert etiqueta in salidas, (etiqueta, salidas)
    assert resultado.jobs


def test_un_tmap_que_alimenta_a_otro_no_se_escribe_y_queda_pendiente(tmp_path: Path):
    """`l1_10` (dos etapas) hace que un `tMap` alimente a otro. Studio no carga esa conexión
    («Error al cargar el trabajo», row1): el Job no se escribe y queda como P-JOB-INVALIDO."""
    caso = Path("tests/corpus/L1/l1_10_dos_etapas_faltantes")
    resultado = migrar(caso / "programa.sas", tmp_path / "out", muestra=caso / "entradas")
    assert not list(tmp_path.rglob("*.item")), "un Job con defectos no debe escribirse"
    assert any(p.codigo == "P-JOB-INVALIDO" and "row1" in p.mensaje for p in resultado.pendientes)


def test_un_case_de_texto_no_se_tipa_como_predicado():
    """`CASE WHEN x IS MISSING THEN 'A' ... END` devuelve texto; no es una condición booleana
    (sin este caso, el emisor la envolvía como Long y Studio no compilaba l2_08)."""
    from sgm.ir.types_code import expression_type

    assert expression_type("CASE WHEN v.id IS MISSING THEN 'SIN_VENTAS' ELSE 'CON' END") is None
    assert expression_type("saldo > 0 AND activo = 1") is not None
