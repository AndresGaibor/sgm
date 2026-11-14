"""Mapa de contexto que el ayudante de Studio deduce o lee desde un caso."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))

import validar_caso_studio  # noqa: E402
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


def test_mapa_explicito_del_caso_cubre_todas_las_variables(tmp_path):
    (tmp_path / "mapa.yaml").write_text(
        "ruta_base_clientes_nequi: entradas/Base_datos_Nequi.csv\n"
        "ruta_fa_no_vigentes_aho: salida/FA_NO_VIGENTES_AHO.csv\n",
        encoding="utf-8",
    )
    assert validar_caso_studio._mapa_del_caso(
        tmp_path,
        ["ruta_base_clientes_nequi", "ruta_fa_no_vigentes_aho"],
        ["Base_datos_Nequi.csv"],
        ["FA_NO_VIGENTES_AHO"],
    ) == {
        "ruta_base_clientes_nequi": "entradas/Base_datos_Nequi.csv",
        "ruta_fa_no_vigentes_aho": "salida/FA_NO_VIGENTES_AHO.csv",
    }


def test_mapa_explicito_rechaza_variables_sin_ruta(tmp_path):
    (tmp_path / "mapa.yaml").write_text("ruta_clientes: entradas/clientes.csv\n", encoding="utf-8")
    with pytest.raises(ValueError, match="variables sin mapa"):
        validar_caso_studio._mapa_del_caso(tmp_path, ["ruta_clientes", "ruta_final"], [], [])


def test_variable_sin_archivo_conocido_se_rechaza() -> None:
    try:
        mapa_de_contexto(["ruta_fantasma"], entradas=["A.csv"], salidas=["B"])
    except ValueError as error:
        assert "ruta_fantasma" in str(error)
    else:  # pragma: no cover
        raise AssertionError("debía rechazar la variable sin archivo")


def test_encuentra_casos_del_corpus_real(tmp_path, monkeypatch):
    raiz = tmp_path
    caso = raiz / "tests/corpus_reales/L8/ejemplo"
    caso.mkdir(parents=True)
    monkeypatch.setattr(validar_caso_studio, "RAIZ", raiz)

    assert validar_caso_studio._caso("ejemplo") == caso


def test_rechaza_nombres_duplicados_entre_los_corpus(tmp_path, monkeypatch):
    raiz = tmp_path
    for corpus in ("corpus", "corpus_reales"):
        (raiz / "tests" / corpus / "L8" / "ejemplo").mkdir(parents=True)
    monkeypatch.setattr(validar_caso_studio, "RAIZ", raiz)

    with pytest.raises(SystemExit, match="ambiguo"):
        validar_caso_studio._caso("ejemplo")


def test_validar_pasa_la_raiz_del_corpus_real_al_arnes(tmp_path, monkeypatch):
    raiz = tmp_path
    caso = raiz / "tests/corpus_reales/L8/ejemplo"
    (caso / "entradas").mkdir(parents=True)
    (caso / "programa.sas").write_text("data x; run;", encoding="utf-8")
    (caso / "caso.yaml").write_text("salidas: []\n", encoding="utf-8")
    monkeypatch.setattr(validar_caso_studio, "RAIZ", raiz)
    comandos = []

    def correr(argumentos):
        comandos.append(argumentos)
        if "migrar" in argumentos:
            destino = Path(argumentos[argumentos.index("--out") + 1]) / "programa"
            (destino / "process").mkdir(parents=True)
            (destino / "contextos").mkdir()
            (destino / "contextos/Default.yaml").write_text(
                "variables: []\n", encoding="utf-8"
            )
        return subprocess.CompletedProcess(argumentos, 0, "ok", "")

    monkeypatch.setattr(validar_caso_studio, "_correr", correr)

    assert validar_caso_studio.validar("ejemplo", "h1a")
    assert comandos[1][0:3] == ["tools/corpus_studio.py", "validar", "ejemplo"]
    assert comandos[1][comandos[1].index("--corpus") + 1] == str(
        raiz / "tests/corpus_reales"
    )
