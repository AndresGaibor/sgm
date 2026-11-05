"""Especificaciones de los casos L5: macros simples (`%let`, `%macro`, `%if`, `%do`, `&var`).

El programa `programa.sas` (escrito a mano en la carpeta del caso) usa macros. El generador escribe
`programa_expandido.sas` con `expansor_macros.expandir`, y el oráculo SQL (capa A) calcula el
esperado sobre ese programa expandido. `into` indica las macrovariables que llenan
`SELECT ... INTO :var`: toman el valor de la primera fila de la columna indicada.

Datos ficticios: clientes y productos inventados.
"""

from __future__ import annotations

_URL_INTO = (
    "https://support.sas.com/documentation/cdl/en/sqlproc/63043/HTML/default/"
    "n1tupenuhmu1j0n19d3curl9igt4.htm"
)
_URL_MACROS = (
    "https://support.sas.com/documentation/cdl/en/mcrolref/62978/HTML/default/"
    "p1mw9xt2ti8f2xn1ozbct4305aqa.htm"
)

_LEALTAD = (
    ["ID", "SALDO", "ESTADO"],
    [
        (1, 150, "ACTIVO"),
        (2, 80, "INACTIVO"),
        (3, 220, "ACTIVO"),
        (4, 100, "ACTIVO"),
        (5, 45, "ACTIVO"),
        (6, 300, "INACTIVO"),
    ],
)
_AHORRO = (
    ["ID", "SALDO", "ESTADO"],
    [(1, 120, "ACTIVO"), (2, 480, "ACTIVO"), (3, 700, "INACTIVO"), (4, 500, "INACTIVO")],
)
_FECHAS = (["AÑO"], [(2026,), (2026,), (2025,)])

_BASE = {
    "capa": "A",
    "estado": "traducible",
    "fuentes": [_URL_MACROS],
}

ESPECIFICACIONES_L5: dict[str, dict] = {
    "l5_01_let_nombre_tabla": {
        "construcciones": ["%LET", "&VAR", "PROC SQL", "CREATE TABLE AS"],
        "entradas": {"DATOS_LEALTAD": _LEALTAD},
        "salidas": ["RES_LEALTAD"],
        "invariantes": ["filas(RES_LEALTAD) == 4"],
        "razonamiento": (
            "Macrovariable en el nombre de tabla y en el origen; el SQL se calcula sobre el "
            "programa expandido."
        ),
    },
    "l5_02_macro_con_parametros": {
        "construcciones": ["%MACRO", "PARAMETROS", "&VAR", "PROC SQL"],
        "entradas": {"DATOS_LEALTAD": _LEALTAD},
        "salidas": ["RES_LEALTAD"],
        "invariantes": ["filas(RES_LEALTAD) == 2"],
        "razonamiento": "Llamada con dos argumentos posicionales: producto y mínimo.",
    },
    "l5_03_dos_productos_misma_macro": {
        "construcciones": ["%MACRO", "LLAMADAS MULTIPLES", "PROC SQL"],
        "entradas": {"DATOS_LEALTAD": _LEALTAD, "DATOS_AHORRO": _AHORRO},
        "salidas": ["RES_LEALTAD", "RES_AHORRO"],
        "invariantes": ["filas(RES_LEALTAD) == 4", "filas(RES_AHORRO) == 2"],
        "razonamiento": "Una macro llamada dos veces con productos distintos genera dos tablas.",
    },
    "l5_04_if_then_else_macro": {
        "construcciones": ["%IF", "%THEN %DO", "%ELSE %DO", "PROC SQL"],
        "entradas": {"DATOS_LEALTAD": _LEALTAD, "DATOS_AHORRO": _AHORRO},
        "salidas": ["RES_TIPO"],
        "invariantes": ["filas(RES_TIPO) == 2"],
        "razonamiento": "La condición elige la rama; la rama de LEALTAD no se expande.",
    },
    "l5_05_macrovariable_en_ruta": {
        "construcciones": ["%LET", "&VAR", "RUTA CON COMILLAS DOBLES", "PROC EXPORT"],
        "entradas": {"DATOS_LEALTAD": _LEALTAD},
        "salidas": ["RES_LEALTAD"],
        "invariantes": ["filas(RES_LEALTAD) == 4"],
        "razonamiento": (
            "La ruta usa macrovariables entre comillas dobles, que SAS sí resuelve; no se crea "
            "archivo."
        ),
    },
    "l5_06_sysfunc_upcase": {
        "construcciones": ["%SYSFUNC", "UPCASE", "%LET", "PROC SQL"],
        "entradas": {"DATOS_LEALTAD": _LEALTAD},
        "salidas": ["RES_LEALTAD"],
        "invariantes": ["filas(RES_LEALTAD) == 4"],
        "razonamiento": (
            "%SYSFUNC(UPCASE(...)) de una macrovariable en minúsculas (upcase-01 documentado)."
        ),
    },
    "l5_07_eval_aritmetica": {
        "construcciones": ["%EVAL", "%LET", "PROC SQL"],
        "entradas": {"DATOS_LEALTAD": _LEALTAD},
        "salidas": ["RES_LIMITE"],
        "invariantes": ["filas(RES_LIMITE) == 1"],
        "razonamiento": "%EVAL con enteros: 100*2+50 vale 250.",
    },
    "l5_08_str_filtro_completo": {
        "construcciones": ["%STR", "%LET", "WHERE CON MACRO", "PROC SQL"],
        "entradas": {"DATOS_LEALTAD": _LEALTAD},
        "salidas": ["RES_FILTRO"],
        "invariantes": ["filas(RES_FILTRO) == 2"],
        "razonamiento": (
            "%STR guarda una condición con comillas simples y espacios; se pega en el WHERE."
        ),
    },
    "l5_09_into_primer_fila": {
        "construcciones": ["SELECT INTO", "PROC SQL", "&VAR"],
        "entradas": {"DATOS_LEALTAD": _LEALTAD, "VALIDACION_FECHA": _FECHAS},
        "into": {"ANIO": ("VALIDACION_FECHA", "AÑO")},
        "salidas": ["RES_ANIO"],
        "invariantes": ["filas(RES_ANIO) == 4", "valor(RES_ANIO.ANIO_CORTE) == 2026"],
        "razonamiento": (
            "SELECT ... INTO :var con varias filas toma la primera (documentacion de INTO, PROC "
            "SQL)."
        ),
    },
    "l5_10_macrovariables_en_nombre_tabla": {
        "construcciones": ["%LET", "&VAR", "NOMBRE COMPUESTO"],
        "entradas": {"DATOS_LEALTAD": _LEALTAD},
        "salidas": ["CORTE_20261104"],
        "invariantes": ["filas(CORTE_20261104) == 4"],
        "razonamiento": (
            "El nombre de la tabla se arma con &ANIO&MES&DIA. (el punto cierra el último)."
        ),
    },
    "l5_11_macro_llama_macro": {
        "construcciones": ["%MACRO", "LLAMADA ANIDADA", "PROC SQL"],
        "entradas": {"DATOS_LEALTAD": _LEALTAD},
        "salidas": ["BASE_LEALTAD", "DEP_LEALTAD"],
        "invariantes": ["filas(BASE_LEALTAD) == 6", "filas(DEP_LEALTAD) == 4"],
        "razonamiento": (
            "Una macro llama a otra con su parámetro; la segunda lee la tabla que creó la primera."
        ),
    },
    "l5_12_do_iterativo": {
        "construcciones": ["%DO ITERATIVO", "%MACRO", "PROC SQL"],
        "entradas": {"DATOS_LEALTAD": _LEALTAD},
        "salidas": ["PARTE_1", "PARTE_2"],
        "invariantes": ["filas(PARTE_1) == 3", "filas(PARTE_2) == 6"],
        "razonamiento": "%DO i=1 %TO 2 genera dos tablas; el límite se aplica con &i.*3.",
    },
}

ESPECIFICACIONES_L5 = {nombre: {**_BASE, **spec} for nombre, spec in ESPECIFICACIONES_L5.items()}
