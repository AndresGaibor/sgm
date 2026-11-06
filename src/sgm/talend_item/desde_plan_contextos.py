"""Contextos por entorno: las rutas de archivo salen del Job y pasan a variables de contexto.

Una ruta escrita dentro de un `.item` obliga a abrir el Job y volver a compilarlo para mover el
proceso de un entorno a otro. Aquí cada ruta literal del SAS se convierte en una variable
`ruta_<tabla>`, y el Job queda igual en los cuatro entornos: solo cambia el valor.

Los cuatro grupos (`Default`, `DEV`, `QA`, `PROD`) llevan **las mismas claves** en el mismo orden,
que es lo que Studio necesita para que el selector de contexto funcione. El literal del SAS va solo
al grupo `Default`; los demás quedan vacíos y se llenan en cada entorno, porque el valor de
producción no está en el programa.

Ninguna credencial: aquí solo se crean variables de ruta, y el nombre de la variable sale del nombre
de la tabla. Si algún día se añade una, `test_sin_secretos` la rechaza.
"""

from __future__ import annotations

from sgm.ir.models import Plan
from sgm.talend_item.desde_plan_nodos import ruta
from sgm.talend_item.modelo import Nodo, ParametroContexto

GRUPOS = ("Default", "DEV", "QA", "PROD")
# El nombre del parámetro que lleva la ruta de un componente de archivo, en Studio.
PARAMETRO = "FILENAME"


def _tabla(dataset: str) -> str:
    """`WORK.clientes` a `clientes`: el nombre de la variable sale de la tabla, no de la ruta."""
    return dataset.strip().lower().split(".")[-1] or "archivo"


def _primero(params: dict, clave: str) -> str:
    valores = params.get(clave) or [""]
    return str(valores[0])


def rutas_de_plan(plan: Plan) -> dict[str, str]:
    """Ruta literal del SAS -> nombre de su variable de contexto, sin repetir nombres.

    La lectura nombra su variable por la tabla que produce y la escritura por la que escribe: así el
    `ruta_ventas` de la lectura y el de la escritura son el mismo cuando el SAS habla de la misma
    tabla, y distintos cuando no.
    """
    rutas: dict[str, str] = {}
    usados: set[str] = set()
    for op in plan.graph.operators():
        if op.kind == "read_file":
            literal, dataset = op.params.get("datafile"), _primero(op.params, "outputs")
        elif op.kind == "write_file":
            literal, dataset = op.params.get("outfile"), _primero(op.params, "inputs")
        else:
            continue
        camino = ruta(str(literal or ""))
        if not camino:
            continue
        base = f"ruta_{_tabla(dataset)}"
        nombre, n = base, 1
        while nombre in usados:
            n += 1
            nombre = f"{base}_{n}"
        usados.add(nombre)
        rutas.setdefault(camino, nombre)
    return rutas


def contextos_de_plan(plan: Plan) -> dict[str, list[ParametroContexto]]:
    """Los cuatro grupos con las mismas claves; el literal del SAS solo en `Default`."""
    rutas = rutas_de_plan(plan)
    por_ruta: dict[str, str] = {}
    for camino, nombre in rutas.items():
        por_ruta.setdefault(nombre, camino)
    grupos: dict[str, list[ParametroContexto]] = {}
    for grupo in GRUPOS:
        grupos[grupo] = [
            ParametroContexto(
                nombre,
                valor=camino if grupo == "Default" else "",
                comentario=f"ruta del archivo de {nombre.removeprefix('ruta_')}",
            )
            for nombre, camino in por_ruta.items()
        ]
    return grupos


def reemplazar_rutas(nodos: list[Nodo], rutas: dict[str, str]) -> None:
    """Deja `context.ruta_<tabla>` en el `FILENAME` de cada nodo que llevaba una ruta literal.

    Solo se tocan los parámetros cuyo valor es una ruta conocida: un `FILENAME` que ya venía como
    expresión de contexto se queda como está.
    """
    for nodo in nodos:
        nuevos: list = []
        for parametro in nodo.parametros:
            if not isinstance(parametro, tuple):
                nuevos.append(parametro)
                continue
            campo, nombre, valor, show = parametro
            if nombre == PARAMETRO and valor in rutas:
                valor = f"context.{rutas[valor]}"
            nuevos.append((campo, nombre, valor, show))
        nodo.parametros = nuevos


__all__ = ["GRUPOS", "PARAMETRO", "contextos_de_plan", "reemplazar_rutas", "rutas_de_plan"]
