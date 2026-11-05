"""Especificaciones de los casos L4 11 a 20 (segunda mitad; la primera está en especificaciones_l4).

Mismo formato que `especificaciones_l4.py`: entrada, asignaciones, salida y razonamiento.
"""

from __future__ import annotations

from .especificaciones_l4 import (
    _FUENTES_COALESCE,
    _FUENTES_COMPARACION,
    _FUENTES_ROUND,
    _FUENTES_SCAN,
    _FUENTES_SUBSTR,
    _FUENTES_TEXTO,
)

ESPECIFICACIONES_L4B: dict[str, dict] = {
    "l4_11_substr_posicion_longitud": {
        "construcciones": ["DATA STEP", "SUBSTR"],
        "entrada": (
            "CODIGOS_L4_11",
            ["ID", "CODIGO"],
            [("1", "ABCD1234"), ("2", "CUENTA-001"), ("3", "WXYZ")],
            (),
        ),
        "asignaciones": [
            ("SUBCODIGO", "CODIGO", (("substr", 2, 3),), "SUBCODIGO=substr(CODIGO, 2, 3);"),
            ("SUFIJO", "CODIGO", (("substr", 4, 2),), "SUFIJO=substr(CODIGO, 4, 2);"),
        ],
        "salida": "CODIGOS_PARTIDOS",
        "fuentes": [_FUENTES_SUBSTR],
        "invariantes": ["filas(CODIGOS_PARTIDOS) == 3"],
        "razonamiento": (
            "Posición y longitud; si la longitud pasa el final, llega al final (substr-01 y "
            "substr-02)."
        ),
    },
    "l4_12_substr_hasta_el_final": {
        "construcciones": ["DATA STEP", "SUBSTR"],
        "entrada": (
            "PRODUCTOS_L4_12",
            ["ID", "CODIGO"],
            [("1", "AB-000123"), ("2", "CD-000456"), ("3", "EF-7")],
            (),
        ),
        "asignaciones": [
            ("NUMERO", "CODIGO", (("substr", 4),), "NUMERO=substr(CODIGO, 4);"),
        ],
        "salida": "CODIGOS_NUMERO",
        "fuentes": [_FUENTES_SUBSTR],
        "invariantes": ["filas(CODIGOS_NUMERO) == 3"],
        "razonamiento": "Sin longitud, SUBSTR llega al final del valor (substr-01 documentado).",
    },
    "l4_13_substrn_numerico": {
        "construcciones": ["DATA STEP", "SUBSTRN"],
        "entrada": (
            "SALDOS_L4_13",
            ["ID", "SALDO"],
            [("1", 1234.5678), ("2", 98.7), ("3", 12345.5)],
            ("SALDO",),
        ),
        "asignaciones": [
            ("SALDO_TXT", "SALDO", (("substrn", 2, 6),), "SALDO_TXT=substrn(SALDO, 2, 6);"),
        ],
        "salida": "SALDOS_TEXTO",
        "fuentes": [_FUENTES_SUBSTR],
        "invariantes": ["filas(SALDOS_TEXTO) == 3"],
        "razonamiento": (
            "SUBSTRN toma el número sin blancos iniciales: 1234.5678 da 234.56 (substrn-01 "
            "documentado)."
        ),
    },
    "l4_14_scan_palabra": {
        "construcciones": ["DATA STEP", "SCAN"],
        "entrada": (
            "FRASES_L4_14",
            ["ID", "TEXTO"],
            [("1", "ABC.DEF(X=Y)"), ("2", "a  b"), ("3", " ab cd")],
            (),
        ),
        "asignaciones": [
            ("PALABRA_2", "TEXTO", (("scan", 2),), "PALABRA_2=scan(TEXTO, 2);"),
        ],
        "salida": "FRASES_PALABRA",
        "fuentes": [_FUENTES_SCAN],
        "invariantes": ["filas(FRASES_PALABRA) == 3"],
        "razonamiento": (
            "Delimitadores por omisión; los consecutivos y los de los extremos no cuentan "
            "(scan-01, scan-02, scan-03 documentados)."
        ),
    },
    "l4_15_scan_delimitador_fuera_de_rango": {
        "construcciones": ["DATA STEP", "SCAN"],
        "entrada": (
            "CAMPOS_L4_15",
            ["ID", "TEXTO"],
            [("1", "ab,cd,ef"), ("2", "a,b,,c"), ("3", "ab-cd")],
            (),
        ),
        "asignaciones": [
            ("CAMPO_2", "TEXTO", (("scan", 2, ","),), "CAMPO_2=scan(TEXTO, 2, ',');"),
        ],
        "salida": "CAMPOS_EXTRAIDOS",
        "fuentes": [_FUENTES_SCAN],
        "invariantes": ["filas(CAMPOS_EXTRAIDOS) == 3"],
        "razonamiento": (
            "Sin la palabra pedida, SCAN da un blanco (scan-04 y scan-06, este deducido). "
            "Delimitador explícito en scan-05."
        ),
    },
    "l4_16_trim_concat_sufijo": {
        "construcciones": ["DATA STEP", "TRIM", "CONCATENAR"],
        "entrada": (
            "CODIGOS_L4_16",
            ["ID", "CODIGO"],
            [("1", "AB  "), ("2", "XYZ "), ("3", "Q")],
            (),
        ),
        "asignaciones": [
            ("CODIGO_OK", "CODIGO", (("trim_concat", "-OK"),), "CODIGO_OK=trim(CODIGO)||'-OK';"),
        ],
        "salida": "CODIGOS_CON_SUFIJO",
        "fuentes": [_FUENTES_TEXTO],
        "invariantes": ["filas(CODIGOS_CON_SUFIJO) == 3"],
        "razonamiento": (
            "TRIM(x)||y quita los blancos finales antes de unir (concat-02 documentado, con el "
            "ejemplo de blackjack)."
        ),
    },
    "l4_17_coalescec_texto_vacio": {
        "construcciones": ["DATA STEP", "COALESCEC", "FALTANTES"],
        "entrada": (
            "CLIENTES_L4_17",
            ["ID", "CIUDAD"],
            [("1", ""), ("2", "   "), ("3", "Lima")],
            (),
        ),
        "asignaciones": [
            (
                "CIUDAD_OK",
                "CIUDAD",
                (("coalescec", "SIN CIUDAD"),),
                "CIUDAD_OK=coalescec(CIUDAD, 'SIN CIUDAD');",
            ),
        ],
        "salida": "CLIENTES_CIUDAD",
        "fuentes": [_FUENTES_COALESCE],
        "invariantes": ["filas(CLIENTES_CIUDAD) == 3"],
        "razonamiento": (
            "Un texto vacío o solo de blancos cuenta como faltante (coalescec-01 y coalescec-03 "
            "documentados)."
        ),
    },
    "l4_18_round_multiplo_y_mitad": {
        "construcciones": ["DATA STEP", "ROUND"],
        "entrada": (
            "MONTOS_L4_18",
            ["ID", "MONTO"],
            [("1", 1234.56789), ("2", 2.5), ("3", -2.5)],
            ("MONTO",),
        ),
        "asignaciones": [
            ("MONTO_CENT", "MONTO", (("round", 0.01),), "MONTO_CENT=round(MONTO, 0.01);"),
            ("MONTO_ENTERO", "MONTO", (("round", 1),), "MONTO_ENTERO=round(MONTO, 1);"),
        ],
        "salida": "MONTOS_REDONDEADOS",
        "fuentes": [_FUENTES_ROUND],
        "invariantes": [
            "filas(MONTOS_REDONDEADOS) == 3",
            "suma(MONTOS_REDONDEADOS.MONTO_ENTERO) == 1235",
        ],
        "razonamiento": (
            "round-03 (1234.57) y round-05/06 (la mitad va al de mayor valor absoluto: 3 y -3). "
            "Documentados."
        ),
    },
    "l4_19_cmp_faltantes": {
        "construcciones": ["DATA STEP", "COMPARACION", "FALTANTES", "IS MISSING"],
        "entrada": (
            "SALDOS_L4_19",
            ["ID", "SALDO"],
            [("1", 1200), ("2", 300), ("3", None), ("4", 500)],
            ("SALDO",),
        ),
        "asignaciones": [
            ("BAJO_500", "SALDO", (("cmp", "<", 500),), "BAJO_500 = (SALDO < 500);"),
            ("ES_FALTANTE", "SALDO", (("is_missing",),), "ES_FALTANTE = missing(SALDO);"),
        ],
        "salida": "SALDOS_MARCADOS",
        "fuentes": [_FUENTES_COMPARACION],
        "invariantes": [
            "filas(SALDOS_MARCADOS) == 4",
            "suma(SALDOS_MARCADOS.BAJO_500) == 2",
            "suma(SALDOS_MARCADOS.ES_FALTANTE) == 1",
        ],
        "razonamiento": (
            "En SAS el faltante numérico es menor que cualquier número: el faltante cuenta como "
            "menor de 500 (cmp-missing-01 documentado). Este resultado NO es el de SQL (ver "
            "DIFERENCIAS.md)."
        ),
    },
    "l4_20_put_fechas_pendiente": {
        "construcciones": ["DATA STEP", "PUT", "MDY", "INPUT YYMMDD10."],
        "entrada": (
            "FECHAS_L4_20",
            ["ID", "FECHA"],
            [("1", "2026-11-04"), ("2", "2026-03-01")],
            (),
        ),
        "asignaciones": [],
        "salida": "FECHAS_TEXTO",
        "fuentes": [],
        "invariantes": [],
        "pendiente": (
            "No hay vector de PUT, MDY ni de informat yymmdd10. en "
            "tests/corpus/semantica/vectores.yaml. Sin fuente no se fija el resultado; el caso "
            "queda para la tarea de semántica."
        ),
        "razonamiento": (
            "Caso reservado: el programa usa PUT y fechas, pero la capa B no las implementa "
            "todavía."
        ),
    },
}
