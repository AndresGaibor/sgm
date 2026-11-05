"""Especificaciones de los casos L4: funciones de DATA step con vectores de la capa B.

Cada caso declara su entrada (columnas, filas y cuáles son numéricas), sus asignaciones y la tabla
de salida. Una asignación es `(variable, columna, pasos, texto_sas)`: `pasos` son tuplas
`(función, argumentos extra...)` que se aplican en orden sobre el valor de `columna`, y
`texto_sas` es la sentencia tal como aparece en `programa.sas` (la prueba comprueba que lo está).

El esperado sale de la capa B (`corpus_semantica_funciones.evaluar`), no del SQL. Un faltante
numérico es `None` en la fila y `.` en SAS; un faltante de texto es cadena vacía (blanco). Un
caso con `pendiente` no tiene esperado: su función no tiene vector.
"""

from __future__ import annotations

_FUENTES_LEFT = (
    "https://support.sas.com/documentation/cdl/en/lefunctionsref/63354/HTML/default/"
    "n1awii5zy0u6g0n1fy6yu1hwqiw4.htm"
)
_FUENTES_INPUT = (
    "https://support.sas.com/documentation/cdl/en/leforinforref/64790/HTML/default/"
    "n14sqpf1cubqknn1vmkzkp1oph87.htm"
)
_FUENTES_COMPRESS = (
    "https://support.sas.com/documentation/cdl/en/lefunctionsref/63354/HTML/default/"
    "n0fcshr0ir3h73n1b845c4aq58hz.htm"
)
_FUENTES_STRIP = (
    "https://support.sas.com/documentation/cdl/en/lefunctionsref/63354/HTML/default/"
    "n0xk6tl87f4b4qn1sp1ywen1ntan.htm"
)
_FUENTES_SUBSTR = (
    "https://support.sas.com/documentation/cdl/en/lrdict/64316/HTML/default/a002255112.htm"
)
_FUENTES_SCAN = (
    "https://support.sas.com/documentation/cdl/en/lefunctionsref/63354/HTML/default/"
    "p0jshdjy2z9zdzn1h7k90u99lyq6.htm"
)
_FUENTES_ROUND = (
    "https://support.sas.com/documentation/cdl/en/lefunctionsref/63354/HTML/default/"
    "p0tj6cmga7p8qln1ejh6ebevm0c9.htm"
)
_FUENTES_COMPARACION = (
    "https://support.sas.com/documentation/cdl/en/lrcon/65287/HTML/default/"
    "p00iah2thp63bmn1lt20esag14lh.htm"
)
_FUENTES_COALESCE = (
    "https://support.sas.com/documentation/cdl/en/lefunctionsref/63354/HTML/default/"
    "p1g9btrql8d9x6n1iz6yowaqrq1v.htm"
)
_FUENTES_TEXTO = "https://support.sas.com/documentation/cdl/en/lrcon/65287/HTML/default/p00iah2thp63bmn1lt20esag14lh.htm"

ESPECIFICACIONES_L4: dict[str, dict] = {
    "l4_01_input_left_numerico": {
        "construcciones": ["DATA STEP", "INPUT", "LEFT", "FALTANTES"],
        "entrada": (
            "CUENTAS_L4_01",
            ["ID", "VAR7"],
            [("1", "   1234567"), ("2", "  7654321"), ("3", "1000001")],
            (),
        ),
        "asignaciones": [
            ("NRO_CTA", "VAR7", (("left",), ("input", 30, 0)), "NRO_CTA=input(left(VAR7), 30.);"),
        ],
        "salida": "CUENTAS_CONVERTIDAS",
        "fuentes": [_FUENTES_LEFT, _FUENTES_INPUT],
        "invariantes": [
            "filas(CUENTAS_CONVERTIDAS) == filas(CUENTAS_L4_01)",
            "suma(CUENTAS_CONVERTIDAS.NRO_CTA) == 9888889",
        ],
        "razonamiento": (
            "left y input con informat 30. (vectores left-01, input-07 y input-01). Cuentas "
            "ficticias."
        ),
    },
    "l4_02_input_decimales_signo": {
        "construcciones": ["DATA STEP", "INPUT", "FALTANTES"],
        "entrada": (
            "IMPORTES_L4_02",
            ["ID", "IMPORTE"],
            [
                ("1", "23.0"),
                ("2", "123.456"),
                ("3", "23."),
                ("4", "2300"),
                ("5", "-2300"),
                ("6", "0023"),
            ],
            (),
        ),
        "asignaciones": [
            ("IMP_NUM", "IMPORTE", (("input", 8, 2),), "IMP_NUM=input(IMPORTE, 8.2);"),
        ],
        "salida": "IMPORTES_CONVERTIDOS",
        "fuentes": [_FUENTES_INPUT],
        "invariantes": [
            "filas(IMPORTES_CONVERTIDOS) == 6",
            "suma(IMPORTES_CONVERTIDOS.IMP_NUM) == 169.686",
        ],
        "razonamiento": (
            "w.d con punto decimal ignora d (input-01, input-02, input-03); sin punto d=2 "
            "(input-04, input-05, input-06, deducidos de la misma regla)."
        ),
    },
    "l4_03_input_punto_y_texto_invalido": {
        "construcciones": ["DATA STEP", "INPUT", "FALTANTES"],
        "entrada": (
            "CODIGOS_L4_03",
            ["ID", "CODIGO"],
            [("1", "12.5"), ("2", "."), ("3", "abc"), ("4", "7.25")],
            (),
        ),
        "asignaciones": [
            ("CODIGO_NUM", "CODIGO", (("input", 6, 2),), "CODIGO_NUM=input(CODIGO, 6.2);"),
        ],
        "salida": "CODIGOS_VALIDOS",
        "fuentes": [_FUENTES_INPUT],
        "invariantes": [
            "filas(CODIGOS_VALIDOS) == 4",
            "suma(CODIGOS_VALIDOS.CODIGO_NUM) == 19.75",
        ],
        "razonamiento": (
            "Un punto solo es faltante (input-09 documentado). El texto 'abc' da faltante "
            "(input-10 deducido). Las dos filas quedan vacías."
        ),
    },
    "l4_04_compress_blancos": {
        "construcciones": ["DATA STEP", "COMPRESS"],
        "entrada": (
            "NOMBRES_L4_04",
            ["ID", "DESCRIPCION"],
            [("1", "AB C D "), ("2", " 12 34"), ("3", "Ana   Lopez")],
            (),
        ),
        "asignaciones": [
            ("CLAVE", "DESCRIPCION", (("compress",),), "CLAVE=compress(DESCRIPCION);"),
        ],
        "salida": "NOMBRES_LIMPIOS",
        "fuentes": [_FUENTES_COMPRESS],
        "invariantes": ["filas(NOMBRES_LIMPIOS) == 3"],
        "razonamiento": (
            "Sin lista de caracteres, COMPRESS quita blancos (compress-01 documentado)."
        ),
    },
    "l4_05_compress_lista_caracteres": {
        "construcciones": ["DATA STEP", "COMPRESS"],
        "entrada": (
            "REFERENCIAS_L4_05",
            ["ID", "REF"],
            [("1", "A1B2-3"), ("2", "X12Y"), ("3", "Z-9")],
            (),
        ),
        "asignaciones": [
            ("REF_LIMPIA", "REF", (("compress", "12"),), "REF_LIMPIA=compress(REF, '12');"),
        ],
        "salida": "REFERENCIAS_LIMPIAS",
        "fuentes": [_FUENTES_COMPRESS],
        "invariantes": ["filas(REFERENCIAS_LIMPIAS) == 3"],
        "razonamiento": "Los caracteres del segundo argumento se quitan (compress-02 documentado).",
    },
    "l4_06_compress_modificador_k": {
        "construcciones": ["DATA STEP", "COMPRESS"],
        "entrada": (
            "CLAVES_L4_06",
            ["ID", "CLAVE"],
            [("1", "ABCABX"), ("2", "DCBA99"), ("3", "ZABX")],
            (),
        ),
        "asignaciones": [
            (
                "CLAVE_K",
                "CLAVE",
                (("compress", "ABCD", "k"),),
                "CLAVE_K=compress(CLAVE, 'ABCD', 'k');",
            ),
        ],
        "salida": "CLAVES_K",
        "fuentes": [_FUENTES_COMPRESS],
        "invariantes": ["filas(CLAVES_K) == 3"],
        "razonamiento": (
            "Con la K solo se conservan los caracteres de la lista (compress-04 documentado)."
        ),
    },
    "l4_07_compress_clase_digitos": {
        "construcciones": ["DATA STEP", "COMPRESS"],
        "entrada": (
            "PLACAS_L4_07",
            ["ID", "CODIGO"],
            [("1", "a1b2"), ("2", "C3-D4"), ("3", "9X")],
            (),
        ),
        "asignaciones": [
            (
                "SOLO_LETRAS",
                "CODIGO",
                (("compress", "", "d"),),
                "SOLO_LETRAS=compress(CODIGO, '', 'd');",
            ),
        ],
        "salida": "PLACAS_SIN_DIGITOS",
        "fuentes": [_FUENTES_COMPRESS],
        "invariantes": ["filas(PLACAS_SIN_DIGITOS) == 3"],
        "razonamiento": (
            "El modificador D añade los dígitos a la lista de quitados (compress-05 documentado)."
        ),
    },
    "l4_08_compress_ignora_mayusculas": {
        "construcciones": ["DATA STEP", "COMPRESS"],
        "entrada": (
            "CODIGOS_L4_08",
            ["ID", "COD"],
            [("1", "Ab1"), ("2", "AAa2"), ("3", "Bb3")],
            (),
        ),
        "asignaciones": [
            ("COD_SIN_A", "COD", (("compress", "a", "i"),), "COD_SIN_A=compress(COD, 'a', 'i');"),
        ],
        "salida": "CODIGOS_SIN_A",
        "fuentes": [_FUENTES_COMPRESS],
        "invariantes": ["filas(CODIGOS_SIN_A) == 3"],
        "razonamiento": "El modificador I ignora mayúsculas en la lista (compress-07 documentado).",
    },
    "l4_09_strip_blancos": {
        "construcciones": ["DATA STEP", "STRIP", "FALTANTES"],
        "entrada": (
            "TEXTOS_L4_09",
            ["ID", "TEXTO"],
            [("1", "  abcd  "), ("2", " x y z"), ("3", "Lima   "), ("4", "   ")],
            (),
        ),
        "asignaciones": [
            ("TEXTO_LIMPIO", "TEXTO", (("strip",),), "TEXTO_LIMPIO=strip(TEXTO);"),
        ],
        "salida": "TEXTOS_LIMPIOS",
        "fuentes": [_FUENTES_STRIP],
        "invariantes": ["filas(TEXTOS_LIMPIOS) == 4"],
        "razonamiento": (
            "STRIP quita blancos de ambos lados; un campo en blanco da cadena vacía (strip-01 y "
            "strip-02 documentados)."
        ),
    },
    "l4_10_upcase_lowcase": {
        "construcciones": ["DATA STEP", "UPCASE", "LOWCASE"],
        "entrada": (
            "NOMBRES_L4_10",
            ["ID", "NOMBRE", "CODIGO"],
            [("1", "John B. Smith", "IntroDuccion"), ("2", "ana maria", "INTRODUCTION")],
            (),
        ),
        "asignaciones": [
            ("NOMBRE_MAYUS", "NOMBRE", (("upcase",),), "NOMBRE_MAYUS=upcase(NOMBRE);"),
            ("CODIGO_MIN", "CODIGO", (("lowcase",),), "CODIGO_MIN=lowcase(CODIGO);"),
        ],
        "salida": "NOMBRES_NORMALIZADOS",
        "fuentes": [_FUENTES_TEXTO],
        "invariantes": ["filas(NOMBRES_NORMALIZADOS) == 2"],
        "razonamiento": "UPCASE (upcase-01, pagina de FedSQL) y LOWCASE (lowcase-01).",
    },
}
