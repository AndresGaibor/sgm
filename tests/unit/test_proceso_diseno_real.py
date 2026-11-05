"""Secciones 1.1, 1.2, 1.3 y 3 del documento emitido para `client_large.sas` (lo que prueba el SAS)."""

from __future__ import annotations

from functools import lru_cache

from sgm.proceso.diseno_doc import construir_documento
from tests.conformidad.cargador import RAIZ

PROGRAMA = RAIZ / "tests" / "fixtures" / "sas" / "client" / "client_large.sas"
DECISIONES = RAIZ / "decisiones"
DEPOSITOS = (
    "Depósitos corriente (origen CTE)",
    "Depósitos ahorros (origen AHO)",
    "Depósitos Nequi (origen NEQUI)",
)


@lru_cache(maxsize=1)
def _doc():
    return construir_documento(
        PROGRAMA,
        DECISIONES / f"{PROGRAMA.stem}.agrupacion.yaml",
        DECISIONES / f"{PROGRAMA.stem}.diseno.yaml",
    )


def test_depositos_son_csv_hallados_en_el_sas_y_no_tablas_impala() -> None:
    seccion = _doc().secciones["1.1"]
    origenes = _doc().origenes["1.1"]
    for clave in DEPOSITOS:
        assert seccion[clave]["tipo"] == "CSV", clave
        assert seccion[clave]["estado"] == "Ruta confirmada en SAS", clave
        assert origenes[clave] == "sas", clave


def test_lecturas_de_impala_del_sas_figuran_como_tablas() -> None:
    seccion = _doc().secciones["1.1"]
    for clave in ("Maestro de clientes (Impala)", "Firmas autorizadas (Impala)", "MCDQ (Impala)"):
        assert seccion[clave]["tipo"] == "Tabla Impala", clave
        assert seccion[clave]["estado"] == "Ruta confirmada en SAS", clave


def test_seccion_1_2_tiene_los_diez_intercambios_del_manual() -> None:
    claves = set(_doc().secciones["1.2"])
    assert claves == {
        "cache_hom_doc", "cache_hom_nequi", "cache_paises", "cache_dane",
        "totales_origen_cte", "totales_origen_aho", "totales_origen_nequi",
        "totales_salida_cte", "totales_salida_aho", "totales_salida_nequi",
    }  # fmt: skip


def test_seccion_1_2_no_declara_ningun_lookup_de_ubicacion_como_hecho() -> None:
    seccion = _doc().secciones["1.2"]
    for clave in ("cache_paises", "cache_dane"):
        assert seccion[clave]["leida_en"].startswith("pendiente"), clave


def test_seccion_1_3_el_padre_crea_las_tres_variables_de_periodo() -> None:
    seccion = _doc().secciones["1.3"]
    assert set(seccion) == {"periodo_anio", "periodo_mes", "periodo_dia"}
    assert all(f["creada_en"] == "job_exogena_depositos (padre)" for f in seccion.values())
    assert _doc().origenes["1.3"]["periodo_anio"] == "sas"


def test_seccion_3_lista_los_cuatro_jobs_con_su_conteo() -> None:
    seccion = _doc().secciones["3"]
    assert set(seccion) == {
        "job_exogena_depositos", "job_producto", "job_totales", "job_conciliacion",
    }  # fmt: skip
    assert all(int(fila["componentes"]) >= 1 for fila in seccion.values())


def test_seccion_3_no_sale_del_documento_si_no_hay_jobs_declarados(tmp_path) -> None:
    # Sin `<programa>.jobs.yaml` el emisor no corre y la sección queda vacía, no inventada.
    programa = tmp_path / "p.sas"
    programa.write_text("data a; set b; run;\n", encoding="utf-8")
    decisiones = tmp_path / "p.diseno.yaml"
    decisiones.write_text("etapas:\n  - {nombre: cargar, patrones: ['^carga']}\n", encoding="utf-8")
    agrupacion = tmp_path / "a.yaml"
    agrupacion.write_text(
        'region_marcador: "%macro ambiente"\nproductos:\n  - {nombre: a, sufijos: [AAA]}\n',
        encoding="utf-8",
    )
    doc = construir_documento(programa, agrupacion, decisiones)
    assert doc.secciones["3"] == {}
    assert doc.secciones["1.3"] == {}
