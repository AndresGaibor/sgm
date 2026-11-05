"""Arnés de Studio del corpus, sin Studio: comparador, modo `comparar`, mapa y limpieza.

El ejecutor con Studio se prueba con un doble del cliente MCP y un lanzador falso. Así se
comprueba el protocolo (qué se copia, qué se compila, qué se borra) sin tocar un proyecto real.
La demostración de punta a punta con Studio está en tools/corpus_lib/STUDIO.md.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))

import corpus_studio  # noqa: E402
from corpus_lib import studio_mapa, studio_validar  # noqa: E402
from corpus_lib.caso import cargar_caso  # noqa: E402
from corpus_lib.studio_comparar import (  # noqa: E402
    comparar_archivos,
    comparar_carpetas,
    comparar_tablas,
)
from corpus_lib.studio_informe import comparar_caso  # noqa: E402
from mcp_cliente import ErrorValidacion  # noqa: E402

from sgm.talend_item.escritura import escribir_job  # noqa: E402
from sgm.talend_item.modelo import Job  # noqa: E402

CASO_DIR = REPO / "tests" / "corpus" / "L2" / "l2_01_inner_join_clientes_ventas"
CASO = "l2_01_inner_join_clientes_ventas"


def tabla(columnas: list[str], *filas: list) -> tuple[list[str], list[list]]:
    return columnas, [list(fila) for fila in filas]


# --- Comparador de tablas ---------------------------------------------------------------------


def test_tablas_iguales_no_tienen_diferencias():
    esperada = tabla(["a", "b"], ["1", "x"])
    assert comparar_tablas(esperada, tabla(["a", "b"], ["1", "x"])) == []


def test_columnas_en_otro_orden_son_diferencia_salvo_que_se_ignore_el_orden():
    esperada, obtenida = tabla(["a", "b"], ["1", "x"]), tabla(["b", "a"], ["x", "1"])
    (diferencia,) = comparar_tablas(esperada, obtenida)
    assert diferencia.tipo == "columnas"
    assert "distinto orden" in diferencia.mensaje
    assert comparar_tablas(esperada, obtenida, ignorar_orden_columnas=True) == []


def test_columnas_faltantes_y_de_mas_se_nombran():
    (diferencia,) = comparar_tablas(tabla(["a", "b"], ["1", "x"]), tabla(["a", "c"], ["1", "x"]))
    assert "faltan ['b']" in diferencia.mensaje
    assert "sobran ['c']" in diferencia.mensaje


def test_las_filas_se_comparan_como_conjunto_si_el_orden_no_es_relevante():
    esperada, obtenida = tabla(["n"], ["1"], ["2"]), tabla(["n"], ["2"], ["1"])
    assert comparar_tablas(esperada, obtenida, orden_relevante=False) == []


def test_el_orden_relevante_detecta_filas_en_otra_posicion():
    esperada, obtenida = tabla(["n"], ["1"], ["2"]), tabla(["n"], ["2"], ["1"])
    diferencias = comparar_tablas(esperada, obtenida, orden_relevante=True)
    assert [(d.tipo, d.fila, d.columna) for d in diferencias] == [
        ("celda", 1, "n"),
        ("celda", 2, "n"),
    ]


def test_los_numeros_usan_la_tolerancia():
    esperada, obtenida = tabla(["v"], ["1.00"]), tabla(["v"], ["1.04"])
    assert comparar_tablas(esperada, obtenida, tolerancia=0.05) == []
    (diferencia,) = comparar_tablas(esperada, obtenida, tolerancia=0.0)
    assert (diferencia.esperado, diferencia.obtenido) == ("1.00", "1.04")


def test_el_texto_ignora_blancos_finales_pero_no_iniciales():
    assert comparar_tablas(tabla(["t"], ["ana"]), tabla(["t"], ["ana   "])) == []
    assert comparar_tablas(tabla(["t"], ["ana"]), tabla(["t"], ["  ana"])) != []


def test_una_celda_vacia_es_igual_a_otra_vacia_y_distinta_de_un_valor():
    assert comparar_tablas(tabla(["t"], [None]), tabla(["t"], [""])) == []
    (diferencia,) = comparar_tablas(tabla(["t"], [""]), tabla(["t"], ["x"]))
    assert (diferencia.esperado, diferencia.obtenido) == ("", "x")


def test_una_fila_que_falta_se_reporta_como_faltante():
    esperada = tabla(["n"], ["1"], ["2"], ["3"])
    resumen, diferencia = comparar_tablas(esperada, tabla(["n"], ["1"], ["3"]))
    assert resumen.tipo == "filas"
    assert (diferencia.tipo, diferencia.fila) == ("faltante", 2)
    assert diferencia.esperado == "(2)"


def test_una_fila_de_mas_se_reporta_como_sobrante():
    resumen, diferencia = comparar_tablas(tabla(["n"], ["1"]), tabla(["n"], ["1"], ["2"]))
    assert resumen.tipo == "filas"
    assert (diferencia.tipo, diferencia.fila, diferencia.obtenido) == ("sobrante", 2, "(2)")


def test_la_celda_exacta_se_reporta_con_fila_columna_y_valores():
    esperada = tabla(["id", "nombre"], ["1", "Hugo"])
    (diferencia,) = comparar_tablas(esperada, tabla(["id", "nombre"], ["1", "Hugo X"]))
    assert diferencia.texto() == (
        "fila 1, columna 'nombre': esperado 'Hugo', obtenido 'Hugo X'"
    )


# --- Comparador de archivos y carpetas --------------------------------------------------------


def test_un_csv_con_encabezado_ilegible_queda_como_ilegible(tmp_path):
    ruta = tmp_path / "malo.csv"
    ruta.write_text("nombre completo\nHugo\n", encoding="utf-8")
    resultado = comparar_archivos(ruta, ruta)
    assert resultado.estado == "ilegible"


def test_carpetas_emparejan_por_nombre_sin_mayusculas_y_marcan_faltantes_y_de_mas(tmp_path):
    esperado, salida = tmp_path / "esperado", tmp_path / "salida"
    esperado.mkdir()
    salida.mkdir()
    (esperado / "Ventas.csv").write_text("a\n1\n", encoding="utf-8")
    (esperado / "solo_esperado.csv").write_text("a\n1\n", encoding="utf-8")
    (salida / "ventas.CSV").write_text("a\n1\n", encoding="utf-8")
    (salida / "solo_salida.csv").write_text("a\n1\n", encoding="utf-8")
    estados = {r.nombre: r.estado for r in comparar_carpetas(esperado, salida)}
    assert estados == {
        "solo_esperado.csv": "faltante",
        "solo_salida.csv": "de_mas",
        "Ventas.csv": "coincide",
    }


# --- Modo `comparar` de la CLI ----------------------------------------------------------------


def _copiar_esperado(destino: Path) -> Path:
    shutil.copytree(CASO_DIR / "esperado", destino)
    return destino


def test_comparar_una_copia_del_esperado_coincide(tmp_path, capsys):
    salida = _copiar_esperado(tmp_path / "salida")
    assert corpus_studio.main(["comparar", CASO, "--salida", str(salida)]) == 0
    assert "1 coinciden" in capsys.readouterr().out


def test_comparar_una_salida_alterada_reporta_la_celda_exacta(tmp_path, capsys):
    salida = _copiar_esperado(tmp_path / "salida")
    archivo = salida / "ventas_con_nombre.csv"
    archivo.write_text(
        archivo.read_text(encoding="utf-8").replace("1,Carla Muestra,655", "1,Carla Muestra,656"),
        encoding="utf-8",
    )
    assert corpus_studio.main(["comparar", CASO, "--salida", str(salida)]) == 1
    salida_texto = capsys.readouterr().out
    assert "fila 1, columna 'monto': esperado '655', obtenido '656'" in salida_texto
    assert "no coincide" in salida_texto


def test_comparar_con_una_carpeta_inexistente_da_error_de_uso(tmp_path):
    assert corpus_studio.main(["comparar", CASO, "--salida", str(tmp_path / "no")]) == 2


def test_la_tolerancia_y_el_orden_salen_del_caso():
    caso = cargar_caso(CASO_DIR)
    resultado = comparar_caso(caso, CASO_DIR / "esperado")
    assert resultado.coincide
    assert (caso.tolerancia, caso.orden_relevante) == (0.0, False)


# --- Mapa de contexto -------------------------------------------------------------------------


def test_leer_mapa_acepta_rutas_relativas(tmp_path):
    ruta = tmp_path / "mapa.yaml"
    ruta.write_text("ruta_origen: entradas/ventas.csv\nruta_resultados: salida/\n", "utf-8")
    assert studio_mapa.leer_mapa(ruta) == {
        "ruta_origen": "entradas/ventas.csv",
        "ruta_resultados": "salida/",
    }


@pytest.mark.parametrize("ruta", ["C:/datos/ventas.csv", "/tmp/x.csv", "../fuera.csv"])
def test_leer_mapa_rechaza_rutas_fuera_del_caso(tmp_path, ruta):
    archivo = tmp_path / "mapa.yaml"
    archivo.write_text(f"ruta_origen: '{ruta}'\n", encoding="utf-8")
    with pytest.raises(ValueError, match="relativa"):
        studio_mapa.leer_mapa(archivo)


def test_leer_mapa_sin_archivo_es_vacio_y_inexistente_es_error(tmp_path):
    assert studio_mapa.leer_mapa(None) == {}
    with pytest.raises(ValueError, match="no existe"):
        studio_mapa.leer_mapa(tmp_path / "falta.yaml")


def test_parametros_crean_la_salida_y_exigen_los_archivos_de_entrada(tmp_path):
    trabajo = tmp_path / "trabajo"
    (trabajo / "entradas").mkdir(parents=True)
    (trabajo / "entradas" / "ventas.csv").write_text("a\n1\n", encoding="utf-8")
    mapa = {"ruta_origen": "entradas/ventas.csv", "ruta_resultados": "salida/"}
    pares = studio_mapa.parametros_contexto(mapa, trabajo, ["env=DEV"])
    assert pares[0].endswith("/trabajo/entradas/ventas.csv")
    assert pares[1].startswith("ruta_resultados=") and pares[1].endswith("/salida/")
    assert pares[2] == "env=DEV"
    assert (trabajo / "salida").is_dir()
    with pytest.raises(ValueError, match="no existe en el caso"):
        studio_mapa.parametros_contexto({"x": "entradas/falta.csv"}, trabajo, [])


def test_una_variable_en_el_mapa_y_en_contexto_a_la_vez_es_error(tmp_path):
    with pytest.raises(ValueError, match="a la vez"):
        studio_mapa.parametros_contexto({"env": "salida/"}, tmp_path, ["env=PRO"])


# --- Ejecución con Studio (doble del cliente y lanzador falso) --------------------------------


class DobleStudio:
    """Cliente MCP falso: registra las llamadas, falla en `fallar_en` y exporta un lanzador."""

    def __init__(self, fallar_en: str | None = None) -> None:
        self.llamadas: list[str] = []
        self.fallar_en = fallar_en

    def llamar(self, tool: str, argumentos: dict | None = None):
        self.llamadas.append(tool)
        if tool == self.fallar_en:
            raise ErrorValidacion(f"{tool}: falla simulada")
        if tool == "talend_job_build_batch":
            return {"jobs": [{"ok": True}]}
        if tool == "talend_deliverables_build_job":
            destino = Path(argumentos["destinationDir"])
            job = argumentos["jobName"]
            (destino / job).mkdir(parents=True, exist_ok=True)
            (destino / job / f"{job}_run.bat").write_text("@echo off\n", encoding="utf-8")
        return {}


@pytest.fixture
def proyecto(tmp_path) -> Path:
    raiz = tmp_path / "PRJ_PRUEBA"
    (raiz / "process").mkdir(parents=True)
    (raiz / "talend.project").write_text(
        '<TalendProperties:Project technicalLabel="PRJ_PRUEBA"/>', encoding="utf-8"
    )
    return raiz


@pytest.fixture
def jobs(tmp_path) -> Path:
    carpeta = tmp_path / "jobs"
    escribir_job(Job("demo_prueba"), carpeta, fecha="2026-01-01T00:00:00.000-0500")
    return carpeta


def _archivos_del_proyecto(proyecto: Path) -> list[str]:
    return sorted(p.name for p in (proyecto / "process").iterdir())


def test_un_fallo_de_compilacion_no_deja_jobs_de_prueba_en_el_proyecto(proyecto, jobs, tmp_path):
    doble = DobleStudio(fallar_en="talend_job_build_batch")
    ejecucion = studio_validar.validar_en_studio(
        caso=cargar_caso(CASO_DIR),
        carpeta_jobs=jobs,
        padre="demo_prueba",
        proyecto=proyecto,
        trabajo=tmp_path / "trabajo",
        cliente=doble,
        sufijo="falla",
    )
    assert not ejecucion.ok
    assert "falla simulada" in ejecucion.error
    assert _archivos_del_proyecto(proyecto) == []
    assert doble.llamadas.count("talend_bridge_refresh_workspace") == 2


def test_sin_el_padre_entre_los_jobs_no_se_copia_nada(proyecto, jobs, tmp_path):
    ejecucion = studio_validar.validar_en_studio(
        caso=cargar_caso(CASO_DIR),
        carpeta_jobs=jobs,
        padre="otro_job",
        proyecto=proyecto,
        trabajo=tmp_path / "trabajo",
        cliente=DobleStudio(),
    )
    assert "no está entre los Jobs" in ejecucion.error
    assert _archivos_del_proyecto(proyecto) == []


def test_una_ejecucion_correcta_pasa_los_parametros_y_recoge_la_salida(
    proyecto, jobs, tmp_path, monkeypatch
):
    caso = cargar_caso(CASO_DIR)
    recibidos: dict = {}

    def lanzador_falso(lanzador, contexto, pares, java_bin):
        recibidos["pares"] = pares
        salida = dict(p.split("=", 1) for p in pares)["ruta_resultados"]
        shutil.copytree(CASO_DIR / "esperado", Path(salida), dirs_exist_ok=True)
        return {"exitCode": 0, "stdout": "", "stderr": ""}

    monkeypatch.setattr(studio_validar, "ejecutar", lanzador_falso)
    mapa = {
        "ruta_origen": "entradas/ventas.csv",
        "ruta_clientes": "entradas/clientes.csv",
        "ruta_resultados": "salida/",
    }
    ejecucion = studio_validar.validar_en_studio(
        caso=caso,
        carpeta_jobs=jobs,
        padre="demo_prueba",
        proyecto=proyecto,
        mapa=mapa,
        parametros=["env=DEV"],
        trabajo=tmp_path / "trabajo",
        cliente=DobleStudio(),
        sufijo="ok",
    )
    assert ejecucion.ok
    assert any(p.startswith("ruta_origen=") and p.endswith("entradas/ventas.csv")
               for p in recibidos["pares"])
    assert "env=DEV" in recibidos["pares"]
    assert _archivos_del_proyecto(proyecto) == []
    resultado = comparar_caso(caso, ejecucion.trabajo / "salida")
    assert resultado.coincide


def test_el_arnes_usa_la_exportacion_del_validador_y_no_una_copia():
    """R0-03: la búsqueda recursiva del lanzador vive en un solo módulo."""
    assert not hasattr(studio_validar, "_exportar")
    assert studio_validar.exportar is sys.modules["validar_en_studio"].exportar


def test_la_ejecucion_borra_el_build_temporal(proyecto, jobs, tmp_path, monkeypatch):
    creados: list[Path] = []
    original = studio_validar.crear_destino_build

    def anotado() -> Path:
        creados.append(original())
        return creados[-1]

    monkeypatch.setattr(studio_validar, "crear_destino_build", anotado)
    monkeypatch.setattr(
        studio_validar, "ejecutar", lambda *a, **k: {"exitCode": 0, "stdout": "", "stderr": ""}
    )
    studio_validar.validar_en_studio(
        caso=cargar_caso(CASO_DIR),
        carpeta_jobs=jobs,
        padre="demo_prueba",
        proyecto=proyecto,
        trabajo=tmp_path / "trabajo",
        cliente=DobleStudio(),
        sufijo="limpio",
    )
    assert creados and not creados[0].exists()


def test_un_job_que_termina_con_error_no_puede_dar_coincide(proyecto, jobs, tmp_path, monkeypatch):
    caso = cargar_caso(CASO_DIR)

    def lanzador_roto(lanzador, contexto, pares, java_bin):
        return {"exitCode": 1, "stdout": "", "stderr": "NullPointerException"}

    monkeypatch.setattr(studio_validar, "ejecutar", lanzador_roto)
    ejecucion = studio_validar.validar_en_studio(
        caso=caso,
        carpeta_jobs=jobs,
        padre="demo_prueba",
        proyecto=proyecto,
        trabajo=tmp_path / "trabajo",
        cliente=DobleStudio(),
        sufijo="roto",
    )
    resultado = comparar_caso(caso, ejecucion.trabajo / "salida", error=ejecucion.error)
    assert not resultado.coincide
    assert "código 1" in resultado.error
