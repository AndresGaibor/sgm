"""Comando `sgm migrar`: un programa SAS a Jobs de Talend sin ningún YAML.

Lo que se prueba aquí no es la traducción —eso está en los módulos de `sgm.migrar` y en el emisor—
sino la promesa del comando: escribe los informes, dos corridas dan los mismos bytes, y
**nunca falla**: ni con un `PROC REG` que no sabe traducir, ni con un archivo que no es SAS, ni con
un backend que se rompe a mitad de la escritura. Cuando algo no se puede hacer, queda dicho en
`pendientes.md` con su línea.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from sgm.cli import app

RAIZ = Path(__file__).resolve().parents[1]
CORPUS = RAIZ / "corpus"
L2_01 = CORPUS / "L2" / "l2_01_inner_join_clientes_ventas" / "programa.sas"

runner = CliRunner()


def test_migrar_command_conserva_importacion_legacy():
    from sgm.cli_migrar import migrar_command
    from sgm.cli_migrar_comando import migrar_command as command

    assert migrar_command is command

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
        "cobertura.md",
        "trace.json",
        "migracion.log",
    } <= archivos

    cobertura = _leer(carpeta, "cobertura.md")
    traza = json.loads(_leer(carpeta, "trace.json"))
    lineas_trazadas = {
        linea for nodos in traza["jobs"].values() for lineas in nodos.values() for linea in lineas
    }
    assert "# Cobertura de migración" in cobertura
    assert all(f"| {linea} |" in cobertura for linea in lineas_trazadas)
    assert "porcentaje de líneas" in cobertura.lower()


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
    cobertura = _leer(tmp_path / "salida" / "con_reg", "cobertura.md")
    assert "P-OPERADOR-SIN-SOPORTE" in cobertura
    assert "| 5 |" in cobertura


def test_migrar_carpeta_conserva_rutas_y_nombres_repetidos(tmp_path):
    fuente = tmp_path / "programas"
    anidada = fuente / "subcarpeta"
    anidada.mkdir(parents=True)
    texto = L2_01.read_text(encoding="utf-8")
    (fuente / "programa.sas").write_text(texto, encoding="utf-8")
    (anidada / "programa.sas").write_text(texto, encoding="utf-8")
    (fuente / "ignorar.txt").write_text("no es SAS", encoding="utf-8")

    resultado = runner.invoke(app, ["migrar", str(fuente), "--out", str(tmp_path / "salida")])

    assert resultado.exit_code == 0, resultado.output
    assert "2 programa(s)" in resultado.output
    for carpeta in (tmp_path / "salida" / "programa", tmp_path / "salida" / "subcarpeta" / "programa"):
        assert (carpeta / "trace.json").is_file()
        assert (carpeta / "cobertura.md").is_file()
        assert any((carpeta / "process").glob("*.item"))
    assert not (tmp_path / "salida" / "ignorar").exists()


def test_migrar_carpeta_vacia_informa_sin_fallar(tmp_path):
    fuente = tmp_path / "vacia"
    fuente.mkdir()

    resultado = runner.invoke(app, ["migrar", str(fuente), "--out", str(tmp_path / "salida")])

    assert resultado.exit_code == 0, resultado.output
    assert "No hay programas SAS" in resultado.output


def test_migrar_carpeta_es_determinista(tmp_path):
    fuente = tmp_path / "programas"
    fuente.mkdir()
    (fuente / "programa.sas").write_text(L2_01.read_text(encoding="utf-8"), encoding="utf-8")

    primera = runner.invoke(app, ["migrar", str(fuente), "--out", str(tmp_path / "una")])
    segunda = runner.invoke(app, ["migrar", str(fuente), "--out", str(tmp_path / "otra")])

    assert primera.exit_code == 0, primera.output
    assert segunda.exit_code == 0, segunda.output
    una, otra = tmp_path / "una" / "programa", tmp_path / "otra" / "programa"
    archivos = _archivos(una)
    assert archivos == _archivos(otra)
    assert all((una / nombre).read_bytes() == (otra / nombre).read_bytes() for nombre in archivos)


def test_migrar_carpeta_valida_backend_antes_de_escribir(tmp_path):
    fuente = tmp_path / "programas"
    fuente.mkdir()
    (fuente / "programa.sas").write_text(L2_01.read_text(encoding="utf-8"), encoding="utf-8")
    salida = tmp_path / "salida"

    resultado = runner.invoke(
        app, ["migrar", str(fuente), "--out", str(salida), "--backend", "desconocido"]
    )

    assert resultado.exit_code == 2
    assert "backend desconocido" in resultado.output
    assert not salida.exists()


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
    if nombre == "vacio":
        cobertura = _leer(tmp_path / "salida" / nombre, "cobertura.md")
        assert "P-SIN-PASOS" in cobertura
        assert "Pendientes sin línea" in cobertura


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


SECRETO_PLANTADO = "Zx9-ficticio-123"


def test_migrar_no_publica_paquete_con_secreto_y_no_lo_muestra(tmp_path, monkeypatch):
    from sgm.backend_talend.archivos import escribir_job as escritura_original

    def escribir_con_secreto(job, carpeta, fecha=None):
        rutas = escritura_original(job, carpeta, fecha)
        item = next(ruta for ruta in rutas if ruta.suffix == ".item")
        item.write_text(
            item.read_text(encoding="utf-8") + f"\n# password={SECRETO_PLANTADO}\n",
            encoding="utf-8",
        )
        return rutas

    monkeypatch.setattr("sgm.backend_talend.archivos.escribir_job", escribir_con_secreto)

    resultado = _correr(tmp_path, L2_01)

    assert resultado.exit_code == 1, resultado.output
    assert SECRETO_PLANTADO not in resultado.output
    assert "password_en_cadena" in resultado.output
    assert "no publicado" in resultado.output
    assert not (tmp_path / "salida" / "programa").exists()


def test_migrar_no_modifica_paquete_existente_con_hallazgo(tmp_path):
    destino = tmp_path / "salida" / "programa"
    destino.mkdir(parents=True)
    previo = destino / "manual.txt"
    previo.write_text(f"password={SECRETO_PLANTADO}\n", encoding="utf-8")

    resultado = _correr(tmp_path, L2_01)

    assert resultado.exit_code == 1, resultado.output
    assert SECRETO_PLANTADO not in resultado.output
    assert previo.read_text(encoding="utf-8") == f"password={SECRETO_PLANTADO}\n"
    assert not (destino / "process").exists()


def test_migrar_falla_cerrado_si_no_puede_comprobar(tmp_path, monkeypatch):
    from sgm.seguridad import escaner_secretos

    def fallar(_ruta):
        raise OSError(f"fallo de lectura que no debe exponerse {SECRETO_PLANTADO}")

    monkeypatch.setattr(escaner_secretos, "escanear_ruta", fallar)

    resultado = _correr(tmp_path, L2_01)

    assert resultado.exit_code == 1, resultado.output
    assert "no se pudo completar" in resultado.output
    assert SECRETO_PLANTADO not in resultado.output
    assert not (tmp_path / "salida" / "programa").exists()


@pytest.mark.parametrize("metodo", ("is_symlink", "is_junction"))
def test_compuerta_rechaza_la_ruta_destino_si_es_enlace(tmp_path, monkeypatch, metodo):
    from pathlib import Path

    from sgm.seguridad.compuerta_migracion import publicar_con_revision

    destino = tmp_path / "programa"
    metodo_original = getattr(Path, metodo)

    def es_enlace(ruta):
        return ruta == destino or metodo_original(ruta)

    monkeypatch.setattr(Path, metodo, es_enlace)
    llamada = False

    def generar(_destino):
        nonlocal llamada
        llamada = True

    resultado = publicar_con_revision(destino, generar)

    assert not resultado.publicado
    assert "enlace simbólico" in resultado.motivo
    assert not llamada


def test_compuerta_rechaza_enlace_dentro_del_paquete(tmp_path, monkeypatch):
    from pathlib import Path

    from sgm.seguridad.compuerta_migracion import publicar_con_revision

    destino = tmp_path / "programa"
    destino.mkdir()
    enlace = destino / "manual.txt"
    enlace.write_text("archivo simulado como enlace", encoding="utf-8")
    is_symlink_original = Path.is_symlink

    def es_enlace(ruta):
        return ruta == enlace or is_symlink_original(ruta)

    monkeypatch.setattr(Path, "is_symlink", es_enlace)
    resultado = publicar_con_revision(destino, lambda _carpeta: None)

    assert not resultado.publicado
    assert "enlace simbólico" in resultado.motivo


def test_migrar_conserva_archivos_manuales_del_paquete(tmp_path):
    destino = tmp_path / "salida" / "programa"
    destino.mkdir(parents=True)
    manual = destino / "nota-operativa.md"
    manual.write_text("Revisar el contexto QA antes de ejecutar.\n", encoding="utf-8")

    resultado = _correr(tmp_path, L2_01)

    assert resultado.exit_code == 0, resultado.output
    assert manual.read_text(encoding="utf-8") == "Revisar el contexto QA antes de ejecutar.\n"
    assert any((destino / "process").glob("*.item"))


def test_migrar_lote_publica_limpios_y_falla_si_uno_se_bloquea(tmp_path, monkeypatch):
    from sgm.backend_talend.archivos import escribir_job as escritura_original

    fuente = tmp_path / "programas"
    fuente.mkdir()
    texto = L2_01.read_text(encoding="utf-8")
    (fuente / "limpio.sas").write_text(texto, encoding="utf-8")
    (fuente / "filtrado.sas").write_text(texto, encoding="utf-8")

    def escribir_uno_con_secreto(job, carpeta, fecha=None):
        rutas = escritura_original(job, carpeta, fecha)
        if carpeta.parent.name == "filtrado":
            item = next(ruta for ruta in rutas if ruta.suffix == ".item")
            item.write_text(
                item.read_text(encoding="utf-8") + f"\n# password={SECRETO_PLANTADO}\n",
                encoding="utf-8",
            )
        return rutas

    monkeypatch.setattr("sgm.backend_talend.archivos.escribir_job", escribir_uno_con_secreto)

    resultado = runner.invoke(app, ["migrar", str(fuente), "--out", str(tmp_path / "salida")])

    assert resultado.exit_code == 1, resultado.output
    assert SECRETO_PLANTADO not in resultado.output
    assert (tmp_path / "salida" / "limpio" / "trace.json").is_file()
    assert not (tmp_path / "salida" / "filtrado").exists()
