"""Arnés de R1-02 sin Studio: vectores, oráculo, CSV, comparación y limpieza.

La ejecución real queda registrada en `PROGRESS.md` (hito 83). Aquí se comprueba que el esperado
sale de fuentes independientes, que el `.item` lleva una expresión por vector, que la comparación
detecta desvíos y que el protocolo no deja Jobs copiados en el proyecto de Studio.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))

import prueba_normalizacion as prueba  # noqa: E402
from corpus_semantica_funciones import Faltante, evaluar  # noqa: E402
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


def _escribir_csv(pares: list[str], lista: list[dict], cambio: dict[str, str] | None = None):
    """Escribe el CSV que el Job emitiría si todas las expresiones fueran correctas."""
    salida = Path(dict(p.split("=", 1) for p in pares)["ruta_salida"])
    valores = {
        caso["columna"]: "" if isinstance(caso["esperado"], Faltante) else str(caso["esperado"])
        for caso in lista
    }
    valores.update(cambio or {})
    with (salida / "resultados.csv").open("w", encoding="utf-8", newline="") as archivo:
        escritor = csv.DictWriter(
            archivo, fieldnames=[c["columna"] for c in lista], delimiter=prueba.SEPARADOR
        )
        escritor.writeheader()
        escritor.writerow(valores)


def test_los_vectores_tienen_columna_expresion_y_esperado():
    lista = prueba.casos()
    assert len(lista) == 45
    assert len({c["columna"] for c in lista}) == len(lista)
    for caso in lista:
        assert caso["columna"].startswith("v_")
        assert f"row1.{caso['columna']}" in caso["expresion"]
        assert caso["expresion"].startswith("java.util.Objects.toString(")
        assert caso["esperado"] is not None


def test_el_esperado_de_la_semantica_lo_calcula_el_oraculo():
    semanticos = {c["id"]: c for c in prueba.casos_semantica()}
    assert len(semanticos) == 29
    assert semanticos["input-06"]["esperado"] == evaluar("input", "0023", 6, 2)
    assert isinstance(semanticos["input-09"]["esperado"], Faltante)
    assert semanticos["compress-04"]["esperado"] == "ABCAB"
    assert semanticos["left-01"]["esperado"] == "ab  "


def test_los_nombres_de_v06_incluyen_tildes_y_la_llave_viene_del_corpus():
    nombres = prueba.casos_nombres()
    assert len(nombres) == prueba.N_NOMBRES == 16
    assert any("Ñ" in c["entrada"] for c in nombres)
    assert any("Í" in c["entrada"] for c in nombres)
    assert nombres[9]["entrada"] == "  CLIENTE   FICTICIO 00010 "
    assert nombres[9]["esperado"] == "CLIENTE FICTICIO 00010"


def test_nombre_columna_sanea_y_una_funcion_desconocida_se_rechaza():
    assert prueba.nombre_columna("input-01") == "v_input_01"
    with pytest.raises(ValueError, match="no soportada"):
        prueba.expresion({"funcion": "otra", "entrada": []}, "v_x")


def test_el_job_lleva_una_expresion_por_vector_y_escapes_unicode():
    lista = prueba.casos()
    item = render_item(prueba.job_normalizacion(lista))
    for caso in lista:
        assert f'name="{caso["columna"]}"' in item
    assert "java.util.Objects.toString(" in item
    assert r"NI\u00d1O" in item  # las Ñ no dependen de la codificación del .java generado
    assert r"MAR\u00cdA" in item
    assert '&quot;UTF-8&quot;' in item
    assert "ruta_salida" in item


def test_coincide_compara_numeros_texto_y_faltantes():
    assert prueba.coincide(Faltante(), "")
    assert not prueba.coincide(Faltante(), "0")
    assert prueba.coincide(23.0, "23.00")
    assert not prueba.coincide(23.0, "23.5")
    assert not prueba.coincide(23.0, "abc")
    assert prueba.coincide("abc", "abc")
    assert not prueba.coincide("abc", "ABC")


def test_informe_senala_el_vector_que_falta_y_el_que_no_coincide():
    lista = prueba.casos()[:2]
    id_ok = lista[0]["id"]
    columna_ok = lista[0]["columna"]
    esperado_ok = "" if isinstance(lista[0]["esperado"], Faltante) else str(lista[0]["esperado"])
    filas = prueba.informe(lista, {columna_ok: esperado_ok})
    assert filas[0][0] == id_ok and filas[0][3] is True
    assert filas[1][2] == "<sin columna>" and filas[1][3] is False


def test_leer_resultados_lee_cabecera_y_fila(tmp_path):
    ruta = tmp_path / "resultados.csv"
    ruta.write_text("v_a|v_b\n1|2\n", encoding="utf-8")
    assert prueba.leer_resultados(ruta) == {"v_a": "1", "v_b": "2"}
    assert prueba.leer_resultados(tmp_path / "no.csv") == {}


def test_preparar_trabajo_borra_el_csv_de_una_corrida_anterior(tmp_path):
    trabajo = tmp_path / "trabajo"
    salida = trabajo / "salida"
    salida.mkdir(parents=True)
    (salida / "resultados.csv").write_text("v_a|v_b\n99|88\n", encoding="utf-8")
    prueba.preparar_trabajo(trabajo)
    assert prueba.leer_resultados(salida / "resultados.csv") == {}


def test_validar_coincide_con_el_oraculo_y_limpia_lo_que_copio(
    proyecto, tmp_path, monkeypatch, capsys
):
    doble = DobleStudio()
    monkeypatch.setattr(prueba, "MCP", lambda: doble)

    def lanzador_falso(lanzador, contexto, pares, java_bin):
        _escribir_csv(pares, prueba.casos())
        return {"exitCode": 0, "stdout": "", "stderr": "", "comando": "falso"}

    monkeypatch.setattr(prueba, "ejecutar", lanzador_falso)
    assert prueba.validar(proyecto, tmp_path / "trabajo", "v9", None, None) == 0
    texto = capsys.readouterr().out
    assert "Vectores: 45; coinciden: 45; fallan: 0" in texto
    assert "la normalización coincide con el oráculo" in texto
    assert list((proyecto / "process").iterdir()) == []
    assert doble.llamadas.count("talend_bridge_refresh_workspace") == 2


def test_validar_falla_si_un_vector_no_coincide(proyecto, tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(prueba, "MCP", lambda: DobleStudio())

    def lanzador_falso(lanzador, contexto, pares, java_bin):
        _escribir_csv(pares, prueba.casos(), {"v_input_01": "999"})
        return {"exitCode": 0, "stdout": "", "stderr": "", "comando": "falso"}

    monkeypatch.setattr(prueba, "ejecutar", lanzador_falso)
    assert prueba.validar(proyecto, tmp_path / "trabajo", "v9", None, None) == 1
    texto = capsys.readouterr().out
    assert "FALLA input-01" in texto
    assert "hay diferencias" in texto


def test_validar_falla_si_el_job_no_termina(proyecto, tmp_path, monkeypatch):
    monkeypatch.setattr(prueba, "MCP", lambda: DobleStudio())

    def lanzador_falso(lanzador, contexto, pares, java_bin):
        return {"exitCode": 1, "stdout": "", "stderr": "falló", "comando": "falso"}

    monkeypatch.setattr(prueba, "ejecutar", lanzador_falso)
    assert prueba.validar(proyecto, tmp_path / "trabajo", "v9", None, None) == 1


def test_sin_proyecto_talend_el_uso_no_vale(tmp_path, capsys):
    assert prueba.main(["--proyecto", str(tmp_path / "no")]) == 2
    assert "no es un proyecto Talend" in capsys.readouterr().err


def test_un_fallo_del_servidor_se_reporta_como_error(proyecto, tmp_path, monkeypatch):
    class DobleRoto(DobleStudio):
        def llamar(self, tool, argumentos=None):
            raise ErrorValidacion(f"{tool}: falla simulada")

    monkeypatch.setattr(prueba, "MCP", lambda: DobleRoto())
    codigo = prueba.main(
        ["--proyecto", str(proyecto), "--trabajo", str(tmp_path / "trabajo"), "--sufijo", "v9"]
    )
    assert codigo == 1
    assert list((proyecto / "process").iterdir()) == []
