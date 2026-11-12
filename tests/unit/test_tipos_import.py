"""Tipos de columna que `PROC IMPORT` demuestra con su muestra de filas (B-2, MG-P1-02)."""

from sgm.migrar.tipos_import import TipoDemostrado, tipo_desde_muestra, tipos_de_archivo


def test_columna_numerica_en_la_muestra() -> None:
    tipo = tipo_desde_muestra(["1", "2", "3"])
    assert isinstance(tipo, TipoDemostrado)
    assert tipo.tipo_sas == "numerico"
    assert tipo.evidencia == 3
    assert "GUESSINGROWS=20" in tipo.fuente


def test_columna_con_texto_es_caracter() -> None:
    assert tipo_desde_muestra(["1", "x"]).tipo_sas == "caracter"


def test_sin_valores_no_se_inventa_tipo() -> None:
    assert tipo_desde_muestra(["", ""]) is None


def test_vacios_no_cuentan_contra_lo_numerico() -> None:
    tipo = tipo_desde_muestra(["", "5", "  "])
    assert tipo.tipo_sas == "numerico"
    assert tipo.evidencia == 1


def test_texto_fuera_de_la_muestra_se_marca_y_no_cambia_el_tipo() -> None:
    valores = [str(n) for n in range(1, 26)]
    valores[21] = "texto"  # fila 22: fuera de las primeras 20
    tipo = tipo_desde_muestra(valores, guessingrows=20)
    assert tipo.tipo_sas == "numerico"
    assert tipo.pendientes == ("P-TIPO-FUERA-DE-MUESTRA",)


def test_tipos_de_archivo_lee_las_columnas_por_nombre(tmp_path) -> None:
    ruta = tmp_path / "datos.csv"
    ruta.write_text("id,nombre\n1,ana\n2,luis\n", encoding="utf-8")
    tipos = tipos_de_archivo(ruta, ",", ["id", "nombre"])
    assert tipos["id"].tipo_sas == "numerico"
    assert tipos["nombre"].tipo_sas == "caracter"
