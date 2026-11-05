"""Sección 2.1 del diseño: parámetros de ruta y de nombre de archivo, con lo que el SAS demuestra.

Cada parámetro declarado en `decisiones/<programa>.diseno.yaml` (clave `parametros`) lleva una
expresión `busca` sobre las fuentes del SAS (o sobre sus salidas, con `desde: salidas`). Si la
expresión casa, el valor sale de la ruta hallada: su nombre de archivo, o su carpeta cuando
`valor: directorio`. Si no casa, el parámetro no se emite y queda pendiente en el manual.
"""

from __future__ import annotations

import re

from sgm.proceso.entradas_salidas import EntradasSalidas, nombre_archivo
from sgm.proceso.secciones_entrada import ORIGEN_SAS

Fila = dict[str, str]
Seccion = dict[str, Fila]

TIPO_TEXTO = "String"  # en el SAS, rutas y nombres son literales de texto
VALOR_DIRECTORIO = "directorio"


def directorio(ruta: str) -> str:
    """Carpeta de `ruta`, con su separador final, como la escribe el SAS."""
    separador = "\\" if "\\" in ruta else "/"
    return ruta[: ruta.rfind(separador) + 1]


def _rutas(declarado: dict[str, str], es: EntradasSalidas) -> list[str]:
    """Rutas del SAS donde buscar: las fuentes, o las salidas si `desde` lo dice."""
    if declarado.get("desde") == "salidas":
        return [ruta for plantilla in es.salidas for _producto, ruta in plantilla.instancias]
    return [fuente.ubicacion for fuente in es.fuentes]


def _valor(rutas: list[str], modo: str) -> str | None:
    """Valor del parámetro según `modo`; None si las rutas no se pueden reducir a uno."""
    if modo == VALOR_DIRECTORIO:
        carpetas = {directorio(ruta) for ruta in rutas}
        return carpetas.pop() if len(carpetas) == 1 else None
    nombres = {nombre_archivo(ruta) for ruta in rutas}
    return nombres.pop() if len(nombres) == 1 else None


def seccion_parametros(
    declarados: list[dict[str, str]], es: EntradasSalidas
) -> tuple[Seccion, dict[str, str]]:
    """Sección 2.1 y origen de cada fila (`sas` cuando la ruta sale del programa)."""
    seccion: Seccion = {}
    origenes: dict[str, str] = {}
    for d in declarados:
        patron = re.compile(d["busca"], re.IGNORECASE)
        halladas = [ruta for ruta in _rutas(d, es) if patron.search(ruta)]
        valor = _valor(halladas, d.get("valor", "")) if halladas else None
        if valor is None:
            continue
        seccion[d["clave"]] = {"tipo": TIPO_TEXTO, "valor": valor, "nota": ""}
        origenes[d["clave"]] = ORIGEN_SAS
    return seccion, origenes
