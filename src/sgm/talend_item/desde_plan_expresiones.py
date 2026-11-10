"""Expresiones Java del `tMap` escritas desde el SAS, con la fila resuelta y el faltante cubierto.

El traductor de `sgm.expressions` devuelve Java con `input_row` como marcador de fila: no sabe de
qué entrada del `tMap` sale cada columna. Aquí se cambia por el nombre real de la conexión (`row1`
para la principal, `row2` en adelante para los lookups) usando el esquema de cada entrada.

Además se cubre el faltante, que es la diferencia de semántica que rompe el Job: en SAS un faltante
numérico es **menor que cualquier número** y en Java un `null` en una comparación lanza
`NullPointerException`. Una condición copiada tal cual cambia el resultado del programa o lo tumba.
La comprobación del faltante se reutiliza de `filtros_cuenta.faltante`, la misma de R1-06 y R1-07:
nulo, texto vacío o texto no numérico.
"""

from __future__ import annotations

import re

from sgm.expressions.expressions import translate
from sgm.java_expressions import is_safe_java_expression
from sgm.java_identificadores import is_java_identifier
from sgm.talend_item.filtros_cuenta import faltante

# Columnas de Talend que son número: admiten comparación de orden directa.
NUMERICAS = frozenset(
    {"id_Integer", "id_Long", "id_Double", "id_Float", "id_BigDecimal", "id_Short", "id_Byte"}
)

_COLUMNA = re.compile(
    r"input_row\.([A-Za-z_][A-Za-z0-9_]*)(?![A-Za-z0-9_$])", re.ASCII
)
_INPUT_ROW_PREFIX = re.compile(r"(?<![A-Za-z0-9_$])input_row\.", re.ASCII)
# Comparación de orden entre una columna y un literal numérico, tal como la escribe el traductor:
# `(row1.saldo < 500)`. Es la forma que se puede hacer segura sin adivinar nada.
_ORDEN_LITERAL = re.compile(r"\(([A-Za-z_][\w.]*)\s*(<=|>=|<|>)\s*(-?\d+(?:\.\d+)?)\)")
_OPERADOR_ORDEN = re.compile(r"<=|>=|<|>")
# Las comparaciones que el traductor ya escribe con su guarda de faltante (`x != null && ...` para
# `>` y `>=`, `x == null || ...` para `<` y `<=`): no hay que envolverlas, solo comprobar que el
# tipo de la columna sea el que la forma supone.
_NUMERO_GUARDADO = re.compile(
    r"\(\(Number\)\s*([A-Za-z_][\w.]*)\)\.doubleValue\(\)\s*(?:<=|>=|<|>)\s*-?\d+(?:\.\d+)?"
)
_TEXTO_GUARDADO = re.compile(
    r"\(\(Comparable\)\s*([A-Za-z_][\w.]*)\)\.compareTo\(\"[^\"]*\"\)\s*(?:<=|>=|<|>)\s*0"
)
_ORDEN_COMPARABLE = re.compile(
    r"\(\(Comparable\)\s*([A-Za-z_][\w.]*)\)\.compareTo\(([A-Za-z_][\w.]*)\)\s*(<=|>=|<|>)\s*0"
)


def resolver_filas(java: str, filas: dict[str, set[str]]) -> tuple[str | None, str | None]:
    """Cambia `input_row.col` por `rowN.col` según la única entrada que tiene esa columna.

    Devuelve `(expresión, None)` o `(None, motivo)`: una columna que no está en ninguna entrada, o
    que está en más de una, no se resuelve a ciegas.
    """
    if not is_safe_java_expression(java):
        return None, "expresión Java con sintaxis no permitida"
    literales = _rangos_literales(java)
    if literales is None:
        return None, "expresión Java con literal de cadena no válido"
    codigo = _codigo_sin_literales(java, literales)
    if _tiene_separador(codigo):
        return None, "expresión Java con separador de sentencias no permitido"
    referencias = list(_COLUMNA.finditer(codigo))
    invalidas = any(
        (siguiente := codigo[referencia.end() : referencia.end() + 1])
        and (siguiente.isalnum() or siguiente in "_$")
        for referencia in referencias
    )
    if invalidas or len(referencias) != len(list(_INPUT_ROW_PREFIX.finditer(codigo))):
        return None, "expresión Java con referencia de fila incompleta o no portable"
    usadas = [match.group(1) for match in referencias]
    if not usadas:
        return java, None
    if any(
        not is_java_identifier(fila)
        or any(not is_java_identifier(nombre) for nombre in nombres)
        for fila, nombres in filas.items()
    ):
        return None, "esquema de entrada con identificadores Java no portables"
    destino: dict[str, tuple[str, str]] = {}
    for columna in dict.fromkeys(usadas):
        # SAS no distingue mayúsculas en los nombres de columna: `CNAME` y `cname` son la misma.
        candidatas = [
            (fila, propio)
            for fila, nombres in filas.items()
            for propio in nombres
            if propio.lower() == columna.lower()
        ]
        if not candidatas:
            return None, f"la columna '{columna}' no está en ninguna entrada del mapa"
        if len(candidatas) > 1:
            return None, (
                f"la columna '{columna}' está en varias entradas "
                f"({', '.join(sorted(fila for fila, _ in candidatas))}); el SAS no dice de cuál"
            )
        destino[columna] = candidatas[0]
    return _reemplazar_columnas(java, literales, destino), None


def _rangos_literales(java: str) -> list[tuple[int, int]] | None:
    """Encuentra cadenas Java cerradas; devuelve None ante comillas o saltos sin cerrar."""
    rangos: list[tuple[int, int]] = []
    indice = 0
    while indice < len(java):
        if java[indice] != '"':
            indice += 1
            continue
        inicio = indice
        indice += 1
        while indice < len(java):
            if java[indice] in "\r\n":
                return None
            if java[indice] == "\\":
                indice += 2
                continue
            if java[indice] == '"':
                indice += 1
                rangos.append((inicio, indice))
                break
            indice += 1
        else:
            return None
    return rangos


def _codigo_sin_literales(java: str, literales: list[tuple[int, int]]) -> str:
    """Sustituye cadenas por espacios para revisar solo los tokens que son código."""
    codigo = list(java)
    for inicio, fin in literales:
        codigo[inicio:fin] = " " * (fin - inicio)
    return "".join(codigo)


def _tiene_separador(codigo: str) -> bool:
    return any(caracter in codigo for caracter in ";{}\r\n") or any(
        marcador in codigo for marcador in ("//", "/*", "*/")
    )


def _reemplazar_columnas(
    java: str,
    literales: list[tuple[int, int]],
    destino: dict[str, tuple[str, str]],
) -> str:
    partes: list[str] = []
    inicio = 0

    def reemplazo(match: re.Match[str]) -> str:
        return ".".join(destino[match.group(1)])

    for desde, hasta in literales:
        partes.append(_COLUMNA.sub(reemplazo, java[inicio:desde]))
        partes.append(java[desde:hasta])
        inicio = hasta
    partes.append(_COLUMNA.sub(reemplazo, java[inicio:]))
    return "".join(partes)


def _segura(columna: str, operador: str, literal: str, tipos: dict[str, str]) -> str:
    """Comparación de orden con el faltante tratado como en SAS.

    `<` y `<=` son verdaderos con faltante (es menor que cualquier número); `>` y `>=` son falsos.
    Sobre una columna de texto se comprueba primero que el texto sea numérico, como hace el `input`
    del SAS: lo que no lo es, es faltante.
    """
    tipo = tipos.get(columna)
    if tipo in NUMERICAS:
        guarda = f"{columna} == null" if operador in ("<", "<=") else f"{columna} != null"
        union = "||" if operador in ("<", "<=") else "&&"
        return f"({guarda} {union} {columna} {operador} {literal})"
    fila, _, nombre = columna.rpartition(".")
    sin_numero = faltante(nombre, fila)
    valor = f"java.lang.Double.parseDouble({columna})"
    if operador in ("<", "<="):
        return f"({sin_numero} || {valor} {operador} {literal})"
    return f"(!{sin_numero} && {valor} {operador} {literal})"


def cubrir_faltante(java: str, tipos: dict[str, str]) -> tuple[str | None, str | None]:
    """Hace seguras las comparaciones de orden de una expresión Java ya traducida.

    Cubre comparaciones de columna numérica contra literal y entre columnas numéricas tipadas.
    Si queda alguna otra comparación de orden, no se puede demostrar su semántica con faltantes y
    se devuelve el motivo.
    """
    comparaciones_seguras: list[str] = []

    def comparar_columnas(encontrada: re.Match[str]) -> str:
        izquierda, derecha, operador = encontrada.groups()
        if tipos.get(izquierda) not in NUMERICAS or tipos.get(derecha) not in NUMERICAS:
            return encontrada.group(0)
        comparaciones_seguras.append(f"({izquierda} {operador} {derecha})")
        return f"({izquierda} {operador} {derecha})"

    java = _ORDEN_COMPARABLE.sub(comparar_columnas, java)
    partes: list[str] = []
    ultimo = 0
    for encontrada in _ORDEN_LITERAL.finditer(java):
        partes.append(java[ultimo : encontrada.start()])
        columna, operador, literal = encontrada.groups()
        partes.append(_segura(columna, operador, literal, tipos))
        ultimo = encontrada.end()
    partes.append(java[ultimo:])
    # Lo que quedó fuera de las comparaciones cubiertas: si tiene un orden, no está demostrado.
    resto = _ORDEN_LITERAL.sub(" ", java)
    for patron, admitidos, descripcion in (
        (_NUMERO_GUARDADO, NUMERICAS, "numérica"),
        (_TEXTO_GUARDADO, {"id_String"}, "de texto"),
    ):
        for encontrada in patron.finditer(resto):
            if tipos.get(encontrada.group(1)) not in admitidos:
                return None, (
                    f"la comparación de orden de '{encontrada.group(1)}' supone una columna "
                    f"{descripcion} y el tipo no lo demuestra"
                )
        resto = patron.sub(" ", resto)
    for comparacion in comparaciones_seguras:
        resto = resto.replace(comparacion, " ")
    sobrante = _OPERADOR_ORDEN.search(resto)
    if sobrante is not None:
        inicio = max(0, sobrante.start() - 40)
        return None, (
            "comparación de orden sin semántica de faltante demostrada: "
            f"{' '.join(resto[inicio:][:80].split())}"
        )
    return "".join(partes), None


def expresion(
    sas: str, filas: dict[str, set[str]], tipos: dict[str, str]
) -> tuple[str | None, str | None]:
    """Java de una expresión o condición del SAS, con la fila resuelta y el faltante cubierto."""
    traduccion = translate(sas)
    if traduccion.talend is None:
        motivo = "; ".join(traduccion.warnings) or "el traductor no la reconoce"
        return None, motivo
    resuelta, motivo = resolver_filas(traduccion.talend, filas)
    if resuelta is None:
        return None, motivo
    return cubrir_faltante(resuelta, tipos)


__all__ = ["NUMERICAS", "cubrir_faltante", "expresion", "resolver_filas"]
