"""Operadores sobre filas del intérprete: filtrar, proyectar, seleccionar, renombrar y unir.

Y también mezclar, ordenar y quitar duplicados.

Movido desde `interprete.py` sin cambio de comportamiento (decisión del dueño, hito 242m).
"""

from __future__ import annotations

from sgm.ir.models import Plan
from sgm.migrar import semantica
from sgm.migrar.interprete_base import _clave, _nombre_de_columna  # noqa: F401 - reexportado
from sgm.migrar.interprete_orden import _llaves, _ordenar, _unicos  # noqa: F401 - reexportado
from sgm.migrar.interprete_subconsultas import SubconsultaNoSoportada, _fuentes, preparar
from sgm.migrar.interprete_valores import (
    NoSoportadoEnInterprete,
    _arbol,
    _columna,
    _tabla,
    _valor,
    _verdad,
)

_TIPOS_DE_UNION = frozenset({"inner", "left", "left outer", "cross"})
def _filtrar(
    filas: list[dict], expresion: str, tablas: dict[str, list[dict]] | None = None
) -> list[dict]:
    arbol = _arbol(expresion)
    try:
        arbol = preparar(
            arbol,
            filas,
            tablas,
            filtrar=_filtrar,
            evaluar=_valor,
            columna=_columna,
        )
    except SubconsultaNoSoportada as error:
        raise NoSoportadoEnInterprete("subconsulta", str(error)) from error
    return [fila for fila in filas if _verdad(_valor(arbol, fila))]


def _validar_subconsulta_de_union(
    params: dict, actual: list[dict], plan: Plan, por_operador: dict, tablas: dict
) -> None:
    """Valida el IN original antes de ejecutar el cruce que lo representa en el plan."""
    metadatos = params.get("interpreter_subquery")
    if not isinstance(metadatos, dict):
        return
    lector = str(metadatos.get("source_read") or "")
    contexto = dict(tablas)
    if lector in por_operador:
        fuente = plan.graph.operator(lector)
        nombre = _tabla(fuente.params.get("dataset", ""))
        if nombre:
            contexto[nombre] = por_operador[lector]
    fuentes = _fuentes(_arbol(str(metadatos.get("expression") or "")))
    if any(nombre not in contexto for nombre in fuentes):
        # El plan optimizado ya materializa las llaves del IN. No volver a evaluar la subconsulta
        # si su fuente intermedia fue plegada; la validación estructural corresponde al lowering.
        return
    try:
        preparar(
            _arbol(str(metadatos.get("expression") or "")),
            actual,
            contexto,
            filtrar=_filtrar,
            evaluar=_valor,
            columna=_columna,
        )
    except SubconsultaNoSoportada as error:
        raise NoSoportadoEnInterprete("subconsulta", str(error)) from error


def _fila_de(
    pares: list[tuple[str, object, object | None]], fila: dict, secuencial: bool = False
) -> dict:
    """Las columnas de la salida, en el orden de las asignaciones."""
    resultado = {}
    for destino, arbol, condicional in pares:
        contexto = {**fila, **resultado} if secuencial else fila
        if condicional is None:
            valor = _valor(arbol, contexto)
        elif isinstance(condicional, dict):
            valor = None
            for condicion, rama in condicional["branches"]:
                if _verdad(_valor(condicion, contexto)):
                    valor = _valor(rama, contexto)
                    break
            else:
                valor = _valor(condicional["otherwise"], contexto)
        else:
            condicion, alternativa = condicional
            rama = arbol if _verdad(_valor(condicion, contexto)) else alternativa
            valor = _valor(rama, contexto)
        resultado[destino] = semantica.a_texto(valor)
    return resultado


def _con_clave_existente(fila: dict, nuevos: dict) -> dict:
    """Cambia el nombre de cada columna nueva por el de la fila si ya existe con otra mayúscula."""
    existentes = {k.lower(): k for k in fila}
    return {existentes.get(k.lower(), k): v for k, v in nuevos.items()}


def _proyectar(filas: list[dict], asignaciones: list[dict], aditivo: bool) -> list[dict]:
    """Cada asignación es una columna de la salida.

    Un `SELECT` reemplaza la fila —solo salen sus columnas— y una asignación de DATA step le agrega
    columnas a la que ya había. El plan lo dice con `modo: agrega`, que pone el traductor del DATA
    step; sin la marca, el `derive` es una proyección.
    """
    if not asignaciones:
        return filas
    pares = []
    for asignacion in asignaciones:
        condicion = asignacion.get("conditional")
        condicional = None
        if isinstance(condicion, dict):
            if condicion.get("branches"):
                condicional = {
                    "branches": [
                        (
                            _arbol(str(rama.get("condition") or "")),
                            _arbol(str(rama.get("expression") or "")),
                        )
                        for rama in condicion["branches"]
                    ],
                    "otherwise": _arbol(str(condicion.get("otherwise") or "")),
                }
            else:
                condicional = (
                    _arbol(str(condicion.get("condition") or "")),
                    _arbol(str(condicion.get("otherwise") or "")),
                )
        pares.append(
            (
                str(asignacion.get("target") or ""),
                _arbol(str(asignacion.get("expression") or "")),
                condicional,
            )
        )
    # `_N_` (lrcon, p. 79): el número de iteración es la posición de la fila en la lista que recibe
    # esta asignación. Va como clave auxiliar solo para evaluar; no sale como columna.
    contexto = [{**fila, _CLAVE_N: i + 1} for i, fila in enumerate(filas)]
    if aditivo:
        # SAS no distingue mayúsculas en los nombres de variable (`lrcon`, p. 49): una asignación
        # a `VALOR` sobre una columna `valor` la sustituye, no añade una segunda.
        return [
            {**fila, **_con_clave_existente(fila, _fila_de(pares, ctx, secuencial=True))}
            for fila, ctx in zip(filas, contexto, strict=True)
        ]
    return [_fila_de(pares, ctx) for ctx in contexto]


_CLAVE_N = "_n_"


def _seleccionar(filas: list[dict], params: dict) -> list[dict]:
    """Aplica KEEP o DROP como proyección de columnas, sin cambiar el orden de la fila."""
    nombres = {str(nombre).lower() for nombre in params.get("names") or []}
    modo = str(params.get("mode") or "").lower()
    if modo == "keep":
        return [
            {nombre: valor for nombre, valor in fila.items() if nombre.lower() in nombres}
            for fila in filas
        ]
    if modo == "drop":
        return [
            {nombre: valor for nombre, valor in fila.items() if nombre.lower() not in nombres}
            for fila in filas
        ]
    raise NoSoportadoEnInterprete("select", f"modo '{modo}'")


def _renombrar(filas: list[dict], params: dict) -> list[dict]:
    """Renombra variables solo en la fila de salida (`lestmtsref`, pp. 326-327)."""
    cambios = {
        str(origen).lower(): str(destino).lower()
        for origen, destino in params.get("pairs") or []
    }
    return [
        {cambios.get(str(nombre).lower(), nombre): valor for nombre, valor in fila.items()}
        for fila in filas
    ]


def _unir(izquierda: list[dict], derecha: list[dict], params: dict) -> list[dict]:
    """Inner y left join por llaves; una llave repetida da una fila por pareja, como en SQL."""
    tipo = str(params.get("join_type") or "inner").strip().lower()
    if tipo not in _TIPOS_DE_UNION:
        raise NoSoportadoEnInterprete("join", f"tipo '{tipo}'")
    pares = [list(par) for par in params.get("keys") or [] if len(list(par)) == 2]
    if tipo == "cross" or not pares:
        if tipo == "cross":
            return [{**fila, **otra} for fila in izquierda for otra in derecha]
        raise NoSoportadoEnInterprete("join", f"'{tipo}' sin llaves demostrables")
    arboles = [(_arbol(str(uno)), _arbol(str(otro))) for uno, otro in pares]
    indice: dict[tuple, list[dict]] = {}
    for fila in derecha:
        llave = tuple(_clave(_valor(arbol, fila)) for _, arbol in arboles)
        indice.setdefault(llave, []).append(fila)
    vacia = dict.fromkeys(derecha[0], None) if derecha else {}
    resultado: list[dict] = []
    for fila in izquierda:
        llave = tuple(_clave(_valor(arbol, fila)) for arbol, _ in arboles)
        parejas = indice.get(llave)
        if parejas:
            resultado += [{**fila, **otra} for otra in parejas]
        elif tipo in ("left", "left outer"):
            resultado.append({**vacia, **fila})
    return resultado


def _mezclar(entradas: list[list[dict]], banderas: list[str | None], params: dict) -> list[dict]:
    """`MERGE ... BY k` de un DATA step: junta por grupo de llave, fila con fila, no por producto.

    Dentro de un grupo la fila `j` de cada tabla va con la fila `j` de las demás. A la tabla que se
    queda sin filas se le mantienen los últimos valores; a la que no tiene el grupo, ninguno. Las
    columnas con el mismo nombre las pisa la última tabla que aporta fila. `IN=` vale 1 solo si la
    tabla aportó una fila a esa salida. Salida ordenada por la llave, como exige el `BY`.
    """
    llaves = [str(n).split(".")[-1].lower() for n in params.get("by") or []]
    # El MERGE exige entradas ordenadas o agrupadas por BY (lrcon, p. 584): no se ordenan solas.
    for filas in entradas:
        claves = [tuple(_clave(_columna(f, k)) for k in llaves) for f in filas]
        if any(antes > despues for antes, despues in zip(claves, claves[1:], strict=False)):
            raise NoSoportadoEnInterprete("merge", "entrada no ordenada por BY (lrcon, p. 584)")
    grupos: list[dict[tuple, list[dict]]] = []
    for filas in entradas:
        por_llave: dict[tuple, list[dict]] = {}
        for fila in filas:
            por_llave.setdefault(tuple(_clave(_columna(fila, k)) for k in llaves), []).append(fila)
        grupos.append(por_llave)
    columnas: list[str] = []
    for filas in entradas:
        for fila in filas[:1]:
            columnas += [c for c in fila if c not in columnas]
    tipo = str(params.get("join_type") or "full").strip().lower()
    resultado: list[dict] = []
    for llave in sorted({k for g in grupos for k in g}):
        miembros = [g.get(llave, []) for g in grupos]
        for posicion in range(max(len(m) for m in miembros)):
            fila = dict.fromkeys(columnas)
            presentes = []  # la tabla tiene observaciones en el grupo: decide qué filas salen
            aportes = []  # aporta una observación en ESTA iteración: es el `IN=` (lrcon, p. 75)
            for filas in miembros:
                if filas:
                    fila.update(filas[min(posicion, len(filas) - 1)])
                presentes.append(bool(filas))
                aportes.append(posicion < len(filas))
            if tipo == "inner" and not all(presentes):
                continue
            if tipo == "left" and not presentes[0]:
                continue
            if tipo == "right" and not presentes[1]:
                continue
            for nombre, aporto in zip(banderas, aportes, strict=True):
                if nombre:
                    fila[nombre.lower()] = 1 if aporto else 0
            resultado.append(fila)
    return resultado


def _derecha(params: dict) -> str | None:
    """Tabla del lado derecho de la unión: la que califica el segundo elemento de la primera llave.

    Es lo único que dice qué entrada del mapa es la de la derecha: el orden de los predecesores
    en el grafo no lo dice, porque el plegado de `read` mete aristas de más.
    """
    for par in params.get("keys") or []:
        partes = str(list(par)[1]).split(".") if len(list(par)) == 2 else []
        if len(partes) == 2:
            return _tabla(partes[0])
    return None


