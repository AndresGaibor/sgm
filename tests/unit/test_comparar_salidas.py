"""Fase 5.8 de `docs/automatizacion/03-plan-produccion.md`: comparación de salidas SAS y Talend."""

from __future__ import annotations

from pathlib import Path

from sgm.verify import comparar


def _csv(ruta: Path, texto: str) -> Path:
    ruta.write_text(texto, encoding="utf-8")
    return ruta


def test_mismos_datos_en_otro_orden_coinciden(tmp_path: Path) -> None:
    a = _csv(tmp_path / "sas.csv", "id;saldo\n1;10,5\n2;4\n")
    b = _csv(tmp_path / "talend.csv", "id;saldo\n2;4\n1;10,5\n")
    informe = comparar(a, b)
    assert informe.coincide
    assert informe.sumas["saldo"] == (14.5, 14.5)


def test_suma_distinta_no_coincide(tmp_path: Path) -> None:
    a = _csv(tmp_path / "sas.csv", "id;saldo\n1;10\n")
    b = _csv(tmp_path / "talend.csv", "id;saldo\n1;11\n")
    assert not comparar(a, b).coincide


def test_fila_de_mas_no_coincide(tmp_path: Path) -> None:
    a = _csv(tmp_path / "sas.csv", "id\n1\n2\n")
    b = _csv(tmp_path / "talend.csv", "id\n1\n")
    informe = comparar(a, b)
    assert informe.filas == (2, 1)
    assert not informe.coincide


def test_cabeceras_distintas_no_coinciden(tmp_path: Path) -> None:
    a = _csv(tmp_path / "sas.csv", "id;saldo\n1;1\n")
    b = _csv(tmp_path / "talend.csv", "id;total\n1;1\n")
    assert not comparar(a, b).coincide
