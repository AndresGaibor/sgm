"""Hito 89: los comparadores de `v05` y de los vectores propios detectan una sola fila cambiada.

Los esperados salen del corpus `v05_codex_saldos` y de la clasificación escrita a mano en
`VECTORES`; ninguno se calcula con el traductor Java. Se comparan solo las columnas estables por
nombre, porque R1-02 normaliza 15 columnas del SAS real (salvedad medida en el hito 85).
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))

from cuenta_real_datos import (  # noqa: E402
    ARCHIVOS,
    ESTABLES,
    ESTABLES_CUENTA,
    MODOS,
    PRODUCTOS,
    SUFIJO_VECTORES,
    VECTORES,
    anomalias_plantadas,
    esperado,
    esperado_vectores,
    informe,
    informe_vectores,
    invariantes,
    observado,
    vector_csv,
)


def _escribir(ruta: Path, columnas: tuple[str, ...], filas: list[tuple[str, ...]]) -> None:
    with ruta.open("w", encoding="utf-8", newline="") as archivo:
        escritor = csv.writer(archivo, delimiter=",", lineterminator="\n")
        escritor.writerow(columnas)
        escritor.writerows(filas)


def _salida(tmp_path: Path, producto: str) -> Path:
    """Cuatro CSV con cabecera, escritos desde los esperados del corpus, sin Studio."""
    salida = tmp_path / f"salida-{producto}"
    salida.mkdir()
    sabana = esperado(producto, "sabana", ESTABLES)
    codex = esperado(producto, "codex", ESTABLES)
    datos = {
        "tipo_cta": [],
        "codex": codex,
        "valido": [fila for fila in sabana if fila not in codex],
        "cuenta": esperado(producto, "cuenta", ESTABLES_CUENTA),
    }
    for modo, filas in datos.items():
        columnas = ESTABLES_CUENTA if modo == "cuenta" else ESTABLES
        _escribir(salida / ARCHIVOS[modo].format(p=producto), columnas, filas)
    return salida


def test_las_cifras_del_caso_siguen_siendo_las_plantadas():
    assert anomalias_plantadas() == {
        "cte": {"codex_invalido": 3, "saldo_negativo": 4, "validos": 83},
        "aho": {"codex_invalido": 2, "saldo_negativo": 5, "validos": 58},
    }


def test_la_sabana_cubre_validos_rechazos_y_saldos_negativos():
    for producto in PRODUCTOS:
        plantadas = anomalias_plantadas()[producto.casefold()]
        sabana = len(esperado(producto, "sabana", ("RELACION",)))
        codex = len(esperado(producto, "codex"))
        saldo = len(esperado(producto, "saldo", ("NRO_CTA",)))
        assert codex == plantadas["codex_invalido"]
        assert saldo == plantadas["saldo_negativo"]
        assert sabana == plantadas["validos"] + codex + saldo


def test_el_informe_da_ok_con_los_esperados_proyectados(tmp_path, capsys):
    for producto in PRODUCTOS:
        assert informe(producto, observado(_salida(tmp_path, producto), producto)) is True
    assert "DIFERENCIA" not in capsys.readouterr().out


def test_el_informe_detecta_una_sola_fila_cambiada(tmp_path, capsys):
    salida = _salida(tmp_path, "CTE")
    ruta = salida / ARCHIVOS["codex"].format(p="CTE")
    filas = list(csv.reader(ruta.open(encoding="utf-8", newline=""), delimiter=","))
    filas[1][2] = "9999999999"
    with ruta.open("w", encoding="utf-8", newline="") as archivo:
        csv.writer(archivo, delimiter=",", lineterminator="\n").writerows(filas)

    assert informe("CTE", observado(salida, "CTE")) is False
    assert "DIFERENCIA" in capsys.readouterr().out


def test_el_informe_detecta_un_rechazo_de_tipo_cta_inventado(tmp_path, capsys):
    salida = _salida(tmp_path, "CTE")
    ruta = salida / ARCHIVOS["tipo_cta"].format(p="CTE")
    _escribir(ruta, ESTABLES, [("1000", "9", "9999999999", "11", "12001")])

    assert informe("CTE", observado(salida, "CTE")) is False
    assert "DIFERENCIA" in capsys.readouterr().out


def test_las_invariantes_se_cumplen_con_los_esperados(tmp_path, capsys):
    resultados = {
        p: observado(_salida(tmp_path, p), p) for p in PRODUCTOS
    }

    assert invariantes(resultados) is True
    assert "codex del corpus=5 frente a 5" in capsys.readouterr().out


def test_las_invariantes_fallan_si_falta_una_fila_de_codex(tmp_path, capsys):
    resultados = {p: observado(_salida(tmp_path, p), p) for p in PRODUCTOS}
    resultados["CTE"] = {**resultados["CTE"], "codex": resultados["CTE"]["codex"][:-1]}

    assert invariantes(resultados) is False
    assert "NO" in capsys.readouterr().out


def test_vector_csv_escribe_23_campos_y_conserva_el_gmf_faltante(tmp_path):
    ruta = vector_csv(tmp_path / "DETALLE_VECTORES.csv")
    filas = list(csv.reader(ruta.open(encoding="utf-8", newline=""), delimiter=";"))

    assert len(filas) == len(VECTORES) == 8
    assert all(len(fila) == 23 for fila in filas)
    assert filas[0][3] == "1000" and filas[0][5] == "9" and filas[0][6] == "9000000001"
    assert filas[2][10] == ""  # GMF faltante del SAS, no un cero inventado
    assert filas[3][3] == "1001"  # RELACION <> 1000 queda exenta


def test_los_vectores_estan_clasificados_a_mano_y_la_cascada_prioriza_tipo_cta():
    esp = esperado_vectores()

    assert set(esp) == set(MODOS)
    assert {modo: len(filas) for modo, filas in esp.items()} == {
        "tipo_cta": 2, "codex": 2, "valido": 4, "cuenta": 4,
    }
    # TIPO_CTA=9 y GMF=11 violan las dos reglas: el SAS evalúa el codex después del tipo de cuenta.
    assert ("9000000001", "TIPO CTA INVALIDO") in esp["cuenta"]
    assert ("9000000008", "TIPO CTA INVALIDO") in esp["cuenta"]  # TIPO_CTA no numérico
    assert ("9000000004", "") not in esp["cuenta"]  # RELACION=1001 exento


def test_informe_vectores_compara_los_cuatro_flujos_y_detecta_un_motivo_cambiado(tmp_path, capsys):
    salida = tmp_path / "vectores"
    salida.mkdir()
    esp = esperado_vectores()
    for modo in MODOS:
        columnas = ("NRO_CTA", "INCONSISTENCIA") if modo == "cuenta" else ("NRO_CTA",)
        _escribir(salida / ARCHIVOS[modo].format(p=SUFIJO_VECTORES), columnas, esp[modo])

    assert informe_vectores(salida) is True
    filas = esp["cuenta"][:]
    filas[0] = (filas[0][0], "GMF NO NUMERICO")
    _escribir(
        salida / ARCHIVOS["cuenta"].format(p=SUFIJO_VECTORES),
        ("NRO_CTA", "INCONSISTENCIA"),
        filas,
    )
    assert informe_vectores(salida) is False
    assert "DIFERENCIA" in capsys.readouterr().out
