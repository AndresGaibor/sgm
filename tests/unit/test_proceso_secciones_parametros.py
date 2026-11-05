"""Tests de la sección 2.1: parámetros de ruta y de archivo, halladas en el SAS o pendientes."""

from __future__ import annotations

from sgm.proceso.entradas_salidas import EntradasSalidas, Fuente, Plantilla
from sgm.proceso.secciones_entrada import ORIGEN_SAS
from sgm.proceso.secciones_parametros import directorio, seccion_parametros

CARPETA = "\\\\servidor\\FILES\\"


def _es() -> EntradasSalidas:
    return EntradasSalidas(
        fuentes=[
            Fuente("excel", CARPETA + "Cod_pais.xlsx", 1),
            Fuente("excel", CARPETA + "Validacion_fecha.xlsx", 2),
            Fuente("csv", "/work/Base.csv", 3),
        ],
        salidas=[
            Plantilla(
                "RESULTADOS\\out_{P}.csv",
                ((None, CARPETA + "RESULTADOS\\out_cte.csv"),
                 (None, CARPETA + "RESULTADOS\\out_aho.csv")),
            )
        ],
    )


def test_directorio_conserva_el_separador_del_sas() -> None:
    assert directorio(CARPETA + "Cod_pais.xlsx") == CARPETA
    assert directorio("/work/Base.csv") == "/work/"
    assert directorio("archivo_sin_carpeta.csv") == ""


def test_nombre_de_archivo_hallado_en_las_fuentes() -> None:
    declarados = [{"clave": "arch_paises", "busca": r"Cod_pais\.xlsx$"}]
    seccion, origenes = seccion_parametros(declarados, _es())
    assert seccion == {"arch_paises": {"tipo": "String", "valor": "Cod_pais.xlsx", "nota": ""}}
    assert origenes == {"arch_paises": ORIGEN_SAS}


def test_carpeta_comun_de_las_fuentes_excel() -> None:
    declarados = [{"clave": "ruta_insumos", "busca": r"\.xlsx$", "valor": "directorio"}]
    seccion, _ = seccion_parametros(declarados, _es())
    assert seccion["ruta_insumos"]["valor"] == CARPETA


def test_carpeta_no_se_emite_si_las_rutas_casadas_estan_en_carpetas_distintas() -> None:
    es = _es()
    es.fuentes.append(Fuente("excel", "/otra/Dos.xlsx", 4))
    declarados = [{"clave": "ruta_insumos", "busca": r"\.xlsx$", "valor": "directorio"}]
    seccion, origenes = seccion_parametros(declarados, es)
    assert seccion == {}
    assert origenes == {}


def test_parametro_sin_hallazgo_queda_fuera_de_la_seccion() -> None:
    declarados = [{"clave": "arch_dane", "busca": r"CODIGOS_DANE\.xlsx$"}]
    seccion, origenes = seccion_parametros(declarados, _es())
    assert seccion == {}
    assert origenes == {}


def test_desde_salidas_busca_en_las_rutas_de_escritura() -> None:
    declarados = [
        {"clave": "ruta_resultados", "desde": "salidas", "busca": "RESULTADOS",
         "valor": "directorio"}
    ]
    seccion, _ = seccion_parametros(declarados, _es())
    assert seccion["ruta_resultados"]["valor"] == CARPETA + "RESULTADOS\\"


def test_busqueda_sin_distinguir_mayusculas() -> None:
    declarados = [{"clave": "arch_paises", "busca": r"cod_PAIS\.XLSX$"}]
    seccion, _ = seccion_parametros(declarados, _es())
    assert seccion["arch_paises"]["valor"] == "Cod_pais.xlsx"


def test_el_orden_de_la_seccion_sigue_al_de_las_declaraciones() -> None:
    declarados = [
        {"clave": "b", "busca": r"Validacion_fecha"},
        {"clave": "a", "busca": r"Cod_pais"},
    ]
    seccion, _ = seccion_parametros(declarados, _es())
    assert list(seccion) == ["b", "a"]
