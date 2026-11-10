"""Expresiones Java de normalización para el `tMap` (R1-02).

El SAS de `client_large.sas` normaliza con `input(left(VARn), 30.)`, `COMPRESS(...)` y
`COMPBL(STRIP(UPCASE(...)))`. Estas funciones devuelven **expresiones Java puras** (sin rutinas de
Studio, sin sentencias ni punto y coma) para que el generador del `tMap` las escriba tal cual en un
`mapperTableEntries`. La semántica se contrasta, ejecutando en Studio, contra los vectores con
fuente de `tests/corpus/semantica/vectores.yaml` y contra el esperado construido de
`L8/validaciones/v06`; el oráculo independiente es `tools/corpus_semantica_funciones.py`.

`input` devuelve `java.math.BigDecimal` o `null` (faltante de SAS). Las demás devuelven `String`.
"""

from __future__ import annotations

from sgm.java_literals import literal_java

# Clases de caracteres de COMPRESS: las mismas que el oráculo de semántica. Están aquí porque el
# traductor tiene que reproducir su conducta; las pruebas comparan contra el oráculo, no contra
# esta tabla.
_CLASES = {
    "a": "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ",
    "d": "0123456789",
    "f": "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_",
    "h": "\t",
    "l": "abcdefghijklmnopqrstuvwxyz",
    "n": "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_",
    "p": "!\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~",
    "s": " \t\n\r\f\v",
    "u": "ABCDEFGHIJKLMNOPQRSTUVWXYZ",
}
# Mismo patrón que `_NUMERO` del oráculo: signo opcional, dígitos con punto opcional, o .dígitos.
_NUMERO_JAVA = '"[+-]?(\\\\d+\\\\.?\\\\d*|\\\\.\\\\d+)"'
_STRIP_JAVA = '"^ +| +$"'
_QUITAR_INICIO_JAVA = '"^ +"'


def _nulo_seguro(expression: str, cuerpo: str) -> str:
    """Envuelve una expresión que no admite `null` con la comprobación del faltante."""
    return f"({expression} == null ? null : {cuerpo})"


def as_text(expression: str) -> str:
    """Convierte un resultado a texto para escribirlo: el faltante sale como cadena vacía."""
    return f"java.util.Objects.toString({expression}, \"\")"


def numero_valido(expression: str) -> str:
    """`x.matches(...)` con el mismo patrón que `input`: un texto no numérico es faltante.

    Lo reutilizan los filtros de R1-06 para no repetir el patrón del oráculo: si la columna ya
    viene normalizada por `input_left_wd`, siempre da verdadero salvo en el faltante, que se
    comprueba antes con cortocircuito.
    """
    return f"{expression}.matches({_NUMERO_JAVA})"


def left(expression: str) -> str:
    """LEFT: mueve los blancos iniciales al final, sin cambiar la longitud."""
    return _nulo_seguro(
        expression,
        f"{expression}.replaceAll(\"^( *)(.*)$\", \"$2$1\")",
    )


def strip(expression: str) -> str:
    """STRIP: quita blancos iniciales y finales; un campo en blanco da cadena vacía."""
    return _nulo_seguro(
        expression, f"{expression}.replaceAll({_STRIP_JAVA}, \"\")"
    )


def trim(expression: str) -> str:
    """TRIM: quita blancos finales; un campo en blanco da un solo blanco."""
    recortado = f"{expression}.replaceAll(\" +$\", \"\")"
    return _nulo_seguro(expression, f"({recortado}.isEmpty() ? \" \" : {recortado})")


def upcase(expression: str) -> str:
    """UPCASE: mayúsculas con `Locale.ROOT`, para que Ñ e Í no dependan del locale del motor."""
    return _nulo_seguro(
        expression, f"{expression}.toUpperCase(java.util.Locale.ROOT)"
    )


def lowcase(expression: str) -> str:
    """LOWCASE: minúsculas con `Locale.ROOT`."""
    return _nulo_seguro(
        expression, f"{expression}.toLowerCase(java.util.Locale.ROOT)"
    )


def compbl(expression: str) -> str:
    """COMPBL: cada grupo de blancos seguidos se reduce a uno."""
    return _nulo_seguro(
        expression, f"{expression}.replaceAll(\" +\", \" \")"
    )


def normalizar_nombre(expression: str) -> str:
    """`COMPBL(STRIP(UPCASE(x)))`, la llave de nombre de `L8/validaciones/v06`."""
    return compbl(strip(upcase(expression)))


def _clase_java(conjunto: str) -> str:
    """Convierte un conjunto de caracteres en una clase de regex de Java."""
    partes: list[str] = []
    for caracter in sorted(set(conjunto)):
        codigo = ord(caracter)
        if caracter in "\\]^-":
            partes.append("\\" + caracter)
        elif caracter == '"':
            partes.append('\\"')
        elif 32 <= codigo < 127:
            partes.append(caracter)
        else:
            # Una sola barra aquí: `literal_java` la duplicará en el código Java, y será el motor de
            # regex (no el compilador de Java) quien interprete la secuencia \uXXXX.
            partes.append(f"\\u{codigo:04x}")
    return "[" + "".join(partes) + "]"


def compress(expression: str, chars: str | None = None, modifiers: str = "") -> str:
    """COMPRESS: quita (o conserva con `k`) los caracteres de `chars` y de las clases del
    modificador.

    `chars=None` significa argumento omitido: SAS quita blancos. Con `k` solo se conservan los
    caracteres del conjunto; con `i` se añaden sus versiones en el otro caso.
    """
    mods = (modifiers or "").lower()
    conjunto = " " if chars is None else chars
    for letra, clase in _CLASES.items():
        if letra in mods:
            conjunto += clase
    if "i" in mods:
        conjunto += conjunto.swapcase()
    patron = _clase_java(conjunto)
    if "k" in mods:
        patron = "[^" + patron[1:]
    return _nulo_seguro(
        expression, f"{expression}.replaceAll({literal_java(patron + '+')}, \"\")"
    )


def input_left_wd(expression: str, w: int, d: int = 0) -> str:
    """`input(left(x), w.d)`: `BigDecimal`, o `null` si el texto no es numérico o está vacío.

    LEFT mueve los blancos iniciales al final; como `w.d` trunca a `w` caracteres y después
    descarta los blancos de los extremos, el resultado es equivalente a quitar los blancos
    iniciales, truncar y volver a quitar blancos. Con punto decimal, `d` se ignora; sin punto,
    el entero se divide entre `10^d`. Un punto solo, un campo vacío, blancos internos o texto no
    numérico dan faltante, igual que `_NUMERO` del oráculo.
    """
    if w < 1:
        raise ValueError("El ancho w del informat debe ser al menos 1")
    if d < 0:
        raise ValueError("Los decimales d del informat no pueden ser negativos")
    sin_inicio = f"{expression}.replaceAll({_QUITAR_INICIO_JAVA}, \"\")"
    truncado = f"({sin_inicio}.length() > {w} ? {sin_inicio}.substring(0, {w}) : {sin_inicio})"
    texto = f"{truncado}.replaceAll({_STRIP_JAVA}, \"\")"
    numero = f"new java.math.BigDecimal({texto})"
    valor = f"({texto}.contains(\".\") ? {numero} : {numero}.movePointLeft({d}))"
    return _nulo_seguro(
        expression, f"({texto}.matches({_NUMERO_JAVA}) ? {valor} : null)"
    )


__all__ = [
    "as_text",
    "literal_java",
    "compbl",
    "compress",
    "input_left_wd",
    "left",
    "lowcase",
    "normalizar_nombre",
    "numero_valido",
    "strip",
    "trim",
    "upcase",
]
