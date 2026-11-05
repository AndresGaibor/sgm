"""R1-01 (cierre): filtro del `tMap` sobre una columna nula de un `LEFT JOIN`.

El hito 81 probó `expressionFilter` con texto no nulo y dejó anotado el riesgo: en `job_producto`
la columna filtrada viene de un lookup, y una fila sin pareja deja `row2.<columna>` a `null`, así
que `row2.columna.equals("CC")` lanza `NullPointerException`. Este comando arma un Job mínimo con
un lookup sin `innerJoin` (LEFT JOIN), ejecuta las dos formas del filtro en Studio y muestra el
resultado de cada rama.

Job: dos `tFixedFlowInput` (lookup y principal) -> `tMap` con salida filtrada y salida de rechazo
-> dos `tFileOutputDelimited`. Tres de las seis filas principales no tienen pareja en el lookup.

Uso:
    uv run python tools/prueba_filtro_nulo.py --proyecto "$TALEND_PROJECT" \
        [--forma segura|insegura] [--java-bin <jdk>/bin] [--m2 <caché .m2>] \
        [--sufijo vN] [--trabajo CARPETA]

Código de salida: 0 si el resultado observado coincide con lo esperado para la forma elegida;
1 si no; 2 si el uso o el proyecto no son válidos.
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

from sgm.talend_item.componentes import fixed_flow_input
from sgm.talend_item.conexiones import lookup
from sgm.talend_item.escritura import escribir_job
from sgm.talend_item.expresiones import null_safe_equals
from sgm.talend_item.jobs_diseno import java
from sgm.talend_item.modelo import Columna, Conexion, Job, ParametroContexto
from sgm.talend_item.plantillas import nodo_desde_plantilla
from sgm.talend_item.tmap import EntradaMap, SalidaMap, tmap

# Seis filas: D, E y F no están en el lookup, así que el LEFT JOIN deja su valor a null.
PRINCIPAL = (("1", "A"), ("2", "B"), ("3", "C"), ("4", "D"), ("5", "E"), ("6", "F"))
LOOKUP = (("A", "CC"), ("B", "AHO"), ("C", "CC"))
VALOR = "CC"
VALIDOS = ["1", "3"]
RECHAZADOS = ["2", "4", "5", "6"]
FORMAS = ("segura", "insegura")
SEGURO = "segura"
_EXTENSIONES = (".item", ".properties")
_TECNICO = re.compile(r'technicalLabel="([^"]+)"')


def filtro(forma: str) -> str:
    """Expresión Java del filtro: con el literal a la izquierda, o con la columna a la izquierda."""
    if forma not in FORMAS:
        raise ValueError(f"Forma desconocida: {forma}")
    if forma == SEGURO:
        return null_safe_equals("row2.valor", VALOR)
    return f"row2.valor.equals({java(VALOR)})"


def job_filtro_nulo(forma: str = SEGURO) -> Job:
    """Job mínimo con lookup LEFT JOIN y una salida filtrada más su rechazo."""
    principal = [Columna("id"), Columna("clave")]
    consulta = [Columna("clave"), Columna("valor")]
    salida = [Columna("id")]
    filas_principal = [[java(i), java(c)] for i, c in PRINCIPAL]
    filas_lookup = [[java(c), java(v)] for c, v in LOOKUP]
    nodos = [
        fixed_flow_input("tFixedFlowInput_1", consulta, filas_lookup, 0, 0),
        fixed_flow_input("tFixedFlowInput_2", principal, filas_principal, 0, 160),
        tmap(
            "tMap_1",
            [
                EntradaMap("row1", principal),
                EntradaMap("row2", consulta, expresiones_union={"clave": "row1.clave"}),
            ],
            [
                SalidaMap("validos", salida, {"id": "row1.id"}, filtro=filtro(forma)),
                SalidaMap("rechazados", salida, {"id": "row1.id"}, rechazo=True),
            ],
            240,
            80,
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
            columnas=salida,
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
            columnas=salida,
        ),
    ]
    conexiones = [
        lookup("tFixedFlowInput_1", "tMap_1", "row2"),
        Conexion("tFixedFlowInput_2", "tMap_1", "row1"),
        Conexion("tMap_1", "tFileOutputDelimited_1", "validos"),
        Conexion("tMap_1", "tFileOutputDelimited_2", "rechazados", "REJECT"),
    ]
    contextos = {"Default": [ParametroContexto("ruta_salida")]}
    return Job("prueba_filtro_nulo", nodos=nodos, conexiones=conexiones, contextos=contextos)


def _ids(ruta: Path) -> list[str]:
    """Primera columna de cada fila del CSV, en orden; vacío si el archivo no existe."""
    if not ruta.is_file():
        return []
    texto = ruta.read_text(encoding="utf-8")
    return [linea.split(";")[0].strip() for linea in texto.splitlines() if linea]


def preparar_trabajo(trabajo: Path) -> None:
    """Deja la carpeta de salida vacía: una corrida anterior no debe contaminar el resultado."""
    salida = trabajo / "salida"
    salida.mkdir(parents=True, exist_ok=True)
    for nombre in ("validos.csv", "rechazados.csv"):
        (salida / nombre).unlink(missing_ok=True)


def proyecto_tecnico(proyecto: Path) -> str:
    """Nombre técnico del proyecto (`technicalLabel` de talend.project)."""
    archivo = proyecto / "talend.project"
    if archivo.is_file():
        coincide = _TECNICO.search(archivo.read_text(encoding="utf-8", errors="replace"))
        if coincide:
            return coincide.group(1)
    return proyecto.name


def _cuadra(forma: str, resultado: dict, validos: list[str], rechazados: list[str]) -> bool:
    if forma == SEGURO:
        return (
            resultado["exitCode"] == 0
            and validos == VALIDOS
            and rechazados == RECHAZADOS
        )
    # La forma insegura debe fallar en ejecución por la columna nula del LEFT JOIN.
    consola = resultado["stdout"] + resultado["stderr"]
    return resultado["exitCode"] != 0 and "NullPointerException" in consola


def validar(
    proyecto: Path,
    trabajo: Path,
    sufijo: str,
    forma: str,
    java_bin: Path | None,
    m2: Path | None,
) -> int:
    """Ejecuta el Job en Studio y compara el resultado con lo esperado para esa forma."""
    preparar_trabajo(trabajo)
    temporal = Path(tempfile.mkdtemp(prefix="jobs-"))
    exportado = crear_destino_build()
    cliente = MCP()
    copiados: list[Path] = []
    proceso = proyecto / "process"
    try:
        escribir_job(job_filtro_nulo(forma), temporal)
        renombres = renombrar(temporal, sufijo, proyecto_tecnico(proyecto))
        nombre = renombres["prueba_filtro_nulo"]
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
    print(f"Forma: {forma}")
    print(f"Filtro: {filtro(forma)}")
    print(f"Comando: {resultado['comando']}")
    print(f"Código de salida: {resultado['exitCode']}")
    if resultado["stdout"]:
        print(f"Salida del Job (final):\n{resultado['stdout'][-2000:]}")
    if resultado["stderr"]:
        print(f"stderr (final):\n{resultado['stderr'][-1000:]}")
    validos = _ids(trabajo / "salida" / "validos.csv")
    rechazados = _ids(trabajo / "salida" / "rechazados.csv")
    print(f"validos.csv:    {validos}  (esperado {VALIDOS})")
    print(f"rechazados.csv: {rechazados}  (esperado {RECHAZADOS})")
    cuadra = _cuadra(forma, resultado, validos, rechazados)
    if forma == SEGURO:
        texto = "el filtro seguro separa las filas con y sin pareja" if cuadra else "NO coincide"
    else:
        texto = (
            "el filtro inseguro falla con NullPointerException"
            if cuadra
            else "NO falló como se esperaba"
        )
    print("RESULTADO:", texto)
    return 0 if cuadra else 1


def main(argv: list[str] | None = None) -> int:
    for flujo in (sys.stdout, sys.stderr):
        if hasattr(flujo, "reconfigure"):
            flujo.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--proyecto", type=Path, required=True)
    parser.add_argument("--forma", choices=FORMAS, default=SEGURO)
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
    trabajo = args.trabajo or Path(tempfile.mkdtemp(prefix="prueba-filtro-nulo-"))
    print(f"Proyecto: {args.proyecto}\nSufijo: {sufijo}\nTrabajo: {trabajo}")
    try:
        return validar(args.proyecto, trabajo, sufijo, args.forma, args.java_bin, args.m2)
    except ErrorValidacion as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
