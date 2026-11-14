"""Funciones SAS de referencia para el oráculo del traductor (capa B).

Cada función replica la semántica que la documentación pública de SAS indica. Los vectores que
la respaldan viven en `tests/corpus/semantica/vectores.yaml`, con su URL y una cita corta.

Faltante de SAS: `FALTANTE` (instancia de `Faltante`) es el faltante numérico y de texto.
Los argumentos opcionales (`chars`, `delimitadores`) aceptan omitido (`None`) o faltante.
"""

from __future__ import annotations

import math
import operator
import re
import string

from corpus_semantica_numerico import crear_funciones_numericas
from corpus_semantica_texto import (
    compbl,
    count,
    find,
    index,
    length,
    lengthc,
    lengthn,
    propcase,
    repeat,
    reverse,
    right,
    substr_asignar,
    translate,
    tranwrd,
    trimn,
)


class Faltante:
    """Valor faltante de SAS. Se usa la instancia única `FALTANTE`."""

    _instancia: Faltante | None = None

    def __new__(cls) -> Faltante:
        if cls._instancia is None:
            cls._instancia = super().__new__(cls)
        return cls._instancia

    def __repr__(self) -> str:
        return "FALTANTE"


FALTANTE = Faltante()
FUNCIONES_NUMERICAS = crear_funciones_numericas(FALTANTE, lambda valor: isinstance(valor, Faltante))
round_sas = FUNCIONES_NUMERICAS["round"]
_NUMERO = re.compile(r"^[+-]?(\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?$")
_CLASES = {
    "a": string.ascii_letters,
    "d": string.digits,
    "f": string.ascii_letters + "_",
    "h": "\t",
    "l": string.ascii_lowercase,
    "n": string.ascii_letters + string.digits + "_",
    "p": string.punctuation,
    "s": " \t\n\r\f\v",
    "u": string.ascii_uppercase,
}
_DELIMITADORES_ASCII = " !$%&()*+,-./;<^|"
_OPERADORES = {
    "<": operator.lt,
    "<=": operator.le,
    ">": operator.gt,
    ">=": operator.ge,
    "=": operator.eq,
    "^=": operator.ne,
}


def _omitido(valor: object) -> bool:
    """Un argumento opcional cuenta como omitido si es None o faltante."""
    return valor is None or isinstance(valor, Faltante)


def _texto_de_numero(valor: float, justificado: bool) -> str:
    """Convierte un número a texto como lo hace SAS al pasarlo a una función de caracteres.

    `justificado=True` simula el formato BEST12 alineado a la derecha, que usa SUBSTR.
    """
    texto = format(float(valor), ".12g")
    return texto.rjust(12) if justificado else texto


def input_wd(campo: object, w: int, d: int) -> float | Faltante:
    """INPUT con informat numérico `w.d`.

    Lee el campo (hasta `w` caracteres), ignora blancos, y si hay punto decimal ignora `d`.
    Un punto solo, un campo en blanco o texto no numérico dan faltante.
    """
    if isinstance(campo, Faltante) or campo is None:
        return FALTANTE
    texto = str(campo)[: int(w)].strip(" ")
    if texto in ("", ".") or not _NUMERO.match(texto):
        return FALTANTE
    if "." in texto or "e" in texto.lower():
        return float(texto)
    return int(texto) / 10 ** int(d)


def left(texto: str) -> str:
    """LEFT: pasa los blancos iniciales al final; la longitud no cambia."""
    sin_inicio = texto.lstrip(" ")
    return sin_inicio + " " * (len(texto) - len(sin_inicio))


def compress(texto: str, chars: object = None, modificadores: str = "") -> str:
    """COMPRESS: quita los caracteres de `chars` (por omisión, blancos) y los de las clases.

    Con la `k` conserva solo esos caracteres. Con la `i` ignora mayúsculas y minúsculas.
    """
    mods = (modificadores or "").lower()
    conjunto = " " if _omitido(chars) else str(chars)
    for letra, clase in _CLASES.items():
        if letra in mods:
            conjunto += clase
    if "i" in mods:
        conjunto += conjunto.swapcase()
    if "k" in mods:
        return "".join(c for c in texto if c in conjunto)
    return "".join(c for c in texto if c not in conjunto)


def strip(texto: str) -> str:
    """STRIP: quita blancos iniciales y finales. Un campo en blanco da cadena vacía."""
    return texto.strip(" ")


def trim(texto: str) -> str:
    """TRIM: quita blancos finales. Un campo en blanco da un solo blanco."""
    recortado = texto.rstrip(" ")
    return recortado if recortado else " "


def upcase(texto: str) -> str:
    """UPCASE: pasa las letras a mayúsculas."""
    return texto.upper()


def lowcase(texto: str) -> str:
    """LOWCASE: pasa las letras a minúsculas."""
    return texto.lower()


def substr(valor: object, posicion: int, longitud: int | None = None) -> str:
    """SUBSTR: subcadena desde `posicion` (base 1). Si la longitud pasa el final, llega al final.

    Un número se toma como texto alineado a la derecha, de ancho 12.
    """
    if isinstance(valor, Faltante):
        return FALTANTE
    texto = valor if isinstance(valor, str) else _texto_de_numero(valor, justificado=True)
    inicio = int(posicion) - 1
    return texto[inicio:] if _omitido(longitud) else texto[inicio : inicio + int(longitud)]


def substrn(valor: object, posicion: int, longitud: int | None = None) -> str:
    """SUBSTRN: como SUBSTR, pero el número se toma sin alinear (sin blancos iniciales)."""
    if isinstance(valor, Faltante):
        return FALTANTE
    texto = valor if isinstance(valor, str) else _texto_de_numero(valor, justificado=False)
    inicio = int(posicion) - 1
    return texto[inicio:] if _omitido(longitud) else texto[inicio : inicio + int(longitud)]


def scan(texto: str, n: int, delimitadores: object = None) -> str:
    """SCAN: la palabra `n`. Delimitadores consecutivos y del principio o final no cuentan.

    Por omisión usa la lista ASCII de SAS. Si `n` pasa el número de palabras, da un blanco.
    """
    lista = _DELIMITADORES_ASCII if _omitido(delimitadores) else str(delimitadores)
    patron = "[" + "".join(re.escape(c) for c in lista) + "]"
    palabras = [p for p in re.split(patron, texto) if p != ""]
    k = int(n)
    if k == 0 or abs(k) > len(palabras):
        return " "
    return palabras[k - 1] if k > 0 else palabras[k]


def concat(*textos: str) -> str:
    """Operador `||`: une sin quitar blancos."""
    return "".join(str(t) for t in textos)


def trim_concat(izquierda: str, derecha: str) -> str:
    """`trim(a)||b`: quita los blancos finales de `a` antes de unir."""
    return trim(izquierda) + derecha


def catx(separador: str, *elementos: str) -> str:
    """CATX: quita blancos de cada elemento y une los no vacíos con el separador."""
    partes = [_texto_cat(e).strip(" ") for e in elementos]
    return _texto_cat(separador).join(p for p in partes if p != "")


def _texto_cat(valor: object) -> str:
    if isinstance(valor, Faltante):
        raise ValueError("Pendiente: P-CAT-FALTANTE-NUMERICO; falta demostrar BESTw. para missing")
    if isinstance(valor, str):
        return valor
    if isinstance(valor, bool):
        raise ValueError("Pendiente: P-CAT-BOOLEANO-SAS")
    if isinstance(valor, (int, float)):
        return _texto_de_numero(float(valor), justificado=False).strip(" ")
    raise ValueError(f"Pendiente: P-CAT-TIPO-{type(valor).__name__.upper()}")


def cat(*elementos: object) -> str:
    """CAT concatena argumentos sin quitar blancos de carácter."""
    return "".join(_texto_cat(elemento) for elemento in elementos)


def cats(*elementos: object) -> str:
    """CATS quita blancos iniciales y finales de cada argumento."""
    return "".join(_texto_cat(elemento).strip(" ") for elemento in elementos)


def catt(*elementos: object) -> str:
    """CATT quita los blancos finales de cada argumento."""
    return "".join(_texto_cat(elemento).rstrip(" ") for elemento in elementos)


def coalesce(*numeros: object) -> object:
    """COALESCE: el primer valor no faltante; si todos faltan, faltante."""
    for valor in numeros:
        if not isinstance(valor, Faltante):
            return valor
    return FALTANTE


def coalescec(*textos: str) -> str:
    """COALESCEC: el primer texto que no sea vacío ni solo blancos; si no hay, cadena vacía."""
    for valor in textos:
        if str(valor).strip(" ") != "":
            return valor
    return ""


def cmp(izquierda: object, op: str, derecha: object) -> bool:
    """Comparación de SAS. Numéricos: el faltante es menor que cualquier número.

    Textos: se rellena con blancos el más corto antes de comparar.
    """
    if isinstance(izquierda, str) and isinstance(derecha, str):
        ancho = max(len(izquierda), len(derecha))
        return _OPERADORES[op](izquierda.ljust(ancho), derecha.ljust(ancho))
    a = -math.inf if isinstance(izquierda, Faltante) else izquierda
    b = -math.inf if isinstance(derecha, Faltante) else derecha
    return _OPERADORES[op](a, b)


def pertenece(buscado: object, opciones: list[object]) -> bool:
    """IN compara el valor con cada miembro mediante la comparación independiente del oráculo."""
    return any(cmp(buscado, "=", opcion) for opcion in opciones)


def entre(valor: object, bajo: object, alto: object) -> bool:
    """BETWEEN incluye ambos extremos y usa el orden SAS del comparador del oráculo."""
    return cmp(valor, ">=", bajo) and cmp(valor, "<=", alto)


def like(texto: object, patron: object) -> bool:
    """LIKE conserva blancos finales e interpreta `%` y `_` como comodines."""
    if _omitido(texto) or _omitido(patron):
        raise ValueError(
            "Pendiente: P-LIKE-TIPO-Y-LONGITUD-VARIABLE; no se conoce el tipo ni la longitud "
            "declarada del valor faltante"
        )
    if (isinstance(texto, str) and not texto.strip()) or (
        isinstance(patron, str) and not patron.strip()
    ):
        raise ValueError(
            "Pendiente: P-LIKE-TIPO-Y-LONGITUD-VARIABLE; no se conoce la longitud declarada "
            "del valor en blanco"
        )
    valor = texto if isinstance(texto, str) else str(texto)
    especificacion = patron if isinstance(patron, str) else str(patron)
    regex = "".join(
        ".*" if c == "%" else "." if c == "_" else re.escape(c) for c in especificacion
    )
    return re.fullmatch(regex, valor, flags=re.DOTALL) is not None


def suma_mas(izquierda: object, derecha: object) -> float | Faltante:
    """La suma aritmética propaga el faltante según la regla documentada."""
    if _omitido(izquierda) or _omitido(derecha):
        return FALTANTE
    try:
        return float(izquierda) + float(derecha)
    except (TypeError, ValueError):
        return FALTANTE


def sum_sas(*argumentos: object) -> float | Faltante:
    """SUM omite los argumentos faltantes; si todos faltan, el resultado también falta."""
    valores = [float(valor) for valor in argumentos if not _omitido(valor)]
    return sum(valores) if valores else FALTANTE


def is_missing(valor: object) -> bool:
    """IS MISSING / IS NULL: verdadero para el faltante y para el texto en blanco."""
    if isinstance(valor, Faltante):
        return True
    return isinstance(valor, str) and valor.strip(" ") == ""


FUNCIONES = {
    "input": input_wd,
    "left": left,
    "length": length,
    "lengthc": lengthc,
    "lengthn": lengthn,
    "compbl": compbl,
    "tranwrd": tranwrd,
    "translate": translate,
    "index": index,
    "find": lambda texto, buscar, modificadores=None, inicio=None: find(
        texto,
        buscar,
        None if _omitido(modificadores) else modificadores,
        None if _omitido(inicio) else inicio,
    ),
    "count": lambda texto, buscar, modificadores=None: count(
        texto, buscar, None if _omitido(modificadores) else modificadores
    ),
    "propcase": propcase,
    "reverse": reverse,
    "repeat": repeat,
    "right": right,
    "trimn": trimn,
    "compress": compress,
    "strip": strip,
    "trim": trim,
    "upcase": upcase,
    "lowcase": lowcase,
    "substr": substr,
    "substrn": substrn,
    "scan": scan,
    "concat": concat,
    "trim_concat": trim_concat,
    "cat": cat,
    "cats": cats,
    "catt": catt,
    "catx": catx,
    "substr_asignar": lambda texto, posicion, longitud, valor: substr_asignar(
        texto, posicion, None if _omitido(longitud) else longitud, valor
    ),
    "coalesce": coalesce,
    "coalescec": coalescec,
    **FUNCIONES_NUMERICAS,
    "cmp": cmp,
    "is_missing": is_missing,
    "in": pertenece,
    "between": entre,
    "like": like,
    "suma_mas": suma_mas,
    "sum": sum_sas,
}


def evaluar(funcion: str, *args: object) -> object:
    """Evalúa una función SAS de la capa B. `None` se toma como faltante."""
    if funcion not in FUNCIONES:
        raise KeyError(f"función no implementada: {funcion}")
    normalizados = [FALTANTE if a is None else a for a in args]
    return FUNCIONES[funcion](*normalizados)


