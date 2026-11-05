"""Filtros de fila de `NRO_DOC` vacío o cero, leídos del `WHERE` del SAS (R1-04 / T13).

El programa escribe la misma terna de consultas por producto:

- `WHERE ( ( col = 0 ) OR col IS MISSING ) AND ( rel <> 9902 )` -> titulares y cotitulares;
- la misma con `rel = 9902` -> firmas autorizadas (FA);
- `WHERE col IS NOT MISSING AND ( col <> 0 )` -> documentos no vacíos ni cero.

Columnas, valores y tablas de destino salen del SAS: no se declaran en YAML. Solo se reconocen
sentencias `CREATE TABLE ... AS SELECT` con `WHERE`. La regla "Campos vacios" (una larga cadena de
`IS MISSING` sobre 19 columnas) no tiene la forma `= 0 OR ... IS MISSING` y **no** entra aquí:
queda para la parte 2 de R1-04, con su propio caso del corpus.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, replace

from sgm.proceso.columnas_fuente import _sentencias as _partir

_CREATE = re.compile(
    r"(?is)\bCREATE\s+TABLE\s+(?:WORK\.)?(?P<destino>[\w$&]+)\s+AS\s+(?P<cuerpo>SELECT\b.*)$"
)
_WHERE = re.compile(r"(?i)\bWHERE\b")
_SELECT = re.compile(r"(?is)^\s*SELECT\s+(?P<columnas>.*?)\s+FROM\b")
_CAMPO = re.compile(r"(?P<cal>[\w$&]+)\.+(?P<col>[\w$]+)")
# Las tres tablas de la separación, con el nombre que les da el SAS real y `v02`. El sufijo de
# producto (`_CTE`, `_AHO`, `_&sufijo`) lo pone cada bloque; el Job emitido usa `context.sufijo`.
TABLAS = {
    "tit_cot": "NRO_DOC_VACIO_0_TIT_COT",
    "fa": "INCONS_NRO_DOC_VACIO_0_FA",
    "valido": "NRO_DOC_NO_VACIO_NI_0",
}
# En el programa real el alias es `SABANA_NO_DUPLICADOS_AHO.NRO_DOC`; en el corpus v02 es
# `SABANA_&sufijo..NRO_DOC` (el punto extra es el separador de la macro). `\.+` cubre los dos.
_REF = r"(?P<cal>[\w$&]+)\.+(?P<col>[\w$]+)"
_REF2 = r"(?P=cal)\.+(?P=col)"
# `( ALIAS.NRO_DOC = 0 ) OR ALIAS.NRO_DOC IS MISSING`, con o sin paréntesis alrededor del `=`.
_VACIO_CERO = re.compile(
    rf"(?is){_REF}\s*=\s*0\s*\)\s*OR\s+{_REF2}\s+IS\s+MISSING"
)
_VALIDO = re.compile(
    rf"(?is){_REF}\s+IS\s+NOT\s+MISSING\s+AND\s*\(\s*{_REF2}\s*<>\s*0\s*\)"
)
_RELACION = re.compile(
    r"(?is)(?P<cal>[\w$&]+)\.+(?P<col>[\w$]+)\s*(?P<op><>|!=|=)\s*(?P<valor>\d+)\s*\)"
)
MODOS = ("tit_cot", "fa", "valido")


@dataclass(frozen=True)
class ReglaFila:
    """Un `WHERE` que separa un flujo de filas, con la línea del SAS que lo demuestra."""

    destino: str  # tabla que crea la consulta, sin `WORK.`
    columna: str  # NRO_DOC
    modo: str  # tit_cot | fa | valido
    linea: int
    columna_relacion: str = ""  # RELACION; vacío en `valido`
    valor_relacion: str = ""  # 9902; vacío en `valido`
    operador_relacion: str = ""  # <> en tit_cot, = en fa; vacío en `valido`
    columnas: tuple[str, ...] = ()  # proyección del SELECT; vacía si no es `alias.columna`
    tabla: str = ""  # base de la tabla de separación; vacía en las revalidaciones

    @property
    def vacio_o_cero(self) -> bool:
        return self.modo != "valido"

    @property
    def forma(self) -> tuple:
        """Lo que define al flujo, sin la tabla ni la línea: todos los productos deben coincidir."""
        return (
            self.modo,
            self.columna,
            self.columna_relacion,
            self.valor_relacion,
            self.operador_relacion,
            self.columnas,
        )


def _proyeccion(cuerpo: str) -> tuple[str, ...]:
    """Columnas del `SELECT`, leídas del SAS; vacío si algún elemento no es `alias.columna`.

    El programa real proyecta 19 columnas y `v02` proyecta 6/7. No se completa ni se reordena:
    una proyección que no se pueda leer entera se deja vacía para que el emisor la rechace.
    """
    seleccion = _SELECT.search(cuerpo)
    if seleccion is None:
        return ()
    nombres: list[str] = []
    for parte in seleccion.group("columnas").split(","):
        campo = _CAMPO.fullmatch(parte.strip())
        if campo is None:
            return ()
        nombres.append(campo.group("col"))
    return tuple(nombres)


def _relacion(filtro: str, columna: str) -> re.Match[str] | None:
    """El `rel = 9902` / `rel <> 9902` del `WHERE`, descartando el `col = 0` de la propia regla."""
    for m in _RELACION.finditer(filtro):
        if m.group("valor") != "0" and m.group("col").casefold() != columna.casefold():
            return m
    return None


def reglas_fila(texto: str) -> list[ReglaFila]:
    """Reglas de vacío/cero en el orden en que aparecen en el programa."""
    resultado: list[ReglaFila] = []
    for desplazamiento, sentencia in _partir(texto)[1]:
        crear = _CREATE.search(sentencia)
        if crear is None:
            continue
        donde = _WHERE.search(crear.group("cuerpo"))
        if donde is None:
            continue
        cuerpo = crear.group("cuerpo")
        filtro = cuerpo[donde.end() :]
        linea = texto.count("\n", 0, desplazamiento) + 1
        destino = crear.group("destino")
        columnas = _proyeccion(cuerpo)
        valido = _VALIDO.search(filtro)
        if valido is not None:
            resultado.append(
                ReglaFila(destino, valido.group("col"), "valido", linea, columnas=columnas)
            )
            continue
        vacio = _VACIO_CERO.search(filtro)
        if vacio is None:
            continue
        relacion = _relacion(filtro, vacio.group("col"))
        if relacion is None:
            continue
        operador = relacion.group("op")
        modo = "tit_cot" if operador in ("<>", "!=") else "fa"
        resultado.append(
            ReglaFila(
                destino,
                vacio.group("col"),
                modo,
                linea,
                relacion.group("col"),
                relacion.group("valor"),
                operador,
                columnas,
            )
        )
    return resultado


def flujos_producto(texto: str) -> tuple[list[ReglaFila], list[str]]:
    """La terna canónica que el `job_producto` emite, y las reglas que quedan fuera.

    El SAS real repite la separación por producto (CTE, AHO) y añade revalidaciones posteriores
    (`SABANA_SIN_NRO_DOC_VACIOS_NEQUI`, `FINAL_VALIDAR_NRO_DOC_*`). El Job es uno solo,
    parametrizado por `context.sufijo`, así que se emite **una** terna: se exige que todos los
    bloques de producto declaren exactamente la misma forma (filtro y proyección) y se devuelven
    las reglas excluidas como pendientes, nunca descartadas en silencio.
    """
    grupos: dict[str, list[ReglaFila]] = {modo: [] for modo in MODOS}
    otros: list[ReglaFila] = []
    for regla in reglas_fila(texto):
        modo = next(
            (m for m, prefijo in TABLAS.items() if regla.destino.upper().startswith(prefijo)),
            "",
        )
        if modo and modo == regla.modo:
            grupos[modo].append(regla)
        else:
            otros.append(regla)
    for modo, grupo in grupos.items():
        if not grupo:
            raise ValueError(f"El SAS no declara el flujo '{modo}' de R1-04")
        formas = {r.forma for r in grupo}
        if len(formas) != 1:
            raise ValueError(f"Los productos declaran flujos '{modo}' distintos: {formas}")
        if not grupo[0].columnas:
            raise ValueError(f"El flujo '{modo}' no tiene una proyección legible en el SELECT")
    canonicas = [replace(grupos[modo][0], tabla=TABLAS[modo]) for modo in MODOS]
    pendientes = []
    if otros:
        nombres = ", ".join(f"{r.destino} (línea {r.linea})" for r in otros)
        pendientes.append(f"R1-04: revalidaciones posteriores sin emitir: {nombres}")
    pendientes.append(
        "R1-04 parte 2: la cadena larga de `Campos vacios`, `RECHAZO_NRO_DOC_*` y las tablas "
        "de conteo siguen fuera del Job emitido"
    )
    return canonicas, pendientes


def por_modo(reglas: list[ReglaFila], modo: str) -> list[ReglaFila]:
    """Reglas de un modo; falla si el modo no es uno de los tres conocidos."""
    if modo not in MODOS:
        raise ValueError(f"Modo desconocido: {modo!r}")
    return [r for r in reglas if r.modo == modo]


__all__ = ["MODOS", "TABLAS", "ReglaFila", "flujos_producto", "por_modo", "reglas_fila"]
