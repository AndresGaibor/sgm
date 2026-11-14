"""Lector local y acotado de celdas XLSX OOXML para el anillo B."""

from __future__ import annotations

import posixpath
import re
import zipfile
from decimal import Decimal, InvalidOperation
from pathlib import Path, PurePosixPath
from xml.etree import ElementTree as ET

_REF_CELDA = re.compile(r"([A-Z]+)([1-9][0-9]*)\Z", re.IGNORECASE)


class _HojaInexistente(KeyError):
    pass


def _local(nombre: str) -> str:
    return nombre.rsplit("}", 1)[-1]


def _atributo(elemento: ET.Element, nombre: str) -> str | None:
    return next(
        (valor for clave, valor in elemento.attrib.items() if _local(clave) == nombre), None
    )


def _hijos(elemento: ET.Element, nombre: str):
    return (hijo for hijo in elemento if _local(hijo.tag) == nombre)


def _parte(base: str, destino: str) -> str:
    if "\\" in destino or "\x00" in destino or ":" in destino:
        raise ValueError("relación XLSX con ruta no permitida")
    if destino.startswith("/"):
        candidato = posixpath.normpath(destino.lstrip("/"))
    else:
        candidato = posixpath.normpath(posixpath.join(base, destino))
    ruta = PurePosixPath(candidato)
    if (
        ruta.is_absolute()
        or ".." in ruta.parts
        or not ruta.parts
        or ruta.parts[0] != base
        or any(parte == ".." for parte in PurePosixPath(destino).parts)
    ):
        raise ValueError("relación XLSX fuera del paquete")
    return candidato


def _columna(ref: str) -> int:
    match = _REF_CELDA.fullmatch(ref)
    if match is None:
        raise ValueError("referencia de celda XLSX inválida")
    numero = 0
    for letra in match.group(1).upper():
        numero = numero * 26 + ord(letra) - 64
    return numero - 1


def _numero(valor: str) -> str:
    if len(valor) > 4096:
        raise ValueError("valor numérico XLSX demasiado extenso")
    try:
        numero = Decimal(valor)
    except InvalidOperation:
        raise ValueError("valor numérico XLSX inválido") from None
    if not numero.is_finite():
        raise ValueError("valor numérico XLSX no finito")
    normalizado = format(numero.normalize(), "f")
    if "." in normalizado:
        normalizado = normalizado.rstrip("0").rstrip(".")
    return "0" if normalizado in {"", "-0"} else normalizado


def _texto(elemento: ET.Element | None) -> str:
    if elemento is None:
        return ""
    return "".join(nodo.text or "" for nodo in elemento.iter() if _local(nodo.tag) == "t")


def _valor_celda(celda: ET.Element, cadenas: list[str]) -> str:
    tipo = celda.attrib.get("t")
    if tipo == "inlineStr":
        return _texto(next(iter(_hijos(celda, "is")), None))
    valor = next(iter(_hijos(celda, "v")), None)
    texto = "" if valor is None or valor.text is None else valor.text
    if tipo == "s":
        try:
            return cadenas[int(texto)]
        except (ValueError, IndexError):
            raise ValueError("índice de cadena compartida XLSX inválido") from None
    if tipo == "b":
        if texto not in {"0", "1"}:
            raise ValueError("booleano XLSX inválido")
        return texto
    if tipo == "e":
        raise ValueError("celda de error XLSX no soportada")
    return _numero(texto) if texto else ""


def _relaciones(raiz: ET.Element) -> dict[str, tuple[str, str | None, str]]:
    resultado = {}
    for relacion in _hijos(raiz, "Relationship"):
        identificador = relacion.attrib.get("Id")
        destino = relacion.attrib.get("Target")
        tipo = relacion.attrib.get("Type", "")
        if not identificador or not destino or not tipo:
            raise ValueError("relación XLSX incompleta")
        resultado[identificador] = (destino, relacion.attrib.get("TargetMode"), tipo)
    return resultado


def _cargar_hojas(archivo: zipfile.ZipFile):
    libro = ET.fromstring(archivo.read("xl/workbook.xml"))
    relaciones = ET.fromstring(archivo.read("xl/_rels/workbook.xml.rels"))
    mapa = _relaciones(relaciones)
    hojas = []
    for hoja in libro.iter():
        if _local(hoja.tag) != "sheet":
            continue
        nombre = hoja.attrib.get("name")
        rid = _atributo(hoja, "id")
        if not nombre or not rid or rid not in mapa:
            raise ValueError("hoja XLSX sin relación válida")
        destino, modo, tipo = mapa[rid]
        if modo and modo.casefold() == "external":
            raise ValueError("no se admiten relaciones XLSX externas")
        if not tipo.endswith("/worksheet"):
            raise ValueError("tipo de hoja XLSX no soportado")
        hojas.append((nombre, _parte("xl", destino)))
    if not hojas:
        raise ValueError("el libro XLSX no contiene hojas")
    return hojas


def _cadenas_compartidas(archivo: zipfile.ZipFile, relaciones: ET.Element) -> list[str]:
    destino = next(
        (
            _parte("xl", rel.attrib["Target"])
            for rel in _hijos(relaciones, "Relationship")
            if rel.attrib.get("Type", "").endswith("/sharedStrings")
            and rel.attrib.get("TargetMode", "").casefold() != "external"
            and rel.attrib.get("Target")
        ),
        None,
    )
    if destino is None or destino not in archivo.namelist():
        return []
    raiz = ET.fromstring(archivo.read(destino))
    return [_texto(item) for item in _hijos(raiz, "si")]


def _filas(archivo: zipfile.ZipFile, parte: str, cadenas: list[str]) -> list[list[str]]:
    hoja = ET.fromstring(archivo.read(parte))
    sheet_data = next((n for n in hoja.iter() if _local(n.tag) == "sheetData"), None)
    if sheet_data is None:
        raise ValueError("hoja XLSX sin sheetData")
    filas: list[dict[int, str]] = []
    anterior = 0
    for fila in _hijos(sheet_data, "row"):
        numero_texto = fila.attrib.get("r")
        numero = int(numero_texto) if numero_texto and numero_texto.isdigit() else anterior + 1
        if numero <= anterior or numero > 1_048_576:
            raise ValueError("índice de fila XLSX inválido")
        while anterior + 1 < numero:
            filas.append({})
            anterior += 1
        celdas = {}
        siguiente = 0
        for celda in _hijos(fila, "c"):
            referencia = celda.attrib.get("r")
            posicion = _columna(referencia) if referencia else siguiente
            celdas[posicion] = _valor_celda(celda, cadenas)
            siguiente = posicion + 1
        filas.append(celdas)
        anterior = numero
    if not filas:
        raise ValueError("hoja XLSX vacía")
    ancho = max((max(fila, default=-1) + 1 for fila in filas), default=0)
    if ancho == 0 or ancho > 16_384:
        raise ValueError("ancho de hoja XLSX inválido")
    return [[fila.get(indice, "") for indice in range(ancho)] for fila in filas]


def leer_xlsx(
    ruta: Path, hoja: str | None = None, *, getnames: bool = True
) -> tuple[list[str], list[list[str]]]:
    """Lee una hoja XLSX: columnas y filas de texto; sin hoja usa la primera del libro.

    Con `getnames=False`, los nombres son A, B, ... y la primera fila se conserva como dato, según
    la referencia SAS/ACCESS para DBMS=XLSX. Las relaciones externas y rutas fuera del paquete se
    rechazan; no se extrae ningún archivo al sistema de archivos.
    """
    ruta = Path(ruta)
    try:
        with zipfile.ZipFile(ruta) as archivo:
            hojas = _cargar_hojas(archivo)
            elegida = hojas[0] if hoja is None else next(
                (par for par in hojas if par[0].casefold() == hoja.casefold()), None
            )
            if elegida is None:
                nombres = ", ".join(nombre for nombre, _ in hojas)
                raise _HojaInexistente(f"hoja {hoja!r} no existe; hojas disponibles: {nombres}")
            relaciones = ET.fromstring(archivo.read("xl/_rels/workbook.xml.rels"))
            filas = _filas(archivo, elegida[1], _cadenas_compartidas(archivo, relaciones))
    except _HojaInexistente:
        raise
    except (
        OSError,
        KeyError,
        zipfile.BadZipFile,
        RuntimeError,
        ET.ParseError,
        UnicodeDecodeError,
    ) as error:
        raise ValueError(f"archivo XLSX inválido: {ruta.name}") from error
    ancho = len(filas[0])
    if getnames:
        nombres = filas[0]
        if any(not nombre for nombre in nombres):
            raise ValueError("GETNAMES=YES requiere nombres en todas las columnas del XLSX")
        datos = filas[1:]
    else:
        nombres = []
        numero = 1
        while numero <= ancho:
            actual = numero
            letras = ""
            while actual:
                actual, resto = divmod(actual - 1, 26)
                letras = chr(65 + resto) + letras
            nombres.append(letras)
            numero += 1
        datos = filas
    return nombres, datos
