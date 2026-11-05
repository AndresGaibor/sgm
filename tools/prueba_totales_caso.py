"""Hito 97 / R2-02: `job_totales` real se ejecuta en Studio con los datos de L8/totales/04.

Cadena probada, con Jobs emitidos por el código de `src/` salvo el productor y el padre de prueba:

1. `caso_producto` (tools/totales_caso_jobs.py) lee `origen_<producto>.csv` y escribe
   `totales_origen_<producto>.csv` y `totales_salida_<producto>.csv` en la carpeta de resultados.
2. `job_totales` (src/sgm/talend_item/jobs_totales.py) une los archivos de CTE y AHO y escribe
   `<archivo_totales>_<anio><mes><dia>.csv` con la fecha de `context.periodo_*`.
3. El padre de prueba llama a los dos, en orden, con `tRunJob`.

La fecha de la prueba (2026-09-30) es un valor de prueba: el caso no declara la fecha del proceso.
La salida se compara con `esperado/` fila por fila; la tolerancia de las sumas es la de `caso.yaml`.

Uso:
    uv run python tools/prueba_totales_caso.py --proyecto <carpeta> --sufijo v97g
        [--trabajo DIR] [--java-bin DIR] [--m2 DIR]
"""

from __future__ import annotations

import argparse
import csv
import shutil
import sys
import tempfile
from decimal import Decimal
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "tools"))

import yaml  # noqa: E402
from mcp_cliente import MCP, ErrorValidacion  # noqa: E402
from totales_caso_jobs import producto_caso  # noqa: E402
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
from sgm.talend_item.jobs_diseno import java, run_job  # noqa: E402
from sgm.talend_item.jobs_totales import job_totales  # noqa: E402
from sgm.talend_item.modelo import Job, ParametroContexto  # noqa: E402
from sgm.talend_item.plantillas import nodo_desde_plantilla  # noqa: E402

CASO = REPO / "tests/corpus/L8/totales/04_totales_origen_salida"
FECHA = ("2026", "09", "30")  # valores de prueba: el caso no declara la fecha del proceso
PRODUCTOS = ("CTE", "AHO")


def _proyecto_tecnico(proyecto: Path) -> str:
    import re

    texto = (proyecto / "talend.project").read_text(encoding="utf-8", errors="replace")
    coincide = re.search(r'technicalLabel="([^"]+)"', texto)
    return coincide.group(1) if coincide else proyecto.name


def padre_prueba(proyecto: str) -> Job:
    """Padre de prueba: producto CTE, producto AHO y luego `job_totales`."""

    def params(producto: str, origen: str) -> dict[str, str]:
        return {"producto": f'"{producto}"', "ruta_origen": origen, "sufijo": f'"{producto}"'}

    nodos = [
        nodo_desde_plantilla(
            "tJava",
            "tJava_1",
            0,
            0,
            {"CODE": f"System.out.println({java('caso_padre: arranca')});"},
        ),  # fmt: skip
        run_job(
            "tRunJob_1", "caso_producto", proyecto, params("CTE", "context.ruta_origen_cte"), 240, 0
        ),  # noqa: E501
        run_job(
            "tRunJob_2", "caso_producto", proyecto, params("AHO", "context.ruta_origen_aho"), 480, 0
        ),  # noqa: E501
        run_job("tRunJob_3", "job_totales", proyecto, None, 720, 0),
    ]
    conexiones = [
        al_terminar_subjob("tJava_1", "tRunJob_1", 1),
        al_terminar_subjob("tRunJob_1", "tRunJob_2", 2),
        al_terminar_subjob("tRunJob_2", "tRunJob_3", 3),
    ]
    contexto = [
        ParametroContexto(n)
        for n in ("ruta_origen_cte", "ruta_origen_aho", "ruta_resultados", "sufijo",
                  "periodo_anio", "periodo_mes", "periodo_dia")
    ]  # fmt: skip
    return Job("caso_padre", nodos=nodos, conexiones=conexiones, contextos={"Default": contexto})


def esperado() -> list[tuple[str, str, Decimal, str, Decimal]]:
    """Filas esperadas (producto, tipo, filas, saldos no vacíos, suma) desde `esperado/`."""
    filas: list[tuple[str, str, Decimal, str, Decimal]] = []
    carpeta = CASO / "esperado"
    for producto in PRODUCTOS:
        origen = _primera_fila(carpeta / f"TOTAL_ORIGEN_{producto}.csv")
        salida = _primera_fila(carpeta / f"TOTAL_SALIDA_{producto}.csv")
        filas.append(
            (
                producto,
                "origen",
                Decimal(origen["NRO_FILAS_ORIGEN"]),
                origen["NRO_SALDOS_NO_VACIOS"],
                Decimal(origen["SUMA_SALDO_ORIGEN"]),
            )
        )
        filas.append(
            (producto, "salida", Decimal(salida["NRO_FILAS_SALIDA"]), "",
             Decimal(salida["SUMA_SALDO_SALIDA"]))
        )
    return filas


def _primera_fila(archivo: Path) -> dict[str, str]:
    """Primera fila de un CSV de `esperado/` con cabecera, como diccionario."""
    with archivo.open(encoding="utf-8", newline="") as entrada:
        return next(csv.DictReader(entrada))


def tolerancia() -> Decimal:
    datos = yaml.safe_load((CASO / "caso.yaml").read_text(encoding="utf-8"))
    return Decimal(str(datos["tolerancia"]))


def comparar(archivo: Path) -> tuple[list[str], list[str]]:
    """Compara el archivo de exógena con el esperado. Devuelve (tabla, diferencias)."""
    tabla: list[str] = []
    diferencias: list[str] = []
    obtenidas = list(csv.reader(archivo.open(encoding="utf-8", newline=""), delimiter=";"))
    cabecera, filas = obtenidas[0], obtenidas[1:]
    tabla.append(";".join(cabecera))
    tabla.extend(";".join(f) for f in filas)
    if len(filas) != len(esperado()):
        diferencias.append(f"filas: {len(filas)} obtenidas, {len(esperado())} esperadas")
    tol = tolerancia()
    for (producto, tipo, n, saldos, suma), fila in zip(esperado(), filas, strict=False):
        pr, ti, nf, ns, ss = fila
        if (pr, ti) != (producto, tipo):
            diferencias.append(f"orden: {pr}/{ti} en lugar de {producto}/{tipo}")
        if Decimal(nf) != n:
            diferencias.append(f"{producto} {tipo} NRO_FILAS: {nf} != {n}")
        if tipo == "origen" and ns != saldos:
            diferencias.append(f"{producto} origen NRO_SALDOS_NO_VACIOS: {ns} != {saldos}")
        if tipo == "salida" and ns != "":
            diferencias.append(f"{producto} salida NRO_SALDOS_NO_VACIOS debía ir vacío: {ns}")
        if abs(Decimal(ss) - suma) > tol:
            diferencias.append(f"{producto} {tipo} SUMA_SALDO: {ss} != {suma} (tol {tol})")
    return tabla, diferencias


def validar(proyecto: Path, trabajo: Path, sufijo: str, java_bin, m2) -> int:
    trabajo.mkdir(parents=True, exist_ok=True)
    entradas = trabajo / "entradas"
    entradas.mkdir(exist_ok=True)
    for producto in PRODUCTOS:
        shutil.copyfile(CASO / "entradas" / f"origen_{producto.lower()}.csv",
                        entradas / f"origen_{producto.lower()}.csv")  # fmt: skip
    resultados = trabajo / f"resultados_{sufijo}"
    resultados.mkdir(exist_ok=True)
    tec = _proyecto_tecnico(proyecto)
    arq = cargar_arquitectura(REPO / "decisiones" / "client_large.jobs.yaml")
    jobs = [producto_caso(), job_totales(arq, PRODUCTOS), padre_prueba(tec)]
    carpeta = trabajo / f"emit_{sufijo}"
    for job in jobs:
        escribir_job(job, carpeta)
    mapa = renombrar(carpeta, sufijo, tec)
    cliente = MCP()
    copiados: list[Path] = []
    try:
        for nombre in mapa.values():
            for extension in (".item", ".properties"):
                origen = carpeta / f"{nombre}_0.1{extension}"
                if origen.exists():
                    destino = proyecto / "process" / origen.name
                    shutil.copyfile(origen, destino)
                    copiados.append(destino)
        cliente.llamar("talend_bridge_refresh_workspace")
        hijos = [mapa["caso_producto"], mapa["job_totales"]]
        print(f"Compilando hijos: {hijos}")
        construir(cliente, hijos)
        print(f"Compilando padre: {mapa['caso_padre']}")
        construir(cliente, [mapa["caso_padre"]])
        destino = crear_destino_build()
        try:
            lanzador = exportar(cliente, mapa["caso_padre"], destino, m2)
            params = [
                f"ruta_origen_cte={(entradas / 'origen_cte.csv').as_posix()}",
                f"ruta_origen_aho={(entradas / 'origen_aho.csv').as_posix()}",
                f"ruta_resultados={resultados.as_posix()}/",
                f"sufijo={sufijo}",
                f"periodo_anio={FECHA[0]}",
                f"periodo_mes={FECHA[1]}",
                f"periodo_dia={FECHA[2]}",
            ]
            corrida = ejecutar(lanzador, "Default", params, java_bin)
        finally:
            borrar_destino_build(destino)
    finally:
        for archivo in copiados:
            archivo.unlink(missing_ok=True)
        try:
            cliente.llamar("talend_bridge_refresh_workspace")
        except ErrorValidacion:
            pass
        print(f"Limpieza: {len(copiados)} archivos borrados del proyecto")
    print(f"Comando: {corrida['comando']}")
    print(f"Código de salida: {corrida['exitCode']}")
    print("stdout:")
    print(corrida["stdout"])
    if corrida["stderr"].strip():
        print("stderr:\n" + corrida["stderr"])
    if corrida["exitCode"] != 0:
        print("RESULTADO: el padre falló")
        return 1
    archivo = resultados / f"{arq.archivo_totales}_{''.join(FECHA)}.csv"
    if not archivo.is_file():
        print(f"RESULTADO: no existe {archivo.name}")
        return 1
    tabla, diferencias = comparar(archivo)
    print(f"Contenido literal de {archivo.name}:")
    print("\n".join(tabla))
    for d in diferencias:
        print(f"DIFERENCIA: {d}")
    print("RESULTADO: " + ("coincide con esperado/" if not diferencias else "DIFERENCIAS"))
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
    trabajo = args.trabajo or Path(tempfile.mkdtemp(prefix="prueba-caso-"))
    print(f"Proyecto: {args.proyecto}\nSufijo: {args.sufijo}\nTrabajo: {trabajo}")
    try:
        return validar(args.proyecto, trabajo, args.sufijo, args.java_bin, args.m2)
    except ErrorValidacion as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
