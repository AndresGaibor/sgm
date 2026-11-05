"""Pruebas del ejecutor del corpus: formato de caso, oráculo, verificación, informe, CSV y generador.

Los casos sintéticos viven en `tmp_path`. Al final, la verificación del corpus real (capa A) es la
prueba de consistencia que pide el plan: `oraculo todos --verificar` debe pasar sin cambios.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))

from corpus_lib.caso import cargar_caso, resolver  # noqa: E402
from corpus_lib.csv_tabla import (  # noqa: E402
    Tabla,
    celda_texto,
    escribir_csv,
    leer_entradas,
    ordenar_filas,
)
from corpus_lib.generar_entradas import generar_todo  # noqa: E402
from corpus_lib.informe import generar_informe  # noqa: E402

from corpus import main  # noqa: E402

PROGRAMA = """/* Caso sintetico de prueba. */
PROC IMPORT DATAFILE='.../entradas/clientes.csv' OUT=WORK.clientes DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

PROC SQL;
  CREATE TABLE WORK.altos AS
  SELECT id, saldo
  FROM WORK.clientes
  WHERE saldo >= 100
  ORDER BY id;
QUIT;
"""
CSV = "id,saldo\n1,50\n2,150\n3,\n4,200\n"


def _caso(tmp_path, nombre="l1_01_prueba", nivel="L1", extra="", capa="A", programa=PROGRAMA):
    corpus = tmp_path / "corpus"
    carpeta = corpus / nivel / nombre
    (carpeta / "entradas").mkdir(parents=True)
    (carpeta / "programa.sas").write_text(programa, encoding="utf-8")
    (carpeta / "entradas" / "clientes.csv").write_text(CSV, encoding="utf-8")
    estado = "" if "estado:" in extra else "estado: traducible\n"
    texto = (
        f"nivel: {nivel}\nconstrucciones: [PROC SQL]\ncapa: {capa}\nsalidas: [altos]\n"
        f"{estado}{extra}"
    )
    (carpeta / "caso.yaml").write_text(texto, encoding="utf-8")
    return corpus


def _leer(ruta: Path) -> str:
    return ruta.read_text(encoding="utf-8")


def test_oraculo_escribe_esperado_y_verificar_pasa(tmp_path, capsys):
    corpus = _caso(tmp_path)
    assert main(["oraculo", "l1_01_prueba", "--corpus", str(corpus)]) == 0
    esperado = corpus / "L1" / "l1_01_prueba" / "esperado" / "altos.csv"
    assert _leer(esperado) == "id,saldo\n2,150\n4,200\n"
    assert main(["oraculo", "l1_01_prueba", "--verificar", "--corpus", str(corpus)]) == 0
    assert "VERIFICADO" in capsys.readouterr().out


def test_verificar_falla_con_diferencia_clara_y_no_escribe(tmp_path, capsys):
    corpus = _caso(tmp_path)
    main(["oraculo", "l1_01_prueba", "--corpus", str(corpus)])
    esperado = corpus / "L1" / "l1_01_prueba" / "esperado" / "altos.csv"
    esperado.write_text("id,saldo\n2,151\n4,200\n", encoding="utf-8")
    assert main(["oraculo", "l1_01_prueba", "--verificar", "--corpus", str(corpus)]) == 1
    salida = capsys.readouterr().out
    assert "fila 1, columna 'saldo': esperado '151', obtenido '150'" in salida
    assert _leer(esperado) == "id,saldo\n2,151\n4,200\n"


def test_tolerancia_numerica_acepta_diferencia_dentro_del_rango(tmp_path):
    corpus = _caso(tmp_path, extra="tolerancia: 1.5\n")
    main(["oraculo", "l1_01_prueba", "--corpus", str(corpus)])
    esperado = corpus / "L1" / "l1_01_prueba" / "esperado" / "altos.csv"
    esperado.write_text("id,saldo\n2,151.2\n4,200\n", encoding="utf-8")
    assert main(["oraculo", "l1_01_prueba", "--verificar", "--corpus", str(corpus)]) == 0


def test_orden_no_relevante_compara_sin_importar_el_orden(tmp_path):
    corpus = _caso(tmp_path, extra="orden_relevante: false\n")
    main(["oraculo", "l1_01_prueba", "--corpus", str(corpus)])
    esperado = corpus / "L1" / "l1_01_prueba" / "esperado" / "altos.csv"
    esperado.write_text("id,saldo\n4,200\n2,150\n", encoding="utf-8")
    assert main(["oraculo", "l1_01_prueba", "--verificar", "--corpus", str(corpus)]) == 0


def test_verificar_sin_esperado_reporta_falta(tmp_path, capsys):
    corpus = _caso(tmp_path)
    assert main(["oraculo", "l1_01_prueba", "--verificar", "--corpus", str(corpus)]) == 1
    assert "falta el archivo altos.csv" in capsys.readouterr().out


def test_capa_c_se_omite_sin_calcular(tmp_path, capsys):
    corpus = _caso(
        tmp_path,
        nombre="l0_01_prueba",
        nivel="L0",
        capa="C",
        extra="estado: pendiente_revision\nmotivo: prueba\n",
        programa="DATA WORK.x; SET WORK.y; RUN;",
    )
    assert main(["oraculo", "l0_01_prueba", "--corpus", str(corpus)]) == 0
    assert "OMITIDO" in capsys.readouterr().out
    assert not (corpus / "L0" / "l0_01_prueba" / "esperado").exists()


def test_construccion_no_soportada_es_falla_con_mensaje(tmp_path, capsys):
    programa = PROGRAMA.replace("saldo >= 100", "calculated saldo >= 100")
    corpus = _caso(tmp_path, programa=programa)
    assert main(["oraculo", "l1_01_prueba", "--corpus", str(corpus)]) == 1
    assert "no soportada por el oráculo: CALCULATED" in capsys.readouterr().out


@pytest.mark.parametrize(
    ("extra", "error"),
    [
        ("estado: pendiente\n", "motivo"),
        ("campo_raro: 1\n", "no reconocidos"),
        ("tolerancia: -1\n", "tolerancia"),
        ("orden_relevante: si\n", "orden_relevante"),
        ("estado: listo\n", "estado"),
    ],
)
def test_caso_yaml_invalido_se_rechaza(tmp_path, extra, error):
    corpus = _caso(tmp_path, extra=extra)
    with pytest.raises(ValueError, match=error):
        cargar_caso(corpus / "L1" / "l1_01_prueba")


def test_nivel_del_yaml_debe_coincidir_con_la_carpeta(tmp_path):
    corpus = _caso(tmp_path, nivel="L1")
    yaml_path = corpus / "L1" / "l1_01_prueba" / "caso.yaml"
    yaml_path.write_text(yaml_path.read_text(encoding="utf-8").replace("L1", "L2"), encoding="utf-8")
    with pytest.raises(ValueError, match="nivel"):
        cargar_caso(corpus / "L1" / "l1_01_prueba")


def test_resolver_todos_nivel_y_caso(tmp_path):
    corpus = _caso(tmp_path)
    assert [c.nombre for c in resolver(corpus, "todos")] == ["l1_01_prueba"]
    assert [c.nombre for c in resolver(corpus, "L1")] == ["l1_01_prueba"]
    assert [c.nombre for c in resolver(corpus, "l1_01_prueba")] == ["l1_01_prueba"]
    with pytest.raises(ValueError, match="no existe"):
        resolver(corpus, "l9_nada")


def test_informe_lista_casos_con_estado_capa_y_conteo(tmp_path):
    corpus = _caso(tmp_path, extra="")
    texto = generar_informe(corpus)
    assert "| l1_01_prueba | traducible | A |  | PROC SQL | 1 |" in texto
    assert "Construcciones distintas en L1: PROC SQL." in texto
    assert "| L1 | 1 | 1 | 0 | 1 |" in texto


def test_informe_por_cli_escribe_archivo(tmp_path):
    corpus = _caso(tmp_path)
    salida = tmp_path / "informe.md"
    assert main(["informe", "--corpus", str(corpus), "--salida", str(salida)]) == 0
    assert "# Informe del corpus" in _leer(salida)


def test_lectura_de_csv_infiere_tipos_y_vacios(tmp_path):
    carpeta = tmp_path / "entradas"
    carpeta.mkdir()
    (carpeta / "datos.csv").write_text(
        'codigo,precio,cantidad,nombre\n007,2.50,3,"Peña, Ñandú"\n010,,4,\n',
        encoding="utf-8",
    )
    tabla = leer_entradas(carpeta)["DATOS"]
    assert tabla.tipos == ["TEXT", "REAL", "INTEGER", "TEXT"]
    # El vacío de una columna de texto es '' (blanco SAS = faltante e igual a ''); el de número, NULL.
    assert tabla.filas == [("007", 2.5, 3, "Peña, Ñandú"), ("010", None, 4, "")]


def test_escritura_de_csv_cita_lo_necesario(tmp_path):
    ruta = tmp_path / "salida" / "t.csv"
    escribir_csv(ruta, Tabla(["a", "b"], [("Peña, Ñ", 2.5), (None, 3)]))
    assert _leer(ruta) == 'a,b\n"Peña, Ñ",2.5\n,3\n'


def test_celda_texto_de_reales_y_faltantes():
    assert celda_texto(2.0) == "2"
    assert celda_texto(0.1 + 0.2) == "0.3"
    assert celda_texto(None) == ""


def test_orden_de_filas_pone_faltantes_primero():
    filas = [(2, "b"), (None, "z"), (1, None)]
    assert ordenar_filas(filas) == [(None, "z"), (1, None), (2, "b")]


def test_generador_es_reproducible_y_coincide_con_el_repo(tmp_path):
    escritos = generar_todo(tmp_path)
    assert len(escritos) == 31
    for ruta in escritos:
        relativa = ruta.relative_to(tmp_path)
        assert ruta.read_bytes() == (REPO / "tests" / "corpus" / relativa).read_bytes()


def test_corpus_real_pasa_la_verificacion_de_capa_a(capsys):
    """Prueba de consistencia: lo guardado en `esperado/` es lo que da el oráculo hoy."""
    assert main(["oraculo", "todos", "--verificar"]) == 0
    assert "0 con falla" in capsys.readouterr().out


def _caso_anidado_l8(tmp_path, extra="", capa="A"):
    """Caso en L8/<grupo>/<caso>/ con metadatos de L8 (como los de tests/corpus/L8)."""
    corpus = tmp_path / "corpus"
    carpeta = corpus / "L8" / "grupo_x" / "l8_01_anidado"
    (carpeta / "entradas").mkdir(parents=True)
    (carpeta / "programa.sas").write_text(PROGRAMA, encoding="utf-8")
    (carpeta / "entradas" / "clientes.csv").write_text(CSV, encoding="utf-8")
    texto = (
        "id: 01_anidado\nnivel: L8\ntema: prueba\nproductos: [AHO]\nsupuestos: [uno]\n"
        "construcciones: [PROC SQL]\nanomalias_plantadas: {filas: 4}\n"
        "salidas_esperadas:\n  tablas_work: [altos]\n"
        f"capa: {capa}\nestado: traducible\n{extra}"
    )
    (carpeta / "caso.yaml").write_text(texto, encoding="utf-8")
    return corpus


def test_caso_anidado_de_l8_se_carga_con_su_nivel_y_metadatos(tmp_path):
    corpus = _caso_anidado_l8(tmp_path)
    caso = resolver(corpus, "L8")[0]
    assert caso.nivel == "L8"
    assert caso.salidas == ("altos",)  # sin `salidas`, sale de `salidas_esperadas.tablas_work`
    assert caso.extra == {
        "id": "01_anidado",
        "tema": "prueba",
        "productos": ["AHO"],
        "supuestos": ["uno"],
        "anomalias_plantadas": {"filas": 4},
        "salidas_esperadas": {"tablas_work": ["altos"]},
    }
    assert [c.nombre for c in resolver(corpus, "todos")] == ["l8_01_anidado"]


def test_caso_anidado_de_l8_con_capa_a_se_omite_con_motivo(tmp_path, capsys):
    corpus = _caso_anidado_l8(tmp_path)
    assert main(["oraculo", "L8", "--verificar", "--corpus", str(corpus)]) == 0
    salida = capsys.readouterr().out
    assert "OMITIDO" in salida and "formato SAS" in salida
    assert "0 con falla" in salida


def test_caso_anidado_de_l8_con_nivel_distinto_se_rechaza(tmp_path):
    corpus = _caso_anidado_l8(tmp_path, extra="")
    yaml_path = corpus / "L8" / "grupo_x" / "l8_01_anidado" / "caso.yaml"
    yaml_path.write_text(yaml_path.read_text(encoding="utf-8").replace("nivel: L8", "nivel: L1"),
                         encoding="utf-8")
    with pytest.raises(ValueError, match="nivel"):
        cargar_caso(yaml_path.parent)


def test_celda_de_texto_vacia_es_cadena_vacia_y_numerica_es_nula(tmp_path):
    carpeta = tmp_path / "entradas"
    carpeta.mkdir()
    (carpeta / "t.csv").write_text("a,b\nx,\n,2\n", encoding="utf-8")
    tabla = leer_entradas(carpeta)["T"]
    assert tabla.filas == [("x", None), ("", 2)]
