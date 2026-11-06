"""Backend de Talend por la CLI de `talend-mcp`, con el ejecutor inyectado.

Las pruebas no arrancan Studio ni `bun`: el ejecutor falso devuelve la respuesta que se quiera y
anota la línea de comandos, que es lo que hay que vigilar (nombres de herramienta, JSON de entrada,
tiempo máximo y ausencia de secretos). Las respuestas de los fixtures son las reales del puente:
la forma de `result.jobs` y el mapa `findings` no se adivinan, se copian.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from sgm.backend_talend import BackendNoDisponible, ResultadoLote, Veredicto
from sgm.backend_talend.talend_cli import TalendCliBackend

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "talend_cli"


def _respuesta(nombre: str) -> str:
    return (FIXTURES / nombre).read_text(encoding="utf-8").strip()


class EjecutorFalso:
    """Ejecutor de prueba: guarda cada llamada y devuelve siempre la misma respuesta."""

    def __init__(self, salida: str = '{"ok": true, "data": {}}', codigo: int = 0) -> None:
        self.salida = salida
        self.codigo = codigo
        self.llamadas: list[tuple[list[str], float]] = []

    def __call__(self, comando: list[str], tiempo_max: float) -> tuple[int, str]:
        self.llamadas.append((list(comando), tiempo_max))
        return self.codigo, self.salida


def _backend(ejecutor, tiempo_max: float = 120.0, tmp_path=None) -> TalendCliBackend:
    return TalendCliBackend(
        talend_dir=tmp_path or Path("."),
        proyecto=Path("PRJ"),
        ejecutor=ejecutor,
        tiempo_max=tiempo_max,
    )


def _entrada(comando: list[str]) -> dict:
    return json.loads(comando[comando.index("--input") + 1])


def test_compilar_lote_arma_la_linea_de_comandos(tmp_path):
    ejecutor = EjecutorFalso('{"ok": true, "data": {"compilan": ["a"], "noCompilan": []}}')

    _backend(ejecutor, tmp_path=tmp_path).compilar_lote(["a"])

    comando, _ = ejecutor.llamadas[0]
    assert "talend_job_build_batch" in comando
    assert _entrada(comando)["jobs"] == ["a"]
    assert _entrada(comando)["parallelism"] == 4
    assert comando[:3] == ["bun", "run", "cli"]
    assert "--yes" in comando


def test_refrescar_pide_el_refresco_del_workspace(tmp_path):
    """Studio no ve un `.item` copiado a mano hasta que se refresca el workspace."""
    ejecutor = EjecutorFalso('{"ok": true, "data": {}}')

    _backend(ejecutor, tmp_path=tmp_path).refrescar()

    comando, _ = ejecutor.llamadas[0]
    assert "talend_bridge_refresh_workspace" in comando


def test_compilar_lote_mapea_la_respuesta_real(tmp_path):
    """La respuesta real del puente: un mapa `result.jobs` con `ok` y `error` por Job."""
    ejecutor = EjecutorFalso(_respuesta("build_batch.json"))

    resultado = _backend(ejecutor, tmp_path=tmp_path).compilar_lote(["no_existe"])

    assert resultado == ResultadoLote(
        compilan=(), no_compilan={"no_existe": "El job no existe en el repositorio"}
    )


def test_compilar_lote_separa_los_que_compilan(tmp_path):
    salida = json.dumps(
        {
            "ok": True,
            "data": {
                "result": {
                    "jobs": {
                        "a": {"ok": True},
                        "b": {"ok": False, "error": "x"},
                        "c": {"ok": True},
                    }
                }
            },
        }
    )

    resultado = _backend(EjecutorFalso(salida), tmp_path=tmp_path).compilar_lote(["c", "b", "a"])

    assert resultado.compilan == ("c", "a")
    assert resultado.no_compilan == {"b": "x"}


def test_compilar_lote_acepta_la_forma_resumida(tmp_path):
    ejecutor = EjecutorFalso(
        '{"ok": true, "data": {"noCompilan": [{"job": "b", "error": "x"}], "compilan": ["a"]}}'
    )

    resultado = _backend(ejecutor, tmp_path=tmp_path).compilar_lote(["a", "b"])

    assert resultado == ResultadoLote(compilan=("a",), no_compilan={"b": "x"})


def test_verificar_mapea_el_veredicto(tmp_path):
    salida = json.dumps(
        {
            "ok": True,
            "data": {
                "job": "a",
                "compiles": True,
                "verdict": "ok_con_avisos",
                "findings": {"errors": [], "warnings": ["falta una etiqueta"]},
            },
        }
    )
    ejecutor = EjecutorFalso(salida)

    veredicto = _backend(ejecutor, tmp_path=tmp_path).verificar("a", {"ruta_x": "/tmp/x"})

    assert veredicto == Veredicto("ok_con_avisos", ("[WARN] falta una etiqueta",))
    comando, _ = ejecutor.llamadas[0]
    assert "talend_job_verify" in comando
    # `talend_job_verify` no acepta contexto: se manda solo el Job, sin ejecutarlo.
    assert _entrada(comando) == {"job": "a", "run": False}


def test_verificar_un_job_que_no_compila_da_veredicto_de_error(tmp_path):
    salida = json.dumps(
        {"ok": False, "data": {"job": "a", "compiles": False, "verdict": "error", "findings": {}}}
    )

    veredicto = _backend(EjecutorFalso(salida), tmp_path=tmp_path).verificar("a", {})

    assert veredicto == Veredicto("error", ())


def test_cli_ausente_lanza_backend_no_disponible(tmp_path):
    backend = TalendCliBackend(
        talend_dir=tmp_path / "no-existe", proyecto=tmp_path / "PRJ", tiempo_max=1.0
    )

    with pytest.raises(BackendNoDisponible, match="no se encontró"):
        backend.compilar_lote(["a"])


def test_json_invalido_lanza_error_controlado(tmp_path):
    ejecutor = EjecutorFalso("no es json")

    with pytest.raises(BackendNoDisponible, match="respuesta no válida"):
        _backend(ejecutor, tmp_path=tmp_path).compilar_lote(["a"])


def test_tiempo_maximo_se_propaga(tmp_path):
    ejecutor = EjecutorFalso()

    _backend(ejecutor, tiempo_max=7.5, tmp_path=tmp_path).compilar_lote(["a"])

    assert ejecutor.llamadas[0][1] == 7.5


def test_ningun_secreto_en_la_linea(tmp_path):
    ejecutor = EjecutorFalso()

    _backend(ejecutor, tmp_path=tmp_path).verificar("a", {"ruta_clientes": "/data/c.csv"})

    comando, _ = ejecutor.llamadas[0]
    assert not [palabra for palabra in comando if "password" in palabra.lower()]


def test_contexto_con_password_se_rechaza_antes_de_llamar(tmp_path):
    ejecutor = EjecutorFalso()

    with pytest.raises(ValueError, match="secreto"):
        _backend(ejecutor, tmp_path=tmp_path).verificar("a", {"DB_PASSWORD": "x"})

    assert ejecutor.llamadas == []


def test_respuesta_con_error_lanza_backend_no_disponible(tmp_path):
    """Un diálogo abierto en Studio llega así: `ok: false` con `error`, sin `data`."""
    ejecutor = EjecutorFalso(
        '{"ok": false, "error": {"code": "STUDIO_DIALOG_OPEN", "message": "Studio bloqueado"}}'
    )

    with pytest.raises(BackendNoDisponible, match="Studio bloqueado"):
        _backend(ejecutor, tmp_path=tmp_path).verificar("a", {})
