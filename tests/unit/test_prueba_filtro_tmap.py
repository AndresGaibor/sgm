"""Prueba del filtro del `tMap` en Studio, sin Studio: el Job, la lectura y el protocolo.

La ejecución real está registrada en `PROGRESS.md` (hito 81). Aquí se cubre lo que no necesita
Studio: que el `.item` lleve el filtro y la salida de rechazo, que la lectura de la salida tome la
primera columna y que el protocolo copie, compile, exporte, ejecute y borre lo que copió.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))

import prueba_filtro_tmap as prueba  # noqa: E402
from mcp_cliente import ErrorValidacion  # noqa: E402

from sgm.talend_item.item import render_item  # noqa: E402
from sgm.talend_item.modelo import Columna  # noqa: E402

COLUMNAS = [Columna("id"), Columna("tipo")]


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


def test_el_job_lleva_filtro_en_validos_y_rechazo_en_la_otra_rama():
    item = render_item(prueba.job_filtro(COLUMNAS))
    assert 'name="validos" expressionFilter="row1.tipo.equals(&quot;CC&quot;)"' in item
    assert 'activateExpressionFilter="true"' in item
    assert 'name="rechazados" reject="true"' in item
    assert 'connectorName="REJECT"' in item


def test_la_entrada_de_prueba_tiene_las_cinco_filas_sin_cabecera(tmp_path):
    prueba.preparar_trabajo(tmp_path / "trabajo")
    texto = (tmp_path / "trabajo" / "entradas" / "prueba.csv").read_text(encoding="utf-8")
    assert texto.splitlines() == ["1;CC", "2;AHO", "3;CC", "4;NEQUI", "5;CC"]
    assert (tmp_path / "trabajo" / "salida").is_dir()


def test_la_lectura_de_salida_toma_la_primera_columna(tmp_path):
    archivo = tmp_path / "validos.csv"
    archivo.write_text("1;CC\n3;CC\n", encoding="utf-8")
    assert prueba._ids(archivo) == ["1", "3"]
    assert prueba._ids(tmp_path / "no-existe.csv") == []


def test_sin_proyecto_talend_el_uso_no_vale(tmp_path, capsys):
    assert prueba.main(["--proyecto", str(tmp_path / "no")]) == 2
    assert "no es un proyecto Talend" in capsys.readouterr().err


def test_el_protocolo_ejecuta_compara_y_borra_lo_que_copio(proyecto, tmp_path, monkeypatch, capsys):
    doble = DobleStudio()
    monkeypatch.setattr(prueba, "MCP", lambda: doble)

    def lanzador_falso(lanzador, contexto, pares, java_bin):
        salida = dict(p.split("=", 1) for p in pares)["ruta_salida"]
        Path(salida, "validos.csv").write_text("1;CC\n3;CC\n5;CC\n", encoding="utf-8")
        Path(salida, "rechazados.csv").write_text("2;AHO\n4;NEQUI\n", encoding="utf-8")
        return {"exitCode": 0, "stdout": "", "stderr": "", "comando": "falso"}

    monkeypatch.setattr(prueba, "ejecutar", lanzador_falso)
    codigo = prueba.validar(proyecto, tmp_path / "trabajo", "v9", None, None)
    assert codigo == 0
    assert "el filtro funciona" in capsys.readouterr().out
    assert sorted(p.name for p in (proyecto / "process").iterdir()) == []
    assert doble.llamadas.count("talend_bridge_refresh_workspace") == 2


def test_si_una_fila_cae_en_la_rama_equivocada_falla(proyecto, tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(prueba, "MCP", lambda: DobleStudio())

    def lanzador_falso(lanzador, contexto, pares, java_bin):
        salida = dict(p.split("=", 1) for p in pares)["ruta_salida"]
        Path(salida, "validos.csv").write_text("1;CC\n2;AHO\n", encoding="utf-8")
        Path(salida, "rechazados.csv").write_text("3;CC\n", encoding="utf-8")
        return {"exitCode": 0, "stdout": "", "stderr": "", "comando": "falso"}

    monkeypatch.setattr(prueba, "ejecutar", lanzador_falso)
    assert prueba.validar(proyecto, tmp_path / "trabajo", "v9", None, None) == 1
    assert "NO coincide" in capsys.readouterr().out


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
