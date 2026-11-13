"""Extracción de fuentes, predicados y dependencias de rebanadas SAS."""

from tools.datos_sinteticos.manifiesto import Manifiesto, generar_entradas
from tools.datos_sinteticos.requisitos import requisitos_de_rebanada, valores_exigidos


def test_valores_exigidos_resuelve_alias_de_tabla_de_copia():
    text = """
    proc sql;
      create table WORK.ACURA as
      select CARS_POC.Make, CARS_POC.Model
      from WORK.CARS_POC CARS_POC
      where ( CARS_POC.Make = 'Acura' );
    quit;
    """
    required, dynamic = valores_exigidos(text)
    assert required == {"work.cars_poc": {"make": ["Acura"]}}
    assert dynamic == []


def test_macros_no_se_convierten_en_valores_inventados():
    text = """
    proc sql;
      select max(ingestion_day)
      from resultados_vspc_clientes.master_customer_data as b
      where b.year=&ANIO. and b.month=&MES.;
    quit;
    """
    required, dynamic = valores_exigidos(text)
    assert required == {}
    assert dynamic == [
        "resultados_vspc_clientes.master_customer_data.year = &ANIO",
        "resultados_vspc_clientes.master_customer_data.month = &MES",
    ]


def test_macro_en_comillas_dobles_dinamica_y_comilla_simple_literal():
    quoted, quoted_dynamic = valores_exigidos(
        'proc sql; select t.year from lib.t t where t.year="&ANIO."; quit;'
    )
    single, single_dynamic = valores_exigidos(
        "proc sql; select t.year from lib.t t where t.year='&ANIO'; quit;"
    )
    assert quoted == {}
    assert quoted_dynamic == ["lib.t.year = &ANIO"]
    assert single == {"lib.t": {"year": ["&ANIO"]}}
    assert single_dynamic == []


def test_columna_con_macro_dinamico_sigue_siendo_requisito_de_entrada():
    req = requisitos_de_rebanada(
        'proc sql; select t.id from lib.t t where t.year="&ANIO."; quit;'
    )
    assert set(req.tablas_base["lib.t"]) == {"id", "year"}
    assert req.dinamicos == ["lib.t.year = &ANIO"]


def test_macro_funcion_en_comillas_dobles_no_se_toma_como_literal():
    required, dynamic = valores_exigidos(
        'proc sql; select t.x from lib.t t where t.x="%upcase(foo)"; quit;'
    )
    assert required == {}
    assert dynamic == ["lib.t.x = %upcase(foo)"]


def test_in_con_literales_y_macro_conserva_los_literales_conocidos():
    required, dynamic = valores_exigidos(
        "proc sql; select t.x from lib.t t where t.code in ('A','B'); quit;"
    )
    mixed, pending = valores_exigidos(
        "proc sql; select t.x from lib.t t where t.code in ('A', &MES.); quit;"
    )
    several, several_pending = valores_exigidos(
        "proc sql; select t.x from lib.t t where t.code in ('A', &X., 'B', &Y.); quit;"
    )
    macro_first, macro_first_pending = valores_exigidos(
        "proc sql; select t.x from lib.t t where t.code in (&X., 'B'); quit;"
    )
    assert required == {"lib.t": {"code": ["A", "B"]}}
    assert dynamic == []
    assert mixed == {"lib.t": {"code": ["A"]}}
    assert pending == ["lib.t.code IN &MES"]
    assert several == {"lib.t": {"code": ["A", "B"]}}
    assert several_pending == ["lib.t.code IN &X, &Y"]
    assert macro_first == {"lib.t": {"code": ["B"]}}
    assert macro_first_pending == ["lib.t.code IN &X"]


def test_no_in_y_expresiones_no_se_inventan_como_literales():
    not_in, _ = valores_exigidos(
        "proc sql; select t.x from lib.t t where t.x not in ('A','B'); quit;"
    )
    expression, _ = valores_exigidos(
        "proc sql; select t.x from lib.t t where t.x=2+3; quit;"
    )
    assert not_in == {}
    assert expression == {}


def test_negacion_de_un_predicado_no_crea_un_valor_exigido():
    required, _ = valores_exigidos(
        "proc sql; select t.x from lib.t t where not (t.x='A'); quit;"
    )
    assert required == {}


def test_valores_exigidos_tambien_lee_on_y_resuelve_alias_multiple():
    text = """
    proc sql;
      select a.id
      from lib.a as a inner join lib.b b
        on a.status = 'Y' and b.kind in ('x', 'y');
    quit;
    """
    required, dynamic = valores_exigidos(text)
    assert required == {"lib.a": {"status": ["Y"]}, "lib.b": {"kind": ["x", "y"]}}
    assert dynamic == []


def test_alias_reutilizado_en_subconsulta_no_se_atribuye_a_tabla_interior():
    text = """
    proc sql;
      select a.id from lib.a a where a.status='Y'
        and exists (select 1 from lib.b a where a.kind='X');
    quit;
    """
    required, _ = valores_exigidos(text)
    assert required.get("lib.b", {}).get("status") != ["Y"]


def test_fuentes_separadas_por_coma_no_resuelven_predicado_ambiguo():
    req = requisitos_de_rebanada(
        "proc sql; select a.id from lib.a a, lib.b b where status='X'; quit;"
    )
    assert set(req.tablas_base) == {"lib.a", "lib.b"}
    assert req.exigidos == {}


def test_sql_passthrough_usa_el_sql_interno_sin_fuente_connection_ficticia():
    req = requisitos_de_rebanada(
        "proc sql; select * from connection to impala "
        "(select x from lib.t where x=1); quit;"
    )
    assert req.exigidos == {"lib.t": {"x": ["1"]}}
    assert "work.connection" not in req.tablas_work_externas
    assert "work.connection" not in req.tablas_base


def test_filtro_sin_alias_solo_se_asigna_a_una_fuente_unica():
    one, _ = valores_exigidos("proc sql; select id from lib.t where id=3; quit;")
    many, _ = valores_exigidos(
        "proc sql; select a.id from lib.a a join lib.b b where status='x'; quit;"
    )
    assert one == {"lib.t": {"id": ["3"]}}
    assert many == {}


def test_requisitos_separa_importaciones_productores_y_work_externo():
    text = """
    proc import datafile='/x/a.csv' out=WORK.a dbms=dlm replace; run;
    data WORK.b; set WORK.a; run;
    proc sql; create table WORK.c as select k from WORK.z; quit;
    """
    req = requisitos_de_rebanada(text)
    assert req.archivos == ["/x/a.csv"]
    assert req.tablas_work_externas == {"work.z": ["k"]}
    assert "work.a" not in req.tablas_work_externas
    assert "work.b" not in req.tablas_work_externas
    assert "work.c" not in req.tablas_work_externas


def test_requisitos_conserva_entrada_work_que_se_sobrescribe():
    req = requisitos_de_rebanada("data work.t; set work.t; run;")
    assert "work.t" in req.tablas_work_externas


def test_normaliza_a_work_lecturas_sas_sin_biblioteca():
    data_step = requisitos_de_rebanada("data t; set t; run;")
    sql = requisitos_de_rebanada("proc sql; select x from t; quit;")
    assert "work.t" in data_step.tablas_work_externas
    assert sql.tablas_work_externas == {"work.t": ["x"]}
    assert sql.tablas_base == {}


def test_requisitos_identifica_tabla_local_configurada():
    text = """
    data work.cars_poc; set sashelp.cars; run;
    proc sql; select c.make from work.cars_poc c; quit;
    """
    req = requisitos_de_rebanada(text)
    assert req.tablas_locales == {"sashelp.cars": ["make"]}
    assert req.tablas_base == {}


def test_filtros_de_tablas_producidas_no_piden_entrada_de_manifiesto(tmp_path):
    req = requisitos_de_rebanada(
        "data work.c; set sashelp.cars; run; "
        "proc sql; select c.make from work.c c where c.make='A'; quit;"
    )
    assert req.exigidos == {"work.c": {"make": ["A"]}}
    assert req.tablas_work_externas == {}
    assert generar_entradas(req, {}, Manifiesto(1, {}), tmp_path) == []
    assert list(tmp_path.iterdir()) == []


def test_clasifica_tabla_local_desde_raiz_del_proyecto(tmp_path, monkeypatch):
    (tmp_path / "env").mkdir()
    (tmp_path / "env" / "tablas_locales.json").write_text(
        '{"_nota":"fixture local", "local.libros": {"archivo":"libros.csv"}}',
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    req = requisitos_de_rebanada("data work.c; set local.libros; run;")
    assert req.tablas_locales == {"local.libros": []}
