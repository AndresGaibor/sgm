"""Hito 90 / R1-07: la rama de saldo llega al `job_producto` emitido, y solo cuando el SAS la declara.

Sin Studio: `sgm talend` sobre `client_large.sas` no emite la rama (su SAS no tiene la tabla) y
publica los dos pendientes; `emitir_producto` de `tools/prueba_saldo.py` emite la rama con la
regla de v05 y añade tres componentes al Job de 21 nodos.
"""

from __future__ import annotations

import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "tools"))

from sgm.cli_talend import _saldo, talend_command  # noqa: E402
from sgm.proceso.reglas_cuenta_real import reglas_cuenta_real  # noqa: E402
from sgm.proceso.reglas_saldo import PENDIENTE_CERO, reglas_saldo  # noqa: E402
from sgm.talend_item.flujos_saldo import SALIDA, TMAP, componentes  # noqa: E402
from sgm.talend_item.modelo import Columna  # noqa: E402

PROGRAMA = RAIZ / "tests" / "fixtures" / "sas" / "client" / "client_large.sas"
V05 = RAIZ / "tests" / "corpus" / "L8" / "validaciones" / "v05_codex_saldos" / "programa.sas"
TEXTO_CLIENTE = PROGRAMA.read_text(encoding="utf-8", errors="replace")
TEXTO_V05 = V05.read_text(encoding="utf-8", errors="replace")
CUENTA, _ = reglas_cuenta_real(TEXTO_CLIENTE)
REGLA, _ = reglas_saldo(TEXTO_V05)
COLS = [Columna(c) for c in CUENTA.columnas]
INFORMATS = {"FIN_SALDO_CTA": (20, 0), "GMF": (3, 0)}


def _nodos_por_nombre(item: Path) -> dict[str, ET.Element]:
    raiz = ET.parse(item).getroot()
    resultado = {}
    for nodo in raiz.iter("node"):
        for parametro in nodo.findall("elementParameter"):
            if parametro.get("name") == "UNIQUE_NAME":
                resultado[parametro.get("value")] = nodo
    return resultado


def test_el_cliente_no_emite_la_rama_y_publica_los_dos_pendientes(tmp_path, capsys):
    talend_command(PROGRAMA, out=tmp_path)
    salida = capsys.readouterr().out
    assert PENDIENTE_CERO in salida
    assert "R1-07: no se emiten los saldos negativos" in salida
    item = tmp_path / PROGRAMA.stem / "talend" / "process" / "job_producto_0.1.item"
    assert TMAP not in _nodos_por_nombre(item)


def test_sin_regla_de_saldo_el_cli_devuelve_none():
    regla, avisos = _saldo(TEXTO_CLIENTE, CUENTA)
    assert regla is None
    assert any(PENDIENTE_CERO == a for a in avisos)


def test_sin_cascada_de_codex_no_se_emite_aunque_haya_regla():
    regla, avisos = _saldo(TEXTO_V05, None)
    assert regla is None
    assert any("sin la cascada de R1-06" in a for a in avisos)


def test_la_regla_de_v05_se_emite_con_cascada():
    regla, avisos = _saldo(TEXTO_V05, CUENTA)
    assert regla == REGLA
    assert avisos and all("R1-07" in a for a in avisos)


def test_componentes_un_tmap_y_dos_csv():
    nodos, conexiones = componentes(REGLA, CUENTA, COLS, INFORMATS)
    assert len(nodos) == 3 and len(conexiones) == 3
    assert nodos[0].unico == TMAP
    assert [n.unico for n in nodos[1:]] == [SALIDA.format(n=1), SALIDA.format(n=2)]
    assert conexiones[0].origen == "tReplicate_1" and conexiones[0].destino == TMAP


def test_los_nombres_de_conexion_no_repiten_los_de_las_otras_ramas():
    _, conexiones = componentes(REGLA, CUENTA, COLS, INFORMATS)
    nombres = {c.nombre for c in conexiones}
    # Nombres de R1-04 y R1-06 que ya viven en el Job.
    ocupados = {"valido", "cuenta", "cta_tipo_cta", "cta_codex", "cta_valido", "cta_incons"}
    assert not nombres & ocupados


def test_sin_el_saldo_en_numericas_no_se_emite():
    with pytest.raises(ValueError, match="normalización de R1-02"):
        componentes(REGLA, CUENTA, COLS, {"GMF": (3, 0)})


def test_sin_cuenta_no_se_emite():
    with pytest.raises(ValueError, match="cascada de codex"):
        componentes(REGLA, None, COLS, INFORMATS)


def test_sin_la_columna_de_saldo_en_el_csv_no_se_emite():
    sin_saldo = [c for c in COLS if c.nombre != "FIN_SALDO_CTA"]
    with pytest.raises(ValueError, match="no se leen"):
        componentes(REGLA, CUENTA, sin_saldo, INFORMATS)


def test_el_item_con_regla_de_v05_tiene_tres_componentes_mas(tmp_path):
    from prueba_saldo import emitir_producto

    item = emitir_producto(tmp_path)
    nodos = _nodos_por_nombre(item)
    assert TMAP in nodos
    assert SALIDA.format(n=1) in nodos and SALIDA.format(n=2) in nodos
    assert len(list(ET.parse(item).getroot().iter("node"))) == 24


def test_el_replicate_alimenta_la_rama_de_saldo(tmp_path):
    from prueba_saldo import emitir_producto

    item = emitir_producto(tmp_path)
    raiz = ET.parse(item).getroot()
    conexiones = [(c.get("source"), c.get("target"), c.get("label")) for c in raiz.findall("connection")]
    assert ("tReplicate_1", TMAP, "saldo_fuente") in conexiones
    assert (TMAP, SALIDA.format(n=1), "saldo_neg") in conexiones
    assert (TMAP, SALIDA.format(n=2), "saldo_valida") in conexiones
