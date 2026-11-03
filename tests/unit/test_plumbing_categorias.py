"""Un caso que sí cae y un caso cercano que no cae, por cada una de las 19 categorías de fontanería.

Los casos cercanos (`sleepers`, `%globals`, `drop = 1`...) prueban que el patrón está anclado y no
atrapa cualquier texto que contenga la palabra clave.
"""

import pytest

from sgm.passes.plumbing_patterns import PLUMBING_PATTERNS, match_plumbing

# (categoría, paso que debe caer en ella, paso cercano que NO debe caer en ella)
CASOS = [
    ("espera", "sleep 5;", "data sleepers; set b; run;"),
    ("shell_auxiliar", 'x "ls -l";', "x = 1;"),
    ("conexion", "connect to oracle;", "x = connect;"),
    ("limpieza_tablas", "drop table x;", "drop = 1;"),
    ("control_macro", "%do i=1 %to 3;", "%let do_x = 1;"),
    ("mensajes", "%put traza;", "put traza;"),
    ("variables_control", "call symput('a', x);", "call execute('x');"),
    ("medicion", "t = datetime();", "t = datetime;"),
    ("troceado_lotes", "set a(firstobs=&ini obs=&fin);", "set a(firstobs=10);"),
    ("visor_studio", "%web_drop_table(x);", "%web = 1;"),
    ("presentacion", 'title "Reporte";', "my title = 1;"),
    ("configuracion_macro", "%global x;", "%globals = 1;"),
    ("remoto", "rsubmit;", "rsubmitted = 1;"),
    ("fin_de_paso", "quit;", "quit = 1;"),
    ("conteo", "select count(*) into :n from x;", "select count(*) from x;"),
    ("borrado_datasets", "proc delete data=work.x;", "proc print data=x;"),
    ("redireccion_log", 'proc printto log="x" new;', "proc print data=x;"),
    ("mensajes_sistema", 'sysecho "en lectura";', "x = sysecho;"),
    ("ods_close", "ods html close;", "ods html;"),
]


def _categoria(paso: str) -> str | None:
    # El pipeline recibe la sentencia sin el punto y coma final (ver p02_plumbing.primary_text).
    encontrado = match_plumbing(paso.rstrip(";"))
    return encontrado.category if encontrado else None


def test_hay_un_caso_por_cada_categoria():
    assert {c for c, _, _ in CASOS} == {p.category for p in PLUMBING_PATTERNS}


@pytest.mark.parametrize(("categoria", "paso", "_cercano"), CASOS)
def test_el_paso_cae_en_su_categoria(categoria, paso, _cercano):
    assert _categoria(paso) == categoria


@pytest.mark.parametrize(("categoria", "_paso", "cercano"), CASOS)
def test_el_paso_cercano_no_cae_en_la_categoria(categoria, _paso, cercano):
    assert _categoria(cercano) != categoria
