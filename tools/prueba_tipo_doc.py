"""R1-03 / hito 85: ejecuta en Studio el `job_producto` **emitido** contra `v01_tipo_doc`.

No se construye un Job a mano: se emite con `sgm talend` (`emitir`), se toma solo el
`job_producto_0.1.item/.properties`, se compila, se exporta y se corre dos veces (CTE y AHO) con
las entradas del caso. Es la primera ejecución con datos del emisor desde R1-02.

Las variantes de códigos y sus esperados están en `tipo_doc_variantes.py`. `--sin-normalizar`
restaura `row1.TIPO_DOC` en el `tMap_normalizacion` del `.item` emitido: es un experimento del
arnés, no un cambio del producto, para medir la comparación de texto puro.

Uso:
    uv run python tools/prueba_tipo_doc.py --proyecto <carpeta> --variante ceros \
        [--excel-sin-ceros] [--sin-normalizar] [--sufijo v85a] [--trabajo DIR] \
        [--java-bin DIR] [--m2 DIR]

Código de salida 0 solo si el lanzador termina bien, se cumple
`origen == válidos + rechazados` y los conteos son los declarados para esa variante.
"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
import tempfile
from contextlib import ExitStack
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tools"))

from mcp_cliente import MCP, ErrorValidacion  # noqa: E402
from tipo_doc_variantes import (  # noqa: E402
    EXCEL,
    PRODUCTOS,
    VARIANTES,
    esperado_corpus,
    expectativa,
    informe,
    medir,
    preparar_entradas,
)
from validar_en_studio import (  # noqa: E402
    borrar_destino_build,
    construir,
    crear_destino_build,
    ejecutar,
    emitir,
    exportar,
    renombrar,
)

PROGRAMA = REPO / "tests" / "fixtures" / "sas" / "client" / "client_large.sas"
_EXTENSIONES = (".item", ".properties")
_EXPRESION = re.compile(r'(<mapperTableEntries name="TIPO_DOC" expression=")[^"]*(")')


def quitar_normalizacion(item: Path) -> None:
    """Experimento: deja `TIPO_DOC` crudo en el `tMap_normalizacion` del `.item` emitido."""
    texto = item.read_text(encoding="utf-8")
    reescrito, cambios = _EXPRESION.subn(r"\1row1.TIPO_DOC\2", texto, count=1)
    if cambios != 1:
        raise ErrorValidacion(f"no se encontró la expresión de TIPO_DOC en {item.name}")
    item.write_text(reescrito, encoding="utf-8", newline="\n")


def _proyecto_tecnico(proyecto: Path) -> str:
    archivo = proyecto / "talend.project"
    if archivo.is_file():
        coincide = re.search(r'technicalLabel="([^"]+)"', archivo.read_text(encoding="utf-8"))
        if coincide:
            return coincide.group(1)
    return proyecto.name


def parametros(trabajo: Path, producto: str) -> list[str]:
    entradas = (trabajo / "entradas").as_posix()
    return [
        f"producto={producto}",
        f"ruta_origen={entradas}/DETALLE_{producto}.csv",
        f"sufijo={producto}",
        "periodo_anio=2026",
        "periodo_mes=10",
        "periodo_dia=01",
        f"arch_hom_tipo_doc={EXCEL}",
        f"ruta_insumos={entradas}/",
        f"ruta_resultados={(trabajo / 'salida').as_posix()}/",
        "hoja_excel=Sheet1",
    ]


def validar(
    proyecto: Path,
    trabajo: Path,
    sufijo: str,
    variante: str,
    sin_normalizar: bool,
    excel_plano: bool,
    java_bin: Path | None,
    m2: Path | None,
) -> int:
    preparar_entradas(trabajo, variante, excel_plano)
    cliente = MCP()
    proceso = proyecto / "process"
    exportado = crear_destino_build()
    copiados: list[Path] = []
    buenos = 0
    try:
        with ExitStack() as pila:
            emision = Path(pila.enter_context(tempfile.TemporaryDirectory(prefix="emision-v01-")))
            carpeta = Path(pila.enter_context(tempfile.TemporaryDirectory(prefix="jobs-v01-")))
            emitido = emitir(PROGRAMA, None, emision)
            for extension in _EXTENSIONES:
                shutil.copyfile(
                    emitido / f"job_producto_0.1{extension}",
                    carpeta / f"job_producto_0.1{extension}",
                )
            if sin_normalizar:
                quitar_normalizacion(carpeta / "job_producto_0.1.item")
            nombre = renombrar(carpeta, sufijo, _proyecto_tecnico(proyecto))["job_producto"]
            for extension in _EXTENSIONES:
                origen = carpeta / f"{nombre}_0.1{extension}"
                if origen.is_file():
                    destino = proceso / origen.name
                    shutil.copyfile(origen, destino)
                    copiados.append(destino)
            cliente.llamar("talend_bridge_refresh_workspace")
            construir(cliente, [nombre])
            lanzador = exportar(cliente, nombre, exportado, m2)
            for producto in PRODUCTOS:
                corrida = ejecutar(lanzador, "Default", parametros(trabajo, producto), java_bin)
                print(f"Comando {producto}: {corrida['comando']}")
                print(f"Código de salida {producto}: {corrida['exitCode']}")
                if corrida["exitCode"] != 0:
                    print(f"stderr: {corrida['stderr'][-800:]}")
                observado = medir(corrida["stdout"], trabajo / "salida", producto)
                corpus = esperado_corpus(producto)
                esperado, motivo = expectativa(variante, sin_normalizar, excel_plano, corpus)
                if corrida["exitCode"] == 0 and informe(
                    producto, corpus, esperado, observado, motivo
                ):
                    buenos += 1
    finally:
        for archivo in copiados:
            archivo.unlink(missing_ok=True)
        borrar_destino_build(exportado)
        try:
            cliente.llamar("talend_bridge_refresh_workspace")
        except ErrorValidacion:
            pass
        print(f"Limpieza: {len(copiados)} archivos borrados del proyecto y build temporal borrado")
    print(f"RESULTADO: {buenos} de {len(PRODUCTOS)} productos reproducen lo esperado")
    return 0 if buenos == len(PRODUCTOS) else 1


def main(argv: list[str] | None = None) -> int:
    for flujo in (sys.stdout, sys.stderr):
        if hasattr(flujo, "reconfigure"):
            flujo.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--proyecto", type=Path, required=True)
    parser.add_argument("--variante", choices=VARIANTES, default="texto")
    parser.add_argument("--sin-normalizar", action="store_true")
    parser.add_argument(
        "--excel-sin-ceros",
        action="store_true",
        help="el Excel de homologación usa 1..4 aunque el CSV lleve 01..04",
    )
    parser.add_argument("--trabajo", type=Path)
    parser.add_argument("--sufijo", help="sufijo nuevo de los Jobs (por defecto con fecha)")
    parser.add_argument("--java-bin", type=Path)
    parser.add_argument("--m2", type=Path)
    args = parser.parse_args(argv)
    if not (args.proyecto / "talend.project").is_file():
        print(f"error: no es un proyecto Talend: {args.proyecto}", file=sys.stderr)
        return 2
    from corpus_lib.studio_validar import sufijo_nuevo

    sufijo = args.sufijo or sufijo_nuevo()
    trabajo = args.trabajo or Path(tempfile.mkdtemp(prefix="prueba-tipo-doc-"))
    print(
        f"Proyecto: {args.proyecto}\nVariante: {args.variante}; sin normalizar: "
        f"{args.sin_normalizar}; Excel sin ceros: {args.excel_sin_ceros}\n"
        f"Sufijo: {sufijo}\nTrabajo: {trabajo}"
    )
    try:
        return validar(
            args.proyecto, trabajo, sufijo, args.variante, args.sin_normalizar,
            args.excel_sin_ceros, args.java_bin, args.m2,
        )
    except ErrorValidacion as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
