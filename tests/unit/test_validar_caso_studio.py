"""Mapa de contexto que el ayudante `validar_caso_studio` deduce de un caso del corpus."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))

from validar_caso_studio import mapa_de_contexto  # noqa: E402


def test_entradas_existentes_y_salidas_del_esperado() -> None:
    mapa = mapa_de_contexto(
        variables=["ruta_registros", "ruta_principal", "ruta_copia"],
        entradas=["REGISTROS.csv"],
        salidas=["PRINCIPAL", "COPIA"],
    )
    assert mapa == {
        "ruta_registros": "entradas/REGISTROS.csv",
        "ruta_principal": "salida/PRINCIPAL.csv",
        "ruta_copia": "salida/COPIA.csv",
    }


def test_la_coincidencia_no_distingue_mayusculas() -> None:
    mapa = mapa_de_contexto(["ruta_clientes"], entradas=["Clientes.csv"], salidas=[])
    assert mapa == {"ruta_clientes": "entradas/Clientes.csv"}


def test_variable_sin_archivo_conocido_se_rechaza() -> None:
    try:
        mapa_de_contexto(["ruta_fantasma"], entradas=["A.csv"], salidas=["B"])
    except ValueError as error:
        assert "ruta_fantasma" in str(error)
    else:  # pragma: no cover
        raise AssertionError("debía rechazar la variable sin archivo")
