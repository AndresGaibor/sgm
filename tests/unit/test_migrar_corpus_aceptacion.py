"""Aceptación de `sgm migrar` sobre el corpus: nada falla, nada se pierde y nada se inventa.

Cuatro propiedades, y cada una cubre una forma distinta de perder información:

1. **Nada falla.** Los 190 programas de `tests/fixtures/sas` se migran sin una excepción y con su
   `pendientes.md` escrito. Es la prueba de la instrucción del usuario: la herramienta no revienta.
2. **Nada se pierde.** Cada operador del plan quedó visitado, y el que no se plegó sobre otro dejó su
   línea en la traza o en un pendiente. Un operador sin nodo y sin pendiente es un paso del SAS que
   desapareció sin que nadie lo diga.
3. **Nada se inventa.** Los casos con pendientes de traducción son **exactamente** los de la lista
   viva `tests/corpus/migrar_pendientes.yaml`, y la lista no guarda casos ya resueltos.
4. **Los Jobs abren.** `validar_job` no devuelve nada en los 101 casos.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from pathlib import Path

import pytest
import yaml

from sgm.cli_migrar import ResultadoMigrar, migrar
from sgm.compile import compile_file, project_base
from sgm.frontend.program import analyze_program
from sgm.ir.desplegar import plan_desplegado
from sgm.ir.models import Plan
from sgm.migrar.esquemas import esquemas_de_entrada
from sgm.talend_item.desde_plan import plan_a_jobs
from sgm.talend_item.validador import validar_job

RAIZ = Path(__file__).resolve().parents[1]
CORPUS = RAIZ / "corpus"
FIXTURES = RAIZ / "fixtures" / "sas"
LISTA = CORPUS / "migrar_pendientes.yaml"

# El tipo sin demostrar no es una pérdida de traducción: sin catálogo del entorno no hay tipo que
# demostrar, el Job se ejecuta igual con `String`, y contarlo dejaría los 101 casos en la lista para
# siempre. Lo que cuenta es lo que no se tradujo. El porqué está en el encabezado del YAML.
NOTAS = frozenset({"P-TIPO-DESCONOCIDO", "P-CONFIGURACION-RESUELTA"})
NIVELES = ("L0", "L1", "L2", "L3", "L4", "L5", "L6")


def _casos() -> list[Path]:
    return [
        caso
        for nivel in NIVELES
        for caso in sorted((CORPUS / nivel).iterdir())
        if (caso / "programa.sas").is_file()
    ]


CASOS = _casos()


def _plan(programa: Path) -> Plan:
    texto = programa.read_text(encoding="utf-8")
    return compile_file(analyze_program({programa.name: texto}), programa.name, project_base()).plan


def _reales(resultado: ResultadoMigrar) -> list:
    """Pendientes que sí son una pérdida de traducción, en el orden en que los lista el informe."""
    reales = [p for p in resultado.pendientes if p.codigo not in NOTAS]
    reales.sort(key=lambda p: (p.linea if p.linea is not None else 10**9, p.codigo, p.mensaje))
    return reales


def _lista() -> dict[str, str]:
    """Caso -> motivo, tal como lo declara el YAML de pendientes vivos."""
    return yaml.safe_load(LISTA.read_text(encoding="utf-8")) or {}


@pytest.fixture(scope="session")
def base(tmp_path_factory) -> Path:
    return tmp_path_factory.mktemp("migrar")


@pytest.fixture(scope="session")
def migrados(base: Path) -> Callable[[Path], ResultadoMigrar]:
    """Migra cada caso la primera vez que se pide: los cuatro usos no repiten el trabajo."""
    hechos: dict[str, ResultadoMigrar] = {}

    def obtener(caso: Path) -> ResultadoMigrar:
        if caso.name not in hechos:
            hechos[caso.name] = migrar(
                caso / "programa.sas", base / caso.name, muestra=caso / "entradas"
            )
        return hechos[caso.name]

    return obtener


@pytest.fixture(scope="session")
def planes() -> Callable[[Path], Plan]:
    hechos: dict[str, Plan] = {}

    def obtener(caso: Path) -> Plan:
        if caso.name not in hechos:
            hechos[caso.name] = _plan(caso / "programa.sas")
        return hechos[caso.name]

    return obtener


def test_robustez_sobre_todo_el_repositorio(tmp_path):
    programas = sorted(FIXTURES.rglob("*.sas"))

    assert len(programas) >= 190, "los programas de referencia del repositorio desaparecieron"
    for posicion, programa in enumerate(programas):
        inicio = time.perf_counter()
        resultado = migrar(programa, tmp_path / str(posicion))
        assert time.perf_counter() - inicio < 60, f"{programa} tardó más de un minuto"
        assert (resultado.carpeta / "pendientes.md").is_file(), programa


@pytest.mark.parametrize("caso", CASOS, ids=[caso.name for caso in CASOS])
def test_ningun_operador_se_pierde(caso, migrados, planes):
    resultado = migrados(caso)
    plan = planes(caso)

    assert resultado.visitados == {op.id for op in plan.graph.operators()}
    cubiertas = {linea for lineas in resultado.traza.values() for linea in lineas}
    cubiertas |= {p.linea for p in resultado.pendientes if p.linea is not None}
    sueltos = [
        (op.id, op.kind, op.evidence[0].line_start if op.evidence else None)
        for op in plan.graph.operators()
        if op.id not in resultado.plegados
        and (not op.evidence or op.evidence[0].line_start not in cubiertas)
    ]
    assert sueltos == []


def test_solo_los_casos_listados_tienen_pendientes(migrados):
    lista = _lista()
    con_pendientes = {}
    for caso in CASOS:
        reales = _reales(migrados(caso))
        if reales:
            con_pendientes[caso.name] = reales[0].codigo

    assert {nombre: codigo for nombre, codigo in con_pendientes.items() if nombre not in lista} == {}
    assert con_pendientes == {nombre: lista[nombre] for nombre in con_pendientes}


def test_la_lista_no_tiene_casos_resueltos(migrados):
    resueltos = []
    for nombre in _lista():
        programa = CORPUS / nombre[:2].upper() / nombre / "programa.sas"
        assert programa.is_file(), f"la lista nombra un caso que no existe: {nombre}"
        if not _reales(migrados(programa.parent)):
            resueltos.append(nombre)

    assert resueltos == [], "quita de tests/corpus/migrar_pendientes.yaml los casos ya resueltos"


def test_todos_los_jobs_son_validos(planes):
    invalidos = {}
    for caso in CASOS:
        plan = planes(caso)
        plan, _ = plan_desplegado(plan)
        tablas, _ = esquemas_de_entrada(plan, {}, caso / "entradas")
        for job in plan_a_jobs(plan, tablas).jobs:
            defectos = validar_job(job)
            if defectos:
                invalidos[f"{caso.name}/{job.nombre}"] = defectos

    assert invalidos == {}
