"""Pruebas de los casos L4 a L6: regeneración reproducible, expansor de macros, referencia de
DATA step (MERGE con la documentación de SAS) y coherencia de los `caso.yaml` con los programas.

Las pruebas del expansor usan programas pequeños en `tmp_path`. La regeneración copia los
programas del corpus real a una carpeta temporal y comprueba que el generador da los mismos bytes.
"""

from __future__ import annotations

import filecmp
import shutil
import sys
from pathlib import Path

import pytest

from sgm.frontend.macros import MacroDynamic
from sgm.frontend.program import analyze_program
from sgm.frontend.steps_tipos import ProcSql

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))

from corpus_lib import referencia_datastep as ref  # noqa: E402
from corpus_lib.caso import cargar_caso  # noqa: E402
from corpus_lib.expansor_macros import ErrorMacro, expandir  # noqa: E402
from corpus_lib.generar_entradas_l4l6 import (  # noqa: E402
    ESPECIFICACIONES,
    generar_todo,
)
from corpus_lib.invariantes import comprobar  # noqa: E402

CORPUS = REPO / "tests" / "corpus"
NIVELES = ("L4", "L5", "L6")


def _filas(texto: str) -> list[dict]:
    """Tabla pequeña escrita como texto: primera línea con nombres de columna, separados por coma."""
    lineas = [linea for linea in texto.strip().splitlines()]
    columnas = lineas[0].split(",")
    return [dict(zip(columnas, linea.split(","), strict=True)) for linea in lineas[1:]]


def _todos_los_casos() -> list[tuple[str, str]]:
    return [
        (nivel, nombre)
        for nivel, especificaciones in ESPECIFICACIONES.items()
        for nombre in especificaciones
    ]


# --- Regeneración reproducible -------------------------------------------------------------


def test_regeneracion_da_los_mismos_bytes(tmp_path: Path) -> None:
    """Generar en una copia de los programas reproduce exactamente los archivos del corpus."""
    copia = tmp_path / "corpus"
    for nivel in NIVELES:
        shutil.copytree(CORPUS / nivel, copia / nivel)
    generados = generar_todo(copia)
    assert generados, "el generador no escribió nada"
    for ruta in generados:
        relativa = ruta.relative_to(copia)
        original = CORPUS / relativa
        assert original.exists(), f"falta el archivo del corpus: {relativa}"
        assert filecmp.cmp(ruta, original, shallow=False), f"difiere: {relativa}"


@pytest.mark.parametrize(("nivel", "nombre"), _todos_los_casos())
def test_caso_carga_y_coincide_con_su_especificacion(nivel: str, nombre: str) -> None:
    """Cada caso L4-L6 carga con su `caso.yaml` y su estado es el de la especificación."""
    caso = cargar_caso(CORPUS / nivel / nombre)
    spec = ESPECIFICACIONES[nivel][nombre]
    if "pendiente" in spec:
        assert caso.estado == "pendiente"
        assert not (caso.directorio / "esperado").exists()
    elif spec.get("pendiente_revision"):
        assert caso.estado == "pendiente_revision"
        assert caso.razonamiento
    else:
        assert caso.estado == "traducible"


@pytest.mark.parametrize(("nivel", "nombre"), _todos_los_casos())
def test_invariantes_se_cumplen_sobre_esperado_y_entradas(nivel: str, nombre: str) -> None:
    """Las invariantes del caso se cumplen con los CSV de `esperado/` y `entradas/`."""
    caso = cargar_caso(CORPUS / nivel / nombre)
    if not caso.invariantes:
        pytest.skip("el caso no declara invariantes")
    carpetas = [caso.esperado, caso.entradas]
    fallos = comprobar(list(caso.invariantes), carpetas, caso.tolerancia)
    assert fallos == []


@pytest.mark.parametrize(("nivel", "nombre"), _todos_los_casos())
def test_asignaciones_del_programa_estan_en_el_sas(nivel: str, nombre: str) -> None:
    """Cada asignación de la especificación (L4) aparece tal cual en `programa.sas`."""
    if nivel != "L4":
        pytest.skip("solo L4 declara asignaciones de DATA step")
    spec = ESPECIFICACIONES[nivel][nombre]
    programa = (CORPUS / nivel / nombre / "programa.sas").read_text(encoding="utf-8")
    for _variable, _columna, _pasos, texto_sas in spec["asignaciones"]:
        assert texto_sas in programa, f"no está en el programa: {texto_sas}"


def test_l5_programa_expandido_es_la_expansion_del_programa() -> None:
    """El `programa_expandido.sas` guardado sale de expandir el `programa.sas` con su `INTO`."""
    for nombre in ESPECIFICACIONES["L5"]:
        caso = CORPUS / "L5" / nombre
        fuente = (caso / "programa.sas").read_text(encoding="utf-8")
        guardado = (caso / "programa_expandido.sas").read_text(encoding="utf-8")
        into = {}
        spec = ESPECIFICACIONES["L5"][nombre]
        for variable, (tabla, columna) in spec.get("into", {}).items():
            columnas, filas = spec["entradas"][tabla]
            into[variable] = str(filas[0][columnas.index(columna)])
        assert expandir(fuente, into) == guardado, nombre


def test_l5_06_sysfunc_upcase_expands_in_frontend() -> None:
    """El frontend resuelve el UPCASE constante antes de analizar el SQL del caso L5-06."""
    case_dir = CORPUS / "L5" / "l5_06_sysfunc_upcase"
    source = (case_dir / "programa.sas").read_text(encoding="utf-8")
    analysis = analyze_program({"l5_06.sas": source})

    sql_text = "\n".join(
        statement.text
        for entry in analysis.items
        if isinstance(entry.item, ProcSql)
        for statement in entry.item.statements
    )

    assert not any(isinstance(entry.item, MacroDynamic) for entry in analysis.items)
    assert "CREATE TABLE WORK.RES_LEALTAD AS" in sql_text
    assert "FROM WORK.DATOS_LEALTAD" in sql_text


# --- Expansor de macros --------------------------------------------------------------------


def test_expansor_resuelve_let_y_ampersand() -> None:
    texto = (
        "%let PRODUCTO=LEALTAD;\nCREATE TABLE WORK.RES_&PRODUCTO. AS SELECT * FROM DATOS_&PRODUCTO;"
    )
    assert expandir(texto) == "\nCREATE TABLE WORK.RES_LEALTAD AS SELECT * FROM DATOS_LEALTAD;"


def test_expansor_macro_con_parametros_y_llamada() -> None:
    texto = "%macro t(a, b);\nSELECT &a, &b;\n%mend t;\n%t(X, 2);"
    assert expandir(texto).strip() == "SELECT X, 2;"


def test_expansor_if_then_else_con_do() -> None:
    texto = "%let T=B;\n%if &T = A %then %do;\nRAMA_A;\n%end;\n%else %do;\nRAMA_B;\n%end;"
    assert expandir(texto).strip() == "RAMA_B;"


def test_expansor_do_iterativo_genera_una_vuelta_por_indice() -> None:
    texto = "%do i = 1 %to 3;\nPARTE_&i.;\n%end;"
    assert expandir(texto).split() == ["PARTE_1;", "PARTE_2;", "PARTE_3;"]


def test_expansor_eval_y_str_y_sysfunc() -> None:
    texto = (
        "%let LIMITE=%eval(100*2+50);\n%let F=%str(A = 'B');\n"
        "%let P=%sysfunc(upcase(lealtad));\nX &LIMITE &F &P;"
    )
    assert expandir(texto).strip() == "X 250 A = 'B' LEALTAD;"


def test_expansor_no_resuelve_dentro_de_comilla_simple_ni_comentario() -> None:
    texto = "%let V=1;\n'&V' /* &V */ \"&V\""
    assert expandir(texto) == "\n'&V' /* &V */ \"1\""


def test_expansor_into_toma_el_valor_dado_y_quita_la_sentencia() -> None:
    texto = "PROC SQL;\nSELECT AÑO INTO :ANIO FROM WORK.VALIDACION;\nQUIT;\nX &ANIO;"
    assert expandir(texto, {"ANIO": "2026"}).split() == ["PROC", "SQL;", "QUIT;", "X", "2026;"]


def test_expansor_rechaza_lo_no_soportado() -> None:
    with pytest.raises(ErrorMacro):
        expandir("X &NO_EXISTE;")
    with pytest.raises(ErrorMacro):
        expandir("%macro t(a);\n%mend t;\n%t(1, 2);")
    with pytest.raises(ErrorMacro):
        expandir("%let X=%eval(2/1);")


# --- Referencia de DATA step (MERGE y documentación) ----------------------------------------


def test_merge_muchos_a_muchos_coincide_con_el_ejemplo_de_la_documentacion() -> None:
    """KB 24752 de SAS: 7 filas, sin producto cartesiano, con los valores retenidos."""
    one = _filas("id,fruit\na,apple\na,apricot\nb,banana\nc,coconut\nc,cherry\nc,crabapple")
    two = _filas("id,color\na,amber\nb,brown\nb,black\nc,cocoa\nc,cream")
    salida = ref.merge_by([one, two], ["id"])
    esperado = [
        ("a", "apple", "amber"),
        ("a", "apricot", "amber"),
        ("b", "banana", "brown"),
        ("b", "banana", "black"),
        ("c", "coconut", "cocoa"),
        ("c", "cherry", "cream"),
        ("c", "crabapple", "cream"),
    ]
    assert [(f["id"], f["fruit"], f["color"]) for f in salida] == esperado


def test_merge_filas_son_la_suma_de_los_maximos_por_grupo() -> None:
    """Regla de la documentación de MERGE: suma del máximo de observaciones por grupo."""
    a = _filas("k,x\n1,p\n1,q\n2,r")
    b = _filas("k,y\n1,s\n2,t\n2,u\n2,v")
    assert len(ref.merge_by([a, b], ["k"])) == 2 + 3


def test_merge_in_marca_el_origen_de_cada_llave() -> None:
    izquierda = _filas("k,x\n1,a\n2,b")
    derecha = _filas("k,y\n2,c\n3,d")
    salida = ref.merge_by([izquierda, derecha], ["k"], ["EN_A", "EN_B"])
    marcas = [(f["k"], f["EN_A"], f["EN_B"]) for f in salida]
    assert marcas == [("1", 1, 0), ("2", 1, 1), ("3", 0, 1)]


def test_merge_rechaza_entrada_desordenada() -> None:
    desordenada = _filas("k,x\n2,a\n1,b")
    with pytest.raises(ValueError, match="no está ordenada"):
        ref.merge_by([desordenada, _filas("k,y\n1,z")], ["k"])


def test_first_last_marca_el_primer_y_ultimo_de_cada_grupo() -> None:
    filas = _filas("g,v\nA,1\nA,2\nB,3")
    marcadas = ref.marcas_first_last(filas, ["g"])
    assert [(f["FIRST.g"], f["LAST.g"]) for f in marcadas] == [(1, 0), (0, 1), (1, 1)]


def test_acumulado_se_reinicia_en_first() -> None:
    filas = [{"g": "A", "v": 5}, {"g": "A", "v": 10}, {"g": "B", "v": 2}]
    salida = ref.acumulado_por_grupo(filas, ["g"], "v", "ACUM")
    assert [f["ACUM"] for f in salida] == [5, 15, 2]


def test_nodupkey_conserva_la_primera_fila_de_cada_llave() -> None:
    filas = [{"k": 3, "t": "c1"}, {"k": 1, "t": "a1"}, {"k": 3, "t": "c2"}, {"k": 1, "t": "a2"}]
    salida = ref.proc_sort(filas, ["k"], nodupkey=True)
    assert salida == [{"k": 1, "t": "a1"}, {"k": 3, "t": "c1"}]


def test_nodup_quita_solo_los_registros_identicos() -> None:
    filas = [{"k": 1, "t": "A"}, {"k": 1, "t": "A"}, {"k": 1, "t": "B"}]
    assert ref.proc_sort_nodup(filas, ["k", "t"]) == [{"k": 1, "t": "A"}, {"k": 1, "t": "B"}]


def test_ultima_de_grupo_conserva_el_ultimo() -> None:
    filas = [{"k": 1, "v": 10}, {"k": 1, "v": 30}, {"k": 2, "v": 5}]
    assert ref.ultima_de_grupo(filas, ["k"]) == [{"k": 1, "v": 30}, {"k": 2, "v": 5}]
