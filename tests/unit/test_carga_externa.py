"""Región de carga externa (R3): la maquinaria completa se absorbe en un único `external_load`.

Los nombres de macros, variables y datasets son aleatorios a propósito: la región se reconoce por
estructura (lanzamiento en segundo plano, espera con conteo de procesos, troceo en sesiones), no
por cómo se llaman las cosas.
"""

from sgm.compile import compile_project

PREPARACION = """
%let qw_origen = WORK.DATOS_ZX;
%let qw_ruta = %sysfunc(cat(%sysfunc(pathname(work)), /));
%let qw_nombre = %scan(&qw_origen, -1, '.');
"""

TROCEO = """
%macro hk_trocea(ruta, tabla, partes);
%let qw_bloques = %sysevalf(&partes/2, ceil);
%do i=1 %to &qw_bloques;
signon sesion&i;
%syslput tabla_k=&tabla / remote = sesion&i;
rsubmit sesion&i wait=no;
data work.trozo&i;
set work.origen;
run;
endrsubmit;
%end;
waitfor _all_ %do i=1 %to &qw_bloques;
sesion&i %end;
signoff _all_;
%let qw_ruta2 = %sysfunc(cat(%sysfunc(pathname(work)), /));
%mend hk_trocea;
"""

LANZAMIENTO = """
%macro hk_lanza;
%global qw_cmd;
%let qw_cmd = cmdtable77;
proc sql noprint;
insert into &qw_cmd values("sh /bin/cargar_zx.sh &qw_ruta &qw_nombre &");
quit;
%mend hk_lanza;
"""

ESPERA_Y_LIMPIEZA = """
%macro hk_espera;
x " nq=5; until [ $nq -eq 0 ]; do nq=$( ps -fea | grep -i cargar_zx | wc -l ); done ";
%mend hk_espera;

%macro hk_limpia;
proc sql noprint;
select count(*) into :qw_filas from work.trozo1;
quit;
proc delete data=work.trozo1;
run;
%mend hk_limpia;
"""

LLAMADAS = """
%hk_trocea(&qw_ruta, &qw_nombre, 3);
%hk_lanza;
%hk_espera;
%hk_limpia;
"""


def _program(extra: str = "", llamadas: str = LLAMADAS) -> str:
    return PREPARACION + TROCEO + LANZAMIENTO + ESPERA_Y_LIMPIEZA + llamadas + extra


def _line_of(program: str, prefix: str) -> int:
    """Número de línea (desde 1) de la primera línea que empieza por `prefix`."""
    return next(i for i, line in enumerate(program.splitlines(), 1) if line.startswith(prefix))


def _loads(compiled):
    return [op for op in compiled.plan.graph.operators() if op.kind == "external_load"]


def _gap_text(compiled) -> str:
    return " ".join(g.signature + " " + g.text for g in compiled.plan.gaps)


def test_la_maquinaria_completa_se_absorbe_en_una_sola_carga():
    program = _program()
    compiled, _ = compile_project({"p.sas": program})
    loads = _loads(compiled["p.sas"])
    assert len(loads) == 1
    lines = {e.line_start for e in loads[0].evidence}
    assert _line_of(program, "%let qw_origen") in lines  # arranca en la preparación
    assert _line_of(program, "proc delete") in lines  # llega hasta la limpieza
    assert loads[0].params["verify_count"] is True  # hay un select count(*) dentro de la región


def test_no_quedan_huecos_de_troceo_ni_de_preparacion_en_la_region():
    compiled, _ = compile_project({"p.sas": _program()})
    text = _gap_text(compiled["p.sas"])
    for marker in ("pathname", "countw", "sysevalf", "sesion", "_all_", "waitfor"):
        assert marker not in text.lower(), marker


def test_una_variable_usada_fuera_de_la_carga_no_se_lleva_con_ella():
    # Un DATA step que lee qw_ruta después de la carga es cálculo, no fontanería: no entra.
    program = _program(extra='data work.fuera;\nx = "&qw_ruta";\nrun;\n')
    compiled, _ = compile_project({"p.sas": program})
    lines = {e.line_start for e in _loads(compiled["p.sas"])[0].evidence}
    assert _line_of(program, "%let qw_ruta") not in lines
    assert _line_of(program, "data work.fuera") not in lines


def test_sin_lanzamiento_no_hay_carga():
    compiled, _ = compile_project(
        {"p.sas": _program(llamadas=LLAMADAS.replace("%hk_lanza;\n", ""))}
    )
    assert _loads(compiled["p.sas"]) == []


def test_dos_cargas_en_el_mismo_programa_son_dos_regiones():
    compiled, _ = compile_project({"p.sas": _program() + _program()})
    assert len(_loads(compiled["p.sas"])) == 2


def test_asignacion_a_una_columna_x_no_es_comando_de_shell():
    """`x = ...;` dentro de un DATA step no es la sentencia X de SAS (comando del sistema)."""
    compiled, _ = compile_project({"p.sas": "data work.a;\nx = 1;\nrun;\n"})
    shell = [op for op in compiled["p.sas"].plan.graph.operators() if op.params.get("plumbing")]
    assert not any(op.params.get("plumbing") == "shell_auxiliar" for op in shell)
