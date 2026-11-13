"""Tablas locales declaradas como fuentes de archivo, sin consultar bases."""

import ast
import csv
import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from sgm.cli import app
from sgm.cli_migrar import migrar
from sgm.compile import compile_file, project_base
from sgm.frontend.program import analyze_program
from sgm.ir.models import Operator, Plan
from sgm.ir.pase_tablas_locales import tablas_locales_a_archivos
from sgm.migrar.interprete import ejecutar_plan
from sgm.migrar.tablas_locales import cargar_tablas_locales

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "env/tablas_locales.json"
DATA = ROOT / "tests/fixtures/datos/sashelp/cars.csv"
PROGRAM = """data work.c; set sashelp.cars; run;
proc sql; create table work.a as select Make, MSRP from work.c where Make = 'Acura'; quit;"""


def test_migracion_optativa_emite_archivo_contexto_y_aviso(tmp_path):
    source = tmp_path / "p.sas"
    source.write_text(PROGRAM, encoding="utf-8")
    plain = migrar(source, tmp_path / "sin")
    assert any(p.codigo == "P-OPERADOR-SIN-SOPORTE" for p in plain.pendientes)
    result = CliRunner().invoke(
        app,
        ["migrar", str(source), "--out", str(tmp_path / "con"), "--tablas-locales", str(CONFIG)],
    )
    assert result.exit_code == 0, result.output
    folder = tmp_path / "con/p"
    pending = (folder / "pendientes.md").read_text(encoding="utf-8")
    assert "P-OPERADOR-SIN-SOPORTE" not in pending
    assert "P-DATOS-SINTETICOS" in pending and "tests/fixtures/datos/sashelp/cars.csv" in pending
    assert "sintétic" in pending.lower() and "no son datos reales" in pending.lower()
    context = (folder / "contextos/Default.yaml").read_text(encoding="utf-8")
    assert "ruta_cars" in context and "tests/fixtures/datos/sashelp/cars.csv" in context
    items = list((folder / "process").glob("*.item"))
    assert items and any("tFileInputDelimited" in p.read_text(encoding="utf-8") for p in items)


def test_pase_no_toca_otras_lecturas():
    plan = Plan(program="p")
    read = Operator("a", "read", {"dataset": "WORK.otra"})
    file = Operator("b", "read_file", {"datafile": "otro.csv", "outputs": ["WORK.x"]})
    plan.graph.add_operator(read)
    plan.graph.add_operator(file)
    transformed, pending = tablas_locales_a_archivos(plan, cargar_tablas_locales(CONFIG, ROOT))
    assert transformed.graph.operator("a").kind == "read"
    assert transformed.graph.operator("b").params == {"datafile": "otro.csv", "outputs": ["WORK.x"]}
    assert not pending


def test_ficha_ausente_identifica_tabla(tmp_path):
    (tmp_path / "datos.csv").write_text("a\n1\n", encoding="utf-8")
    cfg = tmp_path / "locales.json"
    cfg.write_text(
        json.dumps({"lib.t": {"archivo": "datos.csv", "delimitador": ","}}), encoding="utf-8"
    )
    with pytest.raises(ValueError, match=r"lib\.t"):
        cargar_tablas_locales(cfg, tmp_path)


def test_pase_interprete_con_fixture():
    plan = compile_file(analyze_program({"p.sas": PROGRAM}), "p.sas", project_base()).plan
    plan, pending = tablas_locales_a_archivos(plan, cargar_tablas_locales(CONFIG, ROOT))
    assert any(p.codigo == "P-DATOS-SINTETICOS" for p in pending)
    with DATA.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    result = ejecutar_plan(plan, {"sashelp.cars": rows})
    assert len(result["a"]) == 4
    assert all(row["Make"] == "Acura" for row in result["a"])


def test_fuente_compartida_y_limite_de_aislamiento():
    from sgm.migrar.ficha import Ficha, leer_ficha
    from tools.datos_sinteticos.ficha import Ficha as ToolsFicha

    assert ToolsFicha is Ficha
    assert leer_ficha(DATA.with_suffix(".ficha.yaml")).origen == "sintetico"
    for path in (ROOT / "src/sgm").rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                assert all(
                    a.name != "tools" and not a.name.startswith("tools.") for a in node.names
                )
            if isinstance(node, ast.ImportFrom):
                assert node.module != "tools" and not (node.module or "").startswith("tools.")


@pytest.mark.parametrize("location", ["config", "archivo", "ficha"])
def test_rutas_no_pueden_salir_de_raiz(tmp_path, location):
    root = tmp_path / "repo"
    root.mkdir()
    outside = tmp_path / "external"
    outside.mkdir()
    csvpath = root / "datos.csv"
    csvpath.write_text("a\n1\n", encoding="utf-8")
    ficha = root / "datos.ficha.yaml"
    ficha.write_text(
        "tabla: lib.t\norigen: real\nfilas: 1\ncolumnas:\n  a: String\nprocedencia: prueba\n",
        encoding="utf-8",
    )
    config = root / "config.json"
    config.write_text(
        json.dumps({"lib.t": {"archivo": "datos.csv", "delimitador": ","}}), encoding="utf-8"
    )
    if location == "config":
        config = outside / "config.json"
        config.write_text("{}", encoding="utf-8")
    elif location == "archivo":
        config.write_text(
            json.dumps({"lib.t": {"archivo": "../external/x.csv", "delimitador": ","}}),
            encoding="utf-8",
        )
    else:
        ficha.unlink()
        (outside / "datos.ficha.yaml").write_text("tabla: lib.t", encoding="utf-8")
        try:
            ficha.symlink_to(outside / "datos.ficha.yaml")
        except OSError:
            pytest.skip("symlink no disponible")
    with pytest.raises(ValueError):
        cargar_tablas_locales(config, root)


def test_migracion_conecta_lectura_y_mapa_con_tipos_de_ficha(tmp_path, monkeypatch):
    import sgm.cli_migrar as module

    source = tmp_path / "p.sas"
    source.write_text(PROGRAM, encoding="utf-8")
    captured = {}
    original = module.plan_a_jobs

    def registrar(plan, schemas):
        captured.update(schemas)
        return original(plan, schemas)

    monkeypatch.setattr(module, "plan_a_jobs", registrar)
    result = module.migrar(source, tmp_path / "out", tablas_locales=CONFIG)
    ficha = cargar_tablas_locales(CONFIG, ROOT)["sashelp.cars"]
    assert captured["sashelp.cars"] == list(ficha.columnas)
    assert all(c.source == "fixture" for c in captured["sashelp.cars"])
    assert not any(
        p.codigo == "P-TIPO-DESCONOCIDO" and "sashelp.cars" in p.mensaje for p in result.pendientes
    )
    job = result.jobs[0]
    read = next(n for n in job.nodos if n.componente == "tFileInputDelimited")
    mapping = next(n for n in job.nodos if n.componente == "tMap")
    assert any(
        c.origen == read.unico and c.destino == mapping.unico and c.conector == "FLOW"
        for c in job.conexiones
    )
    flow = next(m for m in read.metadatas if m.conector == "FLOW")
    assert [(c.nombre, c.tipo) for c in flow.columnas] == [
        (c.name, "id_" + c.type) for c in ficha.columnas
    ]
    assert any(p.codigo == "P-DATOS-SINTETICOS" for p in result.pendientes)


def test_no_sustituye_lectura_de_tabla_ya_producida():
    from sgm.ir.models import Edge

    plan = Plan(program="p")
    producer = Operator("a", "derive", {"outputs": ["SASHELP.cars"]})
    read = Operator("b", "read", {"dataset": "SASHELP.cars"})
    plan.graph.add_operator(producer)
    plan.graph.add_operator(read)
    plan.graph.add_edge(Edge("a", "b", "SASHELP.cars"))
    transformed, pending = tablas_locales_a_archivos(plan, cargar_tablas_locales(CONFIG, ROOT))
    assert transformed.graph.operator("b").kind == "read"
    assert not pending


def test_tipos_salen_de_ficha_y_no_de_contenido_csv(tmp_path):
    (tmp_path / "datos.csv").write_text("a\ntexto-no-numerico\n", encoding="utf-8")
    (tmp_path / "datos.ficha.yaml").write_text(
        "tabla: lib.t\norigen: real\nfilas: 1\ncolumnas:\n  a: Double\nprocedencia: prueba\n",
        encoding="utf-8",
    )
    cfg = tmp_path / "config.json"
    cfg.write_text(
        json.dumps({"lib.t": {"archivo": "datos.csv", "delimitador": ","}}), encoding="utf-8"
    )
    col = cargar_tablas_locales(cfg, tmp_path)["lib.t"].columnas[0]
    assert (col.name, col.type, col.source) == ("a", "Double", "fixture")


def test_cli_rechaza_config_absoluta_fuera_del_proyecto(tmp_path, monkeypatch):
    project = tmp_path / "proyecto"
    project.mkdir()
    source = project / "p.sas"
    source.write_text(PROGRAM, encoding="utf-8")
    config = tmp_path / "config.json"
    config.write_text("{}", encoding="utf-8")
    monkeypatch.chdir(project)
    result = CliRunner().invoke(
        app,
        ["migrar", str(source), "--out", str(project / "out"), "--tablas-locales", str(config)],
    )
    assert result.exit_code == 2
    assert not (project / "out").exists()


def test_cli_rechaza_config_absoluta_de_otro_repositorio(tmp_path, monkeypatch):
    source = tmp_path / "p.sas"
    source.write_text(PROGRAM, encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(
        app,
        ["migrar", str(source), "--out", str(tmp_path / "out"), "--tablas-locales", str(CONFIG)],
    )
    assert result.exit_code == 2
    assert not (tmp_path / "out").exists()


def test_ficha_sintetica_sin_procedencia_sintetica_es_invalida(tmp_path):
    (tmp_path / "datos.csv").write_text("a\n1\n", encoding="utf-8")
    (tmp_path / "datos.ficha.yaml").write_text(
        "tabla: lib.t\norigen: sintetico\nfilas: 1\ncolumnas:\n  a: Double\n", encoding="utf-8"
    )
    config = tmp_path / "config.json"
    config.write_text(
        json.dumps({"lib.t": {"archivo": "datos.csv", "delimitador": ","}}), encoding="utf-8"
    )
    with pytest.raises(ValueError, match="lib.t"):
        cargar_tablas_locales(config, tmp_path)


@pytest.mark.parametrize("kind", ["config", "archivo"])
def test_symlink_a_exterior_es_rechazado(tmp_path, kind):
    root = tmp_path / "repo"
    root.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    cfg = root / "config.json"
    csvpath = root / "datos.csv"
    external = outside / ("config.json" if kind == "config" else "datos.csv")
    external.write_text("{}" if kind == "config" else "a\n1\n", encoding="utf-8")
    link = cfg if kind == "config" else csvpath
    try:
        link.symlink_to(external)
    except OSError:
        pytest.skip("symlink no disponible")
    if kind == "archivo":
        cfg.write_text(
            json.dumps({"lib.t": {"archivo": "datos.csv", "delimitador": ","}}), encoding="utf-8"
        )
    with pytest.raises(ValueError, match="fuera"):
        cargar_tablas_locales(cfg, root)


def test_ficha_invalida_informa_tabla_en_lugar_de_error_interno(tmp_path):
    (tmp_path / "datos.csv").write_text("a\n1\n", encoding="utf-8")
    (tmp_path / "datos.ficha.yaml").write_text("columnas: [", encoding="utf-8")
    config = tmp_path / "config.json"
    config.write_text(
        json.dumps({"lib.t": {"archivo": "datos.csv", "delimitador": ","}}), encoding="utf-8"
    )
    with pytest.raises(ValueError, match=r"lib\.t"):
        cargar_tablas_locales(config, tmp_path)
