"""Caso sintético de las dos tablas de totales de la rebanada K-7e."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))

from rebanar_programa import armar, leer_rebanada, verificar  # noqa: E402

from sgm.cli_migrar import migrar  # noqa: E402
from sgm.compile import compile_file, project_base  # noqa: E402
from sgm.frontend.program import analyze_program  # noqa: E402
from sgm.ir.desplegar import plan_desplegado  # noqa: E402
from sgm.seguridad.escaner_secretos import escanear_ruta  # noqa: E402
from tools.contenedores.preparar_rebanada import preparar  # noqa: E402
from tools.corpus_lib.caso import cargar_caso  # noqa: E402
from tools.corpus_lib.csv_tabla import comparar_con_guardado  # noqa: E402
from tools.corpus_lib.esperado_interprete import calcular, escribir  # noqa: E402
from tools.datos_sinteticos.requisitos import requisitos_de_rebanada  # noqa: E402

CASE = REPO / "tests/corpus_reales/L8/k7e_totales"
SOURCE = REPO / "tests/fixtures/sas/client/client_large.sas"
INPUT_COLUMNS = [
    "FIN_SALDO_CTA",
    "PROM_SALDO_CTA",
    "MED_SALDO_CTA",
    "MAX_SALDO_CTA",
    "MIN_SALDO_CTA",
    "VAL_CRED_MES",
    "NRO_CRED_MES",
    "PROM_CRED_MES",
    "MED_CRED_MES",
    "VAL_DEB_MES",
    "NRO_DEB_MES",
    "PROM_DEB_MES",
]
OUTPUT_COLUMNS = [
    "FIN_SAL_CTA",
    "PROM_SAL_CTA",
    "MED_SAL_CTA",
    "MAX_SAL_CTA",
    "MIN_SAL_CTA",
    "VAL_CRED_MES",
    "NRO_CRED_MES",
    "PROM_CRED_MES",
    "MED_CRED_MES",
    "VAL_DEB_MES",
    "NRO_DEB_MES",
    "PROM_DEB_MES",
]


def _case() -> Path:
    assert CASE.is_dir(), "falta el caso K-7e"
    return CASE


def _copy_case(tmp_path: Path) -> Path:
    level = tmp_path / "L8"
    level.mkdir(parents=True, exist_ok=True)
    return shutil.copytree(_case(), level / "k7e_totales")


def test_rebanada_k7e_verifica_hash_y_conserva_sus_rangos():
    case = _case()
    slice_ = leer_rebanada(case / "rebanada.yaml")
    with SOURCE.open(encoding="utf-8", newline="") as source:
        source_text = source.read()

    assert slice_.rangos == ((24615, 24653),)
    assert verificar(slice_, REPO) == []
    assert (case / "programa.sas").read_bytes() == armar(slice_, source_text).encode("utf-8")


def test_requisitos_k7e_cubren_las_dos_entradas_y_sus_columnas():
    requirements = requisitos_de_rebanada(
        (_case() / "programa.sas").read_text(encoding="utf-8"), "k7e_totales"
    )

    assert requirements.tablas_work_externas == {
        "work.resultado_aho_ext": INPUT_COLUMNS,
        "work.resultado_aho_nal": INPUT_COLUMNS,
    }
    assert requirements.tablas_base == {}


def test_plan_k7e_despliega_las_dos_sumatorias_sin_perder_alias():
    text = (_case() / "programa.sas").read_text(encoding="utf-8")
    plan = compile_file(analyze_program({"programa.sas": text}), "programa.sas", project_base()).plan
    expanded, _ = plan_desplegado(plan)
    aggregates = [op for op in expanded.graph.operators() if op.kind == "aggregate"]

    assert len(aggregates) == 2
    assert [op.params["outputs"] for op in aggregates] == [
        ["WORK.total_exterior"],
        ["WORK.total_nacional"],
    ]
    assert all(op.status == "soportado" and op.params["group_by"] == [] for op in aggregates)
    assert all([item["alias"].upper() for item in op.params["aggregations"]] == OUTPUT_COLUMNS
               for op in aggregates)


def test_anillo_b_suma_doce_columnas_y_escribe_las_dos_salidas(tmp_path):
    case_dir = _copy_case(tmp_path)
    generated = preparar(case_dir)
    case = cargar_caso(case_dir)
    tables = calcular(case)

    assert len(generated) == 2
    assert case.salidas == ("TOTAL_EXTERIOR", "TOTAL_NACIONAL")
    assert [column.upper() for column in tables["TOTAL_EXTERIOR"].columnas] == OUTPUT_COLUMNS
    assert tables["TOTAL_EXTERIOR"].filas == [tuple(str(value) for value in range(2, 26, 2))]
    assert [column.upper() for column in tables["TOTAL_NACIONAL"].columnas] == OUTPUT_COLUMNS
    assert tables["TOTAL_NACIONAL"].filas == [tuple(str(value) for value in range(20, 44, 2))]

    for name in case.salidas:
        assert comparar_con_guardado(
            case_dir / "esperado" / f"{name}.csv",
            tables[name],
            case.tolerancia,
            case.orden_relevante,
            delimitador=case.delimitadores_salida.get(name, ","),
        ) == []
    written = escribir(case, tables)
    assert {path.name for path in written} == {"TOTAL_EXTERIOR.csv", "TOTAL_NACIONAL.csv"}
    for path in generated:
        ficha_path = path.with_name(f"{path.stem}.ficha.yaml")
        ficha = yaml.safe_load(ficha_path.read_text(encoding="utf-8"))
        assert set(ficha["columnas"].values()) == {"Double"}


def test_anillo_a_conserva_los_origenes_ausentes_como_pendientes(tmp_path):
    case = _case()
    result = migrar(case / "programa.sas", tmp_path / "out")
    codes = {pending.codigo for pending in result.pendientes}

    assert result.jobs
    assert "P-OPERADOR-SIN-SOPORTE" in codes
    assert "P-FALLO-INTERNO" not in codes
    assert not any(node.componente for job in result.jobs for node in job.nodos)


def test_k7e_fixture_y_job_no_exponen_secretos(tmp_path):
    result = migrar(_case() / "programa.sas", tmp_path / "out")

    assert escanear_ruta(_case()).hallazgos == ()
    assert escanear_ruta(result.carpeta).hallazgos == ()
