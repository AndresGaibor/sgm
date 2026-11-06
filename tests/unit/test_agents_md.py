"""Pruebas de `AGENTS.md`: que nombre lo que un agente necesita y que sus rutas existan.

`AGENTS.md` es lo primero que lee quien llega al repositorio. Si nombra una ruta que ya no está,
manda a leer el vacío; si no nombra el plan maestro, el agente trabaja sobre una secuencia de fases
superada y descubre el error cincuenta líneas más tarde.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools" / "referencia"))

import fuentes  # noqa: E402

AGENTS = (REPO / "AGENTS.md").read_text(encoding="utf-8")

# Rutas de `docs/` citadas entre comillas invertidas. Se descartan las que llevan comodín o
# marcadores de plantilla (`<docset>`): no son archivos concretos y no se pueden comprobar.
_RUTA_DOCS = re.compile(r"`(docs/[^`\s]+?)`")


def _rutas_de_docs() -> list[str]:
    return [r for r in _RUTA_DOCS.findall(AGENTS) if "<" not in r and "*" not in r]


def test_agents_md_dice_donde_esta_la_documentacion():
    # Sin esto, un agente escribe equivalencias sin saber que hay 13 guías a un `grep`.
    for ruta in ("docs/referencia/", "rules/sas/catalogo/", "schemas/rules/catalogo.schema.json"):
        assert ruta in AGENTS, f"AGENTS.md no menciona {ruta}"


def test_agents_md_nombra_cada_guia_sas():
    # Se compara con comillas invertidas y no con el nombre suelto: `proc` aparecería por
    # casualidad dentro de `PROC SQL` y la prueba pasaría sin que la guía esté nombrada.
    sin_nombrar = [g.docset for g in fuentes.SAS_DOCSETS if f"`{g.docset}`" not in AGENTS]
    assert sin_nombrar == []


def test_agents_md_dice_cual_es_el_plan_maestro():
    # Los tres planes no dicen lo mismo; el orden de lectura es parte de la instrucción.
    for ruta in (
        "docs/plan-reescritura/plan-migrador-general.md",
        "docs/plan-reescritura/ruta-a-produccion.md",
        "docs/plan-reescritura/plan.md",
        "docs/plan-sgm-v2/",
    ):
        assert ruta in AGENTS, f"AGENTS.md no menciona {ruta}"
    assert "plan maestro" in AGENTS.lower()


def test_agents_md_avisa_que_la_secuencia_de_fases_de_plan_sgm_v2_esta_superada():
    # `02-fases.md` se lee como un plan vivo si nadie dice lo contrario: es el error de orden que
    # esta sección existe para evitar.
    assert "02-fases.md" in AGENTS
    assert "superada" in AGENTS.lower()


def test_las_rutas_de_docs_que_agents_md_nombra_existen():
    faltan = [r for r in _rutas_de_docs() if not (REPO / r).exists()]
    assert faltan == [], f"AGENTS.md manda a rutas que no existen: {faltan}"


def test_el_readme_de_plan_sgm_v2_no_apunta_a_una_carpeta_inexistente():
    # Decía `docs/plan/`, que nunca existió con ese nombre: quien lo siguiera no encontraba nada.
    readme = (REPO / "docs" / "plan-sgm-v2" / "00-README.md").read_text(encoding="utf-8")
    assert "`docs/plan/`" not in readme
