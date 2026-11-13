"""Mapa y huellas literales de las cinco rebanadas de client_large."""

from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))

from rebanar_programa import Rebanada, huella, rebanar, verificar  # noqa: E402

from sgm.agrupacion import cargar_declaracion  # noqa: E402
from sgm.flow.regiones import dividir_regiones, region_de_linea  # noqa: E402
from sgm.seguridad.escaner_secretos import escanear_ruta, escanear_texto  # noqa: E402

MANIFEST = REPO / "decisiones/client_large.rebanadas.yaml"
SOURCE = REPO / "tests/fixtures/sas/client/client_large.sas"
SOURCE_RELATIVE = "tests/fixtures/sas/client/client_large.sas"
UNSAFE_PASS = re.compile(r"\bpass\s*=\s*(['\"])(?!\*\*\*\1)[^'\"]*\1", re.IGNORECASE)
UNSAFE_PWENCODE = re.compile(
    r"\bpwencode\s+in\s*=\s*(['\"])(?!\*\*\*\1)[^'\"]*\1", re.IGNORECASE
)

EXPECTED = {
    "k7a_import_export": (
        "IMPORT/EXPORT",
        ((5, 13), (160, 164), (24263, 24267)),
        ("K-1", "K-8", "K-10"),
    ),
    "k7b_sql_impala": (
        "SQL a Impala",
        ((166, 181), (183, 212)),
        ("K-3", "K-4", "K-13", "MG-P2-05"),
    ),
    "k7c_sort_delete": (
        "SORT/DELETE",
        ((45, 57), (15816, 15819)),
        ("B-3", "B-8"),
    ),
    "k7d_upload_download": (
        "UPLOAD/DOWNLOAD",
        ((146, 164), (24263, 24278)),
        ("K-5",),
    ),
    "k7e_totales": ("totales", ((24615, 24653),), ("K-10",)),
}


def _entries() -> list[dict[str, object]]:
    assert MANIFEST.is_file(), "falta el mapa decisiones/client_large.rebanadas.yaml"
    data = yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))
    assert isinstance(data, list), "el mapa debe ser una lista de rebanadas"
    return data


def _source_text() -> str:
    with SOURCE.open(encoding="utf-8", newline="") as source:
        return source.read()


def _slice(entry: dict[str, object]) -> Rebanada:
    return Rebanada(
        fuente=str(entry["fuente"]),
        rangos=tuple(tuple(span) for span in entry["rangos"]),
        sha256=str(entry["sha256"]),
    )


def test_mapa_declara_las_cinco_rebanadas_y_sus_dependencias():
    entries = _entries()

    assert len(entries) == len(EXPECTED)
    assert {entry["id"] for entry in entries} == set(EXPECTED)
    for entry in entries:
        assert set(entry) == {"id", "tipo", "fuente", "rangos", "sha256", "depende_de"}
        kind, spans, dependencies = EXPECTED[entry["id"]]
        assert entry["tipo"] == kind
        assert entry["fuente"] == SOURCE_RELATIVE
        assert tuple(tuple(span) for span in entry["rangos"]) == spans
        assert tuple(entry["depende_de"]) == dependencies


def test_huellas_corresponden_a_los_fragmentos_literales():
    text = _source_text()
    entries = _entries()

    for entry in entries:
        slice_ = _slice(entry)
        assert slice_.sha256 == huella(rebanar(text, slice_.rangos))
        assert verificar(slice_, REPO) == []


def test_rebanadas_quedan_en_las_regiones_medidas_del_programa():
    declaration = cargar_declaracion(REPO / "decisiones/client_large.agrupacion.yaml")
    regions = dividir_regiones(_source_text(), declaration.marcador)
    expected = {
        "k7a_import_export": (0, 0, 29),
        "k7b_sql_impala": (0, 0),
        "k7c_sort_delete": (0, 17),
        "k7d_upload_download": (0, 29),
        "k7e_totales": (29,),
    }

    assert len(regions) == 30
    for entry in _entries():
        actual = tuple(region_de_linea(regions, span[0]) for span in entry["rangos"])
        assert actual == expected[entry["id"]]


def test_rebanadas_excluyen_la_introspeccion_de_work():
    text = _source_text()

    for entry in _entries():
        fragment = rebanar(text, tuple(tuple(span) for span in entry["rangos"]))
        assert not re.search(r"(?im)^\s*proc\s+contents\s+data\s*=\s*work\._all_\b", fragment)


def test_rebanadas_y_fixture_no_exponen_secretos():
    text = _source_text()

    for entry in _entries():
        fragment = rebanar(text, tuple(tuple(span) for span in entry["rangos"]))
        assert not UNSAFE_PASS.search(fragment), "el mapa contiene una contraseña sin enmascarar"
        assert not UNSAFE_PWENCODE.search(fragment), "el mapa contiene una clave PWENCODE sin enmascarar"
        assert escanear_texto(fragment) == []

    assert escanear_ruta(SOURCE.parent).hallazgos == ()


def test_patrones_de_secreto_rechazan_valores_que_empiezan_con_el_marcador():
    for statement in ("pass='***suffix'", "pass='*** '", "pwencode in='***suffix'"):
        assert UNSAFE_PASS.search(statement) or UNSAFE_PWENCODE.search(statement), (
            "el patrón debe permitir únicamente el marcador exacto ***"
        )


def test_patrones_de_secreto_permiten_el_marcador_exacto():
    for statement in ("pass='***'", 'pwencode in="***"'):
        assert not UNSAFE_PASS.search(statement)
        assert not UNSAFE_PWENCODE.search(statement)


def test_rebanada_upload_download_conserva_las_senales_de_transferencia():
    entry = next(row for row in _entries() if row["id"] == "k7d_upload_download")
    fragment = rebanar(_source_text(), tuple(tuple(span) for span in entry["rangos"]))

    assert "RSUBMIT server;" in fragment
    assert 'PROC UPLOAD INFILE="/work_sasstudio/pcfiles/FA_NO_VIGENTES_AHO.csv"' in fragment
