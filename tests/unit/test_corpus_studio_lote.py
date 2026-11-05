"""Compilación en lote de los Jobs del corpus: una sola llamada y `process/` limpio al terminar."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))

from corpus_lib.studio_lote import compilar_en_lote  # noqa: E402

from sgm.backend_talend import BackendNoDisponible, ResultadoLote  # noqa: E402


class BackendFalso:
    """Anota las llamadas y devuelve que todo compiló."""

    def __init__(self, error: Exception | None = None) -> None:
        self.llamadas: list[list[str]] = []
        self.error = error

    def compilar_lote(self, nombres: list[str]) -> ResultadoLote:
        self.llamadas.append(list(nombres))
        if self.error is not None:
            raise self.error
        return ResultadoLote(compilan=tuple(nombres), no_compilan={})


def _job(carpeta: Path, nombre: str) -> Path:
    """Carpeta de un Job mínimo con su `.item` y su `.properties`."""
    carpeta.mkdir(parents=True, exist_ok=True)
    (carpeta / f"{nombre}_0.1.item").write_text(
        f'<node><elementParameter name="UNIQUE_NAME" value="{nombre}"/></node>', encoding="utf-8"
    )
    (carpeta / f"{nombre}_0.1.properties").write_text(
        f'<Property label="{nombre}" displayName="{nombre}"/>', encoding="utf-8"
    )
    return carpeta


def _proyecto(tmp_path: Path) -> Path:
    proyecto = tmp_path / "PRJ"
    (proyecto / "process").mkdir(parents=True)
    return proyecto


def test_copia_llama_una_vez_y_limpia(tmp_path):
    proyecto = _proyecto(tmp_path)
    carpetas = [_job(tmp_path / "a", "job_a"), _job(tmp_path / "b", "job_b")]
    backend = BackendFalso()

    resultado = compilar_en_lote(carpetas, proyecto, backend, "cs1")

    assert backend.llamadas == [["job_a_cs1", "job_b_cs1"]]
    assert resultado.compilan == ("job_a_cs1", "job_b_cs1")
    assert list((proyecto / "process").iterdir()) == []


def test_limpia_aunque_el_backend_falle(tmp_path):
    proyecto = _proyecto(tmp_path)
    carpetas = [_job(tmp_path / "a", "job_a")]
    backend = BackendFalso(error=BackendNoDisponible("Studio bloqueado"))

    with pytest.raises(BackendNoDisponible):
        compilar_en_lote(carpetas, proyecto, backend, "cs1")

    assert list((proyecto / "process").iterdir()) == []


def test_no_pisa_jobs_ajenos(tmp_path):
    proyecto = _proyecto(tmp_path)
    ajeno = proyecto / "process" / "otro_0.1.item"
    ajeno.write_text("<node/>", encoding="utf-8")
    carpetas = [_job(tmp_path / "a", "job_a")]

    compilar_en_lote(carpetas, proyecto, BackendFalso(), "cs1")

    assert ajeno.exists()
    assert [ruta.name for ruta in (proyecto / "process").iterdir()] == ["otro_0.1.item"]


def test_nombres_con_sufijo_unico(tmp_path):
    proyecto = _proyecto(tmp_path)
    carpetas = [_job(tmp_path / "a", "job_a")]
    backend = BackendFalso()

    compilar_en_lote(carpetas, proyecto, backend, "cs1")
    compilar_en_lote(carpetas, proyecto, backend, "cs2")

    assert backend.llamadas == [["job_a_cs1"], ["job_a_cs2"]]
