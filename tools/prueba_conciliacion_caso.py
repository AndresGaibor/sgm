"""Hito 98d / R2-03 y R2-07: `job_conciliacion` real, en Studio, con los datos de L8/totales/05.

Tres escenarios, cada uno con su Job exportado y ejecutado con el launcher (ver
`prueba_totales_caso`):

A. `concilia`: `caso_conc_cte` (solo CTE). Sale con 0 y `conciliacion_<fecha>.csv` coincide con la
   fila de CTE de `esperado/CONCILIACION_FINAL.csv`.
B. `no_concilia`: `caso_conc_ambos` (CTE y AHO). Sale con el código de `tDie` (3) y el mensaje
   nombra AHO con diferencia de filas 1 y de saldo 5.00. El archivo ya tiene las dos filas.
C. `politica`: `caso_politica` (padre) llama a `caso_conc_ambos` sin `totales_origen_AHO.csv`.
   El hijo debe fallar, el padre debe salir con código distinto de 0 y no debe correr el paso
   siguiente (R2-07, DC-08).

Los totales de entrada (`totales_origen_<p>.csv` y `totales_salida_<p>.csv`) se escriben desde
`esperado/TOTALES_CONC_<p>.csv`: la salida es válidos más rechazados, que es la regla del SAS. Así
se prueba la conciliación y no el productor de totales, que todavía no escribe esos archivos.

Uso:
    uv run python tools/prueba_conciliacion_caso.py --proyecto <carpeta> --sufijo v98a
        [--trabajo DIR] [--java-bin DIR] [--m2 DIR]
"""

from __future__ import annotations

import argparse
import shutil
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "tools"))

from mcp_cliente import MCP, ErrorValidacion  # noqa: E402
from prueba_conciliacion_utiles import (  # noqa: E402
    FECHA,
    PRODUCTOS,
    comparar,
    escribir_totales,
    proyecto_tecnico,
)
from validar_en_studio import (  # noqa: E402
    borrar_destino_build,
    construir,
    crear_destino_build,
    ejecutar,
    exportar,
    renombrar,
)

from sgm.talend_item.arquitectura import cargar_arquitectura  # noqa: E402
from sgm.talend_item.conexiones import al_terminar_subjob  # noqa: E402
from sgm.talend_item.escritura import escribir_job  # noqa: E402
from sgm.talend_item.jobs_conciliacion import (  # noqa: E402
    ARCHIVO_CONCILIACION,
    CODIGO_NO_CONCILIA,
    job_conciliacion,
)
from sgm.talend_item.jobs_diseno import java, run_job  # noqa: E402
from sgm.talend_item.jobs_totales import variables_fecha  # noqa: E402
from sgm.talend_item.modelo import Job, ParametroContexto  # noqa: E402
from sgm.talend_item.plantillas import nodo_desde_plantilla  # noqa: E402

ESCENARIOS = ("concilia", "no_concilia", "politica")


def padre_politica(proyecto: str, variables: dict[str, str]) -> Job:
    """Padre de R2-07: llama al hijo que debe fallar y, si el hijo no falla, marca que siguió."""
    nodos = [
        nodo_desde_plantilla(
            "tJava", "tJava_1", 0, 0,
            {"CODE": f"System.out.println({java('caso_politica: arranca')});"},
        ),  # fmt: skip
        run_job("tRunJob_1", "caso_conc_ambos", proyecto, None, 240, 0),
        nodo_desde_plantilla(
            "tJava", "tJava_2", 480, 0,
            {"CODE": f"System.out.println({java('caso_politica: NO DEBIA CORRER')});"},
        ),  # fmt: skip
    ]
    conexiones = [
        al_terminar_subjob("tJava_1", "tRunJob_1", 1),
        al_terminar_subjob("tRunJob_1", "tJava_2", 2),
    ]
    nombres = ("ruta_resultados", variables["anio"], variables["mes"], variables["dia"])
    contexto = [ParametroContexto(n) for n in nombres]
    contexto.append(ParametroContexto("tolerancia_conciliacion", valor="0"))
    return Job("caso_politica", nodos=nodos, conexiones=conexiones, contextos={"Default": contexto})


def _parametros(carpeta: Path, variables: dict[str, str]) -> list[str]:
    """Parámetros de contexto de un escenario. La tolerancia no se pasa: prueba la omisión."""
    return [
        f"ruta_resultados={carpeta.as_posix()}/",
        f"{variables['anio']}={FECHA[0]}",
        f"{variables['mes']}={FECHA[1]}",
        f"{variables['dia']}={FECHA[2]}",
    ]


def _entradas(trabajo: Path, sufijo: str, quitar: str | None = None) -> Path:
    """Carpeta de resultados con los totales de entrada; `quitar` deja fuera un archivo."""
    carpeta = trabajo / f"entradas_{sufijo}"
    carpeta.mkdir(parents=True, exist_ok=True)
    escribir_totales(carpeta)
    if quitar is not None:
        (carpeta / f"totales_origen_{quitar}.csv").unlink()
    return carpeta


def _evaluar(nombre: str, corrida: dict, carpeta: Path, archivo: Path | None) -> list[str]:
    """Diferencias de un escenario frente a lo esperado. Lista vacía = el escenario se cumple."""
    diferencias: list[str] = []
    salida = corrida["stdout"] + corrida["stderr"]
    codigo = corrida["exitCode"]
    if nombre == "concilia":
        if codigo != 0:
            diferencias.append(f"código {codigo} en lugar de 0")
        if archivo is None or not archivo.is_file():
            diferencias.append("no existe el archivo de conciliación")
        else:
            diferencias += comparar(archivo, ("CTE",))
    elif nombre == "no_concilia":
        if codigo != CODIGO_NO_CONCILIA:
            diferencias.append(f"código {codigo} en lugar de {CODIGO_NO_CONCILIA}")
        esperado = "NO CONCILIA AHO: diferencia de filas 1, diferencia de saldo 5.00"
        if esperado not in salida:
            diferencias.append(f"el mensaje de tDie no contiene: {esperado}")
        if archivo is None or not archivo.is_file():
            diferencias.append("no existe el archivo de conciliación")
        else:
            diferencias += comparar(archivo, PRODUCTOS)
    else:
        if codigo == 0:
            diferencias.append("el padre salió con 0 aunque el hijo debía fallar")
        if "NO DEBIA CORRER" in salida:
            diferencias.append("el padre siguió después del hijo fallido")
    return diferencias


NOMBRE_JOB = {
    "concilia": "caso_conc_cte",
    "no_concilia": "caso_conc_ambos",
    "politica": "caso_politica",
}


def _correr(
    cliente: MCP, mapa: dict[str, str], nombre: str, carpeta: Path, m2, java_bin, variables
) -> dict:
    """Exporta el Job del escenario, lo ejecuta y borra su carpeta de build."""
    destino = crear_destino_build()
    try:
        lanzador = exportar(cliente, mapa[NOMBRE_JOB[nombre]], destino, m2)
        return ejecutar(lanzador, "Default", _parametros(carpeta, variables), java_bin)
    finally:
        borrar_destino_build(destino)


def validar(proyecto: Path, trabajo: Path, sufijo: str, java_bin, m2) -> int:
    trabajo.mkdir(parents=True, exist_ok=True)
    tec = proyecto_tecnico(proyecto)
    arq = cargar_arquitectura(REPO / "decisiones" / "client_large.jobs.yaml")
    variables = variables_fecha(arq)
    jobs = [
        job_conciliacion(arq, ("CTE",), nombre="caso_conc_cte"),
        job_conciliacion(arq, PRODUCTOS, nombre="caso_conc_ambos"),
        padre_politica(tec, variables),
    ]
    carpeta_emit = trabajo / f"emit_{sufijo}"
    for job in jobs:
        escribir_job(job, carpeta_emit)
    mapa = renombrar(carpeta_emit, sufijo, tec)
    cliente = MCP()
    copiados: list[Path] = []
    resultado = 1
    try:
        for nombre in mapa.values():
            for extension in (".item", ".properties"):
                origen = carpeta_emit / f"{nombre}_0.1{extension}"
                if origen.exists():
                    destino = proyecto / "process" / origen.name
                    shutil.copyfile(origen, destino)
                    copiados.append(destino)
        cliente.llamar("talend_bridge_refresh_workspace")
        print("Compilando hijos: " + str([mapa["caso_conc_cte"], mapa["caso_conc_ambos"]]))
        construir(cliente, [mapa["caso_conc_cte"], mapa["caso_conc_ambos"]])
        print(f"Compilando padre: {mapa['caso_politica']}")
        construir(cliente, [mapa["caso_politica"]])
        resultado = 0
        for nombre in ESCENARIOS:
            resultado |= _escenario(cliente, mapa, nombre, trabajo, sufijo, m2, java_bin, variables)
    finally:
        for archivo in copiados:
            archivo.unlink(missing_ok=True)
        try:
            cliente.llamar("talend_bridge_refresh_workspace")
        except ErrorValidacion:
            pass
        print(f"Limpieza: {len(copiados)} archivos borrados del proyecto")
    return resultado


def _escenario(cliente, mapa, nombre, trabajo, sufijo, m2, java_bin, variables) -> int:
    quitar = "AHO" if nombre == "politica" else None
    carpeta = _entradas(trabajo, f"{sufijo}_{nombre}", quitar)
    print(f"--- escenario {nombre} (carpeta {carpeta})")
    corrida = _correr(cliente, mapa, nombre, carpeta, m2, java_bin, variables)
    print(f"Comando: {corrida['comando']}")
    print(f"Código de salida: {corrida['exitCode']}")
    print("stdout:\n" + corrida["stdout"])
    if corrida["stderr"].strip():
        print("stderr:\n" + corrida["stderr"])
    archivo = carpeta / f"{ARCHIVO_CONCILIACION}_{''.join(FECHA)}.csv"
    if archivo.is_file():
        print(f"Contenido literal de {archivo.name}:")
        print(archivo.read_text(encoding="utf-8"))
    diferencias = _evaluar(nombre, corrida, carpeta, archivo if archivo.is_file() else None)
    for d in diferencias:
        print(f"DIFERENCIA: {d}")
    print(f"RESULTADO {nombre}: " + ("OK" if not diferencias else "DIFERENCIAS"))
    return 0 if not diferencias else 1


def main(argv: list[str] | None = None) -> int:
    for flujo in (sys.stdout, sys.stderr):
        if hasattr(flujo, "reconfigure"):
            flujo.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--proyecto", type=Path, required=True)
    parser.add_argument("--trabajo", type=Path)
    parser.add_argument("--sufijo", required=True)
    parser.add_argument("--java-bin", type=Path)
    parser.add_argument("--m2", type=Path)
    args = parser.parse_args(argv)
    if not (args.proyecto / "talend.project").is_file():
        print(f"error: no es un proyecto Talend: {args.proyecto}", file=sys.stderr)
        return 2
    trabajo = args.trabajo or Path(tempfile.mkdtemp(prefix="prueba-conc-"))
    print(f"Proyecto: {args.proyecto}\nSufijo: {args.sufijo}\nTrabajo: {trabajo}")
    try:
        return validar(args.proyecto, trabajo, args.sufijo, args.java_bin, args.m2)
    except ErrorValidacion as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
