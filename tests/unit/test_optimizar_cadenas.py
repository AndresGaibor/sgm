"""Fusión de pasos encadenados: cuándo se hace, qué queda escrito y cuándo no se debe hacer."""

from __future__ import annotations

from sgm.compile import compile_file, project_base
from sgm.frontend.program import analyze_program
from sgm.ir.desplegar import plan_desplegado
from sgm.migrar.interprete import ejecutar_plan
from sgm.optimizar import optimizar

VENTAS = [
    {"id": "1", "zona": "N", "monto": "10"},
    {"id": "2", "zona": "S", "monto": "20"},
    {"id": "3", "zona": "N", "monto": "30"},
]
ZONAS = [{"zona": "N", "nombre": "Norte"}]


def _plan(cuerpo: str):
    texto = f"PROC SQL;\n{cuerpo}\nQUIT;\n"
    return compile_file(analyze_program({"p.sas": texto}), "p.sas", project_base()).plan


def _mapas(plan) -> list[dict]:
    return [op.params for op in plan.graph.operators() if op.kind in ("map", "filter", "derive")]


def test_una_columna_calculada_se_sustituye_por_su_expresion():
    plan = _plan(
        "CREATE TABLE WORK.a AS SELECT id, monto * 2 AS doble FROM WORK.ventas WHERE zona = 'N';\n"
        "CREATE TABLE WORK.b AS SELECT id, doble + 1 AS mas FROM WORK.a WHERE doble > 30;"
    )
    optimizado, informe = optimizar(plan)

    assert [d.tabla for d in informe.decisiones] == ["a"]
    (mapa,) = _mapas(optimizado)
    filtros = [p["params"]["expression"] for p in mapa["steps"] if p["kind"] == "filter"]
    assert filtros == ["zona = 'N'", "(monto * 2) > 30"]
    asignaciones = mapa["steps"][-1]["params"]["assignments"]
    assert [(a["target"], a["expression"]) for a in asignaciones] == [
        ("id", "id"),
        ("mas", "(monto * 2) + 1"),
    ]
    assert ejecutar_plan(optimizado, {"ventas": VENTAS})["b"] == [{"id": "3", "mas": "61"}]


def test_el_plan_original_no_se_toca():
    plan = _plan(
        "CREATE TABLE WORK.a AS SELECT id, monto FROM WORK.ventas;\n"
        "CREATE TABLE WORK.b AS SELECT id FROM WORK.a;"
    )
    antes = len(plan.graph)
    optimizado, _ = optimizar(plan)
    assert len(plan.graph) == antes
    assert len(optimizado.graph) < antes


def test_reutilizar_nombre_de_work_no_confunde_las_versiones():
    plan = _plan(
        "CREATE TABLE WORK.temporal AS SELECT id, monto * 2 AS doble FROM WORK.ventas;\n"
        "CREATE TABLE WORK.primera AS SELECT id, doble + 1 AS total FROM WORK.temporal;\n"
        "CREATE TABLE WORK.temporal AS SELECT id FROM WORK.otra;\n"
        "CREATE TABLE WORK.segunda AS SELECT id FROM WORK.temporal;"
    )
    optimizado, informe = optimizar(plan)

    assert [decision.tabla for decision in informe.decisiones] == ["temporal", "temporal"]
    assert ejecutar_plan(
        optimizado, {"ventas": VENTAS, "otra": [{"id": "x"}]}
    )["primera"] == [{"id": "1", "total": "21"}, {"id": "2", "total": "41"}, {"id": "3", "total": "61"}]
    assert ejecutar_plan(
        optimizado, {"ventas": VENTAS, "otra": [{"id": "x"}]}
    )["segunda"] == [{"id": "x"}]


def test_dos_data_steps_aditivos_se_funden_y_conservan_las_columnas():
    plan = compile_file(
        analyze_program(
            {
                "p.sas": "DATA WORK.a; SET WORK.ventas; doble = monto * 2; RUN;\n"
                "DATA WORK.b; SET WORK.a; total = doble + 1; RUN;"
            }
        ),
        "p.sas",
        project_base(),
    ).plan

    optimizado, informe = optimizar(plan)

    assert [decision.tabla for decision in informe.decisiones] == ["a"]
    (mapa,) = _mapas(optimizado)
    asignaciones = mapa["steps"][-1]["params"]["assignments"]
    assert [(item["target"], item["expression"]) for item in asignaciones] == [
        ("doble", "monto * 2"),
        ("total", "(monto * 2) + 1"),
    ]
    assert ejecutar_plan(optimizado, {"ventas": VENTAS})["b"] == [
        {"id": "1", "zona": "N", "monto": "10", "doble": "20", "total": "21"},
        {"id": "2", "zona": "S", "monto": "20", "doble": "40", "total": "41"},
        {"id": "3", "zona": "N", "monto": "30", "doble": "60", "total": "61"},
    ]


def test_data_step_encadenado_aplica_keep_y_rename_en_la_salida():
    programa = (
        "DATA WORK.a; SET WORK.ventas; total = monto * 2; RUN;\n"
        "DATA WORK.b; SET WORK.a; KEEP id total; RENAME total=balance; RUN;"
    )
    plan = compile_file(
        analyze_program({"p.sas": programa}), "p.sas", project_base()
    ).plan

    optimizado, informe = optimizar(plan)

    assert [decision.tabla for decision in informe.decisiones] == ["a"]
    assert ejecutar_plan(optimizado, {"ventas": VENTAS})["b"] == [
        {"id": "1", "balance": "20"},
        {"id": "2", "balance": "40"},
        {"id": "3", "balance": "60"},
    ]


def test_data_step_encadenado_aplica_drop_en_la_salida():
    programa = (
        "DATA WORK.a; SET WORK.ventas; total = monto * 2; RUN;\n"
        "DATA WORK.b; SET WORK.a; DROP zona monto; RUN;"
    )
    plan = compile_file(
        analyze_program({"p.sas": programa}), "p.sas", project_base()
    ).plan

    optimizado, informe = optimizar(plan)

    assert [decision.tabla for decision in informe.decisiones] == ["a"]
    assert ejecutar_plan(optimizado, {"ventas": VENTAS})["b"] == [
        {"id": "1", "total": "20"},
        {"id": "2", "total": "40"},
        {"id": "3", "total": "60"},
    ]


def test_dos_filtros_hermanos_comparten_tmap_con_dos_salidas():
    plan = _plan(
        "CREATE TABLE WORK.norte AS SELECT id, zona FROM WORK.ventas WHERE zona = 'N';\n"
        "CREATE TABLE WORK.sur AS SELECT id, zona FROM WORK.ventas WHERE zona = 'S';"
    )
    plan, _ = plan_desplegado(plan)

    optimizado, informe = optimizar(plan)

    (mapa,) = [op for op in optimizado.graph.operators() if op.kind == "map"]
    assert len(mapa.params["branches"]) == 2
    assert {rama["outputs"][0] for rama in mapa.params["branches"]} == {
        "WORK.norte",
        "WORK.sur",
    }
    assert any(
        decision.regla == "ramificar-transformaciones-hermanas"
        for decision in informe.decisiones
    )
    salidas = ejecutar_plan(optimizado, {"ventas": VENTAS})
    assert salidas["norte"] == [{"id": "1", "zona": "N"}, {"id": "3", "zona": "N"}]
    assert salidas["sur"] == [{"id": "2", "zona": "S"}]


def test_una_intermedia_que_leen_dos_pasos_no_se_funde():
    plan = _plan(
        "CREATE TABLE WORK.a AS SELECT id, monto FROM WORK.ventas WHERE zona = 'N';\n"
        "CREATE TABLE WORK.b AS SELECT id FROM WORK.a;\n"
        "CREATE TABLE WORK.c AS SELECT monto FROM WORK.a;"
    )
    _, informe = optimizar(plan)
    assert informe.decisiones == []


def test_un_filtro_antes_de_un_cruce_externo_por_el_lado_de_consulta_no_se_funde():
    """`zonas` filtrada entra como consulta de un LEFT JOIN: fundir el filtro lo aplicaría después
    del cruce y quitaría las ventas sin zona, que el SAS conserva."""
    plan = _plan(
        "CREATE TABLE WORK.z AS SELECT zona, nombre FROM WORK.zonas WHERE nombre = 'Norte';\n"
        "CREATE TABLE WORK.b AS SELECT v.id, z.nombre FROM WORK.ventas v "
        "LEFT JOIN WORK.z z ON v.zona = z.zona;"
    )
    optimizado, informe = optimizar(plan)
    assert informe.decisiones == []
    assert len(ejecutar_plan(optimizado, {"ventas": VENTAS, "zonas": ZONAS})["b"]) == 3


def test_dos_cruces_en_cascada_quedan_como_dos_lookups_del_mismo_mapa():
    plan = _plan(
        "CREATE TABLE WORK.a AS SELECT v.id, v.zona, v.monto FROM WORK.ventas v "
        "INNER JOIN WORK.zonas z ON v.zona = z.zona;\n"
        "CREATE TABLE WORK.b AS SELECT a.id, c.tipo FROM WORK.a a "
        "INNER JOIN WORK.clases c ON a.id = c.id;"
    )
    optimizado, informe = optimizar(plan)

    assert [d.tabla for d in informe.decisiones] == ["a"]
    (mapa,) = _mapas(optimizado)
    cruces = [p["params"] for p in mapa["steps"] if p["kind"] == "join"]
    assert [c["keys"] for c in cruces] == [
        [["ventas.zona", "zonas.zona"]],
        [["ventas.id", "clases.id"]],
    ]
    salida = ejecutar_plan(
        optimizado, {"ventas": VENTAS, "zonas": ZONAS, "clases": [{"id": "3", "tipo": "X"}]}
    )["b"]
    assert salida == [{"id": "3", "tipo": "X"}]
