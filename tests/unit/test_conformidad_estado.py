"""Estado de cada fila de la conformidad, con referencias pequeñas construidas a mano."""

from __future__ import annotations

import json

from sgm.conformidad import informe
from sgm.conformidad.estado import DIFERENCIAS_CONOCIDAS, clasificar_filas
from sgm.conformidad.referencia import Fila, Seccion
from sgm.proceso.secciones_entrada import ORIGEN_DECLARADA, ORIGEN_SAS


def _seccion(*filas: Fila) -> dict[str, Seccion]:
    return {"1.1": Seccion("1.1", "Fuentes", True, ["tipo"], list(filas))}


def _fila(id_: str, clave: str, clasificacion: str = "derivable", tipo: str = "Excel") -> Fila:
    return Fila("1.1", id_, clave, clasificacion, f"motivo de {id_}", {"tipo": tipo})


def _estados(secciones, diseno, origenes, emitidas=("1.1",)):
    filas = clasificar_filas(secciones, diseno, origenes, emitidas)
    return {f.id: (f.estado, f.motivo) for f in filas}


def test_fila_de_seccion_no_emitida_queda_pendiente_con_el_motivo_del_manual() -> None:
    secciones = _seccion(_fila("Z01", "Fuente"))
    estados = _estados(secciones, {}, {}, emitidas=())
    assert estados["Z01"] == ("pendiente", "el migrador aún no emite esta fila: motivo de Z01")


def test_fila_derivable_y_hallada_en_el_sas_es_derivada() -> None:
    secciones = _seccion(_fila("Z01", "Fuente"))
    diseno = {"1.1": {"Fuente": {"tipo": "Excel"}}}
    origenes = {"1.1": {"Fuente": ORIGEN_SAS}}
    assert _estados(secciones, diseno, origenes)["Z01"] == ("derivada", "")


def test_fila_con_valor_de_decisiones_es_declarada_aunque_coincida() -> None:
    secciones = _seccion(_fila("Z01", "Fuente"))
    diseno = {"1.1": {"Fuente": {"tipo": "Excel"}}}
    origenes = {"1.1": {"Fuente": ORIGEN_DECLARADA}}
    estado, motivo = _estados(secciones, diseno, origenes)["Z01"]
    assert estado == "declarada"
    assert "decisiones/" in motivo


def test_fila_declarada_en_el_manual_no_es_derivada_aunque_el_sas_la_halle() -> None:
    secciones = _seccion(_fila("Z01", "Fuente", clasificacion="declarada"))
    diseno = {"1.1": {"Fuente": {"tipo": "Excel"}}}
    origenes = {"1.1": {"Fuente": ORIGEN_SAS}}
    assert _estados(secciones, diseno, origenes)["Z01"][0] == "declarada"


def test_valor_distinto_del_manual_es_diferente_y_dice_la_columna() -> None:
    secciones = _seccion(_fila("Z01", "Fuente", tipo="CSV"))
    diseno = {"1.1": {"Fuente": {"tipo": "Excel"}}}
    origenes = {"1.1": {"Fuente": ORIGEN_SAS}}
    estado, motivo = _estados(secciones, diseno, origenes)["Z01"]
    assert estado == "diferente"
    assert "tipo" in motivo and "'CSV'" in motivo


def test_fila_ausente_en_el_diseno_emitido_queda_pendiente() -> None:
    secciones = _seccion(_fila("Z01", "Fuente"))
    assert _estados(secciones, {"1.1": {}}, {})["Z01"][0] == "pendiente"


def test_diferencia_conocida_gana_sobre_la_comparacion() -> None:
    clave_conocida = next(iter(DIFERENCIAS_CONOCIDAS))
    secciones = _seccion(_fila(clave_conocida, "Fuente"))
    diseno = {"1.1": {"Fuente": {"tipo": "Excel"}}}
    estado, motivo = _estados(secciones, diseno, {})[clave_conocida]
    assert (estado, motivo) == ("diferente", DIFERENCIAS_CONOCIDAS[clave_conocida])


def test_fila_humana_que_coincide_sigue_pendiente() -> None:
    secciones = _seccion(_fila("Z01", "Fuente", clasificacion="humana"))
    diseno = {"1.1": {"Fuente": {"tipo": "Excel"}}}
    origenes = {"1.1": {"Fuente": ORIGEN_SAS}}
    estado, motivo = _estados(secciones, diseno, origenes)["Z01"]
    assert estado == "pendiente"
    assert motivo.startswith("requiere decisión humana")


def test_resumen_cuenta_por_estado_y_porcentaje_de_derivadas() -> None:
    secciones = _seccion(
        _fila("Z01", "a"), _fila("Z02", "b"), _fila("Z03", "c", tipo="CSV"), _fila("Z04", "d")
    )
    diseno = {"1.1": {"a": {"tipo": "Excel"}, "b": {"tipo": "Excel"}, "c": {"tipo": "Excel"}}}
    origenes = {"1.1": {"a": ORIGEN_SAS, "b": ORIGEN_DECLARADA}}
    resumen = informe.resumir(clasificar_filas(secciones, diseno, origenes, ("1.1",)))
    assert resumen["total"] == 4
    assert (resumen["derivadas"], resumen["declaradas"]) == (1, 1)
    assert (resumen["pendientes"], resumen["diferentes"]) == (1, 1)
    assert resumen["porcentaje_derivadas"] == 25.0
    assert [d["id"] for d in resumen["diferencias"]] == ["Z03"]


def test_resumen_sin_filas_no_divide_por_cero() -> None:
    assert informe.resumir([])["porcentaje_derivadas"] == 0.0


def test_json_del_informe_es_determinista() -> None:
    secciones = _seccion(_fila("Z01", "a"), _fila("Z02", "b"))
    filas = clasificar_filas(secciones, {}, {}, ("1.1",))
    uno = informe.json_del_informe("p.sas", informe.resumir(filas), filas)
    dos = informe.json_del_informe("p.sas", informe.resumir(filas), filas)
    assert uno == dos
    assert [f["id"] for f in json.loads(uno)["filas"]] == ["Z01", "Z02"]
