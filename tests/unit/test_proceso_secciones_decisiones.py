"""Tests de la sección 5: decisiones abiertas o tomadas desde su YAML."""

from __future__ import annotations

from pathlib import Path

import pytest

from sgm.proceso.secciones_decisiones import cargar_decisiones, seccion_decisiones

REAL = Path(__file__).resolve().parents[2] / "decisiones" / "client_large.decisiones.yaml"

BUENA = """\
decisiones:
  - id: 'DC-01'
    texto: 'Alcance'
    motivo: 'La decide Usuario'
    estado: abierta
    valor_por_omision: 'Primero el programa'
  - id: 'DC-02'
    texto: 'Rechazos'
    motivo: 'La decide Negocio'
    estado: tomada
    valor_por_omision: 'Uno por producto'
"""


def _escribir(tmp_path: Path, texto: str) -> Path:
    ruta = tmp_path / "x.decisiones.yaml"
    ruta.write_text(texto, encoding="utf-8")
    return ruta


def test_sin_archivo_no_hay_decisiones(tmp_path: Path) -> None:
    assert cargar_decisiones(tmp_path / "no_existe.yaml") == []


def test_lee_las_decisiones_en_su_orden(tmp_path: Path) -> None:
    decisiones = cargar_decisiones(_escribir(tmp_path, BUENA))
    assert [d["id"] for d in decisiones] == ["DC-01", "DC-02"]
    assert decisiones[1]["estado"] == "tomada"


def test_la_seccion_tiene_una_fila_por_id_con_campos_en_espanol(tmp_path: Path) -> None:
    seccion = seccion_decisiones(cargar_decisiones(_escribir(tmp_path, BUENA)))
    assert list(seccion) == ["DC-01", "DC-02"]
    assert seccion["DC-01"] == {
        "texto": "Alcance",
        "motivo": "La decide Usuario",
        "estado": "abierta",
        "valor por omisión": "Primero el programa",
    }


@pytest.mark.parametrize(
    "malo, mensaje",
    [
        ("decisiones:\n  - {texto: 'x', motivo: 'y', estado: abierta, valor_por_omision: 'z'}\n",
         "necesita `id`"),
        ("decisiones:\n  - {id: 'DC-01', texto: '', motivo: 'y', estado: abierta,"
         " valor_por_omision: 'z'}\n", "necesita `texto`"),
        ("decisiones:\n  - {id: 'DC-01', texto: 'x', motivo: 'y', estado: cerrada,"
         " valor_por_omision: 'z'}\n", "tiene estado 'cerrada'"),
        ("decisiones:\n  - {id: 'DC-01', texto: 'x', motivo: 'y', estado: abierta,"
         " valor_por_omision: 'z'}\n  - {id: 'DC-01', texto: 'w', motivo: 'y',"
         " estado: abierta, valor_por_omision: 'z'}\n", "repite el id 'DC-01'"),
    ],
)
def test_rechaza_decisiones_incompletas_o_repetidas(
    tmp_path: Path, malo: str, mensaje: str
) -> None:
    with pytest.raises(ValueError, match=mensaje):
        cargar_decisiones(_escribir(tmp_path, malo))


def test_el_yaml_del_proyecto_trae_las_doce_decisiones_de_la_seccion_3() -> None:
    ids = [d["id"] for d in cargar_decisiones(REAL)]
    assert ids == [f"DC-{n:02d}" for n in range(1, 13)]
    assert {d["estado"] for d in cargar_decisiones(REAL)} == {"abierta"}
