"""Pruebas de la exportación a XLSX sin asumir semántica SAS no documentada."""

from __future__ import annotations

from pathlib import Path

from sgm.cli_migrar import migrar
from sgm.compile import compile_file, project_base
from sgm.frontend.program import analyze_program
from sgm.migrar.escritor_xlsx import escribir_hoja
from sgm.migrar.lector_xlsx import leer_xlsx
from sgm.talend_item import desde_plan_nodos_escritura as emisor_archivos
from sgm.talend_item.modelo import Columna

nodo_escritura = emisor_archivos.nodo_escritura
REPO = Path(__file__).resolve().parents[2]


def _operador_exportacion(texto: str):
    plan = compile_file(analyze_program({"p.sas": texto}), "p.sas", project_base()).plan
    return next(op for op in plan.graph.operators() if op.kind == "write_file")


def test_escribe_y_lee_hoja_xlsx_con_encabezado(tmp_path: Path) -> None:
    ruta = tmp_path / "salida.xlsx"
    escribir_hoja(ruta, "Resumen", ["sku", "unidades"], [["A-1", 2], ["B-2", 3]])

    assert leer_xlsx(ruta, "Resumen") == (
        ["sku", "unidades"],
        [["A-1", "2"], ["B-2", "3"]],
    )


def test_escribe_hoja_xlsx_sin_encabezado(tmp_path: Path) -> None:
    ruta = tmp_path / "sin_encabezado.xlsx"
    escribir_hoja(ruta, "Datos", None, [["A-1", 2]])

    assert leer_xlsx(ruta, "Datos", getnames=False) == (["A", "B"], [["A-1", "2"]])


def test_exportacion_conserva_sheet_y_putnames_explicito_en_el_ir() -> None:
    operador = _operador_exportacion(
        """PROC EXPORT DATA=WORK.ventas OUTFILE='salida.xlsx' DBMS=XLSX REPLACE;
  SHEET='Resumen';
  PUTNAMES=NO;
RUN;"""
    )

    assert operador.params["dbms"] == "xlsx"
    assert operador.params["sheet"] == "Resumen"
    assert operador.params["putnames"] is False


def test_exportacion_delimitada_conserva_putnames() -> None:
    operador = _operador_exportacion(
        "PROC EXPORT DATA=WORK.ventas OUTFILE='salida.csv' DBMS=CSV; PUTNAMES=NO; RUN;"
    )

    assert operador.params["putnames"] is False


def test_exportacion_delimitada_usa_putnames_yes_por_omision() -> None:
    operador = _operador_exportacion(
        "PROC EXPORT DATA=WORK.ventas OUTFILE='salida.csv' DBMS=CSV; RUN;"
    )

    assert operador.params.get("putnames", True) is True


def test_emisor_delimitado_respeta_putnames_no() -> None:
    operador = _operador_exportacion(
        "PROC EXPORT DATA=WORK.ventas OUTFILE='salida.csv' DBMS=CSV; "
        "PUTNAMES=NO; RUN;"
    )

    resultado = nodo_escritura(
        operador, [Columna("sku", "id_String")], "tFileOutputDelimited_1", 0, 0
    )

    assert resultado.nodo is not None
    assert next(
        fila[2]
        for fila in resultado.nodo.parametros
        if isinstance(fila, tuple) and fila[1] == "INCLUDEHEADER"
    ) == "false"


def test_exportar_xlsx_no_emite_sin_semantica_de_encabezado_aun_con_plantilla(monkeypatch) -> None:
    monkeypatch.setattr(emisor_archivos, "disponibles", lambda: {"tFileOutputExcel"})
    operador = _operador_exportacion(
        "PROC EXPORT DATA=WORK.ventas OUTFILE='salida.xlsx' DBMS=XLSX; "
        "SHEET='Resumen'; RUN;"
    )

    resultado = nodo_escritura(
        operador, [Columna("sku", "id_String")], "tFileOutputExcel_1", 0, 0
    )

    assert resultado.nodo is None
    assert [p.codigo for p in resultado.pendientes] == [
        "P-EXPORT-EXCEL-CABECERA-SIN-REFERENCIA"
    ]


def test_exportar_xlsx_marca_putnames_no_documentado() -> None:
    operador = _operador_exportacion(
        "PROC EXPORT DATA=WORK.ventas OUTFILE='salida.xlsx' DBMS=XLSX; "
        "PUTNAMES=NO; RUN;"
    )

    resultado = nodo_escritura(
        operador, [Columna("sku", "id_String")], "tFileOutputExcel_1", 0, 0
    )

    assert resultado.nodo is None
    assert {p.codigo for p in resultado.pendientes} == {
        "P-COMPONENTE-SIN-PLANTILLA",
        "P-PUTNAMES-EXCEL-SIN-SOPORTE",
    }


def test_caso_exportar_xlsx_no_publica_job_parcial_sin_plantilla(tmp_path: Path) -> None:
    caso = REPO / "tests/corpus/L0/l0_20_exportar_xlsx"

    resultado = migrar(caso / "programa.sas", tmp_path / "salida", muestra=caso / "entradas")

    assert not resultado.jobs
    assert "P-COMPONENTE-SIN-PLANTILLA" in {p.codigo for p in resultado.pendientes}
    assert not list(resultado.carpeta.rglob("*.item"))
