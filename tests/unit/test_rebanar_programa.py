"""Rebanadas literales trazables y esperado calculado por el intérprete existente."""

from __future__ import annotations

import hashlib
import subprocess
import sys
from itertools import islice
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))

from corpus_lib.caso import cargar_caso  # noqa: E402
from corpus_lib.csv_tabla import Tabla  # noqa: E402
from corpus_lib.esperado_interprete import _overrides, calcular, escribir  # noqa: E402
from rebanar_programa import (  # noqa: E402
    Rebanada,
    armar,
    escribir_rebanada,
    huella,
    leer_rebanada,
    rebanar,
    verificar,
)


def _case(tmp_path, source, outputs=("s",)):
    directory = tmp_path / "L8" / "c1"
    (directory / "entradas").mkdir(parents=True)
    (directory / "programa.sas").write_text(source, encoding="utf-8")
    (directory / "entradas" / "e.csv").write_text("x\n1\n2\n3\n", encoding="utf-8")
    (directory / "caso.yaml").write_text(
        yaml.safe_dump({
            "nivel": "L8", "construcciones": ["DATA WHERE"], "capa": "B",
            "estado": "parcial", "motivo": "esperado calculado sin SAS real",
            "salidas": list(outputs),
        }),
        encoding="utf-8",
    )
    return cargar_caso(directory)


def test_rebanar_separa_con_una_linea_vacia_y_conserva_salto_final():
    assert rebanar("a\nb\nc\nd\ne\n", [(2, 3), (5, 5)]) == "b\nc\n\ne\n"
    assert rebanar("a\nb", [(2, 2)]) == "b"
    assert rebanar("a\r\nb\r\nc", [(1, 1), (3, 3)]) == "a\r\n\nc"


@pytest.mark.parametrize("span", [(3, 3), (2, 1), (0, 1), (-1, 1)])
def test_rebanar_rechaza_rango_invalido(span):
    with pytest.raises(ValueError, match=str(span[0])):
        rebanar("a\nb", [span])


def test_rebanar_respeta_el_orden_de_los_rangos():
    assert rebanar("a\nb\nc\n", [(3, 3), (1, 1)]) == "c\n\na\n"


def test_huella_es_sha256_del_texto_utf8_literal():
    assert huella("á\n") == hashlib.sha256("á\n".encode("utf-8")).hexdigest()


def test_verificar_informa_huella_y_fuente_inexistente(tmp_path):
    source = tmp_path / "original.sas"
    source.write_text("a\nb\n", encoding="utf-8")
    slice_ = Rebanada("original.sas", ((1, 1),), "0" * 64)
    assert "original.sas" in verificar(slice_, tmp_path)[0]
    source.unlink()
    assert "original.sas" in verificar(slice_, tmp_path)[0]


@pytest.mark.parametrize("prefix", ["%let n = 15;", "%let n = 15;\n"])
def test_armar_aplica_prologo_y_sustitucion_sin_cambiar_hash(prefix):
    source = "%do i=1 %to 15;\n%mend;\n"
    slice_ = Rebanada("original.sas", ((1, 2),), huella(source), prefix,
                     (("%to 15", "%to &n."),))
    assert armar(slice_, source) == "%let n = 15;\n%do i=1 %to &n.;\n%mend;\n"
    assert slice_.sha256 == huella(source)


@pytest.mark.parametrize("old", ["no aparece", "%", ""])
def test_armar_rechaza_sustitucion_ausente_repetida_o_vacia(old):
    source = "%do i=1 %to 15;\n"
    slice_ = Rebanada("original.sas", ((1, 1),), huella(source),
                     sustituciones=((old, "nuevo"),))
    with pytest.raises(ValueError, match="sustituci"):
        armar(slice_, source)


def test_rebanada_yaml_ida_y_vuelta_y_verificacion(tmp_path):
    source = "antes\ná = 1;\ndespués\n"
    (tmp_path / "original.sas").write_text(source, encoding="utf-8", newline="")
    slice_ = Rebanada("original.sas", ((2, 2),), huella("á = 1;\n"),
                     "%let n = 3;", (("1", "&n."),))
    program, metadata = escribir_rebanada(tmp_path / "caso", slice_, source)
    assert program.read_bytes() == "%let n = 3;\ná = &n.;\n".encode("utf-8")
    assert leer_rebanada(metadata) == slice_
    assert yaml.safe_load(metadata.read_text(encoding="utf-8"))["rangos"] == [[2, 2]]
    assert verificar(leer_rebanada(metadata), tmp_path) == []


def test_verificar_conserva_crlf_en_la_huella_original(tmp_path):
    source = "antes\r\ná = 1;\r\n"
    (tmp_path / "original.sas").write_bytes(source.encode("utf-8"))
    slice_ = Rebanada("original.sas", ((2, 2),), huella("á = 1;\r\n"))
    assert verificar(slice_, tmp_path) == []


def test_escribir_rechaza_hash_que_no_corresponde_al_original(tmp_path):
    slice_ = Rebanada("original.sas", ((1, 1),), "0" * 64)
    with pytest.raises(ValueError, match="huella"):
        escribir_rebanada(tmp_path / "destino", slice_, "a\n")
    assert not (tmp_path / "destino").exists()


@pytest.mark.parametrize("body", [
    "- lista\n", "fuente: prueba.sas\n", "!!python/object:object {}",
    "fuente: x\nrangos: [[1, 2, 3]]\nsha256: " + "a" * 64,
    "fuente: x\nrangos: [[0, 2]]\nsha256: " + "a" * 64,
    "fuente: x\nrangos: [[1, 2]]\nsha256: incorrecta",
    "fuente: x\nrangos: [[1, 2]]\nsha256: " + "a" * 64 + "\nprologo: []",
    "fuente: x\nrangos: [[1, 2]]\nsha256: " + "a" * 64 + "\nsustituciones: [[a]]",
])
def test_leer_rebanada_invalida_da_error_legible(tmp_path, body):
    path = tmp_path / "rebanada.yaml"
    path.write_text(body, encoding="utf-8")
    with pytest.raises(ValueError, match="rebanada.yaml"):
        leer_rebanada(path)


def test_leer_rebanada_coacciona_secuencias_y_lineas_decimales(tmp_path):
    path = tmp_path / "rebanada.yaml"
    path.write_text(yaml.safe_dump({
        "fuente": "original.sas", "rangos": [["1", "2"]], "sha256": "a" * 64,
    }), encoding="utf-8")
    assert leer_rebanada(path) == Rebanada("original.sas", ((1, 2),), "a" * 64)


def test_calcular_y_escribir_usan_interprete_sin_efectos_en_calculo(tmp_path):
    case = _case(tmp_path, "data WORK.s; set WORK.e; where x > 1; run;")
    source_before = case.programa.read_bytes()
    tables = calcular(case)
    assert tables["s"].columnas == ["x"]
    assert tables["s"].filas == [(2,), (3,)]
    assert not case.esperado.exists()
    assert case.programa.read_bytes() == source_before
    assert escribir(case, tables) == [case.esperado / "s.csv"]
    assert (case.esperado / "s.csv").read_bytes() == b"x\n2\n3\n"


def test_calcular_respeta_orden_de_salidas_declarado(tmp_path):
    case = _case(tmp_path, "data WORK.s WORK.copia; set WORK.e; run;", ("copia", "s"))
    assert list(calcular(case)) == ["copia", "s"]


def test_override_cambia_solo_literal_numerico_de_declaracion(tmp_path):
    case = _case(tmp_path, "%let n = 15;\n%let otro = 15;\n"
                 "data WORK.s; set WORK.e; where x < &n.; run;")
    before = case.programa.read_bytes()
    assert calcular(case)["s"].filas == [(1,), (2,), (3,)]
    assert calcular(case, {"n": 3})["s"].filas == [(1,), (2,)]
    assert case.programa.read_bytes() == before


@pytest.mark.parametrize("source", [
    "data WORK.s; set WORK.e; run;",
    "%let nn = 15;\ndata WORK.s; set WORK.e; run;",
    "%let n = texto;\ndata WORK.s; set WORK.e; run;",
])
def test_override_sin_declaracion_numerica_pedida_falla(tmp_path, source):
    with pytest.raises(ValueError, match="n"):
        calcular(_case(tmp_path, source), {"n": 3})


@pytest.mark.parametrize("wrapper", ["/*\n{}\n*/", 'x="\n{}\n";'])
def test_override_no_confunde_comentarios_ni_literales_con_declaraciones(wrapper):
    source = wrapper.format("%let n = 15;")
    with pytest.raises(ValueError, match="n"):
        _overrides(source, {"n": 3})
    source += "\n %LeT N = 15;\n%let otro = 15;\n"
    assert _overrides(source, {"n": 3}) == source.replace("%LeT N = 15;", "%LeT N = 3;")


def test_calcular_salida_vacia_usa_columnas_demostradas_del_plan(tmp_path):
    case = _case(tmp_path, "proc sql; create table WORK.s as "
                 "select x from WORK.e where x > 5; quit;")
    table = calcular(case)["s"]
    assert table.columnas == ["x"]
    assert table.filas == []
    escribir(case, {"s": table})
    assert (case.esperado / "s.csv").read_bytes() == b"x\n"


def test_calcular_salida_vacia_sin_cabecera_demostrada_falla(tmp_path):
    case = _case(tmp_path, "data WORK.s; set WORK.e; where x > 5; run;")
    with pytest.raises(ValueError, match="s.*cabecera"):
        calcular(case)


def test_calcular_salida_declarada_ausente_falla(tmp_path):
    case = _case(tmp_path, "data WORK.s; set WORK.e; run;", ("ausente",))
    with pytest.raises(ValueError, match="ausente"):
        calcular(case)


def test_rango_import_del_programa_real_redactado():
    path = REPO / "tests/fixtures/sas/client/client_large.sas"
    with path.open(encoding="utf-8") as source:
        text = "".join(islice(source, 164))
    assert rebanar(text, [(160, 164)]).startswith(
        "proc import datafile='/work_sasstudio/pcfiles/Base_datos_Nequi.csv'"
    )


def test_herramientas_admiten_import_como_modulo_tools_sin_ajustar_sys_path():
    result = subprocess.run(
        [sys.executable, "-c", "from tools.corpus_lib.esperado_interprete import calcular; "
         "from tools.rebanar_programa import rebanar"],
        cwd=REPO, capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0, result.stderr


def test_calcular_no_reutiliza_cabecera_de_una_version_anterior(tmp_path):
    case = _case(tmp_path, "proc sql; create table WORK.s as select x from WORK.e; quit;\n"
                 "data WORK.s; set WORK.e; where x > 5; run;")
    with pytest.raises(ValueError, match="s.*cabecera"):
        calcular(case)


@pytest.mark.parametrize("name", ["no_declarada", "../../escaped"])
def test_escribir_rechaza_nombre_no_declarado_y_no_escapa_de_esperado(tmp_path, name):
    case = _case(tmp_path, "data WORK.s; set WORK.e; run;")
    outside = case.esperado.parent.parent / "escaped.csv"
    with pytest.raises(ValueError, match="declarad|nombre|ruta"):
        escribir(case, {name: Tabla(["x"], [(1,)])})
    assert not outside.exists()
    assert not (case.esperado / "no_declarada.csv").exists()


@pytest.mark.parametrize("absolute", [False, True])
def test_verificar_rechaza_fuente_fuera_de_la_raiz(tmp_path, absolute):
    root = tmp_path / "raiz"
    root.mkdir()
    outside = tmp_path / "outside.sas"
    outside.write_bytes(b"a\n")
    source = str(outside) if absolute else "../outside.sas"
    errors = verificar(Rebanada(source, ((1, 1),), huella("a\n")), root)
    assert errors, "la fuente externa no debe verificarse aunque coincida su huella"
    assert source in errors[0]


def test_verificar_rechaza_symlink_hacia_fuente_fuera_de_la_raiz(tmp_path):
    root = tmp_path / "raiz"
    root.mkdir()
    outside = tmp_path / "outside.sas"
    outside.write_bytes(b"a\n")
    link = root / "link.sas"
    try:
        link.symlink_to(outside)
    except OSError as error:
        if getattr(error, "winerror", None) == 1314:
            pytest.skip("Windows no permite crear symlinks sin privilegio (error 1314)")
        raise
    errors = verificar(Rebanada("link.sas", ((1, 1),), huella("a\n")), root)
    assert errors, "un symlink no debe permitir verificar una fuente externa"
    assert "link.sas" in errors[0]


@pytest.mark.parametrize("folder", [False, True])
def test_escribir_rechaza_symlink_de_salida_hacia_fuera_del_caso(tmp_path, folder):
    case = _case(tmp_path, "data WORK.s; set WORK.e; run;")
    outside = tmp_path / "outside"
    outside.mkdir()
    outside_file = outside / "s.csv"
    outside_file.write_bytes(b"original\n")
    if folder:
        link, target = case.esperado, outside
    else:
        case.esperado.mkdir()
        link, target = case.esperado / "s.csv", outside_file
    try:
        link.symlink_to(target, target_is_directory=folder)
    except OSError as error:
        if getattr(error, "winerror", None) == 1314:
            pytest.skip("Windows no permite crear symlinks sin privilegio (error 1314)")
        raise
    with pytest.raises(ValueError, match="ruta|fuera"):
        escribir(case, {"s": Tabla(["x"], [(1,)])})
    assert outside_file.read_bytes() == b"original\n"
