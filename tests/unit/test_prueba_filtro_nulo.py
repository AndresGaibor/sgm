"""Prueba del filtro con columnas nulas, sin Studio: el Job, los datos y el protocolo.

La ejecución real en Studio queda registrada en `PROGRESS.md` (hito 82). Aquí se cubre lo que no
necesita Studio: que el `.item` lleve el filtro seguro, que el lookup sea un LEFT JOIN, que la
conexión de búsqueda tenga `lineStyle` 8 y que el protocolo compare y limpie lo que copió.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))

import prueba_filtro_nulo as prueba  # noqa: E402
from mcp_cliente import ErrorValidacion  # noqa: E402

from sgm.talend_item.item import render_item  # noqa: E402


class DobleStudio:
    """Cliente falso: deja un lanzador y anota las llamadas."""

    def __init__(self) -> None:
        self.llamadas: list[str] = []

    def llamar(self, tool: str, argumentos: dict | None = None):
        self.llamadas.append(tool)
        if tool == "talend_job_build_batch":
            return {"jobs": [{"ok": True}]}
        if tool == "talend_deliverables_build_job":
            destino = Path(argumentos["destinationDir"])
            job = argumentos["jobName"]
            (destino / job).mkdir(parents=True, exist_ok=True)
            (destino / job / f"{job}_run.bat").write_text("@echo off\n", encoding="utf-8")
        return {}


@pytest.fixture
def proyecto(tmp_path) -> Path:
    raiz = tmp_path / "PRJ_PRUEBA"
    (raiz / "process").mkdir(parents=True)
    (raiz / "talend.project").write_text(
        '<TalendProperties:Project technicalLabel="PRJ_PRUEBA"/>', encoding="utf-8"
    )
    return raiz


def test_el_job_lleva_el_filtro_seguro_y_la_salida_de_rechazo():
    item = render_item(prueba.job_filtro_nulo())
    assert 'name="validos" expressionFilter="&quot;CC&quot;.equals(row2.valor)"' in item
    assert 'activateExpressionFilter="true"' in item
    assert 'name="rechazados" reject="true"' in item
    assert 'connectorName="REJECT"' in item


def test_el_lookup_es_left_join_y_la_conexion_es_de_busqueda():
    item = render_item(prueba.job_filtro_nulo())
    assert 'innerJoin="true"' not in item
    assert 'name="row2"' in item and 'expression="row1.clave"' in item
    assert 'connectorName="LOOKUP" label="row2" lineStyle="8"' in item


def test_la_forma_insegura_pone_la_columna_a_la_izquierda():
    assert prueba.filtro("insegura") == 'row2.valor.equals("CC")'


def test_una_forma_desconocida_se_rechaza():
    with pytest.raises(ValueError, match="Forma desconocida"):
        prueba.filtro("otra")


def test_tres_de_las_seis_filas_no_tienen_pareja():
    claves_lookup = {c for c, _ in prueba.LOOKUP}
    sin_pareja = [i for i, c in prueba.PRINCIPAL if c not in claves_lookup]
    assert sin_pareja == ["4", "5", "6"]
    assert prueba.VALIDOS == ["1", "3"]
    assert prueba.RECHAZADOS == ["2", "4", "5", "6"]


def test_preparar_trabajo_borra_las_salidas_de_una_corrida_anterior(tmp_path):
    trabajo = tmp_path / "trabajo"
    trabajo.mkdir()
    salida = trabajo / "salida"
    salida.mkdir()
    (salida / "validos.csv").write_text("99;CC\n", encoding="utf-8")
    prueba.preparar_trabajo(trabajo)
    assert prueba._ids(salida / "validos.csv") == []


def test_sin_proyecto_talend_el_uso_no_vale(tmp_path, capsys):
    assert prueba.main(["--proyecto", str(tmp_path / "no")]) == 2
    assert "no es un proyecto Talend" in capsys.readouterr().err


def test_la_forma_segura_ejecuta_compara_y_borra_lo_que_copio(
    proyecto, tmp_path, monkeypatch, capsys
):
    doble = DobleStudio()
    monkeypatch.setattr(prueba, "MCP", lambda: doble)

    def lanzador_falso(lanzador, contexto, pares, java_bin):
        salida = Path(dict(p.split("=", 1) for p in pares)["ruta_salida"])
        (salida / "validos.csv").write_text("1\n3\n", encoding="utf-8")
        (salida / "rechazados.csv").write_text("2\n4\n5\n6\n", encoding="utf-8")
        return {"exitCode": 0, "stdout": "", "stderr": "", "comando": "falso"}

    monkeypatch.setattr(prueba, "ejecutar", lanzador_falso)
    codigo = prueba.validar(proyecto, tmp_path / "trabajo", "v9", "segura", None, None)
    assert codigo == 0
    assert "el filtro seguro separa las filas" in capsys.readouterr().out
    assert sorted(p.name for p in (proyecto / "process").iterdir()) == []
    assert doble.llamadas.count("talend_bridge_refresh_workspace") == 2


def test_la_forma_segura_falla_si_una_fila_cae_en_la_rama_equivocada(
    proyecto, tmp_path, monkeypatch, capsys
):
    monkeypatch.setattr(prueba, "MCP", lambda: DobleStudio())

    def lanzador_falso(lanzador, contexto, pares, java_bin):
        salida = Path(dict(p.split("=", 1) for p in pares)["ruta_salida"])
        (salida / "validos.csv").write_text("1\n", encoding="utf-8")
        (salida / "rechazados.csv").write_text("2\n3\n4\n5\n6\n", encoding="utf-8")
        return {"exitCode": 0, "stdout": "", "stderr": "", "comando": "falso"}

    monkeypatch.setattr(prueba, "ejecutar", lanzador_falso)
    assert prueba.validar(proyecto, tmp_path / "trabajo", "v9", "segura", None, None) == 1
    assert "NO coincide" in capsys.readouterr().out


def test_la_forma_insegura_se_acepta_solo_si_falla_con_npe(proyecto, tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(prueba, "MCP", lambda: DobleStudio())

    def lanzador_falso(lanzador, contexto, pares, java_bin):
        return {
            "exitCode": 1,
            "stdout": "",
            "stderr": "java.lang.NullPointerException: Cannot invoke equals",
            "comando": "falso",
        }

    monkeypatch.setattr(prueba, "ejecutar", lanzador_falso)
    trabajo = tmp_path / "trabajo"
    assert prueba.validar(proyecto, trabajo, "v9", "insegura", None, None) == 0
    assert "NullPointerException" in capsys.readouterr().out

    def lanzador_que_no_falla(lanzador, contexto, pares, java_bin):
        return {"exitCode": 0, "stdout": "", "stderr": "", "comando": "falso"}

    monkeypatch.setattr(prueba, "ejecutar", lanzador_que_no_falla)
    assert prueba.validar(proyecto, trabajo, "v10", "insegura", None, None) == 1
    assert "NO falló" in capsys.readouterr().out


def test_un_fallo_del_servidor_se_reporta_como_error(proyecto, tmp_path, monkeypatch):
    class DobleRoto(DobleStudio):
        def llamar(self, tool, argumentos=None):
            raise ErrorValidacion(f"{tool}: falla simulada")

    monkeypatch.setattr(prueba, "MCP", lambda: DobleRoto())
    codigo = prueba.main(
        ["--proyecto", str(proyecto), "--trabajo", str(tmp_path / "trabajo"), "--sufijo", "v9"]
    )
    assert codigo == 1
    assert sorted(p.name for p in (proyecto / "process").iterdir()) == []
