"""Caso K-7d: archivos trasladados entre el equipo y SAS/CONNECT."""

from __future__ import annotations

import csv
import shutil
import sys
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))

from rebanar_programa import armar, leer_rebanada, verificar  # noqa: E402
from validar_caso_studio import mapa_de_contexto  # noqa: E402

from sgm.cli_migrar import migrar  # noqa: E402
from sgm.compile import compile_file, project_base  # noqa: E402
from sgm.frontend.program import analyze_program  # noqa: E402
from sgm.ir.pase_copias_remotas import aplicar_copias, copias_remotas  # noqa: E402
from sgm.seguridad.escaner_secretos import escanear_ruta  # noqa: E402
from sgm.talend_item.desde_plan_contextos import rutas_de_plan  # noqa: E402
from tools.contenedores.preparar_rebanada import preparar  # noqa: E402
from tools.corpus_lib.caso import cargar_caso  # noqa: E402
from tools.corpus_lib.csv_tabla import comparar_con_guardado, leer_entradas  # noqa: E402
from tools.corpus_lib.esperado_interprete import calcular, escribir  # noqa: E402
from tools.corpus_lib.studio_mapa import leer_mapa  # noqa: E402

CASE = REPO / "tests/corpus_reales/L8/k7d_upload_download"
SOURCE = REPO / "tests/fixtures/sas/client/client_large.sas"
REMOTE_INPUT = r"\\sbcldwpsgf01\FILE_VSPC_FINANZAS\Base_datos_Nequi.csv"
REMOTE_OUTPUT = (
    r"\\sbcldwpsgf01\FILE_VSPC_FINANZAS\GST_Informacion_Exogena\RESULTADOS"
    r"\FA_NO_VIGENTES_AHO.csv"
)
LOCAL_TEMP = "/work_sasstudio/pcfiles/"


def _case() -> Path:
    assert CASE.is_dir(), "falta el caso K-7d"
    return CASE


def _copy_case(tmp_path: Path) -> Path:
    level = tmp_path / "L8"
    level.mkdir(parents=True, exist_ok=True)
    return shutil.copytree(_case(), level / "k7d_upload_download")


def _programa_import_export() -> str:
    """Solo los dos PROC del caso; el intérprete no ejecuta SAS/CONNECT."""
    lines = SOURCE.read_text(encoding="utf-8").splitlines(keepends=True)
    return "".join((*lines[159:164], *lines[24262:24267]))


def test_rebanada_k7d_verifica_hash_y_conserva_sus_rangos():
    case = _case()
    slice_ = leer_rebanada(case / "rebanada.yaml")
    with SOURCE.open(encoding="utf-8", newline="") as source:
        source_text = source.read()

    assert slice_.rangos == ((146, 164), (24263, 24278))
    assert verificar(slice_, REPO) == []
    assert (case / "programa.sas").read_bytes() == armar(slice_, source_text).encode("utf-8")
    text = (case / "programa.sas").read_text(encoding="utf-8")
    assert "RSUBMIT server;" in text
    assert "PROC UPLOAD INFILE=" in text


def test_k7d_resuelve_descarga_y_carga_a_rutas_de_red_sin_pendientes():
    case = _case()
    text = (case / "programa.sas").read_text(encoding="utf-8")
    copies, pending = copias_remotas(text)

    assert [(copy.sentido, copy.infile, copy.outfile) for copy in copies] == [
        (
            "download",
            REMOTE_INPUT,
            f"{LOCAL_TEMP}Base_datos_Nequi.csv",
        ),
        (
            "upload",
            f"{LOCAL_TEMP}FA_NO_VIGENTES_AHO.csv",
            REMOTE_OUTPUT,
        ),
    ]
    assert pending == []

    plan = compile_file(analyze_program({"programa.sas": text}), "programa.sas",
                        project_base()).plan
    plan, unmatched = aplicar_copias(plan, copies)

    assert unmatched == []
    assert rutas_de_plan(plan) == {
        REMOTE_INPUT: "ruta_base_clientes_nequi",
        REMOTE_OUTPUT: "ruta_fa_no_vigentes_aho",
    }
    for op in plan.graph.operators():
        if op.kind in {"read_file", "write_file"}:
            assert LOCAL_TEMP not in str(op.params)


def test_anillo_a_expone_rutas_remotas_en_default_y_oculta_el_temporal(tmp_path):
    case = _copy_case(tmp_path)
    preparar(case)
    result = migrar(case / "programa.sas", tmp_path / "out", muestra=case / "entradas")

    context_path = result.carpeta / "contextos/Default.yaml"
    assert context_path.is_file()
    context = yaml.safe_load(context_path.read_text(encoding="utf-8"))
    variables = {item["nombre"]: item["valor"] for item in context["variables"]}
    assert variables["ruta_base_clientes_nequi"] == REMOTE_INPUT
    assert variables["ruta_fa_no_vigentes_aho"] == REMOTE_OUTPUT
    assert all(LOCAL_TEMP not in str(item) for item in context["variables"])

    process_text = "\n".join(
        path.read_text(encoding="utf-8") for path in (result.carpeta / "process").rglob("*.item")
    )
    assert LOCAL_TEMP not in process_text
    pending_text = (result.carpeta / "pendientes.md").read_text(encoding="utf-8").casefold()
    assert "signon" not in pending_text
    assert "pass" not in pending_text
    assert "***" not in pending_text
    assert escanear_ruta(case).hallazgos == ()
    assert escanear_ruta(result.carpeta).hallazgos == ()


def test_mapa_generico_detecta_la_diferencia_y_el_mapa_del_caso_la_resuelve():
    with pytest.raises(ValueError, match="sin entrada ni salida"):
        mapa_de_contexto(
            ["ruta_base_clientes_nequi", "ruta_fa_no_vigentes_aho"],
            ["Base_datos_Nequi.csv"],
            ["FA_NO_VIGENTES_AHO"],
        )

    assert leer_mapa(_case() / "mapa.yaml") == {
        "ruta_base_clientes_nequi": "entradas/Base_datos_Nequi.csv",
        "ruta_fa_no_vigentes_aho": "salida/FA_NO_VIGENTES_AHO.csv",
    }


def test_anillo_b_importa_y_exporta_sin_alterar_las_filas(tmp_path):
    case_dir = _copy_case(tmp_path)
    # Las copias SAS/CONNECT no se simulan en el intérprete; ya se verifica el
    # enrutamiento remoto por separado. Aquí se valida el contrato de IMPORT/EXPORT.
    (case_dir / "programa.sas").write_text(_programa_import_export(), encoding="utf-8")
    preparar(case_dir)
    case = cargar_caso(case_dir)
    tables = calcular(case, salidas=["BASE_CLIENTES_NEQUI", *case.salidas])

    with (case_dir / "entradas/Base_datos_Nequi.csv").open(
        encoding="utf-8", newline=""
    ) as source:
        source_rows = [tuple(row) for row in csv.reader(source, delimiter=";", strict=True)]
    imported = tables["BASE_CLIENTES_NEQUI"]
    assert imported.columnas == ["VAR1", "VAR2", "VAR3"]
    assert imported.filas == source_rows

    exported = tables["FA_NO_VIGENTES_AHO"]
    source_table = leer_entradas(case_dir / "entradas")["WORK.FA_NO_VIGENTES_AHO"]
    assert exported.columnas == source_table.columnas
    assert exported.filas == source_table.filas
    assert comparar_con_guardado(
        case_dir / "esperado/FA_NO_VIGENTES_AHO.csv",
        exported,
        case.tolerancia,
        case.orden_relevante,
        delimitador=case.delimitadores_salida["FA_NO_VIGENTES_AHO"],
    ) == []
    written = escribir(case, {"FA_NO_VIGENTES_AHO": exported})
    assert [path.name for path in written] == ["FA_NO_VIGENTES_AHO.csv"]


def test_k7d_fixture_y_salida_no_exponen_secretos(tmp_path):
    case = _case()
    result = migrar(case / "programa.sas", tmp_path / "out")

    assert escanear_ruta(case).hallazgos == ()
    assert escanear_ruta(result.carpeta).hallazgos == ()
