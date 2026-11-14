"""Caso de SORT, eliminación de duplicados y DELETE de la rebanada K-7c."""

from __future__ import annotations

import csv
import shutil
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))

from rebanar_programa import armar, leer_rebanada, verificar  # noqa: E402

from sgm.cli_migrar import migrar  # noqa: E402
from sgm.compile import compile_file, project_base  # noqa: E402
from sgm.frontend.program import analyze_program  # noqa: E402
from sgm.seguridad.escaner_secretos import escanear_ruta  # noqa: E402
from tools.contenedores.preparar_rebanada import preparar  # noqa: E402
from tools.corpus_lib.caso import cargar_caso  # noqa: E402
from tools.corpus_lib.csv_tabla import Tabla, celda_texto  # noqa: E402
from tools.corpus_lib.esperado_interprete import calcular  # noqa: E402
from tools.datos_sinteticos.requisitos import requisitos_de_rebanada  # noqa: E402

CASE = REPO / "tests/corpus_reales/L8/k7c_sort_delete"
SOURCE = REPO / "tests/fixtures/sas/client/client_large.sas"
SORTED_ROWS = [
    ("1001", "010", "1"),
    ("1002", "020", "2"),
    ("1003", "030", "4"),
    ("1004", "040", "6"),
    ("1005", "050", "7"),
]


def _case() -> Path:
    assert CASE.is_dir(), "falta el caso K-7c"
    return CASE


def _copy_case(tmp_path: Path) -> Path:
    level = tmp_path / "L8"
    level.mkdir(parents=True, exist_ok=True)
    return shutil.copytree(_case(), level / "k7c_sort_delete")


def test_rebanada_k7c_verifica_hash_y_conserva_el_texto_original():
    case = _case()
    slice_ = leer_rebanada(case / "rebanada.yaml")
    with SOURCE.open(encoding="utf-8", newline="") as source:
        source_text = source.read()

    assert slice_.rangos == ((45, 57), (15816, 15819))
    assert verificar(slice_, REPO) == []
    assert (case / "programa.sas").read_bytes() == armar(slice_, source_text).encode("utf-8")


def test_preparar_k7c_escribe_fixtures_reproducibles(tmp_path):
    first = _copy_case(tmp_path / "first")
    second = _copy_case(tmp_path / "second")
    preparar(first)
    preparar(second)

    def entries(case: Path) -> dict[str, bytes]:
        return {path.name: path.read_bytes() for path in (case / "entradas").iterdir()}

    assert entries(first) == entries(second)
    with (first / "entradas/WORK.IMPORT_CODIGOS_PAIS.csv").open(
        encoding="utf-8", newline=""
    ) as source:
        codes = list(csv.DictReader(source))
    assert len(codes) == 5
    assert [row["Codigo_Pais"] for row in codes[:3]] == ["  57", " 169", "  57"]


def test_requisitos_no_declara_intermedios_producidos_como_entradas():
    case = _case()
    requirements = requisitos_de_rebanada(
        (case / "programa.sas").read_text(encoding="utf-8"), case.name
    )

    assert "work.temporal" not in requirements.tablas_work_externas
    assert "work.sabana_completa_info_cli_nequi" in requirements.tablas_work_externas


def test_anillo_b_nodupkey_equals_conserva_primera_fila_por_llave(tmp_path):
    case_dir = _copy_case(tmp_path)
    preparar(case_dir)
    case = cargar_caso(case_dir)

    tables = calcular(case, salidas=["SABANA_DIR_UNICA_NEQUI"])

    result = tables["SABANA_DIR_UNICA_NEQUI"]
    assert [name.casefold() for name in result.columnas] == [
        "nro_doc", "nro_cta", "orden_fila"
    ]
    assert [tuple(celda_texto(value) for value in row) for row in result.filas] == SORTED_ROWS
    with (case_dir / "esperado/SABANA_DIR_UNICA_NEQUI.csv").open(
        encoding="utf-8", newline=""
    ) as expected:
        rows = list(csv.reader(expected))
    assert [name.casefold() for name in rows[0]] == [
        name.casefold() for name in result.columnas
    ]
    assert rows[1:] == [list(row) for row in SORTED_ROWS]


def test_delete_work_se_registra_como_limpieza_y_temporal_no_es_salida(tmp_path):
    case_dir = _copy_case(tmp_path)
    preparar(case_dir)
    case = cargar_caso(case_dir)
    text = case.programa.read_text(encoding="utf-8")
    plan = compile_file(analyze_program({case.programa.name: text}), case.programa.name,
                        project_base()).plan
    tables = calcular(case)
    assert "TEMPORAL" not in {name.upper() for name in case.salidas}
    assert set(tables) == {"SABANA_DIR_UNICA_NEQUI"}
    assert any(
        "proc delete" in item.what.lower() and "work" in item.what.lower()
        for item in plan.not_migrated
    )


@pytest.mark.xfail(
    strict=True,
    reason="el intérprete aún no aplica RENAME= del SET antes de evaluar INPUT/COMPRESS",
)
def test_interprete_mide_conversion_numero_a_texto_sin_suponerla(tmp_path):
    case_dir = _copy_case(tmp_path)
    preparar(case_dir)
    case = cargar_caso(case_dir)

    result = calcular(case, salidas=["IMPORT_CODIGOS_PAIS"])["IMPORT_CODIGOS_PAIS"]

    assert result == Tabla(
        ["Codigo_Pais"],
        [("57",), ("169",), ("57",), ("170",), ("170",)],
    )


def test_anillo_a_informa_fuente_sort_ausente_y_delete_sin_fallo_interno(tmp_path):
    case = _case()
    result = migrar(case / "programa.sas", tmp_path / "out")
    text = (case / "programa.sas").read_text(encoding="utf-8")
    plan = compile_file(analyze_program({"programa.sas": text}), "programa.sas",
                        project_base()).plan
    dedup = next(op for op in plan.graph.operators() if op.kind == "dedup")

    assert result.jobs
    assert dedup.status == "parcial"
    assert "estabilidad de tsortrow" in " ".join(dedup.notes).casefold()
    pending_codes = {item.codigo for item in result.pendientes}
    assert "P-FALLO-INTERNO" not in pending_codes
    assert any("sort" in item.mensaje.lower() and "entrada" in item.mensaje.lower()
               for item in result.pendientes)


def test_k7c_caso_y_job_no_exponen_secretos(tmp_path):
    case = _case()
    result = migrar(case / "programa.sas", tmp_path / "out")

    assert escanear_ruta(case).hallazgos == ()
    assert escanear_ruta(result.carpeta).hallazgos == ()
