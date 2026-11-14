"""Funciones SAS de texto con semántica documentada para el oráculo."""

from __future__ import annotations

import math
import re


def length(texto: str) -> int:
    """LENGTH excluye blancos finales y devuelve uno para una cadena en blanco."""
    if not texto.isascii():
        raise ValueError("Pendiente: P-LENGTH-CODIFICACION; no se conoce la codificación SAS")
    return max(1, len(texto.rstrip(" ")))


def lengthc(texto: str) -> int:
    """LENGTHC incluye todos los caracteres, también los blancos finales."""
    return len(texto)


def lengthn(texto: str) -> int:
    """LENGTHN excluye blancos finales y devuelve cero para un blanco."""
    return len(texto.rstrip(" "))


def compbl(texto: str) -> str:
    """COMPBL sustituye cada secuencia de blancos repetidos por un blanco."""
    return re.sub(r" {2,}", " ", texto)


def tranwrd(texto: str, buscar: str, reemplazo: str) -> str:
    """TRANWRD reemplaza todas las apariciones no solapadas del objetivo."""
    if not buscar:
        raise ValueError("Pendiente: P-TRANWRD-OBJETIVO-VACIO")
    return texto.replace(buscar, reemplazo or " ")


def translate(texto: str, destino: str, origen: str) -> str:
    """TRANSLATE aplica el mapeo de caracteres a la vez, sin sustituciones encadenadas."""
    if not all(valor.isascii() for valor in (texto, destino, origen)):
        raise ValueError("Pendiente: P-TRANSLATE-CODIFICACION-SBCS")
    if len(set(origen)) != len(origen):
        raise ValueError("Pendiente: P-TRANSLATE-ORIGEN-DUPLICADO")
    mapeo = {caracter: destino[i] if i < len(destino) else " " for i, caracter in enumerate(origen)}
    return texto.translate(str.maketrans(mapeo))


def index(texto: str, buscar: str) -> int:
    """INDEX devuelve la primera posición en base uno, o cero si no encuentra el texto."""
    if not texto.isascii() or not buscar.isascii():
        raise ValueError("Pendiente: P-INDEX-CODIFICACION-SBCS")
    return texto.find(buscar) + 1 if buscar in texto else 0


def _modificadores(valor: object, funcion: str, permitidos: str) -> str:
    if valor is None:
        return ""
    if not isinstance(valor, str):
        raise ValueError(f"Pendiente: P-{funcion}-MODIFICADOR-DINAMICO")
    resultado = valor.lower()
    if set(resultado) - set(permitidos):
        raise ValueError(f"Pendiente: P-{funcion}-MODIFICADOR")
    return resultado


def find(texto: str, buscar: str, modificadores: object = None, inicio: object = None) -> int:
    """FIND busca desde la posición indicada y permite los modificadores I y T."""
    if isinstance(modificadores, (int, float)) and not isinstance(modificadores, bool):
        modificadores, inicio = inicio, modificadores
    if not texto.isascii() or not buscar.isascii():
        raise ValueError("Pendiente: P-FIND-CODIFICACION-SBCS")
    mods = _modificadores(modificadores, "FIND", "it")
    posicion = 1 if inicio is None else int(inicio)
    if inicio is not None and (isinstance(inicio, bool) or float(inicio) != posicion):
        raise ValueError("Pendiente: P-FIND-INICIO-DINAMICO")
    if "t" in mods:
        texto, buscar = texto.rstrip(" "), buscar.rstrip(" ")
    if "i" in mods:
        texto, buscar = texto.lower(), buscar.lower()
    if posicion == 0:
        return 0
    if posicion > 0:
        encontrado = texto.find(buscar, posicion - 1)
    else:
        encontrado = texto.rfind(buscar, 0, abs(posicion))
    return encontrado + 1 if encontrado >= 0 else 0


def count(texto: str, buscar: str, modificadores: object = None) -> int:
    """COUNT cuenta apariciones no solapadas y permite los modificadores I y T."""
    if not texto.isascii() or not buscar.isascii():
        raise ValueError("Pendiente: P-COUNT-CODIFICACION-SBCS")
    if not buscar:
        raise ValueError("Pendiente: P-COUNT-SUBCADENA-VACIA")
    mods = _modificadores(modificadores, "COUNT", "it")
    if "t" in mods:
        texto, buscar = texto.rstrip(" "), buscar.rstrip(" ")
    if "i" in mods:
        texto, buscar = texto.lower(), buscar.lower()
    return texto.count(buscar)


def propcase(texto: str, delimitadores: object = None) -> str:
    """PROPCASE baja el texto y sube el carácter inicial y el siguiente a cada delimitador."""
    lista = " /-.(\t" if delimitadores is None else str(delimitadores).lower()
    if not texto.isascii() or not lista.isascii():
        raise ValueError("Pendiente: P-PROPCASE-TRANTAB-LOCALE; no se conoce la codificación SAS")
    resultado: list[str] = []
    mayuscula = True
    for caracter in texto.lower():
        resultado.append(caracter.upper() if mayuscula else caracter)
        mayuscula = caracter in lista
    return "".join(resultado)


def reverse(texto: str) -> str:
    """REVERSE invierte los caracteres; los blancos finales pasan al inicio."""
    if not texto.isascii():
        raise ValueError("Pendiente: P-REVERSE-CODIFICACION-SBCS; no se conoce la codificación SAS")
    return texto[::-1]


def repeat(texto: str, veces: int) -> str:
    """REPEAT devuelve el argumento original y `veces` copias adicionales."""
    numero = float(veces)
    if not math.isfinite(numero) or numero < 0 or not numero.is_integer():
        raise ValueError("REPEAT requiere un número entero no negativo")
    return texto * (int(numero) + 1)


def right(texto: str) -> str:
    """RIGHT desplaza al inicio los blancos finales sin cambiar la longitud."""
    return texto.rstrip(" ").rjust(len(texto), " ")


def trimn(texto: str) -> str:
    """TRIMN quita los blancos finales y puede devolver una cadena de longitud cero."""
    return texto.rstrip(" ")
