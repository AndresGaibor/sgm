"""Serialización de contextos de migración."""

from __future__ import annotations

import json
import re

from sgm.talend_item.modelo import ParametroContexto

# Un nombre de variable que huele a credencial no se escribe con su valor, ni en el YAML.
_SECRETO = re.compile(r"(pass|pwd|secret|token|clave)", re.IGNORECASE)


def _contexto_yaml(grupo: str, parametros: list[ParametroContexto]) -> str:
    """Un grupo de contexto como YAML: la lista de variables, con su valor y para qué sirve."""
    lineas = [
        f"# Contexto {grupo} del Job.",
        "# Editar estos valores y volver a importar el Job: el .item no se toca.",
        f"grupo: {grupo}",
    ]
    if not parametros:
        return "\n".join([*lineas, "variables: []", ""])
    lineas.append("variables:")
    for parametro in parametros:
        oculto = bool(_SECRETO.search(parametro.nombre))
        descripcion = parametro.comentario or "sin descripción"
        if oculto:
            descripcion += " (valor oculto: no se escribe en el archivo)"
        lineas += [
            f"  - nombre: {parametro.nombre}",
            f"    tipo: {parametro.tipo}",
            f"    valor: {json.dumps('' if oculto else parametro.valor, ensure_ascii=False)}",
            f"    descripcion: {json.dumps(descripcion, ensure_ascii=False)}",
        ]
    return "\n".join([*lineas, ""])
