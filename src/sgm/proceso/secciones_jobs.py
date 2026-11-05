"""Sección 3 del documento: los Jobs que `sgm talend` emite y cuántos componentes tiene cada uno.

Las cifras no se copian de ningún otro sitio: `componentes_emitidos` llama al mismo emisor que
`sgm talend` (`talend_command`) escribiendo en una carpeta temporal y cuenta los `<node>` de cada
`.item`. Un Job de un solo componente es un esqueleto: un `tJava` que informa lo que le falta.
"""

from __future__ import annotations

import contextlib
import io
import re
import tempfile
from pathlib import Path

Fila = dict[str, str]
Seccion = dict[str, Fila]

LIMITE_COMPONENTES = 20  # diseño manual, sección 3.3b: límite del proyecto por Job
ESTADO_ESQUELETO = "esqueleto: un tJava que informa lo que le falta"
ESTADO_PARCIAL = "emitido con lógica parcial; sin ejecutar en Studio con este programa"
_NODO = re.compile(r"<node\b")
_VERSION = re.compile(r"_\d+(?:\.\d+)*\.item$")


def componentes_emitidos(
    programa: Path, agrupacion: Path, diseno: Path, jobs_yaml: Path
) -> dict[str, int]:
    """Componentes de cada Job que `sgm talend` emite para `programa` (nombre -> cantidad)."""
    from sgm.cli_talend import talend_command  # import tardío: cli_talend usa sgm.proceso

    with tempfile.TemporaryDirectory(prefix="sgm-jobs-") as temporal:
        with contextlib.redirect_stdout(io.StringIO()):
            talend_command(
                source=programa,
                out=Path(temporal),
                agrupacion=agrupacion,
                jobs_yaml=jobs_yaml,
                diseno=diseno,
            )
        proceso = Path(temporal) / programa.stem / "talend" / "process"
        conteo: dict[str, int] = {}
        for item in sorted(proceso.glob("*.item")):
            texto = item.read_text(encoding="utf-8", errors="replace")
            conteo[_VERSION.sub("", item.name)] = len(_NODO.findall(texto))
    return conteo


def seccion_jobs(conteo: dict[str, int]) -> Seccion:
    """Sección 3: una fila por Job, con sus componentes, su relación con el límite y su estado."""
    seccion: Seccion = {}
    for nombre, componentes in conteo.items():
        seccion[nombre] = {
            "componentes": str(componentes),
            "frente al límite": (
                f"dentro del límite de {LIMITE_COMPONENTES}"
                if componentes <= LIMITE_COMPONENTES
                else f"por encima del límite de {LIMITE_COMPONENTES} (diseño, sección 3.3b)"
            ),
            "estado": ESTADO_ESQUELETO if componentes <= 1 else ESTADO_PARCIAL,
        }
    return seccion
