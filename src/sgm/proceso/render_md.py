"""Markdown del documento de diseño a partir de un `DocumentoDiseno`.

El emisor no decide nada: escribe lo que el modelo ya trae. Los títulos son del documento.
"""

from __future__ import annotations

from sgm.proceso.diseno_doc import DocumentoDiseno

TITULOS = {
    "1.1": "Fuentes externas",
    "1.4": "Salidas (archivos)",
    "3": "Etapas y tamaño estimado",
    "6": "Equivalencias con el SAS",
}
ETIQUETA_RESUMEN = {
    "pasos": "Pasos del programa",
    "regiones": "Regiones",
    "familias": "Familias de regiones (copias por producto)",
    "regiones_sin_copia": "Regiones sin copia",
    "fuentes": "Fuentes externas",
    "persistencias_propias": "Persistencias propias eliminadas",
    "plantillas_de_salida": "Plantillas de salida",
    "sentencias_de_fontaneria": "Sentencias de fontanería",
    "etiquetas": "Etiquetas de etapa",
    "etiquetas_con_etapa": "Etiquetas con etapa asignada",
    "pasos_de_datos": "Pasos de datos (sin fontanería)",
    "bloques_sin_parametrizar": "Bloques tras colapsar tablas intermedias",
    "bloques_en_plantillas": "Bloques si cada familia se escribe una vez, sin etapas eliminadas",
}


def _celda(valor: str) -> str:
    return " ".join(str(valor).split()).replace("|", "\\|") or " "


def _tabla(filas: dict[str, dict[str, str]]) -> list[str]:
    if not filas:
        return ["_Sin filas._"]
    columnas = list(next(iter(filas.values())))
    lineas = ["| Elemento | " + " | ".join(columnas) + " |", "|---|" + "---|" * len(columnas)]
    for clave, campos in filas.items():
        celdas = " | ".join(_celda(campos.get(c, "")) for c in columnas)
        lineas.append(f"| {_celda(clave)} | {celdas} |")
    return lineas


def render_markdown(doc: DocumentoDiseno) -> str:
    """Documento completo: resumen, secciones emitidas y pendientes con su motivo."""
    salida = [
        f"# Diseño deducido de `{doc.programa}`",
        "",
        "Generado por sgm a partir del linaje del programa y de las decisiones declaradas en"
        " `decisiones/`. No sustituye la revisión de una persona: los pendientes dicen qué falta.",
        "",
        "## Resumen",
        "",
        "| Medida | Valor |",
        "|---|---|",
    ]
    for clave, valor in doc.resumen.items():
        salida.append(f"| {ETIQUETA_RESUMEN.get(clave, clave)} | {valor} |")
    for codigo, filas in doc.secciones.items():
        salida += ["", f"## {codigo}. {TITULOS.get(codigo, codigo)}", "", *_tabla(filas)]
    salida += ["", "## Pendientes y decisiones humanas", ""]
    if doc.pendientes:
        salida += ["| Qué | Motivo |", "|---|---|"]
        salida += [f"| {_celda(q)} | {_celda(m)} |" for q, m in doc.pendientes]
    else:
        salida.append("_Sin pendientes._")
    return "\n".join(salida) + "\n"
