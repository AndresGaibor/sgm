"""Caso reproducible de IMPORT/EXPORT del programa grande."""

from __future__ import annotations

import csv
import shutil
import sys
from dataclasses import replace
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))

from rebanar_programa import armar, leer_rebanada, verificar  # noqa: E402

from sgm.cli_migrar import migrar  # noqa: E402
from sgm.migrar.ficha import leer_ficha  # noqa: E402
from sgm.seguridad.escaner_secretos import escanear_ruta  # noqa: E402
from tools.contenedores.preparar_rebanada import preparar  # noqa: E402
from tools.corpus_lib.caso import cargar_caso  # noqa: E402
from tools.corpus_lib.csv_tabla import Tabla, comparar_con_guardado, leer_entradas  # noqa: E402
from tools.corpus_lib.esperado_interprete import calcular, escribir  # noqa: E402
from tools.corpus_lib.studio_informe import comparar_caso  # noqa: E402
from tools.datos_sinteticos.ficha import validar_ficha  # noqa: E402

CASE = REPO / "tests/corpus_reales/L8/k7a_import_export"
SOURCE = REPO / "tests/fixtures/sas/client/client_large.sas"


def _case() -> Path:
    assert CASE.is_dir(), "falta el caso K-7a"
    return CASE


def _copy_case(tmp_path: Path) -> Path:
    level = tmp_path / "L8"
    level.mkdir(parents=True, exist_ok=True)
    return shutil.copytree(_case(), level / "k7a_import_export")


def test_rebanada_k7a_verifica_hash_y_conserva_el_texto_original():
    case = _case()
    slice_ = leer_rebanada(case / "rebanada.yaml")
    with SOURCE.open(encoding="utf-8", newline="") as source:
        source_text = source.read()

    assert slice_.fuente == "tests/fixtures/sas/client/client_large.sas"
    assert slice_.rangos == ((5, 13), (160, 164), (24263, 24267))
    assert verificar(slice_, REPO) == []
    assert (case / "programa.sas").read_bytes() == armar(slice_, source_text).encode("utf-8")


def test_preparar_archivo_dlm_sin_cabecera_es_determinista(tmp_path):
    first = _copy_case(tmp_path / "first")
    second = _copy_case(tmp_path / "second")

    preparar(first)
    preparar(second)

    def file_bytes(case: Path) -> dict[str, bytes]:
        return {
            path.name: path.read_bytes()
            for path in sorted((case / "entradas").iterdir())
            if path.is_file()
        }

    assert file_bytes(first) == file_bytes(second)
    data_path = first / "entradas/Base_datos_Nequi.csv"
    with data_path.open(encoding="utf-8", newline="") as stream:
        rows = list(csv.reader(stream, delimiter=";", strict=True))
    assert len(rows) == 6 and all(len(row) == 3 for row in rows)
    assert rows[0] != ["VAR1", "VAR2", "VAR3"]
    assert all("," not in line for line in data_path.read_text(encoding="utf-8").splitlines())
    ficha = leer_ficha(first / "entradas/Base_datos_Nequi.ficha.yaml")
    assert ficha.origen == "sintetico" and ficha.filas == 6
    assert ficha.columnas == {"VAR1": "String", "VAR2": "String", "VAR3": "String"}
    assert ficha.cabecera is False and ficha.delimitador == ";"
    assert validar_ficha(ficha, data_path) == []


def test_ficha_sin_cabecera_rechaza_filas_con_ancho_distinto(tmp_path):
    case = _copy_case(tmp_path)
    preparar(case)
    data_path = case / "entradas/Base_datos_Nequi.csv"
    data_path.write_text("1;2;3\n4;5\n", encoding="utf-8")
    ficha = leer_ficha(case / "entradas/Base_datos_Nequi.ficha.yaml")

    errors = validar_ficha(ficha, data_path)

    assert any("línea 2: 2 campos, se esperaban 3" in error for error in errors)


def test_preparar_rechaza_archivo_fuente_fuera_de_entradas(tmp_path):
    case = _copy_case(tmp_path)
    manifest_path = case / "datos.yaml"
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    manifest["archivos"]["../escape.csv"] = manifest["archivos"].pop("Base_datos_Nequi.csv")
    manifest_path.write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")

    with pytest.raises(ValueError, match="nombre|ruta"):
        preparar(case)


def test_anillo_b_rechaza_ficha_lateral_fuera_de_entradas(tmp_path):
    case_dir = _copy_case(tmp_path)
    preparar(case_dir)
    ficha = case_dir / "entradas/Base_datos_Nequi.ficha.yaml"
    exterior = tmp_path / "ficha_exterior.yaml"
    exterior.write_text(ficha.read_text(encoding="utf-8"), encoding="utf-8")
    ficha.unlink()
    try:
        ficha.symlink_to(exterior)
    except OSError as error:
        pytest.skip(f"Windows no permite crear este symlink: {error}")
    case = cargar_caso(case_dir)

    with pytest.raises(ValueError, match="ficha del archivo sale de entradas"):
        calcular(case, salidas=["BASE_CLIENTES_NEQUI"])


def test_anillo_b_rechaza_raiz_entradas_resuelta_fuera_del_caso(tmp_path, monkeypatch):
    case_dir = _copy_case(tmp_path)
    preparar(case_dir)
    entradas = case_dir / "entradas"
    exterior = tmp_path / "entradas_exteriores"
    exterior.mkdir()
    original_resolve = Path.resolve

    def resolver_con_entradas_externa(path, *args, **kwargs):
        if path == entradas:
            return exterior.resolve()
        return original_resolve(path, *args, **kwargs)

    monkeypatch.setattr(Path, "resolve", resolver_con_entradas_externa)
    case = cargar_caso(case_dir)

    with pytest.raises(ValueError, match="raíz de entradas fuera de la carpeta del caso"):
        calcular(case, salidas=["BASE_CLIENTES_NEQUI"])


def test_anillo_a_expone_rutas_y_deja_excelcs_pendiente(tmp_path):
    case = _case()
    result = migrar(case / "programa.sas", tmp_path / "out", muestra=case / "entradas")
    context = result.carpeta / "contextos/Default.yaml"
    assert context.is_file()
    context_text = context.read_text(encoding="utf-8")
    assert "ruta_base_clientes_nequi" in context_text
    assert "ruta_fa_no_vigentes_aho" in context_text

    pending = {item.codigo: item.mensaje.casefold() for item in result.pendientes}
    assert "dbms=excelcs" in pending["P-FORMATO-SIN-SOPORTE"]
    assert "work.import_homologacion_tpo_doc" in pending["P-ESQUEMA-VACIO"]
    assert "salida final o de biblioteca permanente" in pending["P-OPERADOR-SIN-SOPORTE"]
    assert "work.fa_no_vigentes_aho" in pending["P-ESCRITURA-SIN-COLUMNAS"]
    assumptions = " ".join(cargar_caso(CASE).extra.get("supuestos", []))
    assert all(code in assumptions for code in pending)
    assert "DBMS=EXCELCS" in assumptions.upper()
    assert "no es un archivo delimitado ni de Excel" in assumptions


def test_anillo_b_importa_var1_a_var3_y_exporta_la_tabla_sin_cambios(tmp_path):
    case_dir = _copy_case(tmp_path)
    preparar(case_dir)
    case = cargar_caso(case_dir)

    tables = calcular(case, salidas=["BASE_CLIENTES_NEQUI", *case.salidas])

    with (case_dir / "entradas/Base_datos_Nequi.csv").open(
        encoding="utf-8", newline=""
    ) as stream:
        imported_rows = [tuple(row) for row in csv.reader(stream, delimiter=";", strict=True)]
    imported = tables["BASE_CLIENTES_NEQUI"]
    assert imported.columnas == ["VAR1", "VAR2", "VAR3"]
    assert imported.filas == imported_rows and len(imported.filas) == 6

    exported = tables["FA_NO_VIGENTES_AHO"]
    source = leer_entradas(case_dir / "entradas")["WORK.FA_NO_VIGENTES_AHO"]
    assert exported.columnas == source.columnas
    assert exported.filas == source.filas and len(exported.filas) == 6
    for name in case.salidas:
        table = tables[name]
        assert comparar_con_guardado(
            case_dir / "esperado" / f"{name}.csv",
            table,
            case.tolerancia,
            case.orden_relevante,
            delimitador=case.delimitadores_salida.get(name, ","),
        ) == []
    written = escribir(case, {name: tables[name] for name in case.salidas})
    assert {path.name for path in written} == {
        "FA_NO_VIGENTES_AHO.csv",
    }
    with (case_dir / "esperado/FA_NO_VIGENTES_AHO.csv").open(
        encoding="utf-8", newline=""
    ) as stream:
        assert next(csv.reader(stream, delimiter=";")) == ["NRO_DOC", "NRO_CTA"]


def test_anillo_c_compara_archivo_exportado_con_su_delimitador_sas(tmp_path):
    case = cargar_caso(_case())
    output = tmp_path / "salida"
    output.mkdir()
    shutil.copy2(case.esperado / "FA_NO_VIGENTES_AHO.csv", output)

    result = comparar_caso(case, output)

    assert result.coincide


def test_escribir_aplica_el_delimitador_correspondiente_a_cada_salida(tmp_path):
    case_dir = _copy_case(tmp_path)
    original = cargar_caso(case_dir)
    case = replace(
        original,
        salidas=("PRIMERA", "SEGUNDA"),
        delimitadores_salida={"PRIMERA": ";", "SEGUNDA": "|"},
    )
    tables = {
        "PRIMERA": Tabla(["A", "B"], [("1", "2")]),
        "SEGUNDA": Tabla(["A", "B"], [("3", "4")]),
    }

    written = escribir(case, tables)

    assert [path.name for path in written] == ["PRIMERA.csv", "SEGUNDA.csv"]
    assert (case_dir / "esperado/PRIMERA.csv").read_text(encoding="utf-8").splitlines() == [
        "A;B", "1;2"
    ]
    assert (case_dir / "esperado/SEGUNDA.csv").read_text(encoding="utf-8").splitlines() == [
        "A|B", "3|4"
    ]


def test_anillo_a_y_caso_no_exponen_secretos(tmp_path):
    case = _case()
    result = migrar(case / "programa.sas", tmp_path / "out", muestra=case / "entradas")

    assert escanear_ruta(result.carpeta).hallazgos == ()
    assert escanear_ruta(case).hallazgos == ()
