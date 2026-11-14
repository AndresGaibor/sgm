"""Especificaciones L4 derivadas de vectores de funciones con oráculo verificable."""

from __future__ import annotations

import math
import re
from collections import defaultdict

from corpus_semantica import Faltante, cargar_vectores, evaluar

from .especificaciones_l4_funciones import FUNCIONES_CON_CASO
from .programas_l4_vectores import generar_programa

_FUENTE_CONFIDENCIAS = {"documentado", "deducido"}


def _coincide(obtenido: object, esperado: object) -> bool:
    if esperado == "faltante":
        return isinstance(obtenido, Faltante)
    if isinstance(obtenido, Faltante):
        return False
    if isinstance(esperado, bool) or isinstance(obtenido, bool):
        return type(obtenido) is bool and obtenido == esperado
    if isinstance(esperado, (int, float)) and isinstance(obtenido, (int, float)):
        return math.isclose(obtenido, esperado, rel_tol=0, abs_tol=1e-9)
    return obtenido == esperado


def _tipo_columna(valor: object) -> str:
    if valor is None:
        return "N"
    if isinstance(valor, bool):
        raise ValueError("los booleanos no tienen tipo de columna SAS demostrado")
    if isinstance(valor, (int, float)):
        return "N"
    if isinstance(valor, str):
        return "T"
    raise ValueError(f"tipo de entrada no admitido: {type(valor).__name__}")


def _parte_literal(valor: object) -> str:
    if valor is None:
        return "omitido"
    if isinstance(valor, bool):
        return "1" if valor else "0"
    if isinstance(valor, int):
        return str(valor).replace("-", "m")
    if isinstance(valor, float):
        return format(valor, ".12g").replace("-", "m").replace(".", "p")
    if isinstance(valor, str):
        if re.fullmatch(r"[A-Za-z0-9]+", valor):
            return "s" + valor
        return "s" + valor.encode("utf-8").hex()
    raise ValueError(f"literal no admitido: {type(valor).__name__}")


def _literal_sas(valor: object, funcion: str) -> str:
    if valor is None:
        # SAS documenta que COMPRESS acepta un argumento nulo y lo trata como cadena de longitud 0.
        return "''" if funcion == "compress" else ""
    if isinstance(valor, bool):
        return "1" if valor else "0"
    if isinstance(valor, str):
        return "'" + valor.replace("'", "''") + "'"
    if isinstance(valor, (int, float)):
        return repr(valor)
    raise ValueError(f"literal SAS no admitido: {type(valor).__name__}")


def _argumentos_sas(funcion: str, argumentos: list, descriptor: dict, columnas: list[str]) -> str:
    if funcion == "input":
        if len(columnas) != 1 or len(argumentos) < 2:
            raise ValueError("INPUT requiere una columna y el ancho del informat")
        ancho = argumentos[1]
        decimales = argumentos[2] if len(argumentos) > 2 else None
        if not isinstance(ancho, int) or isinstance(ancho, bool):
            raise ValueError("el ancho de INPUT debe ser un entero literal")
        if decimales is None:
            informat = f"{ancho}."
        elif isinstance(decimales, int) and not isinstance(decimales, bool):
            informat = f"{ancho}.{decimales}"
        else:
            raise ValueError("los decimales de INPUT deben ser un entero literal")
        return f"{columnas[0]}, {informat}"

    literales = set(descriptor["literales"])
    nombres_por_posicion = iter(columnas)
    partes = [
        _literal_sas(valor, funcion)
        if indice in literales
        else next(nombres_por_posicion)
        for indice, valor in enumerate(argumentos)
    ]
    return ", ".join(partes)


def _preparar_vector(vector: dict, descriptor: dict) -> tuple:
    identificador = vector.get("id", "sin-id")
    argumentos = vector.get("entrada")
    if not isinstance(argumentos, list) or not argumentos:
        raise ValueError(f"{identificador}: se esperaba una lista no vacía en entrada")
    posiciones_literales = tuple(i for i in descriptor["literales"] if i < len(argumentos))
    posiciones_columnas = tuple(i for i in range(len(argumentos)) if i not in posiciones_literales)
    if posiciones_columnas != tuple(range(len(posiciones_columnas))):
        raise ValueError(
            f"{identificador}: los argumentos de columna deben preceder a los literales"
        )
    if len(posiciones_columnas) > len(descriptor["columnas"]):
        raise ValueError(f"{identificador}: faltan nombres para sus columnas de entrada")
    literales = tuple(argumentos[i] for i in posiciones_literales)
    columnas = tuple(argumentos[i] for i in posiciones_columnas)
    forma = (tuple(_tipo_columna(valor) for valor in columnas), len(argumentos))
    return argumentos, literales, columnas, forma


def especificaciones_de_vectores(vectores: list[dict]) -> dict[str, dict]:
    """Agrupa vectores verificables por función, literales y forma de llamada compatible."""
    agrupados: dict[tuple, list[tuple[dict, tuple, tuple, tuple]]] = defaultdict(list)
    for funcion, descriptor in FUNCIONES_CON_CASO.items():
        for vector in vectores:
            if vector.get("funcion") != funcion:
                continue
            if descriptor.get("ignorar_argumentos_con_blancos_finales") and any(
                isinstance(argumento, str) and argumento.endswith(" ")
                for argumento in vector.get("entrada", [])
            ):
                continue
            confianza = vector.get("confianza")
            if confianza == "incierto":
                continue
            identificador = vector.get("id", "sin-id")
            if confianza not in _FUENTE_CONFIDENCIAS:
                raise ValueError(f"{identificador}: confianza no verificable {confianza!r}")
            if not vector.get("fuente_url") or not vector.get("cita"):
                raise ValueError(f"{identificador}: falta la fuente o la cita SAS")
            try:
                argumentos, literales, columnas, forma = _preparar_vector(vector, descriptor)
                resultado = evaluar(funcion, *argumentos)
            except (KeyError, TypeError, ValueError) as exc:
                raise ValueError(f"{identificador}: no se pudo verificar el vector: {exc}") from exc
            if not _coincide(resultado, vector.get("esperado")):
                raise ValueError(
                    f"{identificador}: el oráculo devuelve {resultado!r}, "
                    f"pero el vector espera {vector.get('esperado')!r}"
                )
            if not isinstance(resultado, Faltante):
                resultado_numerico = isinstance(resultado, (int, float)) and not isinstance(
                    resultado, bool
                )
                if resultado_numerico != descriptor["salida_numerica"]:
                    raise ValueError(f"{identificador}: tipo de resultado no coincide con SAS")
            agrupados[(funcion, literales, forma)].append(
                (vector, argumentos, columnas, forma)
            )

    sufijos: dict[tuple[str, str], int] = defaultdict(int)
    for funcion, literales, _forma in agrupados:
        base = "_".join(_parte_literal(valor) for valor in literales) or "sin_literales"
        sufijos[(funcion, base)] += 1

    especificaciones: dict[str, dict] = {}
    numero = 100
    for funcion, descriptor in FUNCIONES_CON_CASO.items():
        grupos = [clave for clave in agrupados if clave[0] == funcion]
        for clave in grupos:
            _, literales, forma = clave
            vectores_grupo = agrupados[clave]
            base = "_".join(_parte_literal(valor) for valor in literales) or "sin_literales"
            sufijo = base
            if sufijos[(funcion, base)] > 1:
                sufijo += "_a" + str(forma[1])
                sufijo += "_" + "".join(forma[0])
            nombre = f"l4_{numero}_vec_{funcion}_{sufijo}"
            numero += 1
            columnas = list(descriptor["columnas"][: len(forma[0])])
            nombre_tabla = "ENTRADA_L4"
            nombre_salida = "RESULTADO_L4"
            filas = [
                tuple(datos[i] for i in range(len(columnas)))
                for _vector, _argumentos, datos, _forma in vectores_grupo
            ]
            numericas = tuple(
                columna for columna, tipo in zip(columnas, forma[0], strict=True) if tipo == "N"
            )
            primera = vectores_grupo[0]
            argumentos = primera[1]
            argumentos_sas = _argumentos_sas(funcion, argumentos, descriptor, columnas)
            expresion = descriptor["sas"].format(argumentos=argumentos_sas)
            texto_sas = f"RESULTADO={expresion};"
            fuente_urls = list(dict.fromkeys(item[0]["fuente_url"] for item in vectores_grupo))
            ids = [item[0]["id"] for item in vectores_grupo]
            confianza = sorted({item[0]["confianza"] for item in vectores_grupo})
            razonamiento = (
                "Vectores verificables por el oráculo: "
                + ", ".join(ids)
                + ". Confianza: "
                + ", ".join(confianza)
                + "."
            )
            asignacion = ("RESULTADO", columnas[0] if len(columnas) == 1 else tuple(columnas),
                          ((funcion, *literales),), texto_sas)
            spec = {
                "construcciones": ["DATA STEP", funcion.upper()],
                "entrada": (nombre_tabla, columnas, filas, numericas),
                "asignaciones": [asignacion],
                "salida": nombre_salida,
                "fuentes": fuente_urls,
                "invariantes": [f"filas({nombre_salida}) == {len(filas)}"],
                "razonamiento": razonamiento,
                "citar_espacios_borde": descriptor.get("citar_espacios_borde", False),
                "programa": generar_programa(
                    nombre, nombre_tabla, nombre_salida, texto_sas, columnas, filas, numericas
                ),
            }
            especificaciones[nombre] = spec
    return especificaciones


ESPECIFICACIONES_L4V = especificaciones_de_vectores(cargar_vectores())
