"""R1-02: expresiones Java de normalización ejecutadas en Studio contra un oráculo independiente.

Arma un Job con un `tFixedFlowInput` de una sola fila y tantas columnas como vectores, un `tMap` que
aplica a cada columna su expresión (`input(left(x), w.d)`, COMPRESS, UPCASE, COMPBL, ...) y un
`tFileOutputDelimited` con cabecera. El esperado NO lo calcula este comando: sale de
`tools/corpus_semantica_funciones.py` para los vectores con fuente de `vectores.yaml`, y del
`esperado/` construido de `L8/validaciones/v06` para los nombres con ñ, tildes y espacios.

Uso:
    uv run python tools/prueba_normalizacion.py --proyecto "$TALEND_PROJECT" \
        [--java-bin <jdk>/bin] [--m2 <caché .m2>] [--sufijo vN] [--trabajo CARPETA]

Código de salida: 0 si todos los vectores coinciden; 1 si alguno no; 2 si el uso no es válido.
"""

from __future__ import annotations

import argparse
import csv
import re
import shutil
import sys
import tempfile
from decimal import Decimal, InvalidOperation
from pathlib import Path

from corpus_semantica import cargar_vectores
from corpus_semantica_funciones import Faltante, evaluar
from mcp_cliente import MCP, ErrorValidacion
from validar_en_studio import (
    borrar_destino_build,
    construir,
    crear_destino_build,
    ejecutar,
    exportar,
    renombrar,
)

from sgm.talend_item.componentes import fixed_flow_input
from sgm.talend_item.escritura import escribir_job
from sgm.talend_item.modelo import Columna, Conexion, Job, ParametroContexto
from sgm.talend_item.normalizacion import (
    as_text,
    compress,
    input_left_wd,
    left,
    literal_java,
    lowcase,
    normalizar_nombre,
    strip,
    trim,
    upcase,
)
from sgm.talend_item.plantillas import nodo_desde_plantilla
from sgm.talend_item.tmap import EntradaMap, SalidaMap, tmap

REPO = Path(__file__).resolve().parents[1]
V06 = REPO / "tests" / "corpus" / "L8" / "validaciones" / "v06_normalizacion"
ENTRADAS_V06 = V06 / "entradas" / "DETALLE_CTE.csv"
ESPERADO_V06 = V06 / "esperado" / "SABANA_NORM_CTE.csv"
FUNCIONES = {"input", "left", "compress", "strip", "trim", "upcase", "lowcase"}
N_NOMBRES = 16
SEPARADOR = "|"
_EXTENSIONES = (".item", ".properties")
_TECNICO = re.compile(r'technicalLabel="([^"]+)"')


def nombre_columna(identificador: str) -> str:
    """Nombre de columna de Talend a partir del id del vector."""
    return "v_" + re.sub(r"\W", "_", identificador)


def expresion(vector: dict, columna: str) -> str:
    """Expresión Java de un vector sobre `row1.<columna>`, convertida a texto para el CSV."""
    funcion = vector["funcion"]
    args = vector["entrada"]
    origen = f"row1.{columna}"
    if funcion == "input":
        cuerpo = input_left_wd(origen, int(args[1]), int(args[2]))
    elif funcion == "left":
        cuerpo = left(origen)
    elif funcion == "compress":
        chars = args[1] if len(args) > 1 else None
        mods = args[2] if len(args) > 2 else ""
        cuerpo = compress(origen, chars if isinstance(chars, str) else None, mods or "")
    elif funcion == "strip":
        cuerpo = strip(origen)
    elif funcion == "trim":
        cuerpo = trim(origen)
    elif funcion == "upcase":
        cuerpo = upcase(origen)
    elif funcion == "lowcase":
        cuerpo = lowcase(origen)
    elif funcion == "nombre_v06":
        cuerpo = normalizar_nombre(origen)
    else:
        raise ValueError(f"Función no soportada: {funcion}")
    return as_text(cuerpo)


def casos_semantica() -> list[dict]:
    """Vectores con fuente; el esperado lo calcula el oráculo de semántica, no este módulo."""
    casos: list[dict] = []
    for vector in cargar_vectores():
        if vector["funcion"] not in FUNCIONES:
            continue
        columna = nombre_columna(vector["id"])
        casos.append(
            {
                "id": vector["id"],
                "columna": columna,
                "entrada": vector["entrada"][0],
                "funcion": vector["funcion"],
                "args": vector["entrada"],
                "confianza": vector.get("confianza", ""),
                "esperado": evaluar(vector["funcion"], *vector["entrada"]),
                "expresion": expresion(vector, columna),
            }
        )
    return casos


def casos_nombres() -> list[dict]:
    """Nombres de v06 con su llave normalizada esperada, construida por el generador del corpus."""
    filas = [linea.split(";") for linea in ENTRADAS_V06.read_text(encoding="utf-8").splitlines()]
    with ESPERADO_V06.open(encoding="utf-8", newline="") as archivo:
        esperado = list(csv.DictReader(archivo))
    casos: list[dict] = []
    for n in range(N_NOMBRES):
        identificador = f"nombre_v06_{n + 1:02d}"
        columna = nombre_columna(identificador)
        vector = {"funcion": "nombre_v06", "entrada": [filas[n][7]]}
        casos.append(
            {
                "id": identificador,
                "columna": columna,
                "entrada": filas[n][7],
                "funcion": "nombre_v06",
                "args": [filas[n][7]],
                "confianza": "esperado del corpus",
                "esperado": esperado[n]["LLAVE_NORMALIZADA"],
                "expresion": expresion(vector, columna),
            }
        )
    return casos


def casos() -> list[dict]:
    return casos_semantica() + casos_nombres()


def job_normalizacion(lista: list[dict]) -> Job:
    """Un `tMap` con una columna de salida por vector, cada una con su expresión."""
    columnas = [Columna(caso["columna"]) for caso in lista]
    filas = [[literal_java(str(caso["entrada"])) for caso in lista]]
    expresiones = {caso["columna"]: caso["expresion"] for caso in lista}
    nodos = [
        fixed_flow_input("tFixedFlowInput_1", columnas, filas, 0, 0),
        tmap(
            "tMap_1",
            [EntradaMap("row1", columnas)],
            [SalidaMap("resultados", columnas, expresiones)],
            240,
            0,
        ),
        nodo_desde_plantilla(
            "tFileOutputDelimited",
            "tFileOutputDelimited_1",
            480,
            0,
            {
                "FILENAME": 'context.ruta_salida + "/resultados.csv"',
                "FIELDSEPARATOR": f'"{SEPARADOR}"',
                "INCLUDEHEADER": "true",
                "APPEND": "false",
            },
            columnas=columnas,
        ),
    ]
    conexiones = [
        Conexion("tFixedFlowInput_1", "tMap_1", "row1"),
        Conexion("tMap_1", "tFileOutputDelimited_1", "resultados"),
    ]
    contextos = {"Default": [ParametroContexto("ruta_salida")]}
    return Job("prueba_normalizacion", nodos=nodos, conexiones=conexiones, contextos=contextos)


def leer_resultados(ruta: Path) -> dict[str, str]:
    """Cabecera y única fila del CSV emitido: nombre de columna -> valor."""
    if not ruta.is_file():
        return {}
    with ruta.open(encoding="utf-8", newline="") as archivo:
        filas = list(csv.DictReader(archivo, delimiter=SEPARADOR))
    return filas[0] if filas else {}


def coincide(esperado: object, obtenido: str) -> bool:
    """Compara numéricamente los `input` y como texto exacto el resto."""
    if isinstance(esperado, Faltante):
        return obtenido == ""
    if isinstance(esperado, bool):
        return obtenido == str(esperado)
    if isinstance(esperado, (int, float)):
        try:
            return Decimal(obtenido) == Decimal(str(esperado))
        except (InvalidOperation, ValueError):
            return False
    return obtenido == str(esperado)


def informe(lista: list[dict], resultados: dict[str, str]) -> list[tuple[str, str, str, bool]]:
    filas = []
    for caso in lista:
        obtenido = resultados.get(caso["columna"], "<sin columna>")
        esperado = "" if isinstance(caso["esperado"], Faltante) else str(caso["esperado"])
        filas.append((caso["id"], esperado, obtenido, coincide(caso["esperado"], obtenido)))
    return filas


def proyecto_tecnico(proyecto: Path) -> str:
    archivo = proyecto / "talend.project"
    if archivo.is_file():
        coincide_ = _TECNICO.search(archivo.read_text(encoding="utf-8", errors="replace"))
        if coincide_:
            return coincide_.group(1)
    return proyecto.name


def preparar_trabajo(trabajo: Path) -> None:
    salida = trabajo / "salida"
    salida.mkdir(parents=True, exist_ok=True)
    (salida / "resultados.csv").unlink(missing_ok=True)


def validar(
    proyecto: Path,
    trabajo: Path,
    sufijo: str,
    java_bin: Path | None,
    m2: Path | None,
) -> int:
    """Ejecuta el Job en Studio y compara cada columna con su esperado independiente."""
    lista = casos()
    preparar_trabajo(trabajo)
    temporal = Path(tempfile.mkdtemp(prefix="jobs-"))
    exportado = crear_destino_build()
    cliente = MCP()
    copiados: list[Path] = []
    proceso = proyecto / "process"
    try:
        escribir_job(job_normalizacion(lista), temporal)
        renombres = renombrar(temporal, sufijo, proyecto_tecnico(proyecto))
        nombre = renombres["prueba_normalizacion"]
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
            [f"ruta_salida={(trabajo / 'salida').as_posix()}"],
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
    if resultado["exitCode"] != 0:
        print(f"Salida del Job (final):\n{resultado['stdout'][-2000:]}")
        print(f"stderr (final):\n{resultado['stderr'][-1000:]}")
    filas = informe(lista, leer_resultados(trabajo / "salida" / "resultados.csv"))
    for identificador, esperado, obtenido, ok in filas:
        print(
            f"{'OK ' if ok else 'FALLA'} {identificador}: "
            f"esperado {esperado!r}, obtenido {obtenido!r}"
        )
    fallan = [f[0] for f in filas if not f[3]]
    print(f"Vectores: {len(filas)}; coinciden: {len(filas) - len(fallan)}; fallan: {len(fallan)}")
    if fallan:
        print("Fallan:", ", ".join(fallan))
    cuadra = resultado["exitCode"] == 0 and not fallan and len(filas) == len(lista)
    print("RESULTADO:", "la normalización coincide con el oráculo" if cuadra else "hay diferencias")
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
    trabajo = args.trabajo or Path(tempfile.mkdtemp(prefix="prueba-normalizacion-"))
    print(f"Proyecto: {args.proyecto}\nSufijo: {sufijo}\nTrabajo: {trabajo}")
    try:
        return validar(args.proyecto, trabajo, sufijo, args.java_bin, args.m2)
    except ErrorValidacion as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
