"""R1-07: la separación de saldos negativos que el SAS demuestra, leída del programa.

La fuente es el caso `v05_codex_saldos`, no `client_large.sas`. Su macro `saldo_negativo` escribe
`INCONS_SALDO_NEG_<P>` con `WHERE <alias>.FIN_SALDO_CTA < 0` sobre la sábana entera, y el paso
`DATA` que sigue le pone `INCONSISTENCIA='SALDO NEGATIVO'`. `SABANA_VALIDA_<P>` excluye, con dos
`NOT IN`, las llaves de `INCONS_CODEX_INVALIDO_<P>` y las de `INCONS_SALDO_NEG_<P>`.

El programa real de cliente no tiene esa tabla. Su `IFN(FIN_SALDO_CTA<0, 0, FIN_SALDO_CTA)` pone
los negativos en cero en `CONSOLIDADO_SIN_NEGATIVOS`, que alimenta sumas y no un rechazo. Eso no
se traduce a rechazo: `negativos_a_cero` lo detecta y `cli_talend` lo publica como pendiente.

Las macros se expanden solo por sustitución de texto, que es lo que hace el caso: un
`%macro nombre(param); ... %mend;` y su llamada `%nombre(VALOR);` cambian `&param`, con su punto
delimitador, por `VALOR`. Cualquier otra macro se deja tal cual.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from sgm.proceso.reglas_cuenta_real import proyeccion

# Prefijos de las tablas que la regla necesita, tal como las nombra el caso.
NEG = "INCONS_SALDO_NEG_"
VALIDA = "SABANA_VALIDA_"
CODEX = "INCONS_CODEX_INVALIDO_"
# Nombres base de los CSV que escribe el Job (sin producto ni sufijo).
TABLAS = {"neg": "INCONS_SALDO_NEG", "valida": "SABANA_VALIDA"}
INCONSISTENCIA = "INCONSISTENCIA"

PENDIENTE_CERO = (
    "R1-07: el SAS real pone en cero los FIN_SALDO_CTA negativos (IFN en "
    "CONSOLIDADO_SIN_NEGATIVOS) y no los rechaza; esa regla no se emite"
)

_MACRO_DEF = re.compile(
    r"(?is)%macro\s+(?P<nombre>\w+)\s*\(\s*(?P<param>\w+)\s*\)\s*;(?P<cuerpo>.*?)%mend\b[^;]*;"
)
_MACRO_CALL = re.compile(r"(?i)%(?P<nombre>\w+)\s*\(\s*(?P<valor>\w+)\s*\)\s*;")
_CREAR = re.compile(r"(?is)\bCREATE\s+TABLE\s+(?:WORK\.)?(?P<tabla>\w+)\s+AS\s+(?P<cuerpo>.*?);")
_CONDICION = re.compile(r"(?is)^\s*\w+\.(?P<col>\w+)\s*<\s*(?P<umbral>-?\d+)\s*$")
_NOT_IN = re.compile(
    r"(?is)(?P<col>\w+)\.(?P<campo>\w+)\s+NOT\s+IN\s*\(\s*SELECT\s+\w+\.(?P<scol>\w+)"
    r"\s+FROM\s+(?:WORK\.)?(?P<tabla>\w+)"
)
_WHERE = re.compile(r"(?i)\bWHERE\b")
_CLAMP = re.compile(r"(?i)\bIFN\s*\(\s*FIN_SALDO_CTA\s*<\s*0\s*,\s*0\s*,")


@dataclass(frozen=True)
class ReglaSaldo:
    """Lo que el caso demuestra para separar los saldos negativos, igual en todos los productos."""

    columna: str
    umbral: int
    motivo: str
    proyeccion_neg: tuple[str, ...]
    proyeccion_valida: tuple[str, ...]
    llave: str
    productos: tuple[str, ...]
    tablas: dict[str, str]


def negativos_a_cero(texto: str) -> bool:
    """Si el programa pone los saldos negativos en cero en vez de rechazarlos."""
    return _CLAMP.search(texto) is not None


def expandir_macros(texto: str) -> str:
    """Sustituye cada llamada `%nombre(VALOR);` por el cuerpo de su macro, con `&param` cambiado.

    Las definiciones se quitan del resultado. Una llamada a una macro sin definición se conserva.
    """
    definiciones = {
        m.group("nombre").casefold(): (m.group("param"), m.group("cuerpo"))
        for m in _MACRO_DEF.finditer(texto)
    }
    sin_definiciones = _MACRO_DEF.sub("", texto)

    def expandir(llamada: re.Match[str]) -> str:
        definicion = definiciones.get(llamada.group("nombre").casefold())
        if definicion is None:
            return llamada.group(0)
        param, cuerpo = definicion
        return re.sub(
            rf"&{re.escape(param)}\.?", llamada.group("valor"), cuerpo, flags=re.IGNORECASE
        )

    return _MACRO_CALL.sub(expandir, sin_definiciones)


def _tablas(texto: str) -> dict[str, str]:
    """Cuerpo de cada `CREATE TABLE` por nombre en mayúsculas.

    Un nombre repetido solo es error si es una de las tablas de la regla: el resto (tablas de
    trabajo que el SAS recrea) no se usa, así que no impide leer la regla.
    """
    tablas: dict[str, str] = {}
    for crear in _CREAR.finditer(texto):
        nombre = crear.group("tabla").upper()
        if nombre in tablas and nombre.startswith((NEG, VALIDA, CODEX)):
            raise ValueError(f"El SAS crea dos veces la tabla {nombre}")
        tablas[nombre] = crear.group("cuerpo")
    return tablas


def _productos(tablas: dict[str, str]) -> tuple[str, ...]:
    neg = {n[len(NEG) :] for n in tablas if n.startswith(NEG)}
    valida = {n[len(VALIDA) :] for n in tablas if n.startswith(VALIDA)}
    if not neg:
        raise ValueError(f"El SAS no declara ninguna tabla {NEG}<producto>")
    if neg != valida:
        raise ValueError(f"Los productos de {NEG}* y {VALIDA}* no coinciden: {neg} / {valida}")
    return tuple(sorted(neg))


def _condicion(cuerpo: str, producto: str) -> tuple[str, int]:
    """El `WHERE` de `INCONS_SALDO_NEG_<P>` debe ser una sola comparación `col < n`."""
    partes = _WHERE.split(cuerpo, maxsplit=1)
    if len(partes) != 2:
        raise ValueError(f"{NEG}{producto} no tiene WHERE: el rechazo sería la sábana entera")
    condicion = _CONDICION.fullmatch(partes[1])
    if condicion is None:
        raise ValueError(f"El WHERE de {NEG}{producto} no es `alias.col < n`: {partes[1]!r}")
    return condicion.group("col").upper(), int(condicion.group("umbral"))


def _motivo(texto: str, producto: str) -> str:
    """El `INCONSISTENCIA='...'` que el paso `DATA` pone justo después de leer la tabla."""
    patron = re.compile(
        rf"(?is)\bset\s+(?:WORK\.)?{NEG}{re.escape(producto)}\s*;\s*"
        rf"INCONSISTENCIA\s*=\s*'(?P<motivo>[^']*)'"
    )
    encontrado = patron.search(texto)
    return encontrado.group("motivo") if encontrado else ""


def _llave(cuerpo: str, producto: str) -> str:
    """La llave de los dos `NOT IN` de la sábana válida: las dos tablas y la misma columna."""
    cruces = list(_NOT_IN.finditer(cuerpo))
    tablas = {c.group("tabla").upper() for c in cruces}
    esperadas = {f"{CODEX}{producto}", f"{NEG}{producto}"}
    if len(cruces) != 2 or tablas != esperadas:
        raise ValueError(f"{VALIDA}{producto} debe excluir {sorted(esperadas)} con dos NOT IN")
    llaves = {c.group("campo").upper() for c in cruces} | {
        c.group("scol").upper() for c in cruces
    }
    if len(llaves) != 1:
        raise ValueError(f"Los NOT IN de {VALIDA}{producto} no cruzan la misma llave: {llaves}")
    return llaves.pop()


def _revisar(valor: tuple[str, ...], nombre: str, columna: str) -> tuple[str, ...]:
    if columna not in valor:
        raise ValueError(f"{nombre} no proyecta la columna {columna}: {valor}")
    return valor


def reglas_saldo(texto: str) -> tuple[ReglaSaldo, list[str]]:
    """La regla de saldo negativo del programa y los pendientes que quedan fuera.

    Falla con `ValueError` si el programa no declara la pareja completa para cada producto. Un
    programa sin esa forma no produce una regla a medias.
    """
    expandido = expandir_macros(texto)
    tablas = _tablas(expandido)
    productos = _productos(tablas)
    reglas: list[ReglaSaldo] = []
    for producto in productos:
        columna, umbral = _condicion(tablas[f"{NEG}{producto}"], producto)
        motivo = _motivo(expandido, producto)
        if not motivo:
            raise ValueError(f"{NEG}{producto} no lleva INCONSISTENCIA='...' en su paso DATA")
        llave = _llave(tablas[f"{VALIDA}{producto}"], producto)
        proy_neg = proyeccion(expandido, f"{NEG}{producto}")
        proy_valida = proyeccion(expandido, f"{VALIDA}{producto}")
        _revisar(proy_neg, f"{NEG}{producto}", columna)
        _revisar(proy_valida, f"{VALIDA}{producto}", columna)
        _revisar(proy_valida, f"{VALIDA}{producto}", llave)
        reglas.append(
            ReglaSaldo(
                columna, umbral, motivo, proy_neg, proy_valida, llave, productos, dict(TABLAS)
            )
        )
    if any(r != reglas[0] for r in reglas):
        raise ValueError(f"Los productos declaran reglas de saldo distintas: {productos}")
    pendientes = [
        f"R1-07: el cruce de {VALIDA}* con la llave {reglas[0].llave} es un filtro por fila en el "
        "Job; la equivalencia del NOT IN depende de que la llave sea única por fila",
    ]
    return reglas[0], pendientes


__all__ = [
    "CODEX",
    "INCONSISTENCIA",
    "NEG",
    "PENDIENTE_CERO",
    "ReglaSaldo",
    "TABLAS",
    "VALIDA",
    "expandir_macros",
    "negativos_a_cero",
    "reglas_saldo",
]
