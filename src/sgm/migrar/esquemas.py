"""Esquemas de las tablas que lee un programa, sin ningún YAML.

Por cada `PROC IMPORT`, el esquema de su tabla sale de la primera fuente que lo demuestre:

1. **Catálogo** (`env/schemas/`, origen `catalog`): los tipos son los del entorno.
2. **Cabecera del archivo de muestra** (origen `file_header`): da los nombres, no los tipos.
3. **Columnas que el programa usa aguas abajo** (origen `derived`): los nombres salen de las
   asignaciones, de las llaves de unión y de los filtros.

Los nombres no son lo único que el programa demuestra: una columna que el SAS multiplica, divide,
suma o resta es numérica, porque en SAS solo los números se operan así, y una columna que se pasa a
`SUM`, `MEAN`, `ROUND` o a un `COALESCE` con un número también. Esas columnas salen `Double` —SAS
guarda todo número como doble— y no cuentan como tipo desconocido. Lo demás sale con `String`, el
tipo por omisión documentado, y su pendiente `P-TIPO-DESCONOCIDO` con la línea del `PROC IMPORT`:
quien migre sabe que el tipo no está demostrado. Un tipo numérico o una fecha nunca se suponen por
el nombre de la columna ni por el aspecto de sus datos.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from sgm.ir.models import Column, Operator, Plan
from sgm.ir.types_code import expression_type

# El tipo que se escribe cuando no hay ninguno demostrado; va siempre con su pendiente.
TIPO_POR_OMISION = "String"
# El tipo que el propio programa demuestra cuando opera con una columna: SAS guarda todo número como
# un doble, así que el tipo fiel es `Double`.
TIPO_NUMERICO = "Double"
_TIPO_DESCONOCIDO = "P-TIPO-DESCONOCIDO"
_REFERENCIA = re.compile(r"\b([A-Za-z_]\w*)\.([A-Za-z_]\w*)\b")
# Identificador suelto que no es llamada a función: `select a, b from t` no califica las columnas.
_SUELTO = re.compile(r"\b([A-Za-z_]\w*)\b(?!\s*\()")
_CADENA = re.compile(r"'[^']*'|\"[^\"]*\"")
# Palabras del SQL que un identificador suelto puede ser sin ser una columna.
_PALABRAS = frozenset(
    {
        "and", "or", "not", "is", "null", "missing", "case", "when", "then", "else", "end",
        "true", "false", "between", "like", "in", "as", "distinct", "on", "select", "from",
        "where", "group", "order", "by", "having", "join", "left", "right", "inner", "outer",
        "desc", "asc", "work",
    }
)


# Operando de una expresión: una cadena, un nombre quizá calificado con su tabla, un número o un
# operador. Se recorre así y no con una expresión regular por caso porque `a*b` y `sum(a, 1)` tienen
# la misma forma por dentro y distinto significado.
_TOKEN = re.compile(
    r"'[^']*'|\"[^\"]*\""
    r"|(?P<ident>[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)?)"
    r"|(?P<numero>\d+(?:\.\d+)?)"
    r"|(?P<operador>[+\-*/])"
    r"|(?P<otro>\S)"
)
_LLAMADA = re.compile(r"\b([A-Za-z_]\w*)\s*\(")
# Una expresión que es solo un nombre de columna, quizá con su tabla: el tipo lo da el esquema.
_SOLO_NOMBRE = re.compile(r"[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)?")
# Funciones que solo aceptan números: cualquiera de sus argumentos con nombre es numérico.
_FUNCIONES_NUMERICAS = frozenset(
    {
        "sum", "mean", "avg", "round", "abs", "int", "floor", "ceil", "sqrt", "exp", "log",
        "nmiss", "n", "min", "max",
    }
)
# Funciones que conservan el tipo de sus argumentos: junto a un número, el nombre es numérico.
# `coalescec` e `ifc` quedan fuera a propósito: son las de texto.
_FUNCIONES_MIXTAS = frozenset({"coalesce", "ifn"})


@dataclass(frozen=True)
class PendienteMigracion:
    """Algo que el migrador no pudo resolver y que una persona tiene que completar o decidir."""

    codigo: str
    mensaje: str
    linea: int | None


def _linea(op: Operator) -> int | None:
    return op.evidence[0].line_start if op.evidence else None


def _nombre_base(tabla: str) -> str:
    """`work.clientes` -> `clientes`: como lo nombran las expresiones del SQL."""
    return tabla.split(".")[-1].lower()


def _textos(plan: Plan) -> list[str]:
    """Expresiones que pueden nombrar columnas: asignaciones, llaves, filtros y condiciones."""
    encontrados: list[str] = []
    for op in plan.graph.operators():
        params = op.params
        if op.kind == "filter":
            encontrados.append(str(params.get("expression") or ""))
        for asignacion in params.get("assignments") or []:
            encontrados.append(str(asignacion.get("expression") or ""))
        for llave in params.get("keys") or []:
            encontrados.extend(str(parte) for parte in llave)
        if params.get("condition"):
            encontrados.append(str(params["condition"]))
        for paso in params.get("steps") or []:
            propios = paso.get("params") or {}
            if paso.get("kind") == "filter":
                encontrados.append(str(propios.get("expression") or ""))
            for asignacion in propios.get("assignments") or []:
                encontrados.append(str(asignacion.get("expression") or ""))
            for llave in propios.get("keys") or []:
                encontrados.extend(str(parte) for parte in llave)
            if propios.get("condition"):
                encontrados.append(str(propios["condition"]))
    return [texto for texto in encontrados if texto]


def _sin_tabla(nombre: str) -> str:
    """`ventas.precio` -> `precio`, en minúsculas: como se compara con el esquema."""
    return nombre.split(".")[-1].lower()


def _columnas_aritmeticas(texto: str) -> set[str]:
    """Nombres que aparecen como operando de `*`, `/`, `+` o `-`.

    `*` y `/` solo unen números en SAS, así que un nombre a cualquiera de sus lados es numérico.
    `+` y `-` pueden ser un signo (`-x`), así que solo cuentan con algo a los dos lados.
    """
    piezas = [(m.lastgroup, m.group(0)) for m in _TOKEN.finditer(texto)]
    nombres: set[str] = set()
    for indice, (tipo, valor) in enumerate(piezas):
        if tipo != "operador":
            continue
        izquierda = piezas[indice - 1] if indice else (None, "")
        derecha = piezas[indice + 1] if indice + 1 < len(piezas) else (None, "")
        if valor in "*/":
            lados = (izquierda, derecha)
        elif izquierda[0] in ("ident", "numero") and derecha[0] in ("ident", "numero"):
            lados = (izquierda, derecha)
        else:
            continue
        nombres |= {_sin_tabla(lado) for tipo_lado, lado in lados if tipo_lado == "ident"}
    return {nombre for nombre in nombres if nombre not in _PALABRAS}


def _llamadas(texto: str) -> list[tuple[str, str]]:
    """Cada llamada de la expresión como `(nombre, argumentos)`, con los paréntesis balanceados."""
    encontradas: list[tuple[str, str]] = []
    for coincidencia in _LLAMADA.finditer(texto):
        nivel = 0
        for posicion in range(coincidencia.end() - 1, len(texto)):
            if texto[posicion] == "(":
                nivel += 1
            elif texto[posicion] == ")":
                nivel -= 1
                if nivel == 0:
                    argumentos = texto[coincidencia.end() : posicion]
                    encontradas.append((coincidencia.group(1).lower(), argumentos))
                    break
    return encontradas


def _nombres(texto: str) -> set[str]:
    """Nombres de columna del texto: sin cadenas, sin llamadas y sin palabras del SQL."""
    limpio = _CADENA.sub(" ", texto)
    return {
        _sin_tabla(nombre)
        for nombre in re.findall(r"[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)?(?!\s*\()", limpio)
        if _sin_tabla(nombre) not in _PALABRAS
    }


def _es_numerica(texto: str) -> bool:
    """La expresión opera con números: `a * b`, `a / 2`, `sum(a, b)`, `coalesce(a, 0)`."""
    piezas = [(m.lastgroup, m.group(0)) for m in _TOKEN.finditer(texto)]
    for indice, (tipo, valor) in enumerate(piezas):
        if tipo != "operador":
            continue
        izquierda = piezas[indice - 1] if indice else (None, "")
        derecha = piezas[indice + 1] if indice + 1 < len(piezas) else (None, "")
        if valor in "*/":
            return True
        if izquierda[0] in ("ident", "numero") and derecha[0] in ("ident", "numero"):
            return True
    for funcion, argumentos in _llamadas(texto):
        if funcion in _FUNCIONES_NUMERICAS:
            return True
        if funcion in _FUNCIONES_MIXTAS and re.search(r"\d", _CADENA.sub(" ", argumentos)):
            return True
    return False


def tipo_de_expresion(texto: str) -> str | None:
    """Tipo que la propia expresión demuestra, sin mirar el esquema de las columnas.

    `Double` si opera con números o pasa por una función numérica; `String` si es texto o una
    concatenación; y `None` cuando es una columna suelta, porque ahí el tipo lo dice el esquema.
    """
    limpio = texto.strip()
    if not limpio or _SOLO_NOMBRE.fullmatch(limpio):
        return None
    demostrado = expression_type(limpio)
    if demostrado is not None:
        return demostrado.type
    return TIPO_NUMERICO if _es_numerica(limpio) else TIPO_POR_OMISION


def _columnas_numericas(plan: Plan) -> set[str]:
    """Columnas cuyo tipo numérico demuestra el propio programa, sin catálogo ni muestra."""
    numericas: set[str] = set()
    for texto in _textos(plan):
        numericas |= _columnas_aritmeticas(texto)
        for funcion, argumentos in _llamadas(texto):
            if funcion in _FUNCIONES_NUMERICAS:
                numericas |= _nombres(argumentos)
            elif funcion in _FUNCIONES_MIXTAS and re.search(r"\d", _CADENA.sub(" ", argumentos)):
                numericas |= _nombres(argumentos)
    return numericas


def _columnas_usadas(plan: Plan, tabla: str) -> list[str]:
    """Columnas de `tabla` que el programa nombra en alguna expresión, en orden de aparición."""
    base = _nombre_base(tabla)
    vistas: dict[str, None] = {}
    for texto in _textos(plan):
        for prefijo, columna in _REFERENCIA.findall(texto):
            if prefijo.lower() == base:
                vistas.setdefault(columna.lower(), None)
    for columna in _columnas_sueltas(plan, base):
        vistas.setdefault(columna.lower(), None)
    return list(vistas)


def _entradas(plan: Plan, op: Operator) -> set[str]:
    """Conjuntos que lee el operador, sin librería: sus `read` o los productores de sus entradas."""
    nombres: set[str] = set()
    for previo in plan.graph.predecessors(op.id):
        anterior = plan.graph.operator(previo)
        if anterior.kind == "read":
            nombres.add(_nombre_base(str(anterior.params.get("dataset") or "")))
            continue
        for salida in anterior.params.get("outputs") or []:
            nombres.add(_nombre_base(str(salida)))
    return {nombre for nombre in nombres if nombre}


def _identificadores(texto: str) -> list[str]:
    """Identificadores sueltos de una expresión: sin cadenas, sin referencias calificadas, sin
    palabras del SQL y sin llamadas a función."""
    limpio = _REFERENCIA.sub(" ", _CADENA.sub(" ", texto))
    return [nombre for nombre in _SUELTO.findall(limpio) if nombre.lower() not in _PALABRAS]


def _sueltos(op: Operator) -> list[str]:
    """Identificadores que son una columna entera: asignación, llave, `KEEP` o filtro."""
    nombres: list[str] = []
    grupos = [op.params, *(paso.get("params") or {} for paso in op.params.get("steps") or [])]
    for grupo in grupos:
        nombres.extend(str(nombre) for nombre in grupo.get("names") or [])
        # Las llaves de un ORDER BY o de un DISTINCT son columnas de la entrada; una posición
        # (`ORDER BY 2`) no nombra ninguna.
        nombres.extend(str(n) for n in grupo.get("by") or [] if not str(n).strip().isdigit())
        for asignacion in grupo.get("assignments") or []:
            expresion = str(asignacion.get("expression") or "")
            if asignacion.get("origin") == "columna":
                nombres.append(expresion.split(".")[-1])
            else:
                nombres.extend(_identificadores(expresion))
        for llave in grupo.get("keys") or []:
            nombres.extend(str(parte).split(".")[-1] for parte in llave)
        textos = [str(grupo.get("condition") or ""), str(grupo.get("expression") or "")]
        for texto in textos:
            nombres.extend(_identificadores(texto))
    return [nombre for nombre in nombres if nombre]


def _columnas_sueltas(plan: Plan, base: str) -> list[str]:
    """Columnas sin calificar, solo cuando el operador lee una única tabla.

    `select a, b from work.clientes` no dice `clientes.a`, pero tampoco deja dudas: hay una sola
    tabla. Con dos tablas el nombre suelto puede ser de cualquiera, y entonces no se atribuye.
    """
    vistas: dict[str, None] = {}
    for op in plan.graph.operators():
        if _entradas(plan, op) != {base}:
            continue
        for nombre in _sueltos(op):
            vistas.setdefault(nombre.lower(), None)
    return list(vistas)


def _sin_comillas(texto: str) -> str:
    return texto.strip().strip("'\"")


def _ruta_de_muestra(muestra: Path | None, datafile: object) -> Path | None:
    """El archivo de muestra que corresponde al `DATAFILE` del paso, si se dio una carpeta."""
    if muestra is None or not datafile:
        return None
    nombre = Path(_sin_comillas(str(datafile)).replace("\\", "/")).name
    if muestra.is_file():
        return muestra if muestra.name == nombre else None
    candidata = muestra / nombre
    return candidata if candidata.is_file() else None


def _cabecera(ruta: Path, delimiter: str | None) -> list[str]:
    """Nombres de la primera línea del archivo, con el separador declarado o el que se vea."""
    try:
        primera = ruta.read_text(encoding="utf-8-sig", errors="replace").splitlines()[0]
    except (OSError, IndexError):
        return []
    separador = delimiter or (";" if ";" in primera else ",")
    return [_sin_comillas(campo) for campo in primera.split(separador) if campo.strip()]


def _de_catalogo(tabla: str, catalogo: dict[str, list[Column]]) -> list[Column] | None:
    columnas = catalogo.get(tabla)
    if columnas is None:
        return None
    return [Column(c.name, c.type, c.length, "catalog") for c in columnas]


def esquemas_de_entrada(
    plan: Plan, catalogo: dict[str, list[Column]], muestra: Path | None = None
) -> tuple[dict[str, list[Column]], list[PendienteMigracion]]:
    """Esquema de cada tabla que el plan lee y los pendientes de tipo que quedan."""
    esquemas: dict[str, list[Column]] = {}
    pendientes: list[PendienteMigracion] = []
    numericas = _columnas_numericas(plan)
    for op in plan.graph.operators():
        if op.kind != "read_file":
            continue
        salidas = [str(salida).lower() for salida in op.params.get("outputs") or []]
        if not salidas:
            continue
        tabla = salidas[0]
        demostrado = _de_catalogo(tabla, catalogo)
        if demostrado is not None:
            esquemas[tabla] = demostrado
            continue
        ruta = _ruta_de_muestra(muestra, op.params.get("datafile"))
        cabecera = _cabecera(ruta, op.params.get("delimiter")) if ruta else []
        if cabecera:
            origen = "file_header"
            nombres = cabecera
        else:
            origen = "derived"
            nombres = _columnas_usadas(plan, tabla)
        esquemas[tabla] = [
            Column(
                nombre,
                TIPO_NUMERICO if nombre.lower() in numericas else TIPO_POR_OMISION,
                None,
                origen,
            )
            for nombre in nombres
        ]
        sin_tipo = [nombre for nombre in nombres if nombre.lower() not in numericas]
        if not sin_tipo:
            continue
        pendientes.append(
            PendienteMigracion(
                _TIPO_DESCONOCIDO,
                f"{tabla}: {len(sin_tipo)} de {len(nombres)} columnas sin tipo demostrado; se "
                f"escriben {TIPO_POR_OMISION} hasta que haya catálogo o muestra",
                _linea(op),
            )
        )
    return esquemas, pendientes


__all__ = ["PendienteMigracion", "esquemas_de_entrada"]
