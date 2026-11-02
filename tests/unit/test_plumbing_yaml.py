"""Fontanería desde `rules/sas/plumbing.yaml` (F1.4): las categorías y su orden no cambian."""

import pytest

from sgm.passes.plumbing_patterns import PLUMBING_PATTERNS, PLUMBING_YAML, cargar, match_plumbing


def test_el_yaml_trae_las_diecinueve_categorias():
    assert len(cargar(PLUMBING_YAML)) == len(PLUMBING_PATTERNS) == 19


@pytest.mark.parametrize(
    ("paso", "categoria"),
    [
        ("sleep 5;", "espera"),
        ('x "ls -l";', "shell_auxiliar"),
        ("%put traza;", "mensajes"),
        ('title "Reporte";', "presentacion"),
        ("proc delete data=work.x;", "borrado_datasets"),
        ('proc printto log="x" new;', "redireccion_log"),
        ('sysecho "en lectura";', "mensajes_sistema"),
        ("ods html close;", "ods_close"),
        ('filename entrada "x.txt";', None),  # FILENAME en un DATA step es fuente, no fontanería
        ("x = 1;", None),
    ],
)
def test_cada_paso_cae_en_su_categoria(paso, categoria):
    encontrado = match_plumbing(paso)
    assert (encontrado.category if encontrado else None) == categoria


def test_el_orden_del_yaml_decide_cuando_varios_coinciden():
    ids = [p.category for p in PLUMBING_PATTERNS]
    assert ids.index("espera") < ids.index("shell_auxiliar")
