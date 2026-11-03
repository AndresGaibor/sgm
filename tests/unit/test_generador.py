"""Generador de joblets por grupo: regiones por macro repetida, grupos y contextos por miembro."""

from __future__ import annotations

import json

from sgm.compile import compile_project
from sgm.facts.project import facts_for_project
from sgm.generador import (
    UMBRAL_DE_AGRUPACION,
    diseno_del_job,
    joblets_por_grupo,
    marcador_de_regiones,
)


def _bloque(nombre: str, tablas: list[str]) -> str:
    cuerpo = "".join(f"data work.{t}; set work.{nombre}_{t}; run;\n" for t in tablas)
    return f"%macro bloque;\n{cuerpo}%mend bloque;\n"


def test_regiones_son_definiciones_de_la_macro_mas_repetida() -> None:
    texto = "%macro otra; %mend otra;\n" + "".join(_bloque(f"a{i}", ["x"]) for i in range(3))
    inicios = marcador_de_regiones(texto.splitlines())
    assert len(inicios) == 3


def test_joblet_por_grupo_con_contexto_por_miembro() -> None:
    ventas = ["ventas_detalle", "ventas_resumen", "ventas_cierre"]
    texto = "".join(_bloque(f"a{i}", ventas) for i in range(3))
    compilados, _ = compile_project({"p.sas": texto})
    plan = compilados["p.sas"].plan
    hechos = facts_for_project({"p.sas": texto})["p.sas"]
    joblets = joblets_por_grupo(list(plan.graph.operators()), hechos, texto.splitlines())
    assert len(joblets) == 1
    assert joblets[0]["miembros"] == 3
    assert len(joblets[0]["contextos"]) == 3


# Dos regiones con Jaccard 0,25 sobre su vocabulario: agrupan con 0,2 y no con 0,3.
REGIONES_UMBRAL = """%macro bloque;
data work.t_aaa; set work.t_bbb; run;
data work.t_ccc; set work.t_ddd; run;
data work.t_eee; set work.t_aaa; run;
%mend bloque;
%macro bloque;
data work.t_aaa; set work.t_fff; run;
data work.t_ggg; set work.t_hhh; run;
data work.t_bbb; set work.t_aaa; run;
%mend bloque;
"""


def test_umbral_de_agrupacion_0_2_une_lo_que_0_3_dejaria_suelto() -> None:
    from sgm.agrupacion import agrupar, inicios_de, palabras_por_region

    lineas = REGIONES_UMBRAL.splitlines()
    hechos = facts_for_project({"p.sas": REGIONES_UMBRAL})["p.sas"]
    inicios = inicios_de(lineas, r"^\s*%macro\s+bloque\b")
    palabras = palabras_por_region(hechos, inicios)
    assert UMBRAL_DE_AGRUPACION == 0.2
    assert [len(g) for g in agrupar(palabras, 0.2).grupos] == [2]
    assert agrupar(palabras, 0.3).grupos == [] or all(
        len(g) == 1 for g in agrupar(palabras, 0.3).grupos
    )


ENCABEZADO = """%let server = anfitrion01 7551;
options remote=server comamid=tcp;
proc pwencode in='clave-del-programa';
run;
proc sql;
connect to impala (dsn = IMPALAX);
select anio into: anio from work.validacion;
disconnect from impala;
quit;
data work.entrada; set work.fuente; run;
%macro bloque;
data work.ventas_a; set work.ventas_a_origen; run;
%mend bloque;
%macro bloque;
data work.ventas_b; set work.ventas_b_origen; run;
%mend bloque;
"""


def _diseno(texto: str) -> dict:
    plan = compile_project({"p.sas": texto})[0]["p.sas"].plan
    hechos = facts_for_project({"p.sas": texto})["p.sas"]
    return diseno_del_job(list(plan.graph.operators()), hechos, texto.splitlines())


def test_contexto_del_encabezado_sin_contrasena_en_claro() -> None:
    diseno = _diseno(ENCABEZADO)
    variables = {v["nombre"]: v for v in diseno["contexto"]["variables"]}
    assert variables["servidor_remoto"]["valor"] == ["anfitrion01"]
    assert variables["base_de_datos"]["valor"][0].upper() == "IMPALA"
    assert variables["credencial"]["valor"] == "***"
    assert variables["anio"]["valor"] is None
    assert variables["anio"]["pendiente"]["motivo"] == "DATO_NO_EN_ARCHIVO"
    assert "clave-del-programa" not in json.dumps(diseno, ensure_ascii=False)


def test_contexto_cuenta_los_operadores_de_entorno() -> None:
    # `%let`, `options remote=` y `pwencode`: tres sentencias de entorno, ninguna de datos.
    assert _diseno(ENCABEZADO)["contexto"]["operadores"] == 3


def test_job_padre_suma_la_llamada_de_contexto_a_sus_nodos() -> None:
    padre = _diseno(ENCABEZADO)["job_padre"]
    assert padre["joblet_de_contexto"] == "jl_contexto"
    assert padre["nodos"] == (
        len(padre["llamadas"])
        + 1
        + padre["componentes_del_encabezado"]
        + padre["componentes_sueltos"]
    )
