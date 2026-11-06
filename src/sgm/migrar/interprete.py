"""Intérprete del plan: ejecuta los operadores sobre filas y devuelve las tablas de `WORK`.

Es el anillo B de la verificación: prueba que el plan —y por lo tanto el Job que sale de él— calcula
lo que el SAS dice, sin abrir Talend Studio. Sirve para dos cosas que ninguna otra pieza cubre: los
casos donde Studio no está disponible, y el contraste con `esperado/` de todo el corpus.

Soporta lo que la primera rebanada vertical traduce: `read_file`, `write_file`, `map` con pasos
`join` (inner y left), `filter` y `derive`, más los `read` y `write` que solo nombran un
conjunto. Lo demás **no se ignora**: lanza `NoSoportadoEnInterprete` con el operador o el paso
que no entiende. Un intérprete que se salta un `sort` en silencio daría filas correctas en el
conjunto y falsas en el orden, y la prueba pasaría sin probar nada.

Las expresiones se leen con `sqlglot`, que ya es dependencia del proyecto para el SQL, y se evalúan
con la semántica de `sgm.migrar.semantica`. Las columnas se resuelven por nombre y sin distinguir
mayúsculas: el calificador (`ventas.monto`) se ignora, así que en un auto-unión las dos tablas
comparten nombre de columna y la última en entrar gana. Es una limitación conocida, anotada en
`PROGRESS.md`, no un descuido: el plan tampoco distingue los alias de una auto-unión.
"""

from __future__ import annotations

import re
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

import sqlglot
from sqlglot import exp
from sqlglot.errors import ParseError

from sgm.ir.models import Operator, Plan
from sgm.migrar import semantica

# Operadores que el intérprete sabe ejecutar; el resto detiene la ejecución con su nombre.
SOPORTADOS = frozenset(
    {"read", "read_file", "write", "write_file", "map", "join", "filter", "derive"}
)
_TIPOS_DE_UNION = frozenset({"inner", "left", "left outer", "cross"})
_FUNCIONES_SAS = re.compile(r"(?i)\b(input|left|substrn|substr|coalescec|compress|scan)\s*(?=\()")


class NoSoportadoEnInterprete(RuntimeError):
    """El plan usa algo que el intérprete no sabe ejecutar; se dice qué, no se salta."""

    def __init__(self, kind: str, detalle: str = "") -> None:
        self.kind = kind
        self.detalle = detalle
        super().__init__(f"{kind}: {detalle}" if detalle else kind)


# -- valores ------------------------------------------------------------------------------------
def _tabla(nombre: object) -> str:
    """`WORK.ventas` a `ventas`: el intérprete no distingue bibliotecas."""
    return str(nombre or "").strip().lower().split(".")[-1]


def _primero(params: dict, clave: str) -> str:
    valores = params.get(clave) or [""]
    return str(valores[0])


def _arbol(expresion: str):
    """Árbol de una expresión SQL; lo que no se puede leer no se adivina."""
    try:
        preparada = _FUNCIONES_SAS.sub(lambda m: f"sgm_{m.group(1).lower()}", expresion)
        return sqlglot.parse_one(preparada)
    except ParseError as error:
        raise NoSoportadoEnInterprete("expresion", f"'{expresion}': {error}") from None


def _numero(valor: object) -> float | None:
    return semantica.como_numero(valor)


def _verdad(valor: object) -> bool:
    """True si la expresión no es cero ni faltante (`lestmtsref`, p. 130)."""
    if isinstance(valor, bool):
        return valor
    numero = _numero(valor)
    return numero is not None and numero != 0


def _patron(patron: str) -> re.Pattern[str]:
    """`LIKE` de SQL: `%` cualquier secuencia, `_` un carácter; el resto, literal."""
    partes = ["^"]
    for caracter in patron:
        if caracter == "%":
            partes.append(".*")
        elif caracter == "_":
            partes.append(".")
        else:
            partes.append(re.escape(caracter))
    partes.append("$")
    return re.compile("".join(partes), re.DOTALL)


def _funcion(nombre: str, argumentos: list) -> object:
    if nombre.startswith("sgm_"):
        nombre = nombre[4:]
    if nombre == "missing":
        return semantica.es_faltante(argumentos[0] if argumentos else None)
    if nombre == "coalesce":
        return next((valor for valor in argumentos if not semantica.es_faltante(valor)), None)
    if nombre == "coalescec":
        return next((valor for valor in argumentos if not semantica.es_faltante(valor)), None)
    if nombre == "trim":
        return semantica.como_texto(argumentos[0] if argumentos else None).rstrip()
    if nombre == "strip":
        return semantica.como_texto(argumentos[0] if argumentos else None).strip()
    if nombre == "upcase":
        return semantica.como_texto(argumentos[0] if argumentos else None).upper()
    if nombre == "lowcase":
        return semantica.como_texto(argumentos[0] if argumentos else None).lower()
    if nombre == "length":
        return len(semantica.como_texto(argumentos[0] if argumentos else None))
    if nombre == "left":
        texto = semantica.como_texto(argumentos[0] if argumentos else None)
        return texto.lstrip(" ") + " " * (len(texto) - len(texto.lstrip(" ")))
    if nombre in ("substr", "substrn"):
        if len(argumentos) < 2 or semantica.es_faltante(argumentos[0]):
            return " "
        texto = _texto_substr(argumentos[0], nombre)
        inicio = int(_numero(argumentos[1]) or 1) - 1
        longitud = (
            None
            if len(argumentos) < 3 or semantica.es_faltante(argumentos[2])
            else int(_numero(argumentos[2]) or 0)
        )
        if inicio < 0:
            inicio = max(len(texto) + inicio, 0)
        return texto[inicio:] if longitud is None else texto[inicio : inicio + max(longitud, 0)]
    if nombre == "input":
        return _input_wd(argumentos)
    if nombre == "compress":
        return _compress(argumentos)
    if nombre == "scan":
        return _scan(argumentos)
    if nombre == "abs":
        numero = _numero(argumentos[0] if argumentos else None)
        return None if numero is None else abs(numero)
    if nombre == "sum":
        valores = [_numero(valor) for valor in argumentos]
        return sum(valor for valor in valores if valor is not None)
    raise NoSoportadoEnInterprete("funcion", nombre)


def _texto_substr(valor: object, funcion: str) -> str:
    """Conversión numérica documentada para SUBSTR/SUBSTRN en las expresiones del corpus."""
    if isinstance(valor, (int, float)):
        texto = format(valor, ".12g")
        return texto if funcion == "substrn" else texto.rjust(12)
    return semantica.como_texto(valor)


def _input_wd(argumentos: list) -> float | None:
    """Subconjunto documentado INPUT(x,w.d): convierte números y aplica d solo sin punto decimal."""
    if len(argumentos) < 2:
        raise NoSoportadoEnInterprete("funcion", "INPUT requiere el valor y un informat w.d")
    texto = semantica.como_texto(argumentos[0]).strip()
    informat = _numero(argumentos[1])
    if not texto or texto == "." or informat is None:
        return None
    decimales = int(round((informat - int(informat)) * 10))
    try:
        if "." in texto:
            return float(texto)
        numero = Decimal(texto) / (Decimal(10) ** decimales)
        return float(numero)
    except (InvalidOperation, ValueError):
        return None


def _compress(argumentos: list) -> str:
    """COMPRESS con lista de caracteres y modificadores usados por los vectores documentados."""
    texto = semantica.como_texto(argumentos[0] if argumentos else None)
    lista = semantica.como_texto(argumentos[1]) if len(argumentos) > 1 else " "
    modificadores = semantica.como_texto(argumentos[2]).lower() if len(argumentos) > 2 else ""
    quitar: set[str] = set(lista)
    if "d" in modificadores:
        quitar.update("0123456789")
    if "a" in modificadores:
        quitar.update("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ")
    if "l" in modificadores:
        quitar.update("abcdefghijklmnopqrstuvwxyz")
    if "u" in modificadores:
        quitar.update("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    if "s" in modificadores:
        quitar.update(" \t\n\r\f\v")
    if "i" in modificadores:
        quitar.update(caracter.lower() for caracter in tuple(quitar))
        quitar.update(caracter.upper() for caracter in tuple(quitar))
    if "k" in modificadores:
        return "".join(caracter for caracter in texto if caracter in quitar)
    return "".join(caracter for caracter in texto if caracter not in quitar)


def _scan(argumentos: list) -> str:
    """SCAN con delimitadores explícitos y blancos por omisión, según vectores del corpus."""
    if len(argumentos) < 2:
        return " "
    texto = semantica.como_texto(argumentos[0])
    posicion = int(_numero(argumentos[1]) or 0)
    delimitadores = (
        semantica.como_texto(argumentos[2])
        if len(argumentos) > 2
        else " \t\n\r!$%&()*+,-./;<^|"
    )
    if not delimitadores:
        delimitadores = " \t\n\r!$%&()*+,-./;<^|"
    patron = "[" + re.escape(delimitadores) + "]+"
    tokens = [token for token in re.split(patron, texto) if token]
    indice = posicion - 1 if posicion > 0 else len(tokens) + posicion
    return tokens[indice] if 0 <= indice < len(tokens) else " "


def _aritmetica(operador: str, izquierda: object, derecha: object) -> object:
    """Suma, resta, producto y división: con un faltante o texto no numérico, el resultado falta."""
    uno, otro = _numero(izquierda), _numero(derecha)
    if uno is None or otro is None:
        return None
    if operador == "+":
        return uno + otro
    if operador == "-":
        return uno - otro
    if operador == "*":
        return uno * otro
    if otro == 0:
        return None  # en SAS dividir por cero da faltante
    return uno / otro


def _columna(fila: dict, nombre: str) -> object:
    """Valor de una columna sin distinguir mayúsculas: `DESCRIPCION` y `descripcion` son iguales."""
    if nombre in fila:
        return fila[nombre]
    buscado = nombre.lower()
    for clave, valor in fila.items():
        if str(clave).lower() == buscado:
            return valor
    return None


def _valor(nodo, fila: dict) -> object:
    """Valor de un nodo del árbol sobre una fila. Lo que no entiende, lo dice."""
    if isinstance(nodo, exp.Paren):
        return _valor(nodo.this, fila)
    if isinstance(nodo, exp.Column):
        return _columna(fila, nodo.name)
    if isinstance(nodo, exp.Literal):
        return nodo.this if nodo.is_string else _numero(nodo.this)
    if isinstance(nodo, exp.Boolean):
        return bool(nodo.this)
    if isinstance(nodo, exp.Null):
        return None
    if isinstance(nodo, exp.Neg):
        valor = _numero(_valor(nodo.this, fila))
        return None if valor is None else -valor
    if isinstance(nodo, exp.Round):
        valor = _numero(_valor(nodo.this, fila))
        precision = nodo.args.get("decimals")
        multiplo = _numero(_valor(precision, fila)) if precision is not None else 1
        if valor is None or multiplo in (None, 0):
            return None
        cociente = Decimal(str(valor)) / Decimal(str(multiplo))
        redondeado = cociente.quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        return float(redondeado * Decimal(str(multiplo)))
    if isinstance(nodo, exp.Cast):
        return _valor(nodo.this, fila)
    if isinstance(nodo, exp.And):
        return _verdad(_valor(nodo.this, fila)) and _verdad(_valor(nodo.expression, fila))
    if isinstance(nodo, exp.Or):
        return _verdad(_valor(nodo.this, fila)) or _verdad(_valor(nodo.expression, fila))
    if isinstance(nodo, exp.Not):
        return not _verdad(_valor(nodo.this, fila))
    if isinstance(nodo, exp.EQ):
        return semantica.iguales(_valor(nodo.this, fila), _valor(nodo.expression, fila))
    if isinstance(nodo, exp.NEQ):
        return semantica.distintos(_valor(nodo.this, fila), _valor(nodo.expression, fila))
    if isinstance(nodo, exp.LT):
        return semantica.menor(_valor(nodo.this, fila), _valor(nodo.expression, fila))
    if isinstance(nodo, exp.LTE):
        return semantica.menor_igual(_valor(nodo.this, fila), _valor(nodo.expression, fila))
    if isinstance(nodo, exp.GT):
        return semantica.mayor(_valor(nodo.this, fila), _valor(nodo.expression, fila))
    if isinstance(nodo, exp.GTE):
        return semantica.mayor_igual(_valor(nodo.this, fila), _valor(nodo.expression, fila))
    if isinstance(nodo, exp.Is):
        nulo = isinstance(nodo.expression, exp.Null)
        return semantica.es_faltante(_valor(nodo.this, fila)) is nulo
    if isinstance(nodo, exp.Like):
        texto = semantica.como_texto(_valor(nodo.this, fila))
        patron = semantica.como_texto(_valor(nodo.expression, fila))
        return _patron(patron).match(texto) is not None
    if isinstance(nodo, exp.In):
        if nodo.args.get("query") is not None:
            raise NoSoportadoEnInterprete("subconsulta", "IN con SELECT")
        buscado = _valor(nodo.this, fila)
        return any(
            semantica.iguales(buscado, _valor(opcion, fila)) for opcion in nodo.expressions
        )
    if isinstance(nodo, exp.Between):
        valor = _valor(nodo.this, fila)
        bajo = _valor(nodo.args["low"], fila)
        alto = _valor(nodo.args["high"], fila)
        return semantica.mayor_igual(valor, bajo) and semantica.menor_igual(valor, alto)
    if isinstance(nodo, exp.Case):
        for rama in nodo.args.get("ifs") or []:
            if _verdad(_valor(rama.this, fila)):
                return _valor(rama.args["true"], fila)
        por_omision = nodo.args.get("default")
        return None if por_omision is None else _valor(por_omision, fila)
    if isinstance(nodo, (exp.Add, exp.Sub, exp.Mul, exp.Div)):
        simbolo = {exp.Add: "+", exp.Sub: "-", exp.Mul: "*", exp.Div: "/"}[type(nodo)]
        return _aritmetica(simbolo, _valor(nodo.this, fila), _valor(nodo.expression, fila))
    if isinstance(nodo, (exp.DPipe, exp.Concat)):
        izquierda = semantica.como_texto(_valor(nodo.this, fila))
        derecha = semantica.como_texto(_valor(nodo.expression, fila))
        return izquierda + derecha
    if isinstance(nodo, exp.Trim):
        return semantica.como_texto(_valor(nodo.this, fila)).rstrip()
    if isinstance(nodo, exp.Coalesce):
        # En sqlglot el primer argumento va en `this`, no en `expressions`.
        argumentos = [nodo.this, *nodo.expressions]
        return _funcion("coalesce", [_valor(arg, fila) for arg in argumentos])
    if isinstance(nodo, exp.Upper):
        return semantica.como_texto(_valor(nodo.this, fila)).upper()
    if isinstance(nodo, exp.Lower):
        return semantica.como_texto(_valor(nodo.this, fila)).lower()
    if isinstance(nodo, exp.Anonymous):
        return _funcion(nodo.name.lower(), [_valor(arg, fila) for arg in nodo.expressions])
    raise NoSoportadoEnInterprete("expresion", f"{type(nodo).__name__}: {nodo.sql()}")


# -- filas --------------------------------------------------------------------------------------
def _clave(valor: object) -> tuple:
    """Llave de unión con la comparación de SAS: el faltante es un valor, el texto sin blancos."""
    if semantica.es_faltante(valor):
        return (0, 0.0, "")
    numero = _numero(valor)
    if numero is not None:
        return (1, numero, "")
    return (2, 0.0, semantica.como_texto(valor))


def _filtrar(filas: list[dict], expresion: str) -> list[dict]:
    arbol = _arbol(expresion)
    return [fila for fila in filas if _verdad(_valor(arbol, fila))]


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
    if aditivo:
        return [{**fila, **_fila_de(pares, fila, secuencial=True)} for fila in filas]
    return [_fila_de(pares, fila) for fila in filas]


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


def _entradas(plan: Plan, op: Operator, por_operador: dict) -> dict[str, list[dict]]:
    """Filas de cada predecesor, por la tabla que entrega."""
    por_tabla: dict[str, list[dict]] = {}
    for previo in plan.graph.predecessors(op.id):
        for nombre in _nombres(plan.graph.operator(previo)):
            por_tabla.setdefault(nombre, por_operador.get(previo, []))
    return por_tabla


def _base(plan: Plan, op: Operator, derechos: set[str], por_operador: dict) -> list[dict]:
    """La entrada que se acumula: el primer predecesor que no es el lado derecho de una unión."""
    previos = plan.graph.predecessors(op.id)
    for previo in previos:
        nombres = _nombres(plan.graph.operator(previo))
        if not nombres or not set(nombres) <= derechos:
            return por_operador.get(previo, [])
    return por_operador.get(previos[0], []) if previos else []


def _pasos(op: Operator, plan: Plan, por_operador: dict) -> list[dict]:
    """Los pasos de un `map` —o el operador suelto— sobre las entradas, en el orden del plan."""
    pasos = op.params.get("steps")
    if not pasos and op.kind != "map":
        pasos = [{"kind": op.kind, "params": op.params}]
    pasos = pasos or []
    por_tabla = _entradas(plan, op, por_operador)
    derechos = {
        _derecha(paso.get("params") or {}) for paso in pasos if paso.get("kind") == "join"
    }
    actual = _base(plan, op, {d for d in derechos if d}, por_operador)
    for paso in pasos:
        clase = str(paso.get("kind") or "")
        params = paso.get("params") or {}
        if clase == "join":
            tabla = _derecha(params)
            if tabla not in por_tabla:
                raise NoSoportadoEnInterprete(
                    "join", f"no hay una entrada para la tabla '{tabla}'"
                )
            actual = _unir(actual, por_tabla[tabla], params)
        elif clase == "filter":
            actual = _filtrar(actual, str(params.get("expression") or ""))
        elif clase == "derive":
            actual = _proyectar(
                actual, params.get("assignments") or [], aditivo=params.get("modo") == "agrega"
            )
        elif clase == "select":
            actual = _seleccionar(actual, params)
        elif clase == "rename":
            actual = _renombrar(actual, params)
        else:
            raise NoSoportadoEnInterprete(clase or "paso", "el intérprete no lo ejecuta")
    return actual


def _nombres(op: Operator) -> list[str]:
    """Conjuntos de `WORK` bajo los que queda el resultado del operador."""
    if op.kind in ("read_file", "map", "filter", "derive", "select", "rename", "join"):
        return [_tabla(nombre) for nombre in op.params.get("outputs") or []]
    if op.kind == "write_file":
        return [_tabla(nombre) for nombre in op.params.get("inputs") or []]
    if op.kind in ("read", "write"):
        return [_tabla(op.params.get("dataset", ""))]
    return []


def _ramas(op: Operator, filas: list[dict]) -> dict[str, list[dict]]:
    """Un `map` con ramas es un IF/THEN/ELSE que escribe en varias salidas: cada rama su filtro."""
    return {
        _tabla(rama.get("outputs", ["WORK.sin_nombre"])[0]): _filtrar(
            filas, str(rama.get("expression") or "")
        )
        for rama in op.params.get("branches") or []
    }


def _ejecutar(
    op: Operator, plan: Plan, tablas: dict, por_operador: dict
) -> tuple[list[dict], dict[str, list[dict]]]:
    """Filas del operador y las tablas que deja, por nombre sin biblioteca.

    Las dos cosas van juntas porque un operador intermedio —un `join` que alimenta un `map`— no
    tiene tabla propia: sus filas solo se pueden encontrar por su id, y el `map` de detrás las pide
    así.
    """
    if op.kind in ("read", "read_file"):
        nombre = (
            _tabla(op.params.get("dataset", ""))
            if op.kind == "read"
            else _tabla(_primero(op.params, "outputs"))
        )
        if nombre in tablas:
            return tablas[nombre], {nombre: tablas[nombre]}
        previos = plan.graph.predecessors(op.id)
        filas = por_operador.get(previos[0], []) if previos else []
        return filas, {nombre: filas}
    if op.kind in ("write", "write_file"):
        previos = plan.graph.predecessors(op.id)
        if not previos:
            raise NoSoportadoEnInterprete(op.kind, "sin operador de origen")
        filas = por_operador.get(previos[0], [])
        return filas, {nombre: tablas.get(nombre, filas) for nombre in _nombres(op)}
    if op.kind in ("map", "join", "filter", "derive", "select", "rename"):
        previos = plan.graph.predecessors(op.id)
        if op.kind == "map" and op.params.get("branches") and not op.params.get("steps"):
            primera = por_operador.get(previos[0], []) if previos else []
            ramas = _ramas(op, primera)
            return primera, ramas
        filas = _pasos(op, plan, por_operador)
        return filas, {nombre: filas for nombre in _nombres(op)}
    raise NoSoportadoEnInterprete(op.kind, "el intérprete no lo ejecuta")


def ejecutar_plan(
    plan: Plan, entradas: dict[str, list[dict[str, str | None]]]
) -> dict[str, list[dict[str, str | None]]]:
    """Ejecuta el plan y devuelve las tablas de `WORK` que produce, por nombre sin biblioteca.

    `entradas` trae las filas de las tablas que el programa lee, con el nombre de la tabla como
    clave (`WORK.clientes`, `clientes` o `CLIENTES` dan igual). Las columnas de cada fila se buscan
    sin distinguir mayúsculas.
    """
    tablas: dict[str, list[dict]] = {
        _tabla(nombre): [{str(c).lower(): v for c, v in fila.items()} for fila in filas]
        for nombre, filas in entradas.items()
    }
    por_operador: dict[str, list[dict]] = {}
    for op_id in plan.graph.topological():
        op = plan.graph.operator(op_id)
        filas, propias = _ejecutar(op, plan, tablas, por_operador)
        por_operador[op.id] = filas
        tablas.update(propias)
    return tablas


__all__ = ["SOPORTADOS", "NoSoportadoEnInterprete", "ejecutar_plan"]
