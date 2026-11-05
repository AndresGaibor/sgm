"""Prueba en Studio del filtro de una salida del `tMap` (`expressionFilter`), R1-01.

El emisor escribe `expressionFilter` y `activateExpressionFilter` en las salidas del `tMap` (ver
`tmap.py`), pero hasta ahora ningún Job con filtro se había **ejecutado**: solo compilado. Este
comando arma un Job mínimo con el modelo del emisor, lo ejecuta en el Studio instalado con un CSV de
prueba y muestra lo que salió por cada rama. Es la comprobación de la que dependen las validaciones
de `job_producto` (R1-04 a R1-09).

Job: `tFileInputDelimited` -> `tMap` con dos salidas (`validos` con filtro, `rechazados` como
rechazo de salida) -> dos `tFileOutputDelimited`.

Uso:
    uv run python tools/prueba_filtro_tmap.py --proyecto "$TALEND_PROJECT" \
        [--java-bin <jdk>/bin] [--m2 <caché .m2>] [--sufijo vN] [--trabajo CARPETA]

Código de salida: 0 si el Job terminó y cada fila fue por la rama esperada; 1 si no; 2 si el uso o
el proyecto no son válidos.
"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
import tempfile
from pathlib import Path

from mcp_cliente import MCP, ErrorValidacion
from validar_en_studio import (
    borrar_destino_build,
    construir,
    crear_destino_build,
    ejecutar,
    exportar,
    renombrar,
)

from sgm.talend_item.escritura import escribir_job
from sgm.talend_item.modelo import Columna, Conexion, Job, ParametroContexto
from sgm.talend_item.plantillas import nodo_desde_plantilla
from sgm.talend_item.tmap import EntradaMap, SalidaMap, tmap

# Entrada sin cabecera: dos columnas de texto separadas por `;`.
FILAS = (("1", "CC"), ("2", "AHO"), ("3", "CC"), ("4", "NEQUI"), ("5", "CC"))
FILTRO = 'row1.tipo.equals("CC")'
VALIDOS = [fila[0] for fila in FILAS if fila[1] == "CC"]
RECHAZADOS = [fila[0] for fila in FILAS if fila[1] != "CC"]
_EXTENSIONES = (".item", ".properties")
_TECNICO = re.compile(r'technicalLabel="([^"]+)"')


def job_filtro(columnas: list[Columna]) -> Job:
    """Job mínimo: lee el CSV y separa las filas que cumplen el filtro de las que no."""
    expresiones = {columna.nombre: f"row1.{columna.nombre}" for columna in columnas}
    nodos = [
        nodo_desde_plantilla(
            "tFileInputDelimited",
            "tFileInputDelimited_1",
            0,
            0,
            {"FILENAME": "context.ruta_origen", "FIELDSEPARATOR": '";"', "HEADER": "0"},
            columnas=columnas,
        ),
        tmap(
            "tMap_1",
            [EntradaMap("row1", columnas)],
            [
                SalidaMap("validos", columnas, expresiones, filtro=FILTRO),
                SalidaMap("rechazados", columnas, expresiones, rechazo=True),
            ],
            240,
            0,
        ),
        nodo_desde_plantilla(
            "tFileOutputDelimited",
            "tFileOutputDelimited_1",
            480,
            0,
            {
                "FILENAME": 'context.ruta_salida + "/validos.csv"',
                "FIELDSEPARATOR": '";"',
                "INCLUDEHEADER": "false",
                "APPEND": "false",
            },
            columnas=columnas,
        ),
        nodo_desde_plantilla(
            "tFileOutputDelimited",
            "tFileOutputDelimited_2",
            480,
            160,
            {
                "FILENAME": 'context.ruta_salida + "/rechazados.csv"',
                "FIELDSEPARATOR": '";"',
                "INCLUDEHEADER": "false",
                "APPEND": "false",
            },
            columnas=columnas,
        ),
    ]
    conexiones = [
        Conexion("tFileInputDelimited_1", "tMap_1", "row1"),
        Conexion("tMap_1", "tFileOutputDelimited_1", "validos"),
        Conexion("tMap_1", "tFileOutputDelimited_2", "rechazados", "REJECT"),
    ]
    contextos = {
        "Default": [
            ParametroContexto("ruta_origen"),
            ParametroContexto("ruta_salida"),
        ]
    }
    return Job("prueba_filtro_tmap", nodos=nodos, conexiones=conexiones, contextos=contextos)


def _ids(ruta: Path) -> list[str]:
    """Primera columna de cada fila del CSV, en orden; vacío si el archivo no existe."""
    if not ruta.is_file():
        return []
    texto = ruta.read_text(encoding="utf-8")
    return [linea.split(";")[0].strip() for linea in texto.splitlines() if linea]


def preparar_trabajo(trabajo: Path) -> None:
    """Escribe la entrada de prueba y deja la carpeta de salida vacía."""
    trabajo.mkdir(parents=True, exist_ok=True)
    (trabajo / "salida").mkdir(exist_ok=True)
    (trabajo / "entradas").mkdir(exist_ok=True)
    filas = "\n".join(";".join(fila) for fila in FILAS)
    (trabajo / "entradas" / "prueba.csv").write_text(filas + "\n", encoding="utf-8")


def proyecto_tecnico(proyecto: Path) -> str:
    """Nombre técnico del proyecto (`technicalLabel` de talend.project)."""
    archivo = proyecto / "talend.project"
    if archivo.is_file():
        coincide = _TECNICO.search(archivo.read_text(encoding="utf-8", errors="replace"))
        if coincide:
            return coincide.group(1)
    return proyecto.name


def validar(proyecto: Path, trabajo: Path, sufijo: str, java_bin: Path | None,
            m2: Path | None) -> int:
    """Ejecuta el Job en Studio y compara las ramas con lo esperado."""
    preparar_trabajo(trabajo)
    temporal = Path(tempfile.mkdtemp(prefix="jobs-"))
    exportado = crear_destino_build()
    cliente = MCP()
    copiados: list[Path] = []
    proceso = proyecto / "process"
    try:
        escribir_job(job_filtro([Columna("id"), Columna("tipo")]), temporal)
        renombres = renombrar(temporal, sufijo, proyecto_tecnico(proyecto))
        nombre = renombres["prueba_filtro_tmap"]
        for extension in _EXTENSIONES:
            origen = temporal / f"{nombre}_0.1{extension}"
            if origen.exists():
                destino = proceso / origen.name
                shutil.copyfile(origen, destino)
                copiados.append(destino)
        cliente.llamar("talend_bridge_refresh_workspace")
        construir(cliente, [nombre])
        lanzador = exportar(cliente, nombre, exportado, m2)
        resultado = ejecutar(
            lanzador,
            "Default",
            [
                f"ruta_origen={(trabajo / 'entradas' / 'prueba.csv').as_posix()}",
                f"ruta_salida={(trabajo / 'salida').as_posix()}",
            ],
            java_bin,
        )
    finally:
        for archivo in copiados:
            archivo.unlink(missing_ok=True)
        shutil.rmtree(temporal, ignore_errors=True)
        borrar_destino_build(exportado)
        try:
            cliente.llamar("talend_bridge_refresh_workspace")
        except ErrorValidacion:
            pass
    print(f"Comando: {resultado['comando']}")
    print(f"Código de salida: {resultado['exitCode']}")
    if resultado["stdout"]:
        print(f"Salida del Job (final):\n{resultado['stdout'][-2000:]}")
    if resultado["stderr"]:
        print(f"stderr (final):\n{resultado['stderr'][-1000:]}")
    validos, rechazados = _ids(trabajo / "salida" / "validos.csv"), _ids(
        trabajo / "salida" / "rechazados.csv"
    )
    print(f"validos.csv:    {validos}  (esperado {VALIDOS})")
    print(f"rechazados.csv: {rechazados}  (esperado {RECHAZADOS})")
    cuadra = resultado["exitCode"] == 0 and validos == VALIDOS and rechazados == RECHAZADOS
    print("RESULTADO:", "el filtro funciona" if cuadra else "el filtro NO coincide con lo esperado")
    return 0 if cuadra else 1


def main(argv: list[str] | None = None) -> int:
    for flujo in (sys.stdout, sys.stderr):
        if hasattr(flujo, "reconfigure"):
            flujo.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--proyecto", type=Path, required=True)
    parser.add_argument("--trabajo", type=Path, help="carpeta de trabajo (por defecto temporal)")
    parser.add_argument("--sufijo", help="sufijo nuevo de los Jobs (por defecto con fecha)")
    parser.add_argument("--java-bin", type=Path, help="carpeta bin del JDK de Studio")
    parser.add_argument("--m2", type=Path, help="caché .m2 de Studio para descargar poms")
    args = parser.parse_args(argv)
    if not (args.proyecto / "talend.project").is_file():
        print(f"error: no es un proyecto Talend: {args.proyecto}", file=sys.stderr)
        return 2
    from corpus_lib.studio_validar import sufijo_nuevo

    sufijo = args.sufijo or sufijo_nuevo()
    trabajo = args.trabajo or Path(tempfile.mkdtemp(prefix="prueba-filtro-"))
    print(f"Proyecto: {args.proyecto}\nSufijo: {sufijo}\nTrabajo: {trabajo}")
    try:
        return validar(args.proyecto, trabajo, sufijo, args.java_bin, args.m2)
    except ErrorValidacion as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
