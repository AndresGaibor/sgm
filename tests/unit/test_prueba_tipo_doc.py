"""Hito 85 / R1-03 sin Studio: variantes de `v01`, esperados y protocolo del arnés.

La ejecución real con los seis sufijos `v85e`..`v85j` queda en `PROGRESS.md`. Aquí se comprueba
que el esperado sale del corpus, que las variantes solo cambian la representación de `TIPO_DOC`,
que la comparación `01` frente a `1` está declarada y que el protocolo limpia el proyecto aunque
falle, con un doble del cliente MCP y un lanzador falso.
"""

from __future__ import annotations

import sys
import zipfile
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))

import prueba_tipo_doc as prueba  # noqa: E402
import tipo_doc_variantes as variantes  # noqa: E402
from mcp_cliente import ErrorValidacion  # noqa: E402


def _cname(ruta: Path) -> list[str]:
    """Valores de la columna A del xlsx escrito por `simular_insumos`."""
    with zipfile.ZipFile(ruta) as paquete:
        texto = paquete.read("xl/worksheets/sheet1.xml").decode("utf-8")
    import re

    return re.findall(r"<t[^>]*>([^<]*)</t>", texto)[1:]


@pytest.mark.parametrize(
    ("valor", "variante", "esperado"),
    [
        ("TD01", "texto", "TD01"),
        ("TD01", "numerico", "1"),
        ("TD01", "ceros", "01"),
        ("TD04", "ceros", "04"),
        ("TD99", "numerico", "99"),
        ("TD99", "ceros", "99"),
    ],
)
def test_codigo_cambia_solo_la_representacion(valor, variante, esperado):
    assert variantes.codigo(valor, variante) == esperado


@pytest.mark.parametrize("valor", ["XX", ""])
def test_codigo_desconocido_falla(valor):
    with pytest.raises(ValueError, match="desconocidos"):
        variantes.codigo(valor, "texto")


def test_codigo_rechaza_variante_desconocida():
    with pytest.raises(ValueError, match="desconocidos"):
        variantes.codigo("TD01", "otra")


@pytest.mark.parametrize(
    ("variante", "sin_normalizar", "excel_plano", "esperado"),
    [
        ("texto", False, False, False),
        ("texto", True, False, True),
        ("numerico", False, False, True),
        ("numerico", True, False, True),
        ("ceros", False, False, False),
        ("ceros", True, False, True),
        ("ceros", False, True, True),
        ("ceros", True, True, False),
    ],
)
def test_la_matriz_texto_frente_a_numero(variante, sin_normalizar, excel_plano, esperado):
    assert variantes.coincide(variante, sin_normalizar, excel_plano) is esperado


def test_coincide_rechaza_variante_desconocida():
    with pytest.raises(ValueError, match="desconocida"):
        variantes.coincide("otra", False, False)


def _filas_csv(ruta: Path) -> list[list[str]]:
    return [linea.split(";") for linea in ruta.read_text(encoding="utf-8").splitlines() if linea]


@pytest.mark.parametrize(
    ("variante", "codigos", "excel"),
    [
        ("texto", {"TD01": "TD01", "TD99": "TD99"}, ["TD01", "TD02", "TD03", "TD04"]),
        ("numerico", {"TD01": "1", "TD99": "99"}, ["1", "2", "3", "4"]),
        ("ceros", {"TD01": "01", "TD99": "99"}, ["01", "02", "03", "04"]),
    ],
)
def test_preparar_entradas_conserva_la_verdad_plantada(tmp_path, variante, codigos, excel):
    variantes.preparar_entradas(tmp_path, variante)
    for producto, esperadas in (("CTE", 95), ("AHO", 65)):
        filas = _filas_csv(tmp_path / "entradas" / f"DETALLE_{producto}.csv")
        assert len(filas) == esperadas
        assert all(len(fila) == 23 for fila in filas)
        assert filas[0][8] in codigos.values()
        assert filas[0][0] == "2026"  # lo demás no se toca
        assert filas[0][9] == f"{1:08d}"  # NRO_DOC conserva sus ceros
    assert _cname(tmp_path / "entradas" / variantes.EXCEL) == excel


def test_excel_sin_ceros_deja_el_csv_con_ceros(tmp_path):
    variantes.preparar_entradas(tmp_path, "ceros", excel_plano=True)
    assert _filas_csv(tmp_path / "entradas" / "DETALLE_CTE.csv")[0][8] in {"01", "02", "03", "04", "99"}
    assert _cname(tmp_path / "entradas" / variantes.EXCEL) == ["1", "2", "3", "4"]


def test_preparar_entradas_borra_las_salidas_anteriores(tmp_path):
    (tmp_path / "salida").mkdir()
    (tmp_path / "salida" / "doc_incorrectos_CTE.csv").write_text("viejo\n", encoding="utf-8")
    variantes.preparar_entradas(tmp_path, "texto")
    assert not (tmp_path / "salida" / "doc_incorrectos_CTE.csv").exists()


@pytest.mark.parametrize(
    ("producto", "esperado"),
    [("CTE", {"origen": 95, "validos": 88, "rechazados": 7}),
     ("AHO", {"origen": 65, "validos": 60, "rechazados": 5})],
)
def test_el_esperado_sale_del_corpus(producto, esperado):
    assert variantes.esperado_corpus(producto) == esperado


@pytest.mark.parametrize(
    ("variante", "sin_normalizar", "excel_plano", "coincide"),
    [("texto", False, False, False), ("texto", True, False, True),
     ("ceros", False, False, False), ("ceros", False, True, True)],
)
def test_expectativa_no_inventa_conteos(variante, sin_normalizar, excel_plano, coincide):
    corpus = variantes.esperado_corpus("CTE")
    conteos, motivo = variantes.expectativa(variante, sin_normalizar, excel_plano, corpus)
    assert conteos == (corpus if coincide else
                       {"origen": 95, "validos": 0, "rechazados": 95})
    assert motivo


def test_medir_lee_los_dos_logrow_y_el_archivo_de_rechazos(tmp_path):
    (tmp_path / "doc_incorrectos_CTE.csv").write_text(
        "ANIO_PROCESO|motivo\n" + "2026|TIPO_DOC_INVALIDO\n" * 7, encoding="utf-8"
    )
    assert variantes.medir("95|1144560\n88|1000000\n", tmp_path, "CTE") == {
        "origen": 95, "validos": 88, "rechazados": 7,
    }


def test_medir_sin_segundo_logrow_cuenta_cero_validos(tmp_path):
    (tmp_path / "doc_incorrectos_CTE.csv").write_text(
        "ANIO_PROCESO|motivo\n" + "2026|TIPO_DOC_INVALIDO\n" * 95, encoding="utf-8"
    )
    assert variantes.medir("95|1144560\n", tmp_path, "CTE") == {
        "origen": 95, "validos": 0, "rechazados": 95,
    }


def test_medir_sin_archivo_de_rechazos(tmp_path):
    assert variantes.medir("95|1144560\n", tmp_path, "CTE")["rechazados"] == 0


def test_informe_detecta_un_invariante_roto(capsys):
    corpus = {"origen": 95, "validos": 88, "rechazados": 7}
    roto = {"origen": 95, "validos": 88, "rechazados": 8}
    assert variantes.informe("CTE", corpus, corpus, roto, "prueba") is False
    assert "invariante origen=válidos+rechazados: NO" in capsys.readouterr().out


def test_quitar_normalizacion_reescribe_una_sola_expresion(tmp_path):
    item = tmp_path / "job_producto_0.1.item"
    item.write_text(
        '<mapperTableEntries name="TIPO_DOC" expression="java.util.Objects.toString(x)" '
        'type="id_String"/>\n<mapperTableEntries name="CNAME" expression="copy2.TIPO_DOC"/>\n',
        encoding="utf-8",
    )
    prueba.quitar_normalizacion(item)
    texto = item.read_text(encoding="utf-8")
    assert 'name="TIPO_DOC" expression="row1.TIPO_DOC"' in texto
    assert 'name="CNAME" expression="copy2.TIPO_DOC"' in texto


def test_quitar_normalizacion_falla_si_no_hay_expresion(tmp_path):
    item = tmp_path / "job_producto_0.1.item"
    item.write_text('<mapperTableEntries name="OTRA" expression="x"/>\n', encoding="utf-8")
    with pytest.raises(ErrorValidacion, match="no se encontró"):
        prueba.quitar_normalizacion(item)


def test_parametros_apuntan_a_las_entradas_y_a_la_salida(tmp_path):
    texto = " ".join(prueba.parametros(tmp_path, "AHO"))
    for clave in ("producto=AHO", "ruta_origen=", "DETALLE_AHO.csv", "sufijo=AHO",
                  "arch_hom_tipo_doc=", "ruta_insumos=", "ruta_resultados=", "hoja_excel=Sheet1"):
        assert clave in texto


class DobleStudio:
    """MCP y lanzador falsos: escriben las salidas que el arnés va a medir."""

    def __init__(self, validos: dict[str, int], rechazados: dict[str, int]) -> None:
        self.llamadas: list[str] = []
        self.validos = validos
        self.rechazados = rechazados

    def llamar(self, tool: str, argumentos: dict | None = None):
        self.llamadas.append(tool)
        return {}


@pytest.fixture
def proyecto(tmp_path) -> Path:
    carpeta = tmp_path / "PRJ_BANCOLOMBIA"
    (carpeta / "process").mkdir(parents=True)
    (carpeta / "talend.project").write_text(
        '<TalendProject technicalLabel="PRJ_BANCOLOMBIA"/>', encoding="utf-8"
    )
    return carpeta


def _parchear(monkeypatch, doble: DobleStudio, trabajo: Path) -> None:
    """Sustituye emisión, build, exportación y ejecución por dobles sin Studio."""
    def emitir(_programa, _jobs, destino):
        carpeta = destino / "client_large" / "talend" / "process"
        carpeta.mkdir(parents=True)
        (carpeta / "job_producto_0.1.item").write_text(
            '<mapperTableEntries name="TIPO_DOC" expression="x"/>', encoding="utf-8"
        )
        (carpeta / "job_producto_0.1.properties").write_text("id=x", encoding="utf-8")
        return carpeta

    def construir(_cliente, _nombres):
        return {"job": {"ok": True}}

    def exportar(_cliente, job, destino, _m2):
        (destino / job).mkdir(parents=True, exist_ok=True)
        lanzador = destino / job / f"{job}_run.bat"
        lanzador.write_text("@echo off\n", encoding="utf-8")
        return lanzador

    def ejecutar(_lanzador, _contexto, parametros, _java_bin):
        producto = next(p.split("=", 1)[1] for p in parametros if p.startswith("sufijo="))
        salida = trabajo / "salida"
        salida.mkdir(parents=True, exist_ok=True)
        (salida / f"doc_incorrectos_{producto}.csv").write_text(
            "ANIO_PROCESO|motivo\n"
            + "2026|TIPO_DOC_INVALIDO\n" * doble.rechazados[producto],
            encoding="utf-8",
        )
        origen = {"CTE": 95, "AHO": 65}[producto]
        stdout = f"{origen}|1000\n"
        if doble.validos[producto]:
            stdout += f"{doble.validos[producto]}|900\n"
        return {"exitCode": 0, "comando": "falso", "stdout": stdout, "stderr": ""}

    monkeypatch.setattr(prueba, "MCP", lambda: doble)
    monkeypatch.setattr(prueba, "emitir", emitir)
    monkeypatch.setattr(prueba, "construir", construir)
    monkeypatch.setattr(prueba, "exportar", exportar)
    monkeypatch.setattr(prueba, "ejecutar", ejecutar)


@pytest.mark.parametrize(
    ("variante", "sin_normalizar", "validos", "rechazados"),
    [
        ("texto", False, {"CTE": 0, "AHO": 0}, {"CTE": 95, "AHO": 65}),
        ("numerico", False, {"CTE": 88, "AHO": 60}, {"CTE": 7, "AHO": 5}),
    ],
    ids=["texto_normalizado_todo_rechazado", "numerico_coincide_con_v01"],
)
def test_validar_cierra_y_limpia_con_dobles(
    monkeypatch, proyecto, tmp_path, capsys, variante, sin_normalizar, validos, rechazados
):
    trabajo = tmp_path / "trabajo"
    doble = DobleStudio(validos, rechazados)
    _parchear(monkeypatch, doble, trabajo)
    assert prueba.validar(
        proyecto, trabajo, "v85test", variante, sin_normalizar, False, None, None
    ) == 0
    salida = capsys.readouterr().out
    assert "RESULTADO: 2 de 2 productos" in salida
    assert "Limpieza: 2 archivos borrados" in salida
    assert not list((proyecto / "process").glob("job_producto_v85test*"))
    assert doble.llamadas.count("talend_bridge_refresh_workspace") == 2


def test_validar_con_ceros_y_excel_plano_coincide(monkeypatch, proyecto, tmp_path, capsys):
    trabajo = tmp_path / "trabajo"
    doble = DobleStudio({"CTE": 88, "AHO": 60}, {"CTE": 7, "AHO": 5})
    _parchear(monkeypatch, doble, trabajo)
    assert prueba.validar(
        proyecto, trabajo, "v85ceros", "ceros", False, True, None, None
    ) == 0
    assert "RESULTADO: 2 de 2 productos" in capsys.readouterr().out


def test_main_rechaza_una_carpeta_que_no_es_proyecto(tmp_path):
    assert prueba.main(["--proyecto", str(tmp_path)]) == 2
