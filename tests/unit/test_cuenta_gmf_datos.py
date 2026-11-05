"""Hito 88: los esperados de `v04` son independientes del Job y se comparan fila por fila."""

from __future__ import annotations

import csv
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))

from cuenta_gmf_datos import (  # noqa: E402
    ARCHIVOS,
    CASO,
    MODOS,
    PRODUCTOS,
    SALIDAS,
    anomalias,
    anomalias_plantadas,
    esperado,
    informe,
    invariantes,
    observado,
)


def _copiar_esperados(destino: Path, producto: str = "CTE") -> Path:
    """Un directorio de salida con los esperados, para probar el comparador sin Studio."""
    carpeta = destino / "salida" / producto
    carpeta.mkdir(parents=True)
    for modo, nombre in ARCHIVOS.items():
        shutil.copyfile(CASO / "esperado" / nombre.format(p=producto), carpeta / SALIDAS[modo])
    return carpeta


def test_las_cuatro_tablas_esperadas_tienen_las_filas_plantadas():
    for producto in PRODUCTOS:
        esp = esperado(producto)
        plantadas = anomalias_plantadas()[producto]
        assert set(esp) == set(MODOS)
        assert len(esp["tipo_cta"]) == plantadas["tipo_cta_invalido"]
        assert len(esp["gmf"]) == plantadas["gmf_invalido"] + plantadas["gmf_fuera_rango"]
        assert len(esp["valido"]) == plantadas["validos"]
        assert len(esp["cuenta"]) == len(esp["tipo_cta"]) + len(esp["gmf"])


def test_el_desglose_por_motivo_reproduce_las_anomalias_plantadas():
    for producto in PRODUCTOS:
        esp = esperado(producto)
        conteo = anomalias(esp["cuenta"])
        plantadas = anomalias_plantadas()[producto]

        assert conteo["tipo_cta_invalido"] == plantadas["tipo_cta_invalido"]
        assert conteo["gmf_invalido"] == plantadas["gmf_invalido"]
        assert conteo["gmf_fuera_rango"] == plantadas["gmf_fuera_rango"]


def test_el_informe_da_ok_cuando_el_job_escribio_lo_esperado(tmp_path, capsys):
    for producto in PRODUCTOS:
        carpeta = _copiar_esperados(tmp_path, producto)
        assert informe(producto, esperado(producto), observado(carpeta)) is True
    assert "DIFERENCIA" not in capsys.readouterr().out


def test_el_informe_detecta_una_sola_fila_cambiada(tmp_path, capsys):
    carpeta = _copiar_esperados(tmp_path)
    ruta = carpeta / SALIDAS["cuenta"]
    filas = list(csv.reader(ruta.open(encoding="utf-8", newline=""), delimiter=","))
    filas[1][-1] = "GMF FUERA DE RANGO"
    with ruta.open("w", encoding="utf-8", newline="") as archivo:
        csv.writer(archivo, delimiter=",").writerows(filas)

    assert informe("CTE", esperado("CTE"), observado(carpeta)) is False
    assert "DIFERENCIA" in capsys.readouterr().out


def test_las_invariantes_se_cumplen_con_los_esperados():
    resultados = {p: esperado(p) for p in PRODUCTOS}

    assert invariantes(resultados) is True


def test_las_invariantes_fallan_si_falta_una_fila_de_rechazo(capsys):
    resultados = {p: esperado(p) for p in PRODUCTOS}
    resultados["CTE"] = {
        **resultados["CTE"],
        "cuenta": resultados["CTE"]["cuenta"][:-1],
    }

    assert invariantes(resultados) is False
    assert "NO" in capsys.readouterr().out


def test_las_cifras_del_caso_siguen_siendo_las_plantadas():
    assert anomalias_plantadas() == {
        "CTE": {"tipo_cta_invalido": 4, "gmf_invalido": 2, "gmf_fuera_rango": 3, "validos": 81},
        "AHO": {"tipo_cta_invalido": 6, "gmf_invalido": 1, "gmf_fuera_rango": 2, "validos": 56},
    }
