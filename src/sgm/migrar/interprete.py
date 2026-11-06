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
# Pasos que el plan también deja sueltos, sin el `map` que los envuelve.
_PASOS_SUELTOS = ("filter", "derive", "select", "rename", "sort", "dedup", "aggregate")
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


def _mezclar(entradas: list[list[dict]], banderas: list[str | None], params: dict) -> list[dict]:
    """`MERGE ... BY k` de un DATA step: junta por grupo de llave, fila con fila, no por producto.

    Dentro de un grupo la fila `j` de cada tabla va con la fila `j` de las demás. A la tabla que se
    queda sin filas se le mantienen los últimos valores; a la que no tiene el grupo, ninguno. Las
    columnas con el mismo nombre las pisa la última tabla que aporta fila. `IN=` vale 1 solo si la
    tabla aportó una fila a esa salida. Salida ordenada por la llave, como exige el `BY`.
    """
    llaves = [str(n).split(".")[-1].lower() for n in params.get("by") or []]
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
            presentes = []
            for filas in miembros:
                if filas:
                    fila.update(filas[min(posicion, len(filas) - 1)])
                # La bandera `IN=` sigue en 1 mientras la tabla tiene valores retenidos en el grupo.
                presentes.append(bool(filas))
            if tipo == "inner" and not all(presentes):
                continue
            if tipo == "left" and not presentes[0]:
                continue
            if tipo == "right" and not presentes[1]:
                continue
            for nombre, aporto in zip(banderas, presentes, strict=True):
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


def _nombre_de_columna(filas: list[dict], nombre: object) -> str:
    """Columna que nombra un `ORDER BY` o `DISTINCT`: por nombre o por posición (`ORDER BY 2`)."""
    texto = str(nombre).strip()
    if texto.isdigit() and filas:
        columnas = list(filas[0])
        posicion = int(texto)
        if 1 <= posicion <= len(columnas):
            return columnas[posicion - 1]
    return texto


def _llaves(filas: list[dict], params: dict) -> list[str]:
    """Columnas del `BY`; `_ALL_` son todas las de la fila."""
    nombres: list[str] = []
    for nombre in params.get("by") or []:
        if str(nombre).strip().lower() == "_all_":
            nombres += list(filas[0]) if filas else []
        else:
            nombres.append(_nombre_de_columna(filas, nombre))
    return nombres


def _ordenar(filas: list[dict], params: dict) -> list[dict]:
    """`ORDER BY` de PROC SQL: el faltante va primero en ascendente (`sqlproc`); orden estable.

    Se ordena de la última llave a la primera, cada una con su sentido; como el orden de Python es
    estable, las filas que empatan en todas las llaves conservan el orden en que llegaron.
    """
    llaves = _llaves(filas, params)
    sentidos = list(params.get("descending") or [])
    resultado = list(filas)
    for posicion in range(len(llaves) - 1, -1, -1):
        descendente = posicion < len(sentidos) and bool(sentidos[posicion])
        llave = llaves[posicion]
        resultado.sort(
            key=lambda fila, llave=llave: _clave(_columna(fila, llave)), reverse=descendente
        )
    return resultado


def _unicos(filas: list[dict], params: dict) -> list[dict]:
    """`SELECT DISTINCT`: la primera fila de cada combinación de llaves; faltante = faltante."""
    llaves = _llaves(filas, params)
    vistas: set[tuple] = set()
    resultado: list[dict] = []
    for fila in filas:
        clave = tuple(_clave(_columna(fila, llave)) for llave in llaves)
        if clave not in vistas:
            vistas.add(clave)
            resultado.append(fila)
    return resultado


_AGREGADO = re.compile(
    r"^\s*(count|sum|avg|mean|min|max)\s*\(\s*(distinct\s+)?(\*|[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)?)\s*\)\s*$",
    re.IGNORECASE,
)


def _calcular(funcion: str, distinto: bool, nombre: str, filas: list[dict]) -> object:
    """Un agregado de `PROC SQL` sobre un grupo: ignora los faltantes; sin valores, es faltante.

    `COUNT(*)` cuenta filas; `COUNT(col)` las no faltantes; `SUM`, `AVG`, `MIN` y `MAX` solo miran
    valores presentes (`sqlproc`, funciones de resumen).
    """
    if nombre == "*":
        return len(filas)
    presentes = [
        valor
        for valor in (_columna(fila, nombre.split(".")[-1]) for fila in filas)
        if not semantica.es_faltante(valor)
    ]
    if funcion == "count":
        return len({_clave(v) for v in presentes}) if distinto else len(presentes)
    if not presentes:
        return None
    if funcion in ("min", "max"):
        elegir = min if funcion == "min" else max
        return elegir(presentes, key=_clave)
    numeros = [n for n in (_numero(v) for v in presentes) if n is not None]
    if not numeros:
        return None
    return sum(numeros) if funcion == "sum" else sum(numeros) / len(numeros)


def _agregar(filas: list[dict], params: dict) -> list[dict]:
    """`GROUP BY` de PROC SQL: una fila por grupo, en orden de llaves; el faltante es un grupo."""
    if params.get("pendiente"):
        raise NoSoportadoEnInterprete("aggregate", "columnas sin agregar junto a un agregado")
    grupos = [str(g).split(".")[-1].lower() for g in params.get("group_by") or []]
    llamadas = []
    for agregado in params.get("aggregations") or []:
        texto = str(agregado.get("expression") or "")
        encontrada = _AGREGADO.match(texto)
        if encontrada is None:
            raise NoSoportadoEnInterprete("aggregate", f"'{texto}' no es FUNCION(columna)")
        funcion = encontrada.group(1).lower()
        llamadas.append(
            (
                str(agregado.get("alias") or texto).lower(),
                "avg" if funcion == "mean" else funcion,
                encontrada.group(2) is not None,
                encontrada.group(3),
            )
        )
    por_grupo: dict[tuple, list[dict]] = {}
    for fila in filas:
        llave = tuple(_clave(_columna(fila, g)) for g in grupos)
        por_grupo.setdefault(llave, []).append(fila)
    if not grupos and not por_grupo:
        por_grupo[()] = []  # sin filas, un agregado total sigue dando una fila: COUNT(*) es 0
    resultado = []
    for llave in sorted(por_grupo):
        miembros = por_grupo[llave]
        salida = {g: _columna(miembros[0], g) for g in grupos} if miembros else {}
        for alias, funcion, distinto, nombre in llamadas:
            salida[alias] = _calcular(funcion, distinto, nombre, miembros)
        resultado.append(salida)
    return resultado


def _apilar(op: Operator, plan: Plan, tablas: dict, por_operador: dict) -> list[dict]:
    """`SET a b` o `UNION ALL`: las filas de cada entrada una tras otra, juntas por nombre.

    Una columna que una entrada no tiene queda faltante en sus filas, como en SAS. Sin `ALL`
    (`UNION` de PROC SQL) se quitan además las filas repetidas.
    """
    fuentes = [_tabla(nombre) for nombre in op.params.get("sources") or []]
    if fuentes:
        entradas = [tablas.get(nombre, []) for nombre in fuentes]
    else:
        entradas = [por_operador.get(previo, []) for previo in plan.graph.predecessors(op.id)]
    columnas: list[str] = []
    for filas in entradas:
        for fila in filas:
            columnas += [c for c in fila if c not in columnas]
    apiladas = [{c: fila.get(c) for c in columnas} for filas in entradas for fila in filas]
    if op.params.get("all", True):
        return apiladas
    vistas: set[tuple] = set()
    unicas = []
    for fila in apiladas:
        clave = tuple(_clave(valor) for valor in fila.values())
        if clave not in vistas:
            vistas.add(clave)
            unicas.append(fila)
    return unicas


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
        if clase == "join" and not params.get("keys") and params.get("by"):
            fuentes = [_tabla(s) for s in params.get("sources") or []]
            if len(fuentes) < 2 or any(f not in por_tabla for f in fuentes):
                raise NoSoportadoEnInterprete("join", "MERGE sin las tablas de sus fuentes")
            banderas = {
                _tabla(plan.graph.operator(p).params.get("dataset", "")): plan.graph.operator(
                    p
                ).params.get("in")
                for p in plan.graph.predecessors(op.id)
                if plan.graph.operator(p).kind == "read"
            }
            actual = _mezclar(
                [por_tabla[f] for f in fuentes], [banderas.get(f) for f in fuentes], params
            )
        elif clase == "join":
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
        elif clase == "sort":
            actual = _ordenar(actual, params)
        elif clase == "dedup":
            actual = _unicos(actual, params)
        elif clase == "aggregate":
            actual = _agregar(actual, params)
        else:
            raise NoSoportadoEnInterprete(clase or "paso", "el intérprete no lo ejecuta")
    return actual


def _nombres(op: Operator) -> list[str]:
    """Conjuntos de `WORK` bajo los que queda el resultado del operador."""
    clases = (*_PASOS_SUELTOS, "read_file", "map", "join", "union")
    if op.kind in clases:
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
    if op.kind == "union":
        filas = _apilar(op, plan, tablas, por_operador)
        return filas, {nombre: filas for nombre in _nombres(op)}
    if op.kind in ("map", "join", *_PASOS_SUELTOS):
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
