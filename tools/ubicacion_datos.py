"""Hito 91 / R1-05: ubicación del `job_producto` contra `v03_pais_dane`, con vectores propios.

El caso trae la sábana (`DETALLE_<P>.csv`, 23 campos) y la ubicación aparte (`UBICACION_<P>.csv`,
4 campos, unida por `LLAVE_NOMBRE`). El Job lee una sola entrada, así que este arnés une los dos
archivos por llave antes de correrlo (`unir`), con el `LEFT JOIN` del SAS: una llave sin ubicación
da `PAIS`, `CODIGO_UBICACION` y `DIRECCION` vacíos. Una llave repetida es error, porque el SAS la
duplicaría y ese caso no se ejercita.

Comparación: por **multiconjunto** de columnas estables (`RELACION`, `PAIS`, `CODIGO_UBICACION`,
`DIRECCION` y, en el rechazo, `INCONSISTENCIA`). `LLAVE_NOMBRE`, `TIPO_DOC` y `NRO_DOC` no entran:
R1-02 deja vacías las dos primeras y quita ceros de la última (hitos 85 y 87).

Vectores propios: 20 filas con la clasificación escrita a mano desde la semántica de SAS, en
`VECTORES`. `clasificar_sas` es un segundo cálculo, en Python, de la misma regla; la prueba
comprueba que coincide con la mano. Ninguno de los dos sale del Job.

Semántica de SAS que aplican los vectores (ver `talend_item/filtros_ubicacion.py`):
* Blancos finales no cuentan: `'900 '` es `'900'`, y `'99002  '` es `'99002'`.
* Un campo solo con blancos es faltante, y el faltante es igual a `''`.
* `LENGTH` no cuenta blancos finales, y un texto en blanco vale 1.
* `CONTAINS` es subcadena literal sobre el texto en mayúsculas (`'SIN  DIR'`, con dos blancos, no
  contiene `'SIN DIR'`).
* Los motivos siguen el orden del `CASE`: país, DANE, extranjera y dirección.

Uso desde `tools/prueba_ubicacion.py`; no se importa desde `src/`.
"""

from __future__ import annotations

import csv
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[1]
CASO = REPO / "tests" / "corpus" / "L8" / "validaciones" / "v03_pais_dane"
ENTRADAS = CASO / "entradas"
PRODUCTOS = ("CTE", "AHO")
SUFIJO_VECTORES = "VECTORES"
COLUMNAS_UBIC = ("PAIS", "CODIGO_UBICACION", "DIRECCION")
ESTABLES_RECHAZO = ("RELACION", "PAIS", "CODIGO_UBICACION", "DIRECCION", "INCONSISTENCIA")
ESTABLES_VALIDA = ("RELACION", "PAIS", "CODIGO_UBICACION", "DIRECCION")
# Lo que escribe el Job emitido, con el sufijo al final.
ARCHIVOS = {"rechazo": "INCONS_UBICACION_{p}.csv", "valida": "UBIC_VALIDA_{p}.csv"}
# Lo que el caso declara, con el producto en el nombre.
ESPERADO = {
    "rechazo": "INCONS_UBICACION_{p}.csv",
    "valida": "UBIC_VALIDA_{p}.csv",
    "sabana": "SABANA_{p}.csv",
}
PAISES_EXCEL = ("900", "902", "903")
DANES_EXCEL = ("99001", "99002", "99003")

# 23 campos de la sábana, en el orden de `esquema_csv`, como en `saldo_datos`.
_BASE = (
    "2026", "10", "FIC", "1001", "S", "1", "5000000001", "LLV00001", "TD01", "00000001",
    "11", "1001", "2001", "3001", "4001", "5001", "6001", "7001", "8001", "9001",
    "10001", "11001", "12001",
)  # fmt: skip

# (llave, país, código DANE, dirección, motivo esperado o "" si es válida). Escritos a mano.
VECTORES = (
    ("VEC01", "777", "", "CALLE VALIDA 1 2 3", "PAIS NO HOMOLOGADO"),
    ("VEC02", "", "", "CALLE VALIDA 1 2 3", "PAIS NO HOMOLOGADO"),
    ("VEC03", "900 ", "99001", "CALLE VALIDA 1 2 3", ""),
    ("VEC04", "900", "99999", "CALLE VALIDA 1 2 3", "DANE NO HOMOLOGADO"),
    ("VEC05", "900", "", "CALLE VALIDA 1 2 3", "DANE NO HOMOLOGADO"),
    ("VEC06", "900", "99002  ", "CALLE VALIDA 1 2 3", ""),
    ("VEC07", "902", "99001", "CALLE VALIDA 1 2 3", "UBICACION EXTRANJERA CON CODIGO"),
    ("VEC08", "903", "", "CALLE VALIDA 1 2 3", ""),
    ("VEC09", "902", "   ", "CALLE VALIDA 1 2 3", ""),
    ("VEC10", "900", "99003", "ABCDEFG", "DIRECCION INVALIDA"),
    ("VEC11", "900", "99003", "ABCDEFGH", ""),
    ("VEC12", "900", "99003", "ABCDEFG   ", "DIRECCION INVALIDA"),
    ("VEC13", "900", "99003", "", "DIRECCION INVALIDA"),
    ("VEC14", "900", "99003", "Sin Dir Nueva 45", "DIRECCION INVALIDA"),
    ("VEC15", "900", "99003", "SIN  DIR 45 NORTE", ""),
    ("VEC16", "777", "99999", "", "PAIS NO HOMOLOGADO"),
    ("VEC17", "900", "", "", "DANE NO HOMOLOGADO"),
    ("VEC18", "902", "99999", "", "UBICACION EXTRANJERA CON CODIGO"),
    ("VEC19", "900", "99001", "sin dir", "DIRECCION INVALIDA"),
    ("VEC20", "903", "", "SIN DIRECCION", "DIRECCION INVALIDA"),
)


def clasificar_sas(pais: str, codigo: str, direccion: str) -> str:
    """Segundo cálculo de la regla en Python, con la semántica de SAS. "" si la fila es válida."""
    p, c, d = pais.rstrip(" "), codigo.rstrip(" "), direccion.rstrip(" ")
    sin_pareja_pais = p not in PAISES_EXCEL
    sin_pareja_dane = p == "900" and c not in DANES_EXCEL
    extranjera = p != "900" and c != ""
    longitud = 1 if d == "" else len(d)
    rechaza = sin_pareja_pais or sin_pareja_dane or extranjera
    rechaza = rechaza or longitud < 8 or "SIN DIR" in d.upper()
    if not rechaza:
        return ""
    if sin_pareja_pais:
        return "PAIS NO HOMOLOGADO"
    if sin_pareja_dane:
        return "DANE NO HOMOLOGADO"
    if extranjera:
        return "UBICACION EXTRANJERA CON CODIGO"
    return "DIRECCION INVALIDA"


def _csv(ruta: Path, delimitador: str = ";") -> list[list[str]]:
    """Filas de un CSV. Las entradas van con `;`; los CSV que escribe el Job y el caso, con `,`."""
    with ruta.open(encoding="utf-8", newline="") as archivo:
        return list(csv.reader(archivo, delimiter=delimitador))


def unir(detalle: Path, ubicacion: Path, destino: Path) -> tuple[Path, int]:
    """Sábana con PAIS, CODIGO_UBICACION y DIRECCION: `LEFT JOIN` por la llave (campo 8).

    Devuelve la ruta y el número de llaves de la sábana sin ubicación. Una llave de ubicación
    repetida falla: el SAS duplicaría filas y no es el caso que se prueba.
    """
    ubic: dict[str, list[str]] = {}
    for fila in _csv(ubicacion):
        if not fila:
            continue
        if fila[0] in ubic:
            raise ValueError(f"La llave {fila[0]} aparece dos veces en {ubicacion.name}")
        ubic[fila[0]] = fila[1:4]
    sin_pareja = 0
    destino.parent.mkdir(parents=True, exist_ok=True)
    with destino.open("w", encoding="utf-8", newline="") as archivo:
        escritor = csv.writer(archivo, delimiter=";", lineterminator="\n")
        for fila in _csv(detalle):
            if not fila:
                continue
            extra = ubic.get(fila[7])
            if extra is None:
                sin_pareja += 1
                extra = ["", "", ""]
            escritor.writerow([*fila, *extra])
    return destino, sin_pareja


def vector_csv(destino: Path) -> Path:
    """CSV de los vectores propios: 23 campos de la sábana y 3 de ubicación, sin cabecera."""
    destino.parent.mkdir(parents=True, exist_ok=True)
    with destino.open("w", encoding="utf-8", newline="") as archivo:
        escritor = csv.writer(archivo, delimiter=";", lineterminator="\n")
        for n, (llave, pais, codigo, direccion, _) in enumerate(VECTORES, start=1):
            fila = list(_BASE)
            fila[3], fila[7], fila[9] = "1001", llave, f"{n:08d}"
            escritor.writerow([*fila, pais, codigo, direccion])
    return destino


def _proyectar(ruta: Path, columnas: tuple[str, ...]) -> list[tuple[str, ...]]:
    """Filas de un CSV con cabecera (separado por `,`), reducidas a `columnas` por nombre."""
    filas = _csv(ruta, ",")
    if not filas:
        raise ValueError(f"CSV vacío: {ruta}")
    cabecera = filas[0]
    faltan = [c for c in columnas if c not in cabecera]
    if faltan:
        raise ValueError(f"{ruta.name} no trae las columnas {faltan}: {cabecera}")
    indices = [cabecera.index(c) for c in columnas]
    return [tuple(fila[i] for i in indices) for fila in filas[1:] if fila]


def esperado(producto: str, clave: str, columnas: tuple[str, ...]) -> list[tuple[str, ...]]:
    return _proyectar(CASO / "esperado" / ESPERADO[clave].format(p=producto), columnas)


def observado(salida: Path, sufijo: str) -> dict[str, list[tuple[str, ...]]]:
    """Los CSV que escribe el Job para un sufijo, proyectados por nombre de columna."""
    return {
        "rechazo": _proyectar(salida / ARCHIVOS["rechazo"].format(p=sufijo), ESTABLES_RECHAZO),
        "valida": _proyectar(salida / ARCHIVOS["valida"].format(p=sufijo), ESTABLES_VALIDA),
    }


def esperado_vectores() -> dict[str, list[tuple[str, ...]]]:
    """Lo que el Job debe escribir para los vectores, según la clasificación a mano."""
    rechazo, valida = [], []
    for _, pais, codigo, direccion, motivo in VECTORES:
        if motivo:
            rechazo.append(("1001", pais, codigo, direccion, motivo))
        else:
            valida.append(("1001", pais, codigo, direccion))
    return {"rechazo": sorted(rechazo), "valida": sorted(valida)}


def anomalias_plantadas() -> dict[str, dict]:
    with (CASO / "caso.yaml").open(encoding="utf-8") as archivo:
        return yaml.safe_load(archivo)["anomalias_plantadas"]


def _multiconjunto(filas: list[tuple[str, ...]]) -> list[tuple[str, ...]]:
    return sorted(filas)


def _cuadra(nombre: str, esp: list, obt: list) -> bool:
    cuadra = _multiconjunto(esp) == _multiconjunto(obt)
    print(
        f"{nombre}: esperadas {len(esp)} filas, obtenidas {len(obt)}; "
        f"{'OK' if cuadra else 'DIFERENCIA'}"
    )
    if not cuadra:
        print(f"  esperado: {_multiconjunto(esp)[:4]}")
        print(f"  obtenido: {_multiconjunto(obt)[:4]}")
    return cuadra


def informe(producto: str, obs: dict[str, list[tuple[str, ...]]]) -> bool:
    """Compara los dos flujos con el esperado del caso y las anomalías plantadas."""
    bueno = _cuadra(
        f"{producto} rechazo",
        esperado(producto, "rechazo", ESTABLES_RECHAZO),
        obs["rechazo"],
    )
    bueno &= _cuadra(
        f"{producto} valida",
        esperado(producto, "valida", ESTABLES_VALIDA),
        obs["valida"],
    )
    plantado = anomalias_plantadas()[producto.casefold()]
    motivos = {
        "pais_no_homologado": "PAIS NO HOMOLOGADO",
        "dane_no_homologado": "DANE NO HOMOLOGADO",
        "ubicacion_extranjera_con_codigo": "UBICACION EXTRANJERA CON CODIGO",
        "direccion_invalida": "DIRECCION INVALIDA",
    }
    conteo = {
        clave: sum(1 for f in obs["rechazo"] if f[-1] == motivo)
        for clave, motivo in motivos.items()
    }
    conteo["validos"] = len(obs["valida"])
    cuadra = conteo == {k: plantado[k] for k in conteo}
    bueno &= cuadra
    print(
        f"{producto} anomalías plantadas {plantado}; obtenidas {conteo}; "
        f"{'OK' if cuadra else 'DIFERENCIA'}"
    )
    return bool(bueno)


def informe_vectores(obs: dict[str, list[tuple[str, ...]]]) -> bool:
    """Compara los vectores con la clasificación escrita a mano."""
    esp = esperado_vectores()
    bueno = _cuadra("Vectores rechazo", esp["rechazo"], obs["rechazo"])
    bueno &= _cuadra("Vectores valida", esp["valida"], obs["valida"])
    return bueno


def invariantes(resultados: dict[str, dict[str, list[tuple[str, ...]]]]) -> bool:
    """La sábana del caso es rechazos más válidos, y los conteos del caso cuadran."""
    uno = True
    for p in PRODUCTOS:
        sabana = len(esperado(p, "sabana", ("LLAVE_NOMBRE",)))
        rechazos = len(resultados[p]["rechazo"])
        validos = len(resultados[p]["valida"])
        cuadra = rechazos + validos == sabana
        uno &= cuadra
        print(
            f"{p} invariante sábana: rechazos {rechazos} + válidos {validos} = "
            f"{rechazos + validos} frente a {sabana}; {'OK' if cuadra else 'DIFERENCIA'}"
        )
    return uno


__all__ = [
    "ARCHIVOS",
    "CASO",
    "ENTRADAS",
    "PRODUCTOS",
    "SUFIJO_VECTORES",
    "VECTORES",
    "clasificar_sas",
    "esperado_vectores",
    "informe",
    "informe_vectores",
    "invariantes",
    "observado",
    "unir",
    "vector_csv",
]
