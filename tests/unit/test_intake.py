"""`sgm intake` (F1.7): UTF-8, sin secretos, compilado y huecos registrados en la base temporal."""

import json

import pytest

from sgm.catalog.config import Env
from sgm.intake import intake
from sgm.store import gaps as gap_store
from sgm.store.db import Store

SECRETO = "claveSECRETA123"
PROGRAMA = (
    "/* programa con acentos: año, señal */\n"
    f"proc pwencode in='{SECRETO}' out=work.clave;\nrun;\n"
    "proc transpose data=a out=b;\n  by x;\n  id y;\n  var z;\nrun;\n"
    "data c;\n  set b;\n  nota = 'año de señal';\nrun;\n"
).encode("cp1252")


@pytest.fixture
def base(tmp_path, monkeypatch):
    monkeypatch.setenv("SGM_DB", str(tmp_path / "sgm.sqlite"))
    return tmp_path


def _lote(tmp_path):
    fuente = tmp_path / "lote"
    fuente.mkdir()
    (fuente / "programa.sas").write_bytes(PROGRAMA)
    return fuente


def test_lote_queda_en_utf8_sin_secretos(base):
    resultado = intake(_lote(base), env=Env(), inbox=base / "inbox")
    fuente = resultado.carpeta / "fuente" / "programa.sas"
    texto = fuente.read_text(encoding="utf-8")
    assert "año" in texto and "señal" in texto
    assert SECRETO not in texto
    assert resultado.lineas_redactadas >= 1
    assert resultado.codificaciones.get("cp1252") == 1


def test_salida_no_contiene_el_secreto(base):
    resultado = intake(_lote(base), env=Env(), inbox=base / "inbox")
    for ruta in (resultado.carpeta / "salida").iterdir():
        assert SECRETO not in ruta.read_text(encoding="utf-8"), ruta.name
    assert any(p.name.endswith(".guide.md") for p in (resultado.carpeta / "salida").iterdir())


def test_huecos_del_lote_quedan_registrados_y_filtrables(base):
    resultado = intake(_lote(base), env=Env(), inbox=base / "inbox")
    huecos = json.loads((resultado.carpeta / "huecos.json").read_text(encoding="utf-8"))
    assert "PROC_NO_SOPORTADO" in {h["reason"] for h in huecos}
    with Store() as store:
        filas = gap_store.top(store, 50, file="programa.sas")
    assert any(f["reason"] == "PROC_NO_SOPORTADO" for f in filas)


def test_el_mismo_lote_cae_en_la_misma_carpeta(base):
    fuente = _lote(base)
    primero = intake(fuente, env=Env(), inbox=base / "inbox")
    segundo = intake(fuente, env=Env(), inbox=base / "inbox")
    assert primero.carpeta == segundo.carpeta
    assert [p.name for p in (base / "inbox").iterdir()] == [primero.carpeta.name]


def test_un_archivo_suelto_tambien_entra(base):
    origen = base / "suelto.sas"
    origen.write_bytes(PROGRAMA)
    resultado = intake(origen, env=Env(), inbox=base / "inbox")
    assert (resultado.carpeta / "fuente" / "suelto.sas").exists()
    assert resultado.programas == 1


def test_fuente_inexistente_falla_con_mensaje(base):
    with pytest.raises(FileNotFoundError):
        intake(base / "no-existe", env=Env(), inbox=base / "inbox")
