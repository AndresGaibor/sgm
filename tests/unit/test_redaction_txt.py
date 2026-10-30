"""Redacción (F1.7): un programa SAS guardado como `.txt` también pierde sus credenciales."""

from sgm.redaction import redact

SECRETO = "SECRETO_DE_PRUEBA_123"
PROGRAMA = (
    f'proc sql;\n  connect to impala (user=u pass="{SECRETO}");\nquit;\n'
    f"proc pwencode in='{SECRETO}' out=work.k;\nrun;\n"
)


def test_txt_con_codigo_sas_se_redacta():
    limpio = redact(PROGRAMA, "lote/programa.txt")
    assert SECRETO not in limpio
    assert "***" in limpio


def test_sas_se_redacta_igual():
    assert SECRETO not in redact(PROGRAMA, "programa.sas")


def test_texto_sin_credenciales_no_cambia():
    texto = "data a; set b; x = 1; run;\n"
    assert redact(texto, "a.txt") == texto
