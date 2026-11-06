"""Comando `sgm migrar`: un programa SAS a Jobs de Talend sin ningún YAML.

Lo que se prueba aquí no es la traducción —eso está en los módulos de `sgm.migrar` y en el emisor—
sino la promesa del comando: escribe los cinco documentos, dos corridas dan los mismos bytes, y
**nunca falla**: ni con un `PROC REG` que no sabe traducir, ni con un archivo que no es SAS, ni con
un backend que se rompe a mitad de la escritura. Cuando algo no se puede hacer, queda dicho en
`pendientes.md` con su línea.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from sgm.cli import app

RAIZ = Path(__file__).resolve().parents[1]
CORPUS = RAIZ / "corpus"
L2_01 = CORPUS / "L2" / "l2_01_inner_join_clientes_ventas" / "programa.sas"

runner = CliRunner()

# `PROC REG` no tiene emisor: es el caso mínimo de "esto no se traduce y hay que decirlo".
CON_REG = """PROC IMPORT DATAFILE='.../entradas/ventas.csv' OUT=WORK.VENTAS DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

PROC REG DATA=WORK.ventas;
  MODEL monto = cantidad;
RUN;
"""

BASURA = {
    "vacio": b"",
    "bytes_aleatorios": bytes(range(256)),
    "sas_truncado": b"PROC SQL; CREATE TABLE WORK.x AS SELECT ",
    "macro_sin_mend": b"%macro foo(a); data x; set y; run;",
}


def _correr(tmp_path: Path, programa: Path, salida: str = "salida"):
    return runner.invoke(app, ["migrar", str(programa), "--out", str(tmp_path / salida)])


def _archivos(carpeta: Path) -> set[str]:
    return {ruta.relative_to(carpeta).as_posix() for ruta in carpeta.rglob("*") if ruta.is_file()}


def _leer(carpeta: Path, nombre: str) -> str:
    return (carpeta / nombre).read_text(encoding="utf-8")


def test_migrar_l2_01_escribe_todo(tmp_path):
    resultado = _correr(tmp_path, L2_01)

    assert resultado.exit_code == 0, resultado.output
    carpeta = tmp_path / "salida" / "programa"
    archivos = _archivos(carpeta)
    assert any(nombre.startswith("process/") and nombre.endswith(".item") for nombre in archivos)
    assert any(nombre.startswith("process/") and nombre.endswith(".properties") for nombre in archivos)
    assert {f"contextos/{grupo}.yaml" for grupo in ("Default", "DEV", "QA", "PROD")} <= archivos
    assert {
        "pendientes.md",
        "configuracion-pendiente.md",
        "decisiones-tomadas.md",
        "trace.json",
        "migracion.log",
    } <= archivos


def test_sin_yaml_no_falla(tmp_path):
    # El caso del corpus no tiene `decisiones/`: el comando tiene que sacar el Job solo.
    assert not (L2_01.parent / "decisiones").exists()

    resultado = _correr(tmp_path, L2_01)

    assert resultado.exit_code == 0, resultado.output
    assert (tmp_path / "salida" / "programa" / "process").is_dir()


def test_determinismo(tmp_path):
    _correr(tmp_path, L2_01, salida="una")
    _correr(tmp_path, L2_01, salida="otra")

    primera, segunda = tmp_path / "una" / "programa", tmp_path / "otra" / "programa"
    archivos = _archivos(primera)
    assert archivos == _archivos(segunda)
    distintos = [
        nombre for nombre in sorted(archivos) if (primera / nombre).read_bytes() != (segunda / nombre).read_bytes()
    ]
    assert distintos == []


def test_pendientes_se_listan_con_codigo_y_linea(tmp_path):
    programa = tmp_path / "con_reg.sas"
    programa.write_text(CON_REG, encoding="utf-8")

    resultado = _correr(tmp_path, programa)

    assert resultado.exit_code == 0, resultado.output
    pendientes = _leer(tmp_path / "salida" / "con_reg", "pendientes.md")
    filas = [linea for linea in pendientes.splitlines() if "P-OPERADOR-SIN-SOPORTE" in linea]
    assert filas, pendientes
    # El `PROC REG` empieza en la línea 5 del programa y el pendiente lo dice.
    assert any("| 5 |" in fila for fila in filas), pendientes
    assert "PROC REG" in pendientes


@pytest.mark.parametrize("nombre", sorted(BASURA))
def test_entrada_basura_sale_con_0(tmp_path, nombre):
    programa = tmp_path / f"{nombre}.sas"
    programa.write_bytes(BASURA[nombre])

    resultado = _correr(tmp_path, programa)

    assert resultado.exit_code == 0, resultado.output
    assert "Traceback" not in resultado.output
    pendientes = _leer(tmp_path / "salida" / nombre, "pendientes.md")
    assert "P-" in pendientes
    assert "pendiente" in pendientes


def test_configuracion_pendiente_lista_las_variables_vacias(tmp_path):
    _correr(tmp_path, L2_01)

    configuracion = _leer(tmp_path / "salida" / "programa", "configuracion-pendiente.md")
    assert "`ruta_clientes`" in configuracion
    assert "`ruta_ventas`" in configuracion
    assert "ruta del archivo de clientes" in configuracion


def test_un_fallo_interno_no_deja_carpeta_a_medias(tmp_path, monkeypatch):
    def romper(job, carpeta, fecha=None):
        raise OSError("disco lleno")

    monkeypatch.setattr("sgm.backend_talend.archivos.escribir_job", romper)

    resultado = _correr(tmp_path, L2_01)

    assert resultado.exit_code == 0, resultado.output
    carpeta = tmp_path / "salida" / "programa"
    archivos = _archivos(carpeta)
    assert {"pendientes.md", "configuracion-pendiente.md", "trace.json", "migracion.log"} <= archivos
    assert "disco lleno" in _leer(carpeta, "migracion.log")
    assert "P-FALLO-ESCRITURA" in _leer(carpeta, "pendientes.md")


def test_un_programa_que_no_se_puede_leer_no_lanza(tmp_path):
    """La fecha de los `.properties` sale del archivo; sin archivo tiene que haber respaldo.

    En Windows `datetime.fromtimestamp(0)` levanta `OSError`, así que el respaldo de un programa
    ilegible tumbaba `migrar` justo cuando el informe importa.
    """
    from sgm.cli_migrar import migrar

    resultado = migrar(tmp_path / "no_existe.sas", tmp_path / "salida")

    assert resultado.carpeta.is_dir()
    assert {p.codigo for p in resultado.pendientes} == {"P-PROGRAMA-ILLEGIBLE"}
    assert (resultado.carpeta / "pendientes.md").is_file()
