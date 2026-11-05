"""Comando `sgm conformidad` sobre el programa pequeño de `tests/fixtures/conformidad`."""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from sgm.cli import app
from sgm.conformidad.referencia import cargar_secciones, todas_las_filas

RAIZ = Path(__file__).resolve().parents[2]
FIXTURES = RAIZ / "tests" / "fixtures" / "conformidad"
MINI = FIXTURES / "mini.sas"
DECISIONES = FIXTURES / "decisiones"


def _correr(*args: str):
    return CliRunner().invoke(app, ["conformidad", *args])


def test_el_programa_pequeno_tiene_una_fila_derivada_y_dos_declaradas() -> None:
    resultado = _correr(str(MINI), "--decisiones", str(DECISIONES), "--formato", "json")
    assert resultado.exit_code == 0, resultado.output
    datos = json.loads(resultado.output)
    por_id = {f["id"]: f["estado"] for f in datos["filas"]}
    assert por_id["F03"] == "derivada"  # Códigos de país: el SAS lee Cod_pais.xlsx
    assert por_id["F06"] == "declarada"  # origen Impala: el valor sale de decisiones/
    assert por_id["S01"] == "declarada"  # salida declarada en el YAML, sin equivalente hallado
    assert (datos["derivadas"], datos["declaradas"], datos["diferentes"]) == (1, 2, 0)


def test_el_total_es_el_de_la_referencia_y_el_orden_es_estable() -> None:
    referencia = [f.id for f in todas_las_filas(cargar_secciones())]
    primera = _correr(str(MINI), "--decisiones", str(DECISIONES), "--formato", "json")
    segunda = _correr(str(MINI), "--decisiones", str(DECISIONES), "--formato", "json")
    assert primera.output == segunda.output
    datos = json.loads(primera.output)
    assert [f["id"] for f in datos["filas"]] == referencia
    assert datos["total"] == len(referencia)


def test_formato_texto_imprime_el_resumen() -> None:
    resultado = _correr(str(MINI), "--decisiones", str(DECISIONES))
    assert resultado.exit_code == 0, resultado.output
    assert "derivadas:  1" in resultado.output
    assert "porcentaje derivado" in resultado.output


def test_formato_desconocido_falla() -> None:
    resultado = _correr(str(MINI), "--decisiones", str(DECISIONES), "--formato", "xml")
    assert resultado.exit_code != 0


def test_sin_decisiones_del_programa_falla_con_el_nombre_del_archivo(tmp_path: Path) -> None:
    resultado = _correr(str(MINI), "--decisiones", str(tmp_path))
    assert resultado.exit_code != 0
    assert "no existe" in resultado.output


def test_programa_inexistente_falla() -> None:
    resultado = _correr(str(FIXTURES / "no_existe.sas"), "--decisiones", str(DECISIONES))
    assert resultado.exit_code != 0
