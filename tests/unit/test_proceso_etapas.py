"""Tests de las etapas declaradas: carga, asignación y cobertura."""

from __future__ import annotations

import pytest

from sgm.proceso.etapas import cargar_etapas, cobertura, etapa_de

YAML = """\
etapas:
  - nombre: persistencia
    patrones: ["^escritura"]
  - nombre: validar_documento
    patrones: ["tipo doc", "nro doc"]
"""


def _cargar(tmp_path, texto=YAML):
    ruta = tmp_path / "d.yaml"
    ruta.write_text(texto, encoding="utf-8")
    return cargar_etapas(ruta)


def test_gana_la_primera_etapa_que_casa_sin_importar_mayusculas(tmp_path):
    etapas = _cargar(tmp_path)
    assert etapa_de("Escritura SABANA_X", etapas) == "persistencia"
    assert etapa_de("TIPO DOC invalido", etapas) == "validar_documento"
    assert etapa_de("Escritura tipo doc", etapas) == "persistencia"


def test_etiqueta_sin_etapa_es_none(tmp_path):
    assert etapa_de("Algo distinto", _cargar(tmp_path)) is None


def test_cobertura_cuenta_por_etapa_y_lista_las_sueltas(tmp_path):
    res = cobertura(["Escritura A", "Tipo doc x", "Rara", "Escritura B"], _cargar(tmp_path))
    assert dict(res.por_etapa) == {"persistencia": 2, "validar_documento": 1}
    assert res.sin_etapa == ["Rara"]
    assert res.total == 4
    assert res.porcentaje_cubierto == 75.0


@pytest.mark.parametrize(
    "texto, mensaje",
    [
        ("etapas: []\n", "no hay etapas"),
        ("etapas:\n  - nombre: a\n", "al menos un patrón"),
        ('etapas:\n  - {nombre: a, patrones: ["("]}\n', "patrón inválido"),
        ('etapas:\n  - {nombre: a, patrones: [x]}\n  - {nombre: a, patrones: [y]}\n', "repetida"),
    ],
)
def test_yaml_mal_formado_falla_con_motivo(tmp_path, texto, mensaje):
    with pytest.raises(ValueError, match=mensaje):
        _cargar(tmp_path, texto)


def test_el_yaml_de_decisiones_del_programa_grande_carga():
    from pathlib import Path

    etapas = cargar_etapas(Path("decisiones/client_large.diseno.yaml"))
    assert len(etapas) >= 5
    assert etapa_de("Escritura SABANA_X_AHO", etapas) == "persistencia_intermedia"
