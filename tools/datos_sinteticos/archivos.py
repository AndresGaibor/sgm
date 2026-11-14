"""Archivos delimitados sintéticos declarados por un manifiesto de caso."""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass, field
from pathlib import Path, PureWindowsPath

from tools.datos_sinteticos.ficha import Ficha, escribir_ficha

_NOMBRE = re.compile(r"[A-Za-z0-9_][A-Za-z0-9_.-]*\.[A-Za-z0-9]{1,10}\Z")
_COLUMNA = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\Z")
_RESERVADOS_WINDOWS = {"aux", "con", "nul", "prn"} | {
    f"{prefijo}{numero}" for prefijo in ("com", "lpt") for numero in range(1, 10)
}


@dataclass(frozen=True)
class ArchivoDeDatos:
    """Forma de un archivo y valores fijados explícitamente por el caso."""

    filas: int
    columnas: tuple[str, ...]
    delimitador: str
    cabecera: bool
    fijos: dict[str, str] = field(default_factory=dict)


def _nombre_seguro(nombre: object) -> str:
    if not isinstance(nombre, str) or not _NOMBRE.fullmatch(nombre):
        raise ValueError(f"nombre de archivo inválido: {nombre!r}")
    if Path(nombre).name != nombre or PureWindowsPath(nombre).name != nombre:
        raise ValueError(f"ruta de archivo no permitida: {nombre!r}")
    if Path(nombre).stem.casefold() in _RESERVADOS_WINDOWS:
        raise ValueError(f"nombre de dispositivo no permitido: {nombre!r}")
    return nombre


def leer_archivos(contenido: object) -> dict[str, ArchivoDeDatos]:
    """Valida la sección `archivos` del manifiesto sin inferir tipos ni valores."""
    if contenido is None:
        return {}
    if not isinstance(contenido, dict):
        raise ValueError("archivos debe ser un objeto")
    resultado: dict[str, ArchivoDeDatos] = {}
    vistos: set[str] = set()
    for nombre, datos in contenido.items():
        seguro = _nombre_seguro(nombre)
        clave = seguro.casefold()
        if clave in vistos:
            raise ValueError(f"{seguro}: archivo duplicado en el manifiesto")
        vistos.add(clave)
        if not isinstance(datos, dict):
            raise ValueError(f"{seguro}: configuración inválida")
        filas = datos.get("filas")
        if isinstance(filas, bool) or not isinstance(filas, int) or filas < 0:
            raise ValueError(f"{seguro}: filas debe ser un entero no negativo")
        columnas = datos.get("columnas")
        if (
            not isinstance(columnas, list)
            or not columnas
            or any(
                not isinstance(columna, str) or not _COLUMNA.fullmatch(columna)
                for columna in columnas
            )
        ):
            raise ValueError(f"{seguro}: columnas debe ser una lista de identificadores")
        if len({columna.casefold() for columna in columnas}) != len(columnas):
            raise ValueError(f"{seguro}: columnas duplicadas")
        delimitador = datos.get("delimitador")
        if not isinstance(delimitador, str) or len(delimitador) != 1 or delimitador in '\r\n"':
            raise ValueError(f"{seguro}: delimitador debe ser un carácter imprimible")
        cabecera = datos.get("cabecera")
        if not isinstance(cabecera, bool):
            raise ValueError(f"{seguro}: cabecera debe ser true o false")
        fijos = datos.get("fijos", {})
        if not isinstance(fijos, dict) or any(
            not isinstance(columna, str) or not isinstance(valor, str)
            for columna, valor in fijos.items()
        ):
            raise ValueError(f"{seguro}: fijos debe mapear columnas a textos")
        nombres = {columna.casefold() for columna in columnas}
        if any(columna.casefold() not in nombres for columna in fijos):
            raise ValueError(f"{seguro}: fijos contiene una columna no declarada")
        if len({columna.casefold() for columna in fijos}) != len(fijos):
            raise ValueError(f"{seguro}: fijos contiene columnas duplicadas")
        resultado[seguro] = ArchivoDeDatos(
            filas, tuple(columnas), delimitador, cabecera, dict(fijos)
        )
    return resultado


def nombres_salida(archivos: dict[str, ArchivoDeDatos]) -> list[str]:
    """Nombres relativos que ocuparán los archivos y sus fichas laterales."""
    return [
        nombre
        for archivo in archivos
        for nombre in (archivo, f"{Path(archivo).stem}.ficha.yaml")
    ]


def generar_archivos(
    archivos: dict[str, ArchivoDeDatos], semilla: int, destino: Path
) -> list[Path]:
    """Escribe archivos CSV deterministas y fichas con formato explícito."""
    if not archivos:
        return []
    raiz = destino.resolve()
    preparados = []
    for nombre, spec in archivos.items():
        nombre = _nombre_seguro(nombre)
        ruta = raiz / nombre
        ficha_path = raiz / f"{Path(nombre).stem}.ficha.yaml"
        if not ruta.resolve().is_relative_to(raiz) or not ficha_path.resolve().is_relative_to(raiz):
            raise ValueError(f"{nombre}: ruta de salida fuera de entradas")
        fijos = {columna.casefold(): valor for columna, valor in spec.fijos.items()}
        filas = [
            [
                fijos.get(columna.casefold(), f"SIM_{semilla}_{numero}_{columna}")
                for columna in spec.columnas
            ]
            for numero in range(1, spec.filas + 1)
        ]
        ficha = Ficha(
            tabla=f"archivo:{nombre}",
            origen="sintetico",
            filas=spec.filas,
            columnas=dict.fromkeys(spec.columnas, "String"),
            semilla=semilla,
            generador="tools/datos_sinteticos/archivos.py:generar_archivos",
            nota="Valores de fixture; no demuestran tipos SAS.",
            cabecera=spec.cabecera,
            delimitador=spec.delimitador,
        )
        preparados.append((ruta, ficha_path, spec, filas, ficha))

    escritos = []
    for ruta, ficha_path, spec, filas, ficha in preparados:
        ruta.parent.mkdir(parents=True, exist_ok=True)
        with ruta.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.writer(stream, delimiter=spec.delimitador, lineterminator="\n")
            if spec.cabecera:
                writer.writerow(spec.columnas)
            writer.writerows(filas)
        escribir_ficha(ficha, ficha_path)
        escritos.extend((ruta, ficha_path))
    return escritos
