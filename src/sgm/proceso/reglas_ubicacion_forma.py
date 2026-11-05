"""R1-05: lectura de la forma de la regla de ubicación del caso v03.

Reconoce cada pieza del programa por su forma: los `LEFT JOIN` contra los lookups, las cinco
alternativas del `WHERE`, las ramas del `CASE` de INCONSISTENCIA, el `NOT IN` de los válidos y la
proyección de cada tabla. Si una pieza no tiene esa forma, falla con `ValueError`. Lo consume
`reglas_ubicacion.py`, que añade los Excel y comprueba que todos los productos declaran lo mismo.
"""

from __future__ import annotations

import re

from sgm.proceso.reglas_cuenta_real import proyeccion

RECHAZO = "INCONS_UBICACION_"
VALIDA = "UBIC_VALIDA_"
ORIGEN = "SABANA_UBIC_"
PAIS_IMPORT = "IMPORT_CODIGOS_PAIS"
DANE_FORMATO = "FORMATO_CODIGO_DANE"
COLUMNAS_BASE = (
    "LLAVE_NOMBRE", "RELACION", "TIPO_DOC", "NRO_DOC", "PAIS", "CODIGO_UBICACION", "DIRECCION",
)  # fmt: skip
INCONSISTENCIA = "INCONSISTENCIA"
_JOIN = re.compile(
    r"(?is)LEFT\s+JOIN\s+WORK\.(?P<tabla>\w+)\s+(?P<alias>\w+)\s+ON\s*\(\s*"
    r"(?P<a>\w+)\.(?P<ca>\w+)\s*=\s*(?P<b>\w+)\.(?P<cb>\w+)\s*\)"
)
_CAMPO = re.compile(r"(?i)^\s*(?P<alias>\w+)\.(?P<col>\w+)\s*$")
_WHEN = re.compile(r"(?is)\bWHEN\s+(?P<cond>.*?)\s+THEN\s+'(?P<motivo>[^']*)'")
_ELSE = re.compile(r"(?is)\bELSE\s+'(?P<motivo>[^']*)'\s*$")
_NOT_IN = re.compile(
    r"(?is)\bWHERE\s+(?P<alias>\w+)\.(?P<campo>\w+)\s+NOT\s+IN\s*\(\s*SELECT\s+\w+\.(?P<scol>\w+)"
    r"\s+FROM\s+WORK\.(?P<tabla>\w+)\s+\w+\s*\)"
)

# Cada alternativa del WHERE y de los WHEN del CASE, por su forma. Los alias se comprueban aparte.
_ATOMOS = {
    "pais": re.compile(r"(?i)(?P<alias>\w+)\.Codigo_Pais IS MISSING"),
    "dane": re.compile(
        r"(?i)(?P<t1>\w+)\.PAIS = '(?P<lit>[^']*)' AND (?P<alias>\w+)\.CODIGO_DANE IS MISSING"
    ),
    "extranjera": re.compile(
        r"(?i)(?P<t1>\w+)\.PAIS <> '(?P<lit>[^']*)' AND "
        r"(?P<t1b>\w+)\.CODIGO_UBICACION IS NOT MISSING"
    ),
    "longitud": re.compile(r"(?i)LENGTH\((?P<t1>\w+)\.DIRECCION\) < (?P<n>\d+)"),
    "fragmento": re.compile(
        r"(?i)UPPER\((?P<t1>\w+)\.DIRECCION\) CONTAINS UPPER\('(?P<frag>[^']*)'\)"
    ),
}
_ORDEN_CASE = ("pais", "dane", "extranjera")
_TODAS = ("pais", "dane", "extranjera", "longitud", "fragmento")

def _atomo(pieza: str) -> tuple[str, re.Match[str]]:
    """Clase de la alternativa `pieza`; falla si no es ninguna de las cinco del caso."""
    normal = " ".join(pieza.split())
    if normal.startswith("(") and normal.endswith(")"):
        normal = normal[1:-1].strip()
    for clase, patron in _ATOMOS.items():
        coincide = patron.fullmatch(normal)
        if coincide:
            return clase, coincide
    raise ValueError(f"Alternativa de ubicación no reconocida: {normal!r}")


def _alias_ok(clase: str, m: re.Match[str], origen: str, joins: dict) -> None:
    """Cada alternativa usa el alias de la sábana y el de su lookup, y ningún otro."""
    t1 = origen.upper()
    if clase == "pais" and m.group("alias").upper() != joins["pais"][0].upper():
        raise ValueError("La alternativa de país no usa el alias del LEFT JOIN de país")
    if clase in ("dane", "extranjera", "longitud", "fragmento") and m.group("t1").upper() != t1:
        raise ValueError(f"La alternativa {clase} no usa el alias {origen} de la sábana")
    if clase == "dane" and m.group("alias").upper() != joins["dane"][0].upper():
        raise ValueError("La alternativa de DANE no usa el alias del LEFT JOIN de DANE")
    if clase == "extranjera" and m.group("t1b").upper() != t1:
        raise ValueError("La alternativa de extranjera no usa el alias de la sábana")


def _joins(cuerpo: str, origen: str) -> dict[str, tuple[str, str]]:
    """Los dos `LEFT JOIN` del rechazo: alias de cada lookup y su columna en el Excel."""
    encontrados: dict[str, tuple[str, str]] = {}
    for join in _JOIN.finditer(cuerpo):
        if join.group("a").upper() != origen.upper():
            raise ValueError(f"El LEFT JOIN no parte de la sábana {origen}")
        tabla = join.group("tabla").upper()
        if tabla == PAIS_IMPORT and join.group("ca").upper() == "PAIS":
            if join.group("cb").upper() != "CODIGO_PAIS":
                raise ValueError("El LEFT JOIN de país no cruza Codigo_Pais")
            clave = "pais"
        elif tabla == DANE_FORMATO and join.group("ca").upper() == "CODIGO_UBICACION":
            if join.group("cb").upper() != "CODIGO_DANE":
                raise ValueError("El LEFT JOIN de DANE no cruza CODIGO_DANE")
            clave = "dane"
        else:
            raise ValueError(f"LEFT JOIN no reconocido contra {join.group('tabla')}")
        if clave in encontrados:
            raise ValueError(f"El SAS une dos veces el lookup de {clave}")
        encontrados[clave] = (join.group("alias"), join.group("cb"))
    if set(encontrados) != {"pais", "dane"}:
        raise ValueError("El rechazo debe unir PAIS y CODIGO_UBICACION con sus dos lookups")
    return encontrados


def _columnas_select(cuerpo: str, origen: str) -> tuple[str, ...]:
    """Columnas base del `SELECT` del rechazo, antes del `CASE`: deben ser las siete de la regla."""
    sel = re.search(r"(?is)\bSELECT\b(?P<sel>.*?)\bCASE\b", cuerpo)
    if sel is None:
        raise ValueError("El rechazo no tiene el CASE de INCONSISTENCIA")
    columnas: list[str] = []
    for parte in sel.group("sel").split(","):
        if not parte.strip():
            continue
        campo = _CAMPO.fullmatch(parte)
        if campo is None or campo.group("alias").upper() != origen.upper():
            raise ValueError(f"Columna de rechazo no reconocida: {parte.strip()!r}")
        columnas.append(campo.group("col").upper())
    if tuple(columnas) != COLUMNAS_BASE:
        raise ValueError(f"El rechazo proyecta {columnas}, se esperaba {list(COLUMNAS_BASE)}")
    return COLUMNAS_BASE


def _where(cuerpo: str, origen: str, joins: dict) -> dict[str, re.Match[str]]:
    """Las cinco alternativas del `WHERE`, cada una una vez, con sus alias comprobados."""
    partes = re.split(r"(?i)\bWHERE\b", cuerpo, maxsplit=1)
    if len(partes) != 2:
        raise ValueError("El rechazo no tiene WHERE: sería la sábana entera")
    piezas = re.split(r"(?i)\bOR\b", partes[1])
    atomos: dict[str, re.Match[str]] = {}
    for pieza in piezas:
        clase, m = _atomo(pieza)
        if clase in atomos:
            raise ValueError(f"La alternativa {clase} aparece dos veces en el WHERE")
        _alias_ok(clase, m, origen, joins)
        atomos[clase] = m
    if set(atomos) != set(_TODAS) or len(piezas) != len(_TODAS):
        raise ValueError(f"El WHERE debe tener {list(_TODAS)}, tiene {sorted(atomos)}")
    return atomos


def _case(cuerpo: str, origen: str, joins: dict) -> tuple[str, ...]:
    """Motivos del `CASE` en orden: país, DANE, extranjera y el `ELSE` de dirección."""
    caso = re.search(r"(?is)\bCASE\b(?P<case>.*?)\bEND\s+AS\s+INCONSISTENCIA", cuerpo)
    if caso is None:
        raise ValueError("El rechazo no termina en `END AS INCONSISTENCIA`")
    texto = caso.group("case")
    whens = list(_WHEN.finditer(texto))
    if len(whens) != len(_ORDEN_CASE):
        raise ValueError(f"El CASE tiene {len(whens)} ramas, se esperaban {len(_ORDEN_CASE)}")
    motivos: list[str] = []
    for esperada, when in zip(_ORDEN_CASE, whens, strict=True):
        clase, m = _atomo(when.group("cond"))
        if clase != esperada:
            raise ValueError(f"La rama {len(motivos) + 1} del CASE es {clase}, no {esperada}")
        _alias_ok(clase, m, origen, joins)
        motivos.append(when.group("motivo"))
    otro = _ELSE.search(texto)
    if otro is None:
        raise ValueError("El CASE no tiene ELSE con el motivo de dirección")
    return (*motivos, otro.group("motivo"))


def _llave_not_in(cuerpo: str, producto: str) -> str:
    """Llave del `NOT IN` de los válidos: misma columna en las dos puntas y la tabla de rechazo."""
    m = _NOT_IN.search(cuerpo)
    if m is None or m.group("tabla").upper() != f"{RECHAZO}{producto}":
        raise ValueError(f"{VALIDA}{producto} debe excluir las llaves de {RECHAZO}{producto}")
    if m.group("campo").upper() != m.group("scol").upper():
        raise ValueError(f"El NOT IN de {VALIDA}{producto} no cruza la misma columna")
    return m.group("campo").upper()


def forma_producto(texto: str, tablas: dict[str, str], producto: str) -> tuple:
    """Lo que el SAS dice de un producto, en una tupla que se compara con la de los demás."""
    cuerpo = tablas[f"{RECHAZO}{producto}"]
    origen = re.search(rf"(?i)\bFROM\s+WORK\.{ORIGEN}{producto}\s+(\w+)", cuerpo)
    if origen is None:
        raise ValueError(f"{RECHAZO}{producto} no lee de WORK.{ORIGEN}{producto}")
    alias = origen.group(1)
    joins = _joins(cuerpo, alias)
    atomos = _where(cuerpo, alias, joins)
    motivos = _case(cuerpo, alias, joins)
    columnas = _columnas_select(cuerpo, alias)
    if f"{VALIDA}{producto}" not in tablas:
        raise ValueError(f"El SAS no declara {VALIDA}{producto}")
    llave = _llave_not_in(tablas[f"{VALIDA}{producto}"], producto)
    valida = proyeccion(texto, f"{VALIDA}{producto}")
    if set(valida) != set(COLUMNAS_BASE):
        raise ValueError(f"{VALIDA}{producto} proyecta {valida}, se esperaban las base")
    literal = atomos["dane"].group("lit")
    if atomos["extranjera"].group("lit") != literal:
        raise ValueError("El país de DANE y el de extranjera no son el mismo literal")
    return (
        literal,
        int(atomos["longitud"].group("n")),
        atomos["fragmento"].group("frag"),
        motivos,
        joins["pais"][1],
        joins["dane"][1],
        (*columnas, INCONSISTENCIA),
        COLUMNAS_BASE,
        llave,
    )


__all__ = [
    "COLUMNAS_BASE",
    "DANE_FORMATO",
    "INCONSISTENCIA",
    "ORIGEN",
    "PAIS_IMPORT",
    "RECHAZO",
    "VALIDA",
    "forma_producto",
]
