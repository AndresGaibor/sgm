"""Pruebas que SÍ pasan hoy: la referencia manual es consistente y fiel al documento."""

from __future__ import annotations

from collections import Counter

import pytest

from tests.conformidad.cargador import (
    CLASIFICACIONES,
    DOCUMENTO,
    RAIZ,
    REFERENCIA,
    cargar_secciones,
    contar_filas_documento,
    todas_las_filas,
)
from tests.conformidad.interfaz import SECCIONES_EMITIDAS, diferencias_fila, obtener_diseno

SECCIONES = cargar_secciones()
FILAS = todas_las_filas(SECCIONES)

# Conteos tomados del documento (tablas y listas), sección por sección.
CONTEOS_DOCUMENTO = {
    "1.1": 8, "1.2": 10, "1.3": 3, "1.4": 5,
    "2.1": 9, "2.2": 6, "2.3": 3, "2.4": 4,
    "3.1": 6, "3.2": 6, "3.3": 6, "3.4": 4, "3.5": 5,
    "4": 6, "5": 6, "6": 8, "7": 12, "8": 7,
}  # fmt: skip


def test_el_yaml_carga_y_tiene_las_secciones_del_documento() -> None:
    assert REFERENCIA.is_file()
    principales = {c for c in SECCIONES if not c.endswith("b")}
    assert principales == set(CONTEOS_DOCUMENTO)


def test_ids_unicos_en_todo_el_archivo() -> None:
    repetidos = [i for i, n in Counter(f.id for f in FILAS).items() if n > 1]
    assert repetidos == []


def test_claves_unicas_dentro_de_cada_seccion() -> None:
    for seccion in SECCIONES.values():
        repetidas = [k for k, n in Counter(f.clave for f in seccion.filas).items() if n > 1]
        assert repetidas == [], seccion.codigo


def test_clasificacion_y_motivo_validos_en_cada_fila() -> None:
    for fila in FILAS:
        assert fila.clasificacion in CLASIFICACIONES, fila.id
        assert fila.motivo.strip(), fila.id


def test_los_campos_de_cada_fila_son_las_columnas_de_su_seccion() -> None:
    for seccion in SECCIONES.values():
        for fila in seccion.filas:
            assert set(fila.campos) <= set(seccion.columnas), fila.id


@pytest.mark.parametrize("codigo,esperado", sorted(CONTEOS_DOCUMENTO.items()))
def test_conteo_de_filas_por_seccion(codigo: str, esperado: int) -> None:
    assert len(SECCIONES[codigo].filas) == esperado


def test_seis_decisiones_y_doce_pendientes_y_riesgos() -> None:
    assert [f.id for f in SECCIONES["5"].filas] == ["D1", "D2", "D3", "D4", "D5", "D6"]
    ids = [f.id for f in SECCIONES["7"].filas]
    assert ids == [f"P{i}" for i in range(1, 9)] + [f"R{i}" for i in range(1, 5)]


@pytest.mark.skipif(not DOCUMENTO.is_file(), reason="el documento de diseño no está en el árbol")
def test_conteos_coinciden_con_el_markdown_del_documento() -> None:
    cuentas = contar_filas_documento()
    for codigo, seccion in SECCIONES.items():
        if seccion.md is False:
            continue
        clase = "lista" if seccion.md == "lista" else "tabla"
        assert cuentas[codigo][clase] == len(seccion.filas), codigo


def test_reparto_por_clasificacion_suma_el_total() -> None:
    cuentas = Counter(f.clasificacion for f in FILAS)
    assert sum(cuentas.values()) == len(FILAS)
    assert cuentas["derivable"] > cuentas["declarada"] > 0
    assert cuentas["humana"] > 0


def test_el_comparador_detecta_diferencias_y_acepta_coincidencias() -> None:
    fila = SECCIONES["1.3"].filas[0]
    assert diferencias_fila(fila, dict(fila.campos)) == []
    assert diferencias_fila(fila, {**fila.campos, "uso": "otro"})
    assert diferencias_fila(fila, None)


def test_el_emisor_produce_solo_las_secciones_emitidas() -> None:
    programa = RAIZ / "tests" / "fixtures" / "sas" / "client" / "client_large.sas"
    assert tuple(obtener_diseno(programa)) == SECCIONES_EMITIDAS
