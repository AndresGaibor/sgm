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


def test_dos_etapas_encadenadas_se_hacen_en_un_solo_tmap(tmp_path: Path):
    """`l1_10` escribe `WORK.disponibles` y la lee en la sentencia siguiente. Antes salían dos
    `tMap` encadenados, que Studio no carga; ahora la intermedia se funde y queda un `tMap` con el
    filtro de la primera etapa y la expresión de la segunda."""
    caso = Path("tests/corpus/L1/l1_10_dos_etapas_faltantes")
    resultado = migrar(caso / "programa.sas", tmp_path / "out", muestra=caso / "entradas")
    texto = next(tmp_path.rglob("*.item")).read_text(encoding="utf-8")
    assert not [p for p in resultado.pendientes if p.codigo == "P-JOB-INVALIDO"]
    assert [n.componente for n in resultado.jobs[0].nodos].count("tMap") == 1
    assert "categoria" in texto and "doble_stock" in texto
    assert [d.tabla for d in resultado.decisiones] == ["disponibles"]
    assert "WORK.disponibles" in (tmp_path / "out/programa/decisiones-tomadas.md").read_text(
        encoding="utf-8"
    )


def test_un_case_de_texto_no_se_tipa_como_predicado():
    """`CASE WHEN x IS MISSING THEN 'A' ... END` devuelve texto; no es una condición booleana
    (sin este caso, el emisor la envolvía como Long y Studio no compilaba l2_08)."""
    from sgm.ir.types_code import expression_type

    assert expression_type("CASE WHEN v.id IS MISSING THEN 'SIN_VENTAS' ELSE 'CON' END") is None
    assert expression_type("saldo > 0 AND activo = 1") is not None
