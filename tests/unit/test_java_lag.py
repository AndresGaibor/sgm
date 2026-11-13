"""B-13/B-14: el código Java de LAG y DIF hace lo que dice lefunctionsref (pp. 1163-1164 y 663).

El test compila y ejecuta el cuerpo de un `tJavaRow` con `javac` y `java` del JDK de Studio. Sin JDK se salta.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from sgm.talend_item.java_lag import codigo_lag

JAVA_STUDIO = Path("C:/Talend/8.0.1/zulu21.50.19-ca-jdk21.0.11-win_x64/bin")


def _jdk(herramienta: str) -> str | None:
    ruta = shutil.which(herramienta) or str(JAVA_STUDIO / f"{herramienta}.exe")
    return ruta if Path(ruta).exists() else None


def _ejecutar(cuerpo: str, filas: list[str], tmp_path: Path, tipo: str = "Double") -> list[str]:
    """Corre el cuerpo una vez por fila de entrada y devuelve la salida de `output_row.prev`."""
    javac, java = _jdk("javac"), _jdk("java")
    if not javac or not java:
        pytest.skip("no hay javac/java disponibles")
    lineas = "\n".join(
        f"""        {{
            Entrada input_row = new Entrada();
            input_row.x = {f};
            Salida output_row = new Salida();
{cuerpo}
            System.out.println(output_row.prev);
        }}"""
        for f in filas
    )
    fuente = f"""import java.util.Map;
public class Prueba {{
    static class Entrada {{ public {tipo} x; }}
    static class Salida {{ public {tipo} x; public Double prev; }}
    public static void main(String[] args) {{
        Map<String, Object> globalMap = new java.util.HashMap<>();
{lineas}
    }}
}}
"""
    (tmp_path / "Prueba.java").write_text(fuente, encoding="utf-8")
    subprocess.run([javac, "-d", str(tmp_path), str(tmp_path / "Prueba.java")], check=True)
    salida = subprocess.run(
        [java, "-cp", str(tmp_path), "Prueba"], check=True, capture_output=True, text=True
    )
    return salida.stdout.split()


def test_lag_con_if_solo_avanza_cuando_se_ejecuta(tmp_path):  # lefunctionsref, p. 1164
    # Igual que l6_40: la fila con x = -1 no cumple la condición y no entra en la cola.
    cuerpo = codigo_lag(
        "t1", "prev", "input_row.x", 1, ["x"],
        condicion="input_row.x != null && input_row.x > 0",
    )
    assert _ejecutar(cuerpo, ["2.0", "-1.0", "3.0"], tmp_path) == ["null", "null", "2.0"]


def test_dif_es_x_menos_su_lag_y_el_primero_falta(tmp_path):  # lefunctionsref, p. 663
    cuerpo = codigo_lag("t2", "prev", "input_row.x", 1, ["x"], dif=True)
    assert _ejecutar(cuerpo, ["2.0", "3.0", "5.0"], tmp_path) == ["null", "1.0", "2.0"]


def test_lag2_usa_una_cola_de_dos(tmp_path):  # lefunctionsref, p. 1164 (n faltantes al empezar)
    cuerpo = codigo_lag("t3", "prev", "input_row.x", 2, ["x"])
    assert _ejecutar(cuerpo, ["1.0", "2.0", "4.0"], tmp_path) == ["null", "null", "1.0"]


def test_el_nombre_de_la_cola_no_admite_caracteres_raros():
    with pytest.raises(ValueError):
        codigo_lag("t 4", "prev", "input_row.x", 1, ["x"])


def test_columna_entera_con_doublevalue_compila_y_da_lo_mismo(tmp_path):  # lefunctionsref, p. 1164
    # La expresión que usa el emisor: vale para cualquier columna numérica, no solo `Double`.
    valor = "(input_row.x == null ? null : input_row.x.doubleValue())"
    cuerpo = codigo_lag("t5", "prev", valor, 1, ["x"], condicion="input_row.x != null && input_row.x > 0")
    assert _ejecutar(cuerpo, ["2", "-1", "3"], tmp_path, tipo="Integer") == ["null", "null", "2.0"]
