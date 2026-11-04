"""H1: qué fracción del programa es fontanería según las reglas existentes (pasadas 2 y 3)."""

from __future__ import annotations

from collections import Counter

from fase0.captura import Captura

# Familias de las categorías de `rules/sas/plumbing.yaml` (más las que añade la pasada 2 en código).
FAMILIAS = {
    "sesion_remota_y_paralelismo": ("remoto", "espera", "shell_auxiliar", "troceado_lotes"),
    "conexion_y_tablas_de_base": ("conexion", "limpieza_tablas"),
    "limpieza_de_temporales": ("limpieza_work", "borrado_datasets"),
    "macro_control_y_configuracion": ("control_macro", "configuracion_macro", "variables_control"),
    "log_medicion_y_presentacion": (
        "mensajes",
        "mensajes_sistema",
        "medicion",
        "presentacion",
        "visor_studio",
        "fin_de_paso",
        "conteo",
        "redireccion_log",
        "ods_close",
        "reporte_diagnostico",
    ),
}
_FAMILIA_DE = {cat: fam for fam, cats in FAMILIAS.items() for cat in cats}


def _pct(parte: int, total: int) -> float:
    return round(100 * parte / total, 1) if total else 0.0


def medir(c: Captura) -> dict:
    total = len(c.ops)
    marcados = [o for o in c.ops if o.plumbing]
    por_categoria = Counter(o.plumbing for o in marcados)
    quitados = Counter(o.plumbing for o in marcados if o.removed)
    en_carga = Counter(o.plumbing for o in marcados if o.absorbed)
    absorbidos_no_marcados = [o for o in c.ops if o.absorbed and not o.plumbing]
    por_familia = Counter(_FAMILIA_DE.get(o.plumbing, "otros") for o in marcados)
    n_marcados = len(marcados)
    n_absorbidos_sin_marca = len(absorbidos_no_marcados)
    maquinaria = n_marcados + n_absorbidos_sin_marca
    por_tipo = Counter(o.kind for o in c.ops)
    sin_traducir_inicial = [o for o in c.ops if o.kind == "unsupported"]
    return {
        "items_del_programa": c.items,
        "operadores_tras_pasada_1": total,
        "operadores_por_tipo_inicial": dict(por_tipo.most_common()),
        "fontaneria_marcada_pasada_2": {
            "total": n_marcados,
            "porcentaje": _pct(n_marcados, total),
            "por_categoria": dict(por_categoria.most_common()),
            "por_familia": dict(por_familia.most_common()),
            "quitada_suelta": sum(quitados.values()),
            "absorbida_en_cargas_externas": sum(en_carga.values()),
            "quitada_por_categoria": dict(quitados.most_common()),
            "absorbida_por_categoria": dict(en_carga.most_common()),
        },
        "absorbidos_por_cargas_sin_marca_de_fontaneria": {
            "total": n_absorbidos_sin_marca,
            "por_tipo": dict(Counter(o.kind for o in absorbidos_no_marcados).most_common()),
        },
        "cargas_externas_creadas": c.cargas_externas,
        "maquinaria_total": {
            "operadores": maquinaria,
            "porcentaje": _pct(maquinaria, total),
            "nota": "fontanería marcada + operadores que una carga externa absorbe sin ser "
            "fontanería por patrón (preparación de la carga)",
        },
        "sin_traducir_inicial": {
            "total": len(sin_traducir_inicial),
            "de_los_cuales_fontaneria": sum(1 for o in sin_traducir_inicial if o.plumbing),
        },
        "operadores_finales": {
            "total": c.finales_total,
            "porcentaje_del_inicial": _pct(c.finales_total, total),
            "por_tipo": {k: v for k, v in sorted(_por_tipo(c).items(), key=lambda kv: -kv[1])},
            "sin_traducir_por_origen_y_motivo": dict(c.sin_traducir.most_common(15)),
        },
        "residuo_estimado": residuo(c),
    }


_DE_ENTORNO = ("CONFIGURACION", "INCLUDE_DECLARADO", "PROC_NO_SOPORTADO")


def residuo(c: Captura) -> dict:
    """Operadores finales que no son datos: cargas externas y sentencias de entorno que quedaron
    como `unsupported` (configuración, include declarado, UPLOAD/DOWNLOAD/PWENCODE)."""
    entorno = sum(n for k, n in c.sin_traducir.items() if k.rsplit(" / ", 1)[-1] in _DE_ENTORNO)
    cargas = _por_tipo(c).get("external_load", 0)
    de_datos = c.finales_total - cargas - entorno
    return {
        "cargas_externas": cargas,
        "sentencias_de_entorno_sin_traducir": entorno,
        "operadores_de_datos_estimados": de_datos,
        "porcentaje_del_inicial": _pct(de_datos, len(c.ops)),
    }


def _por_tipo(c: Captura) -> dict[str, int]:
    resultado: Counter = Counter()
    for (tipo, _estado), n in c.finales.items():
        resultado[tipo] += n
    return dict(resultado)
