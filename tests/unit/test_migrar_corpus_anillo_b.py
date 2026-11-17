"""Anillo B del corpus: el intérprete del plan calcula lo mismo que el SAS de referencia.

Para cada caso de `L0`, `L1` y `L2` en estado `traducible` o `revisado`, se ejecuta el plan sobre las
entradas del caso y se compara con `esperado/`, con la tolerancia y el orden que declara su
`caso.yaml`. No se compara con el Job ni con Studio: se compara con el SAS, que es la referencia.

Los casos que el intérprete todavía no sabe ejecutar están en `CONOCIDOS` con el motivo, y se marcan
`xfail(strict=True)`: si uno empieza a pasar, la prueba falla y obliga a quitar la entrada. Así la
lista no envejece en silencio.
"""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from sgm.compile import compile_file, project_base
from sgm.frontend.program import analyze_program
from sgm.migrar.interprete import ejecutar_plan
from sgm.migrar.interprete_file_put import escribir_archivos_plan
from sgm.migrar.preparar_plan import preparar_plan

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))

from corpus_lib import caso as casos  # noqa: E402
from corpus_lib.csv_tabla import Tabla, comparar_con_guardado, leer_entradas  # noqa: E402
from corpus_lib.esperado_archivos import entradas_de_archivos  # noqa: E402

CORPUS = REPO / "tests" / "corpus"
NIVELES = ("L0", "L1", "L2", "L3", "L4", "L5", "L6")
ESTADOS = ("traducible", "revisado")

# Caso -> motivo por el que el intérprete todavía no lo ejecuta. Las entradas son de dos clases: pasos
# que el intérprete no implementa (y que al implementarlos harán fallar la prueba, como debe ser), y
# dos huecos del plan que no son del intérprete y están anotados en PROGRESS.md.
_NO_LO_EJECUTA = "el intérprete no ejecuta el paso '{paso}' todavía"
CONOCIDOS: dict[str, str] = {
    # Huecos del plan, no del intérprete.
    "l2_12_auto_join_misma_ciudad": (
        "el plan pierde el alias del auto-unión: las dos referencias quedan 'id_cliente < id_cliente'"
    ),
    # Pasos que el intérprete todavía no ejecuta, registrados en el anillo A.
    "l3_07_total_origen_y_salida": (
        "tres SELECT con WHERE sobre la misma tabla se funden en un map con ramas sin salidas"
    ),
    "l3_09_conciliacion_diferencia_plantada": "subconsulta escalar dentro del SELECT",
    "l5_08_str_filtro_completo": "la macro variable &FILTRO llega a la expresión sin resolver",
    "l5_09_into_primer_fila": "SELECT INTO deja la macro variable &ANIO sin resolver en la consulta",
}


def _casos():
    for nivel in NIVELES:
        for caso in casos.casos_de_nivel(CORPUS, nivel):
            if caso.estado not in ESTADOS:
                continue
            marca = []
            if caso.nombre in CONOCIDOS:
                marca = [pytest.mark.xfail(strict=True, reason=CONOCIDOS[caso.nombre])]
            yield pytest.param(caso, id=f"{nivel}/{caso.nombre}", marks=marca)


def _entradas(caso) -> dict[str, list[dict]]:
    return {
        nombre: [dict(zip(tabla.columnas, fila, strict=True)) for fila in tabla.filas]
        for nombre, tabla in leer_entradas(caso.entradas).items()
    }


def _infile_no_cargado(operador, entradas: dict[str, list[dict]]) -> bool:
    if not (operador.params.get("infile_statement") and operador.params.get("input_statement")):
        return False
    tabla = str((operador.params.get("outputs") or [""])[0]).casefold().split(".")[-1]
    return tabla not in {nombre.casefold().split(".")[-1] for nombre in entradas}


def _esperado(caso, tabla: str, filas: list[dict]) -> list[str]:
    """Diferencias con `esperado/<tabla>.csv`, con las columnas del archivo esperado."""
    ruta = caso.esperado / f"{tabla}.csv"
    if not ruta.exists():
        return [f"{tabla}: falta {ruta.name}"]
    columnas = ruta.read_text(encoding="utf-8").splitlines()[0].split(",")
    columnas_esperadas = {columna.lower(): columna for columna in columnas}
    diferencias_columnas: list[str] = []
    for numero, fila in enumerate(filas, start=1):
        columnas_obtenidas = {str(columna).lower(): str(columna) for columna in fila}
        faltantes = sorted(
            columnas_esperadas[nombre]
            for nombre in columnas_esperadas.keys() - columnas_obtenidas.keys()
        )
        adicionales = sorted(
            columnas_obtenidas[nombre]
            for nombre in columnas_obtenidas.keys() - columnas_esperadas.keys()
        )
        detalle = []
        if faltantes:
            detalle.append(f"columnas faltantes: {', '.join(faltantes)}")
        if adicionales:
            detalle.append(f"columnas de más: {', '.join(adicionales)}")
        if detalle:
            diferencias_columnas.append(f"fila {numero}, {'; '.join(detalle)}")
    calculada = Tabla(
        columnas,
        [
            tuple(
                next((valor for clave, valor in fila.items() if clave.lower() == columna.lower()), None)
                for columna in columnas
            )
            for fila in filas
        ],
    )
    return diferencias_columnas + comparar_con_guardado(
        ruta,
        calculada,
        caso.tolerancia,
        caso.orden_relevante,
        orden_grupo=getattr(caso, "extra", {}).get("orden_grupo"),
    )


@pytest.mark.parametrize("caso", list(_casos()))
def test_el_interprete_da_lo_que_el_sas(caso):
    analisis = analyze_program({"p.sas": caso.programa.read_text(encoding="utf-8")})
    plan = compile_file(
        analisis,
        "p.sas",
        project_base(),
    ).plan

    entradas = _entradas(caso)
    archivos_salida = caso.extra.get("archivos_salida", ())
    if archivos_salida:
        plan, pendientes = preparar_plan(
            plan,
            texto=caso.programa.read_text(encoding="utf-8"),
            items=analisis.items,
        )
        assert pendientes == []
        origenes = tuple(
            nombre
            for operador in plan.graph.operators()
            if operador.kind == "write_file"
            for nombre in (operador.params.get("inputs") or [])
        )
        origenes_normalizados = {str(nombre).split(".")[-1].casefold() for nombre in origenes}
        entradas = {
            nombre: filas
            for nombre, filas in entradas.items()
            if str(nombre).split(".")[-1].casefold() not in origenes_normalizados
        }
        imports, _ = entradas_de_archivos(plan, caso, salidas=(*caso.salidas, *origenes))
        entradas.update(imports)
    elif any(
        operador.kind == "read_file"
        and (
            operador.params.get("dbms") == "xlsx"
            or operador.params.get("datarow") is not None
            or _infile_no_cargado(operador, entradas)
        )
        for operador in plan.graph.operators()
    ):
        imports, _ = entradas_de_archivos(plan, caso)
        entradas.update(imports)
    salidas = ejecutar_plan(plan, entradas)

    problemas = [
        problema
        for tabla in caso.salidas
        for problema in _esperado(caso, tabla, salidas.get(tabla.lower(), []))
    ]
    if archivos_salida:
        escritos = escribir_archivos_plan(plan, salidas)
        por_nombre = {Path(ruta).name.casefold(): lineas for ruta, lineas in escritos.items()}
        declarados = {Path(nombre).name.casefold() for nombre in archivos_salida}
        if por_nombre.keys() != declarados:
            problemas.append(
                f"archivos generados {sorted(por_nombre)} distintos de declarados {sorted(declarados)}"
            )
        for nombre in archivos_salida:
            lineas = por_nombre.get(Path(nombre).name.casefold())
            if lineas is None:
                continue
            esperado = (caso.esperado / nombre).read_text(encoding="utf-8")
            obtenido = "\n".join(lineas) + ("\n" if lineas else "")
            esperado_normalizado = esperado.replace("\r\n", "\n").replace("\r", "\n")
            if esperado_normalizado != obtenido:
                problemas.append(f"{nombre}: el contenido de archivo difiere del esperado")
    assert problemas == []


def _caso_con_esperado(tmp_path: Path, contenido: str) -> SimpleNamespace:
    (tmp_path / "salida.csv").write_text(contenido, encoding="utf-8")
    return SimpleNamespace(esperado=tmp_path, tolerancia=0, orden_relevante=True)


def test_anillo_b_detecta_columnas_extra_en_cualquier_fila(tmp_path: Path) -> None:
    caso = _caso_con_esperado(tmp_path, "ID\n1\n2\n")

    diferencias = _esperado(caso, "salida", [{"id": "1"}, {"ID": "2", "Extra": "x"}])

    assert diferencias == ["fila 2, columnas de más: Extra"]


def test_anillo_b_detecta_columna_esperada_ausente_con_valor_vacio(tmp_path: Path) -> None:
    caso = _caso_con_esperado(tmp_path, "id,observacion\n1,\n")

    diferencias = _esperado(caso, "salida", [{"id": "1"}])

    assert diferencias == ["fila 1, columnas faltantes: observacion"]


def test_anillo_b_no_infiere_esquema_de_salida_vacia(tmp_path: Path) -> None:
    caso = _caso_con_esperado(tmp_path, "id\n")

    diferencias = _esperado(caso, "salida", [])

    assert diferencias == []
