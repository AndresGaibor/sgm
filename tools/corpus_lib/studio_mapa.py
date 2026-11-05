"""Mapa de contexto del arnés de Studio: qué variable de contexto recibe qué archivo o carpeta.

`mapa.yaml` es un mapa plano `variable: ruta_relativa_al_caso`:

    ruta_origen: entradas/ventas.csv     archivo del caso
    ruta_clientes: entradas/clientes.csv
    ruta_resultados: salida/             carpeta: termina en '/' y el Job escribe dentro

Las rutas se resuelven dentro de la carpeta de trabajo (copia de `entradas/`). Los valores de
`--contexto clave=valor` se añaden tal cual. El lanzador de `validar_en_studio` no entrecomilla
los parámetros, así que una ruta o valor con espacios se rechaza.
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml

_IDENTIFICADOR = re.compile(r"[A-Za-z_]\w*$")
_PREFIJO_SALIDA = "salida/"


def leer_mapa(ruta: Path | None) -> dict[str, str]:
    """Lee `mapa.yaml`. Sin ruta, el mapa está vacío. Las rutas deben ser relativas al caso."""
    if ruta is None:
        return {}
    if not ruta.is_file():
        raise ValueError(f"no existe el mapa de contexto: {ruta}")
    datos = yaml.safe_load(ruta.read_text(encoding="utf-8"))
    if datos is None:
        return {}
    if not isinstance(datos, dict):
        raise ValueError(f"{ruta}: se esperaba un mapa 'variable: ruta'")
    mapa: dict[str, str] = {}
    for clave, valor in datos.items():
        if not isinstance(clave, str) or not _IDENTIFICADOR.match(clave):
            raise ValueError(f"{ruta}: nombre de variable no válido '{clave}'")
        if not isinstance(valor, str) or not valor.strip():
            raise ValueError(f"{ruta}: la variable '{clave}' necesita una ruta de texto")
        normal = valor.strip().replace("\\", "/")
        if normal.startswith("/") or re.match(r"[A-Za-z]:", normal) or ".." in normal.split("/"):
            raise ValueError(f"{ruta}: la ruta de '{clave}' debe ser relativa al caso: {valor}")
        mapa[clave] = normal
    return mapa


def _literal(texto: str) -> tuple[str, str]:
    if "=" not in texto:
        raise ValueError(f"--contexto espera clave=valor, no '{texto}'")
    clave, valor = texto.split("=", 1)
    clave = clave.strip()
    if not _IDENTIFICADOR.match(clave):
        raise ValueError(f"nombre de variable de contexto no válido: '{clave}'")
    return clave, valor


def parametros_contexto(mapa: dict[str, str], trabajo: Path, literales: list[str]) -> list[str]:
    """Pares `clave=valor` para `--context_param`, con rutas absolutas dentro de `trabajo`.

    Una carpeta del mapa se crea si falta y su valor termina en '/'. Un archivo debe existir en
    el caso, salvo que esté bajo `salida/`, que es donde el Job escribe.
    """
    fijos = dict(_literal(texto) for texto in literales)
    repetidas = sorted(set(mapa) & set(fijos))
    if repetidas:
        raise ValueError(f"variables dadas en el mapa y en --contexto a la vez: {repetidas}")
    pares: list[str] = []
    for clave, relativa in mapa.items():
        destino = trabajo / relativa
        if relativa.endswith("/"):
            destino.mkdir(parents=True, exist_ok=True)
            valor = destino.as_posix() + "/"
        else:
            if not relativa.startswith(_PREFIJO_SALIDA) and not destino.is_file():
                raise ValueError(f"el mapa apunta a '{relativa}', que no existe en el caso")
            valor = destino.as_posix()
        pares.append(f"{clave}={valor}")
    pares += [f"{clave}={valor}" for clave, valor in fijos.items()]
    for par in pares:
        if " " in par:
            raise ValueError(f"el lanzador no admite espacios en los parámetros: {par}")
    return pares
