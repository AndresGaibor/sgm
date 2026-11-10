"""Equivalencia de los planes golden: un cambio solo puede agregar campos documentados.

`test_golden.py` exige igualdad exacta. Esta prueba explica el tipo de cambio: un campo que se
quita o cuyo valor cambia rompe la equivalencia; un campo nuevo solo se acepta si su ruta está en
`CAMPOS_ADITIVOS`, con su motivo. Así una ampliación del plan (p. ej. una nueva clave de
`params`) no se confunde con una regresión de la migración.
"""

import hashlib
import json
from pathlib import Path

import pytest

from sgm.compile import compile_project
from sgm.emit.plan_json import plan_to_dict
from sgm.frontend.splitter import ZERO_WIDTH

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests" / "fixtures" / "sas"
GOLDEN = ROOT / "tests" / "golden"

# Campos que el plan puede ganar sin romper la referencia. Cada uno con su motivo (ver PROGRESS.md).
CAMPOS_ADITIVOS = {
    # Hito 14: candidatas Talend guardadas en `params` de los operadores con expresión traducida.
    "talend_expression_candidates": "candidatas Talend por validar (hito 14)",
    # Hito 104m: `PROC IMPORT` y `PROC EXPORT` llevan sus opciones de archivo en el operador. La
    # firma cambia con ellas (es la llave de las decisiones), y por eso la referencia se regeneró.
    "dbms": "formato del archivo en read_file/write_file (hito 104m, proc p. 1333)",
    "delimiter": "separador declarado en el SAS; `None` si no lo declara (hito 104m, p. 1386)",
    "getnames": "cabecera de la primera fila; `YES` por omisión (hito 104m, p. 1387)",
    "sheet": "hoja del libro de Excel (hito 104m)",
    "guessingrows": "filas que el SAS escanea para tipar (hito 104m, p. 1388)",
    # Hito 104m: el `derive` de un DATA step conserva la fila y le agrega columnas; el de un
    # `SELECT` la reemplaza. La firma cambia con la marca, y por eso la referencia se regeneró.
    "modo": "`agrega` en el derive de un DATA step (hito 104m, DATA step vs SELECT)",
    # Hito 121: `INFILE/INPUT` conservan opciones, campos, fuente y formato inferidos por sintaxis.
    "datafile": "ruta literal de INFILE (hito 121)",
    "file_format": "forma de lectura demostrada por INFILE/INPUT (hito 121)",
    "firstobs": "primera fila de INFILE (hito 121)",
    "infile_line": "línea de INFILE para pendientes de migración (hito 121)",
    "infile_options": "opciones declaradas en INFILE (hito 121)",
    "infile_statement": "sintaxis original de INFILE (hito 121)",
    "input_line": "línea de INPUT para pendientes de migración (hito 121)",
    "input_mode": "modalidad demostrada por INPUT (hito 121)",
    "input_names": "nombres declarados por INPUT, sin inferir tipos (hito 121)",
    "input_statement": "sintaxis original de INPUT (hito 121)",
    "statement": "sentencias originales de lectura (hito 121)",
    "unsupported_options": "opciones INFILE sin equivalencia identificada (hito 121)",
    "group_outputs": "llaves GROUP BY seleccionadas como columnas de salida (hito 129)",
    "output_order": "orden de las columnas del SELECT en la salida agregada (hito 129)",
}

# Cambios intencionales de valor o diagnóstico: se documentan por referencia y ruta para que el
# permiso no cubra otras diferencias. Las referencias exactas también se comprueban en `test_golden.py`.
CAMBIOS_DOCUMENTADOS = {
    "p1_merge_first_last.plan.json": {
        "gaps[2].evidence[0].line_start": "hito 110: conservar solo el origen de la expresión fusionada",
        "gaps[2].evidence[0].line_end": "hito 110: conservar solo el origen de la expresión fusionada",
        "gaps[2].evidence[1]": "hito 110: quitar evidencia ajena a la expresión fusionada",
        "pendientes[2].fuente[0].line_start": "hito 110: conservar solo el origen de la expresión fusionada",
        "pendientes[2].fuente[0].line_end": "hito 110: conservar solo el origen de la expresión fusionada",
        "pendientes[2].fuente[1]": "hito 110: quitar evidencia ajena a la expresión fusionada",
    },
    "client__client_poc.plan.json": {
        "operators[74].params.talend_expression_candidates[0].java": (
            "hito 110: emitir COMPRESS del espacio literal con la rutina Talend de reemplazo"
        ),
        "operators[19].signature": "hito 129: la proyección del agregado forma parte de su firma",
        "operators[24].signature": "hito 129: la proyección del agregado forma parte de su firma",
        "operators[26].signature": "hito 129: la proyección del agregado forma parte de su firma",
        "operators[29].signature": "hito 129: la proyección del agregado forma parte de su firma",
        "operators[31].signature": "hito 129: la proyección del agregado forma parte de su firma",
        "pendientes[33].signature": "hito 129: se precisa la firma dependiente del agregado",
        "pendientes[34].signature": "hito 129: se precisa la firma dependiente del agregado",
        "pendientes[35].signature": "hito 129: se precisa la firma dependiente del agregado",
        "pendientes[36].signature": "hito 129: se precisa la firma dependiente del agregado",
        "pendientes[37].signature": "hito 129: se precisa la firma dependiente del agregado",
        "pending[0].signature": "hito 129: la decisión de salida usa la firma del agregado",
        "pending[1].signature": "hito 129: la decisión de salida usa la firma del agregado",
        "pending[2].signature": "hito 129: la decisión de salida usa la firma del agregado",
        "pending[3].signature": "hito 129: la decisión de salida usa la firma del agregado",
        "pending[4].signature": "hito 129: la decisión de salida usa la firma del agregado",
    },
    "p0_ejemplo_basico.plan.json": {
        "operators[2].signature": "hito 129: la proyección del agregado forma parte de su firma",
        "pendientes[1].signature": "hito 129: se precisa la firma dependiente del agregado",
        "pending[0].signature": "hito 129: la decisión de salida usa la firma del agregado",
    },
    "generalization__etl_archivos_simple.plan.json": {
        "operators[2].signature": "hito 121: INFILE/INPUT pasa a formar parte de la firma",
        "pendientes[5].signature": "hito 121: la firma del hueco de lectura se precisa",
        "pending[1].signature": "hito 121: la decisión del lector usa la firma de INFILE/INPUT",
        "operators[5].status": (
            "hito 124: NODUPKEY queda parcial hasta validar empates estables en tSortRow"
        ),
        "operators[5].notes[0]": (
            "hito 124: explicar por qué la fila conservada no se considera idéntica"
        ),
    },
}

# El plan del cliente contiene un cambio de topología deliberado, no una ampliación de campos:
# MG-P10 añade el orden de proyección de agregados y MG-P13 reconoce cargas Impala antes modeladas
# como pendientes. El cambio desplaza IDs y aristas del grafo completo, por lo que se fija el plan
# revisado por su hash canónico; `test_golden.py` conserva además la comparación exacta.
CAMBIOS_ESTRUCTURALES_DOCUMENTADOS = {
    "client__client_poc.plan.json": "4d30d95add60ceb55efe98897f7cfca640c1731c6305b18a66a6688385c4e98e",
}

CASES = [
    ("p0_ejemplo_basico.sas", "p0_ejemplo_basico.plan.json"),
    ("p1_merge_first_last.sas", "p1_merge_first_last.plan.json"),
    ("generalization/etl_archivos_simple.sas", "generalization__etl_archivos_simple.plan.json"),
    ("client/client_poc.sas", "client__client_poc.plan.json"),
]


def diferencias(esperado, actual, ruta: str = "") -> list[tuple[str, str]]:
    """Lista (ruta, tipo) de cada diferencia entre dos valores JSON.

    Tipos: `quitado` (estaba en la referencia y ya no), `cambiado` (mismo lugar, otro valor) y
    `agregado` (existe solo en el valor actual). Las rutas usan `.` para las claves y `[i]` para
    los elementos de una lista.
    """
    if isinstance(esperado, dict) and isinstance(actual, dict):
        found: list[tuple[str, str]] = []
        for clave in sorted(set(esperado) | set(actual)):
            sub = f"{ruta}.{clave}" if ruta else clave
            if clave not in actual:
                found.append((sub, "quitado"))
            elif clave not in esperado:
                found.append((sub, "agregado"))
            else:
                found += diferencias(esperado[clave], actual[clave], sub)
        return found
    if isinstance(esperado, list) and isinstance(actual, list):
        found = []
        for i in range(max(len(esperado), len(actual))):
            sub = f"{ruta}[{i}]"
            if i >= len(actual):
                found.append((sub, "quitado"))
            elif i >= len(esperado):
                found.append((sub, "agregado"))
            else:
                found += diferencias(esperado[i], actual[i], sub)
        return found
    return [] if esperado == actual else [(ruta, "cambiado")]


def _es_aditivo(ruta: str) -> bool:
    """Una ruta agregada es aceptable si alguno de sus campos está en `CAMPOS_ADITIVOS`.

    Así un campo nuevo documentado puede traer sub-campos (`...talend_expression_candidates[0].java`).
    """
    segmentos = [s.split("[")[0] for s in ruta.split(".")]
    return any(s in CAMPOS_ADITIVOS for s in segmentos)


def test_diferencias_distingue_campo_quitado_cambiado_y_agregado():
    esperado = {"a": 1, "b": {"c": "x"}, "d": [1, 2]}
    actual = {"a": 2, "b": {"c": "x", "nuevo": True}, "d": [1]}

    assert diferencias(esperado, actual) == [
        ("a", "cambiado"),
        ("b.nuevo", "agregado"),
        ("d[1]", "quitado"),
    ]


def test_diferencias_sin_cambios_no_reporta_nada():
    plan = {"graph": {"operators": [{"id": "op1", "params": {"x": [1, 2]}}]}}
    assert diferencias(plan, json.loads(json.dumps(plan))) == []


@pytest.mark.parametrize(("rel", "golden"), CASES)
def test_plan_solo_cambia_por_campos_aditivos_documentados(rel, golden):
    text = (FIXTURES / rel).read_text(encoding="utf-8", errors="replace").replace(ZERO_WIDTH, "")
    compiled, _ = compile_project({rel: text})
    actual = json.loads(json.dumps(plan_to_dict(compiled[rel].plan)))
    esperado = json.loads((GOLDEN / golden).read_text(encoding="utf-8"))

    if golden in CAMBIOS_ESTRUCTURALES_DOCUMENTADOS:
        huella = hashlib.sha256(
            json.dumps(esperado, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            .encode("utf-8")
        ).hexdigest()
        assert huella == CAMBIOS_ESTRUCTURALES_DOCUMENTADOS[golden]
        assert actual == esperado
        return

    cambios = diferencias(esperado, actual)

    permitidos = CAMBIOS_DOCUMENTADOS.get(golden, {})
    quitados_o_cambiados = [
        (ruta, tipo)
        for ruta, tipo in cambios
        if tipo != "agregado" and ruta not in permitidos
    ]
    assert quitados_o_cambiados == []
    no_documentados = [
        ruta for ruta, _tipo in cambios if not _es_aditivo(ruta) and ruta not in permitidos
    ]
    assert no_documentados == []


def test_campo_aditivo_no_documentado_se_reporta():
    """Una clave nueva fuera de `CAMPOS_ADITIVOS` debe fallar la equivalencia."""
    esperado = {"params": {"x": 1}}
    actual = {"params": {"x": 1, "campo_nuevo": 2}}

    cambios = diferencias(esperado, actual)

    assert cambios == [("params.campo_nuevo", "agregado")]
    assert not _es_aditivo("params.campo_nuevo")
