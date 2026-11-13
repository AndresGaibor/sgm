"""Manifiestos humanos y escritura reproducible de datos por rebanada."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from sgm.ir.models import Column
from tools.corpus_lib.datos_ficticios import escribir_entrada
from tools.datos_sinteticos.ficha import Ficha, escribir_ficha
from tools.datos_sinteticos.por_esquema import generar_filas
from tools.datos_sinteticos.requisitos import Requisitos


@dataclass(frozen=True)
class TablaDeDatos:
    """Datos decididos por una persona para una tabla externa."""

    filas: int
    fijos: dict[str, str] = field(default_factory=dict)
    columnas: tuple[str, ...] = ()


@dataclass(frozen=True)
class Manifiesto:
    """Semilla común y configuración explícita de cada tabla."""

    semilla: int
    tablas: dict[str, TablaDeDatos]


@dataclass(frozen=True)
class _Salida:
    tabla: str
    csv_nombre: str
    ficha_nombre: str
    encabezado: list[str]
    filas: list[list[str]]
    ficha: Ficha


def _clave_tabla(nombre: object) -> str:
    if not isinstance(nombre, str):
        raise ValueError("nombre de tabla inválido")
    partes = nombre.split(".")
    if len(partes) != 2 or any(not parte.isidentifier() for parte in partes):
        raise ValueError(f"{nombre}: nombre de tabla debe ser biblioteca.tabla")
    return nombre.casefold()


def leer_manifiesto(ruta: Path) -> Manifiesto:
    """Lee y valida `datos.yaml`; no convierte valores numéricos de forma implícita."""
    try:
        contenido = yaml.safe_load(ruta.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError) as error:
        raise ValueError(f"no se pudo leer el manifiesto {ruta}") from error
    if not isinstance(contenido, dict):
        raise ValueError("el manifiesto debe ser un objeto")
    semilla = contenido.get("semilla")
    tablas_raw = contenido.get("tablas")
    if isinstance(semilla, bool) or not isinstance(semilla, int):
        raise ValueError("semilla debe ser un entero")
    if not isinstance(tablas_raw, dict):
        raise ValueError("tablas debe ser un objeto")
    tablas: dict[str, TablaDeDatos] = {}
    for nombre, datos in tablas_raw.items():
        clave = _clave_tabla(nombre)
        if clave in tablas:
            raise ValueError(f"{nombre}: tabla duplicada en el manifiesto")
        if not isinstance(datos, dict):
            raise ValueError(f"{nombre}: configuración inválida")
        filas = datos.get("filas")
        if isinstance(filas, bool) or not isinstance(filas, int) or filas < 0:
            raise ValueError(f"{nombre}: filas debe ser un entero no negativo")
        fijos = datos.get("fijos", {})
        if not isinstance(fijos, dict) or any(
            not isinstance(columna, str)
            or not isinstance(valor, str)
            for columna, valor in fijos.items()
        ):
            raise ValueError(f"{nombre}: fijos debe mapear columnas a textos")
        columnas = datos.get("columnas", ())
        if not isinstance(columnas, (list, tuple)) or any(
            not isinstance(columna, str) or not columna for columna in columnas
        ):
            raise ValueError(f"{nombre}: columnas debe ser una lista de nombres")
        if len({columna.casefold() for columna in columnas}) != len(columnas):
            raise ValueError(f"{nombre}: columnas duplicadas")
        if len({columna.casefold() for columna in fijos}) != len(fijos):
            raise ValueError(f"{nombre}: valores fijos duplicados")
        tablas[clave] = TablaDeDatos(filas, dict(fijos), tuple(columnas))
    if set(contenido) - {"semilla", "tablas"}:
        raise ValueError("el manifiesto solo admite semilla y tablas")
    return Manifiesto(semilla, tablas)


def _esquemas_por_tabla(
    esquemas: Mapping[str, Sequence[Column]],
) -> dict[str, list[Column]]:
    resultado: dict[str, list[Column]] = {}
    for tabla, columnas in esquemas.items():
        clave = _clave_tabla(tabla)
        if clave in resultado:
            raise ValueError(f"{tabla}: esquema duplicado")
        resultado[clave] = list(columnas)
    return resultado


def _columnas_para(
    tabla: str,
    demostradas: list[str],
    declaradas: TablaDeDatos,
    esquemas: dict[str, list[Column]],
) -> list[Column]:
    existentes = esquemas.get(tabla, [])
    por_nombre = {columna.name.casefold(): columna for columna in existentes}
    nombres: list[str] = []
    vistos: set[str] = set()
    for nombre in [*demostradas, *declaradas.columnas]:
        if nombre.casefold() not in vistos:
            vistos.add(nombre.casefold())
            nombres.append(nombre)
    if not nombres and existentes:
        nombres = [columna.name for columna in existentes]
    if not nombres:
        raise ValueError(
            f"{tabla}: el programa no demuestra sus columnas; declararlas en datos.yaml"
        )
    columnas = [
        por_nombre.get(nombre.casefold(), Column(nombre, None, source="program"))
        for nombre in nombres
    ]
    por_columna = {columna.name.casefold() for columna in columnas}
    for nombre in declaradas.fijos:
        if nombre.casefold() not in por_columna:
            raise ValueError(f"{tabla}: la columna fija {nombre} no está declarada")
    return columnas


def _valores_exigidos(
    tabla: str,
    columnas: list[Column],
    exigidos: dict[str, dict[str, list[str]]],
    declarados: TablaDeDatos,
) -> dict[str, list[str]]:
    por_nombre = {columna.name.casefold(): columna.name for columna in columnas}
    resultado: dict[str, list[str]] = {}
    for columna, valores in exigidos.get(tabla, {}).items():
        nombre = por_nombre.get(columna.casefold())
        if nombre is not None:
            resultado[nombre] = list(valores)
    for columna, valor in declarados.fijos.items():
        nombre = por_nombre[columna.casefold()]
        resultado[nombre] = [valor] * declarados.filas
    return resultado


def _nombres_salida(tabla: str) -> tuple[str, str]:
    partes = tabla.split(".")
    if len(partes) != 2 or any(not parte.isidentifier() for parte in partes):
        raise ValueError(f"{tabla}: nombre inseguro para archivo")
    if tabla.startswith("work."):
        csv_nombre = f"WORK.{partes[1]}.csv"
        return csv_nombre, f"{Path(csv_nombre).stem}.ficha.yaml"
    return f"{tabla}.csv", f"{tabla}.ficha.yaml"


def generar_entradas(
    req: Requisitos,
    esquemas: Mapping[str, Sequence[Column]],
    manifiesto: Manifiesto,
    destino: Path,
) -> list[Path]:
    """Prepara todas las tablas requeridas y solo después escribe CSV y fichas."""
    requeridas: dict[str, list[str]] = {}
    for grupo in (req.tablas_work_externas, req.tablas_base):
        for tabla, columnas in grupo.items():
            clave = _clave_tabla(tabla)
            requeridas.setdefault(clave, [])
            vistos = {nombre.casefold() for nombre in requeridas[clave]}
            for nombre in columnas:
                if nombre.casefold() not in vistos:
                    requeridas[clave].append(nombre)
                    vistos.add(nombre.casefold())
    for tabla, columnas in req.exigidos.items():
        clave = _clave_tabla(tabla)
        if clave not in requeridas:
            continue
        requeridas.setdefault(clave, [])
        vistas = {nombre.casefold() for nombre in requeridas[clave]}
        for nombre in columnas:
            if nombre.casefold() not in vistas:
                requeridas[clave].append(nombre)
                vistas.add(nombre.casefold())
    esquema_por_tabla = _esquemas_por_tabla(esquemas)
    salidas: list[_Salida] = []
    for tabla, columnas_demostradas in requeridas.items():
        declarada = manifiesto.tablas.get(tabla)
        if declarada is None:
            raise ValueError(f"{tabla}: falta en datos.yaml")
        columnas = _columnas_para(tabla, columnas_demostradas, declarada, esquema_por_tabla)
        exigidos = _valores_exigidos(tabla, columnas, req.exigidos, declarada)
        encabezado, filas, avisos = generar_filas(
            tabla, columnas, declarada.filas, manifiesto.semilla, exigidos
        )
        tipos_ficha = {
            columna.name: (
                columna.type
                if columna.type in {"String", "Double", "Integer", "Long"}
                else "String"
            )
            for columna in columnas
        }
        notas = [
            "Tipos de fixture generado; un String no implica tipo SAS demostrado."
        ]
        notas.extend(avisos)
        csv_nombre, ficha_nombre = _nombres_salida(tabla)
        ficha = Ficha(
            tabla=tabla,
            origen="sintetico",
            filas=declarada.filas,
            columnas=tipos_ficha,
            semilla=manifiesto.semilla,
            generador="tools/datos_sinteticos/manifiesto.py:generar_entradas",
            nota=" ".join(notas),
        )
        salidas.append(_Salida(tabla, csv_nombre, ficha_nombre, encabezado, filas, ficha))

    raiz = destino.resolve()
    archivos = [
        raiz / nombre
        for salida in salidas
        for nombre in (salida.csv_nombre, salida.ficha_nombre)
    ]
    for archivo in archivos:
        if not archivo.resolve().is_relative_to(raiz):
            raise ValueError(f"{archivo.name}: ruta de salida fuera del destino")

    escritas: list[Path] = []
    for salida in salidas:
        nombre_csv = Path(salida.csv_nombre).stem
        escribir_entrada(raiz, nombre_csv, salida.encabezado, salida.filas)
        ruta_csv = raiz / salida.csv_nombre
        escribir_ficha(salida.ficha, raiz / salida.ficha_nombre)
        escritas.extend((ruta_csv, raiz / salida.ficha_nombre))
    return escritas
