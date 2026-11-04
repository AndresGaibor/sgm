"""Interfaz mínima del emisor de las ocho secciones del diseño (aún no existe).

`obtener_diseno` es el punto de enganche: cuando el emisor exista, su salida se adapta a este
contrato y las pruebas de `test_conformidad.py` dejan de ser `xfail`.

Contrato de la salida: `{codigo_seccion: {clave_de_fila: {columna: texto}}}`, con los mismos
códigos de sección, claves de fila y nombres de columna que `diseno_manual.yaml`.
"""

from __future__ import annotations

from pathlib import Path

from tests.conformidad.cargador import Fila

Diseno = dict[str, dict[str, dict[str, str]]]


def obtener_diseno(programa_sas: Path) -> Diseno:
    """Devuelve el diseño que el migrador deduce de `programa_sas`.

    Hoy no hay emisor de las ocho secciones: lanza `NotImplementedError`.
    """
    raise NotImplementedError("el emisor de las 8 secciones del diseño aún no existe")


def _norm(valor: str) -> str:
    return " ".join(str(valor).split())


def diferencias_fila(esperada: Fila, obtenida: dict[str, str] | None) -> list[str]:
    """Lista de diferencias entre la fila esperada y la obtenida (vacía si coinciden)."""
    if obtenida is None:
        return [f"falta la fila {esperada.clave!r}"]
    difs = []
    for columna, valor in esperada.campos.items():
        if _norm(obtenida.get(columna, "")) != _norm(valor):
            difs.append(f"{columna}: esperado {valor!r}, obtenido {obtenida.get(columna)!r}")
    return difs
