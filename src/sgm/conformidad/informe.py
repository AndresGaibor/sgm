"""Resumen de la conformidad: conteos, porcentaje y diferencias con su motivo, en orden estable."""

from __future__ import annotations

import json

from sgm.conformidad.estado import ESTADOS, EstadoFila


def resumir(filas: list[EstadoFila]) -> dict:
    """Conteos por estado, porcentaje de derivadas y la lista de diferencias con su motivo."""
    conteo = {estado: sum(1 for f in filas if f.estado == estado) for estado in ESTADOS}
    total = len(filas)
    return {
        "total": total,
        "derivadas": conteo["derivada"],
        "declaradas": conteo["declarada"],
        "pendientes": conteo["pendiente"],
        "diferentes": conteo["diferente"],
        "porcentaje_derivadas": round(100 * conteo["derivada"] / total, 1) if total else 0.0,
        "diferencias": [
            {"id": f.id, "seccion": f.seccion, "clave": f.clave, "motivo": f.motivo}
            for f in filas
            if f.estado == "diferente"
        ],
    }


def texto(programa: str, resumen: dict) -> str:
    """Resumen legible para la consola."""
    lineas = [
        f"Conformidad de {programa} contra el diseño manual ({resumen['total']} filas)",
        f"  derivadas:  {resumen['derivadas']}",
        f"  declaradas: {resumen['declaradas']}",
        f"  pendientes: {resumen['pendientes']}",
        f"  diferencias: {resumen['diferentes']}",
        f"  porcentaje derivado: {resumen['porcentaje_derivadas']} %",
    ]
    if resumen["diferencias"]:
        lineas.append("Diferencias con motivo:")
        lineas += [
            f"  {d['id']} (sección {d['seccion']}, {d['clave']}): {d['motivo']}"
            for d in resumen["diferencias"]
        ]
    return "\n".join(lineas)


def json_del_informe(programa: str, resumen: dict, filas: list[EstadoFila]) -> str:
    """Salida JSON completa (una entrada por fila, en orden de la referencia)."""
    payload = {
        "programa": programa,
        **resumen,
        "filas": [
            {"id": f.id, "seccion": f.seccion, "clave": f.clave, "estado": f.estado,
             "motivo": f.motivo}
            for f in filas
        ],
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)
