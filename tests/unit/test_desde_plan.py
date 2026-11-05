"""Emisor del Job de Talend desde el plan: lectura, `tMap` y escritura, sin ningún YAML.

Las pruebas usan los casos `L2` del corpus tal como los compila el pipeline: si el plan cambia, el
Job cambia con él y la prueba lo dice. Los dos puntos que el plan marca como foco de revisión están
aquí: el faltante de un filtro (en SAS es menor que cualquier número) y un operador que lanza una
excepción (no se lleva el resto del Job).
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from sgm.compile import compile_file, project_base
from sgm.frontend.program import analyze_program
from sgm.ir.models import Column, Plan
from sgm.migrar.esquemas import esquemas_de_entrada
from sgm.talend_item import desde_plan_map
from sgm.talend_item.desde_plan import plan_a_jobs
from sgm.talend_item.modelo import Job

CORPUS = Path(__file__).resolve().parents[1] / "corpus" / "L2"
RAIZ = Path(__file__).resolve().parents[1] / "corpus"

# `WHERE saldo < 500` no está en el corpus L1, que solo compara contra un literal con `>=`. El
# programa es el mínimo que ejercita la comparación de orden con un faltante posible.
CON_SALDO = """PROC IMPORT DATAFILE='.../entradas/clientes.csv' OUT=WORK.CLIENTES DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

PROC SQL;
  CREATE TABLE WORK.morosos AS
  SELECT id_cliente, saldo FROM WORK.clientes
  WHERE saldo < 500;
QUIT;

PROC EXPORT DATA=WORK.morosos OUTFILE='.../salida/morosos.csv' DBMS=CSV REPLACE;
RUN;
"""


def _plan(texto: str) -> Plan:
    return compile_file(analyze_program({"p.sas": texto}), "p.sas", project_base()).plan


def _caso(nombre: str) -> Plan:
    return _plan((CORPUS / nombre / "programa.sas").read_text(encoding="utf-8"))


def _job(plan: Plan, esquemas: dict[str, list[Column]] | None = None) -> Job:
    if esquemas is None:
        esquemas, _ = esquemas_de_entrada(plan, {}, None)
    return plan_a_jobs(plan, esquemas).jobs[0]


def _componentes(job: Job) -> list[str]:
    return [nodo.componente for nodo in job.nodos]


def _tmap(job: Job) -> str:
    return next(nodo.datos for nodo in job.nodos if nodo.componente == "tMap")


def test_un_job_con_cuatro_nodos():
    """Dos lecturas, el `tMap` y la escritura: los `read`/`write` internos no son nodos aparte."""
    job = _job(_caso("l2_01_inner_join_clientes_ventas"))

    assert sorted(_componentes(job)) == [
        "tFileInputDelimited",
        "tFileInputDelimited",
        "tFileOutputDelimited",
        "tMap",
    ]


def test_conexiones_principal_lookup_y_salida():
    job = _job(_caso("l2_01_inner_join_clientes_ventas"))

    flujo = [c for c in job.conexiones if c.estilo == 0]
    lookups = [c for c in job.conexiones if c.estilo == 8]
    assert len(job.conexiones) == 3
    assert len(flujo) == 2  # la principal entra y la salida sale
    assert len(lookups) == 1
    assert lookups[0].conector == "LOOKUP"
    assert lookups[0].destino == "tMap_1"


def test_inner_join_activa_union_interna():
    job = _job(_caso("l2_01_inner_join_clientes_ventas"))

    assert 'name="row2"' in _tmap(job)
    assert 'innerJoin="true"' in _tmap(job)


def test_left_join_no_activa_union_interna():
    job = _job(_caso("l2_02_left_join_con_faltantes"))

    assert 'innerJoin="true"' not in _tmap(job)
    assert 'expression="row1.id_cliente"' in _tmap(job)  # la llave sigue declarada


def test_traza_apunta_a_las_lineas_del_sas():
    plan = _caso("l2_01_inner_join_clientes_ventas")

    traza = plan_a_jobs(plan, esquemas_de_entrada(plan, {}, None)[0]).traza

    assert traza["tMap_1"] == [15, 16, 17, 18, 19, 20, 21]
    assert 16 in traza["tMap_1"]  # la línea del CREATE TABLE


def _filtro_de(job: Job) -> str:
    linea = next(x for x in _tmap(job).splitlines() if "expressionFilter" in x)
    return linea.split('expressionFilter="')[1].split('"')[0]


def test_filtro_con_faltante_es_nulo_seguro():
    """`saldo < 500` es verdadero con `saldo` faltante, como en SAS; en Java un nulo no compara."""
    plan = _plan(CON_SALDO)
    esquema = {"work.clientes": [Column("id_cliente", "Integer"), Column("saldo", "Integer")]}

    job = _job(plan, esquema)
    filtro = _filtro_de(job)

    assert "row1.saldo == null" in filtro
    assert filtro.index("row1.saldo == null") < filtro.index("row1.saldo &lt; 500")


def test_filtro_sobre_texto_comprueba_que_sea_numero():
    """Sin tipo demostrado la columna es texto: el filtro no puede comparar texto con un número."""
    plan = _plan(CON_SALDO)

    job = _job(plan, {"work.clientes": [Column("id_cliente"), Column("saldo")]})
    filtro = _filtro_de(job)

    assert "row1.saldo == null" in filtro
    assert "matches(" in filtro
    assert "Double.parseDouble(row1.saldo)" in filtro


@pytest.mark.skipif(shutil.which("javac") is None, reason="sin JDK para compilar la expresión")
def test_el_filtro_compila_con_javac(tmp_path):
    plan = _plan(CON_SALDO)
    esquema = {"work.clientes": [Column("id_cliente", "Integer"), Column("saldo", "Integer")]}
    filtro = _filtro_de(_job(plan, esquema)).replace("&lt;", "<").replace("&gt;", ">")

    clase = tmp_path / "Prueba.java"
    clase.write_text(
        "public class Prueba {\n"
        "  static class Row { Integer id_cliente; Integer saldo; }\n"
        f"  static boolean filtra(Row row1) {{ return {filtro}; }}\n"
        "  public static void main(String[] a) {\n"
        "    Row nula = new Row();\n"
        "    if (!filtra(nula)) throw new IllegalStateException(\"el faltante debe pasar\");\n"
        "  }\n"
        "}\n",
        encoding="utf-8",
    )
    compilado = subprocess.run(
        ["javac", "-d", str(tmp_path), str(clase)], capture_output=True, text=True
    )
    assert compilado.returncode == 0, compilado.stderr
    ejecutado = subprocess.run(
        ["java", "-cp", str(tmp_path), "Prueba"], capture_output=True, text=True
    )
    assert ejecutado.returncode == 0, ejecutado.stderr


def test_un_select_sin_calificar_arma_el_job_completo():
    """`select a, b from work.clientes`: la columna suelta se resuelve porque hay una sola tabla."""
    plan = _plan((RAIZ / "L1" / "l1_01_select_columnas" / "programa.sas").read_text(encoding="utf-8"))

    resultado = plan_a_jobs(plan, esquemas_de_entrada(plan, {}, None)[0])

    assert resultado.pendientes == []
    assert _componentes(resultado.jobs[0]) == ["tFileInputDelimited", "tMap"]
    assert 'expression="row1.saldo"' in _tmap(resultado.jobs[0])


def test_un_operador_que_falla_no_detiene_a_los_demas(monkeypatch):
    """Un `tMap` que revienta deja su pendiente y el Job conserva lectura y escritura.

    El fallo se provoca en `tmap` —el montaje del nodo— y no en `construir`: así se comprueba lo
    peor, que el nodo no se puede montar, y aun así el esquema de la salida se conoce porque lo
    demuestra el `SELECT`.
    """
    plan = _caso("l2_01_inner_join_clientes_ventas")

    def revienta(*args, **kwargs):
        raise RuntimeError("mapper sin salida")

    monkeypatch.setattr(desde_plan_map, "tmap", revienta)

    resultado = plan_a_jobs(plan, esquemas_de_entrada(plan, {}, None)[0])

    assert sorted(_componentes(resultado.jobs[0])) == [
        "tFileInputDelimited",
        "tFileInputDelimited",
        "tFileOutputDelimited",
    ]
    fallos = [p for p in resultado.pendientes if p.codigo == "P-FALLO-INTERNO"]
    assert len(fallos) == 1
    assert fallos[0].linea == 15
    assert "mapper sin salida" in fallos[0].mensaje
