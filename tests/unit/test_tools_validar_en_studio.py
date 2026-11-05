"""Validador externo de Studio, sin Studio: las cuatro correcciones del hito 80 (R0-02).

Cubre lo que el arnés del corpus encontró roto: `exportar` busca el lanzador solo en la raíz del
destino, `renombrar` exige la versión 0.1, `ejecutar` no entrecomilla los parámetros y las carpetas
`build-*` se quedan en `%TEMP%`. Todo con un doble del cliente MCP; la demostración real necesita
el Studio instalado.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))

import validar_en_studio  # noqa: E402
from mcp_cliente import ErrorValidacion  # noqa: E402

from sgm.talend_item.escritura import escribir_job  # noqa: E402
from sgm.talend_item.modelo import Job  # noqa: E402

PROYECTO = "PRJ_PRUEBA"


class DobleMCP:
    """Cliente falso: anota las llamadas y deja el lanzador donde se le diga."""

    def __init__(self, subcarpeta: bool = True, lanzador: bool = True) -> None:
        self.llamadas: list[str] = []
        self.subcarpeta = subcarpeta
        self.lanzador = lanzador

    def llamar(self, tool: str, argumentos: dict | None = None):
        self.llamadas.append(tool)
        if tool == "talend_deliverables_build_job":
            destino = Path(argumentos["destinationDir"])
            job = argumentos["jobName"]
            carpeta = destino / job if self.subcarpeta else destino
            carpeta.mkdir(parents=True, exist_ok=True)
            if self.lanzador:
                (carpeta / f"{job}_run.bat").write_text("@echo off\n", encoding="utf-8")
        return {}


def _jobs(carpeta: Path, version: str = "0.1", nombre: str = "demo") -> Path:
    """Escribe un Job mínimo con la versión pedida."""
    escribir_job(Job(nombre, version=version), carpeta, fecha="2026-01-01T00:00:00.000-0500")
    return carpeta


# --- renombrar sin versión fija ---------------------------------------------------------------


@pytest.mark.parametrize("version", ["0.1", "0.2", "1.0"])
def test_renombrar_usa_la_version_del_archivo(tmp_path, version):
    carpeta = _jobs(tmp_path, version)
    mapa = validar_en_studio.renombrar(carpeta, "v9", PROYECTO)
    assert mapa == {"demo": "demo_v9"}
    assert sorted(p.name for p in carpeta.iterdir()) == [
        f"demo_v9_{version}.item",
        f"demo_v9_{version}.properties",
    ]


def test_renombrar_recalcula_los_ids_con_la_version_real(tmp_path):
    carpeta = _jobs(tmp_path, "1.0")
    viejo = validar_en_studio._id_propiedad("demo_1.0")
    nuevo = validar_en_studio._id_propiedad("demo_v9_1.0")
    validar_en_studio.renombrar(carpeta, "v9", PROYECTO)
    propiedades = (carpeta / "demo_v9_1.0.properties").read_text(encoding="utf-8")
    assert f'id="{nuevo}"' in propiedades
    assert viejo not in propiedades
    assert 'label="demo_v9"' in propiedades


def test_renombrar_lee_los_jobs_de_cualquier_version(tmp_path):
    _jobs(tmp_path, "0.1", nombre="uno")
    _jobs(tmp_path, "1.0", nombre="dos")
    assert validar_en_studio.versiones(tmp_path) == {"dos": "1.0", "uno": "0.1"}
    mapa = validar_en_studio.renombrar(tmp_path, "v9", PROYECTO)
    assert mapa == {"dos": "dos_v9", "uno": "uno_v9"}


# --- exportar con búsqueda recursiva ------------------------------------------------------------


@pytest.mark.parametrize("subcarpeta", [True, False])
def test_exportar_encuentra_el_lanzador_en_la_raiz_o_en_una_subcarpeta(tmp_path, subcarpeta):
    doble = DobleMCP(subcarpeta=subcarpeta)
    lanzador = validar_en_studio.exportar(doble, "job_x", tmp_path, None)
    esperado = tmp_path / "job_x" / "job_x_run.bat" if subcarpeta else tmp_path / "job_x_run.bat"
    assert lanzador == esperado
    assert lanzador.is_file()
    assert doble.llamadas == ["talend_deliverables_build_job"]


def test_exportar_falla_con_mensaje_si_el_lanzador_no_aparece(tmp_path):
    doble = DobleMCP(lanzador=False)
    with pytest.raises(ErrorValidacion, match="job_x_run.bat"):
        validar_en_studio.exportar(doble, "job_x", tmp_path, None)


# --- ejecutar con comillas ----------------------------------------------------------------------


def test_el_comando_entrecomilla_rutas_y_valores_con_espacios(tmp_path):
    comando = validar_en_studio.comando_lanzador(
        tmp_path / "build dir" / "job_run.bat",
        "DEV",
        ["ruta_insumos=C:/Mis datos/insumos", "env=DEV"],
    )
    assert comando == (
        f'"{tmp_path / "build dir" / "job_run.bat"}" '
        '--context="DEV" '
        '--context_param "ruta_insumos=C:/Mis datos/insumos" '
        '--context_param "env=DEV"'
    )


def test_ejecutar_pasa_el_comando_entrecomillado_al_so(tmp_path, monkeypatch):
    capturado: dict = {}

    def falso_run(comando, **opciones):
        capturado["comando"] = comando
        return subprocess.CompletedProcess(comando, 0, "ok", "")

    monkeypatch.setattr(validar_en_studio.subprocess, "run", falso_run)
    resultado = validar_en_studio.ejecutar(
        tmp_path / "job dir" / "job_run.bat", "DEV", ["a=b c"], None
    )
    assert '"a=b c"' in capturado["comando"]
    assert resultado["exitCode"] == 0
    assert resultado["comando"] == capturado["comando"]


# --- carpetas build-* de %TEMP% -----------------------------------------------------------------


def test_la_carpeta_de_build_se_crea_y_se_borra():
    destino = validar_en_studio.crear_destino_build()
    try:
        assert destino.name.startswith("build-") and destino.is_dir()
    finally:
        validar_en_studio.borrar_destino_build(destino)
    assert not destino.exists()


def test_borrar_una_carpeta_que_ya_no_existe_no_falla(tmp_path):
    validar_en_studio.borrar_destino_build(tmp_path / "no-existe")
