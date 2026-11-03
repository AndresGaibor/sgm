"""Casos de borde de la entrada SAS: el lexer con `;` dentro de cadenas y comentarios, y el redactor
de credenciales con sus variantes (pwencode, password=, pw=, %let con clave).

El lexer sigue la regla de SAS: un comentario `* ...;` termina en el primer `;`, y un comentario
`/* ... */` termina en el primer `*/` (no se anida).
"""

from __future__ import annotations

import pytest

from sgm.frontend.lexer import split_statements
from sgm.redaction import redact


def _sentencias(texto: str) -> list[str]:
    return [s.text.strip() for s in split_statements(texto)]


@pytest.mark.parametrize(
    ("texto", "esperado"),
    [
        ("data a; x = 'a;b'; run;", ["data a", "x = 'a;b'", "run"]),
        ('data a; x = "c;d"; run;', ["data a", 'x = "c;d"', "run"]),
        ('%put "x;y";', ['%put "x;y"']),
        ("/* comentario; con punto y coma */ data a; set b; run;", ["data a", "set b", "run"]),
        ("/* a */ data a; run;", ["data a", "run"]),
        # Un comentario de sentencia termina en su primer `;`, como en SAS.
        ("* comentario;\ndata a; set b; run;", ["data a", "set b", "run"]),
        # El primer `*/` cierra el comentario (SAS no anida). El `*/` que sobra es un comentario de
        # sentencia: se traga el `run;`, igual que en SAS.
        ("/* a /* b */ c; */ run;", ["c"]),
    ],
)
def test_el_lexer_corta_en_los_punto_y_coma_correctos(texto, esperado):
    assert _sentencias(texto) == esperado


@pytest.mark.parametrize(
    "texto",
    [
        "proc pwencode in='Hola1' out=x; run;",
        "libname a odbc password=Secreto1 user=u;",
        'libname b odbc PASSWORD="Otro 2" user=u;',
        "libname c odbc password='Tercero' user=u;",
        "%let pwd = Clave9;",
        "libname d oracle user=u pw=Cuarta;",
    ],
)
def test_la_credencial_no_sale_en_claro(texto):
    secreto = next(
        tok
        for tok in ("Hola1", "Secreto1", "Otro 2", "Tercero", "Clave9", "Cuarta")
        if tok in texto
    )
    salida = redact(texto, "p.sas")
    assert secreto not in salida
    assert "***" in salida
