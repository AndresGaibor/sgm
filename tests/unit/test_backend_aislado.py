"""Aislamiento del núcleo: solo `backend_talend/` conoce la CLI de Talend.

Si un módulo del núcleo importara `talend-mcp`, `sgm` dejaría de funcionar sin Studio instalado.
La prueba recorre el código y nombra los archivos culpables.
"""

from __future__ import annotations

from pathlib import Path

SRC = Path(__file__).resolve().parents[2] / "src" / "sgm"
PROHIBIDO = ("talend-mcp", "mcp_cliente", '"bun"')
EXENTO = SRC / "backend_talend"


def _archivos() -> list[Path]:
    return sorted(
        ruta for ruta in SRC.rglob("*.py") if EXENTO not in ruta.parents and ruta != EXENTO
    )


def test_ningun_modulo_del_nucleo_habla_con_la_cli():
    culpables = []
    for ruta in _archivos():
        texto = ruta.read_text(encoding="utf-8")
        encontrados = [marca for marca in PROHIBIDO if marca in texto]
        if encontrados:
            culpables.append(f"{ruta.relative_to(SRC.parent)}: {', '.join(encontrados)}")

    assert not culpables, (
        "el núcleo no puede depender de talend-mcp; muévelo a backend_talend/: " + "; ".join(culpables)
    )


def test_la_prueba_mira_todos_los_archivos():
    """Sin archivos la prueba anterior pasaría sin comprobar nada."""
    assert len(_archivos()) > 100
