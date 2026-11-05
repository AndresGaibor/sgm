"""Hito 100d / R2-02 (parte 2): totales del `job_producto`, `job_totales` y `job_conciliacion`.

Extremo a extremo en Studio 8.0.1 con el proyecto `PRJ_BANCOLOMBIA`:

1. Se emiten con la misma función que `sgm talend` los tres Jobs: `job_producto` (con
   `escribe_totales=True`), `job_totales` y `job_conciliacion`. Se renombran con el sufijo nuevo.
2. Escenario `tal_cual`: `job_producto` corre para CTE y AHO con las entradas de
   `L8/validaciones/v05_codex_saldos`; después `job_totales` y `job_conciliacion`.
3. Escenario `planta`: igual, pero CTE lleva una fila con `TIPO_DOC` no homologado.

Qué se comprueba: los dos archivos de cada producto contra el oráculo de
`prueba_totales_producto_datos.py` (sin usar el Job ni el productor de `tools/`); origen igual a
válidos más rechazados; el archivo de totales de `job_totales`; y la conciliación: código 0 y
`CONCILIA` cuando no hay diferencia, código 3 y mensaje `NO CONCILIA` con la diferencia plantada.

Los Jobs copiados a `process/` se borran al terminar, aunque falle la prueba.

Uso:
    uv run python tools/prueba_totales_producto.py --proyecto <carpeta> [--sufijo v100a]
        [--trabajo DIR] [--java-bin DIR] [--m2 DIR]
"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
import tempfile
from decimal import Decimal
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "tools"))

from mcp_cliente import MCP, ErrorValidacion  # noqa: E402
from prueba_totales_producto_datos import (  # noqa: E402
    ARCHIVO_HOMOLOGACION,
    CABECERA_TOTALES,
    PERIODO,
    PRODUCTOS,
    TOLERANCIA,
    coincide,
    esperado_totales,
    homologacion_numerica,
    homologados,
    preparar_origen,
)
from validar_en_studio import (  # noqa: E402
    borrar_destino_build,
    construir,
    crear_destino_build,
    ejecutar,
    exportar,
    renombrar,
)

from sgm.agrupacion import cargar_declaracion  # noqa: E402
from sgm.cli_talend import _cuenta, _delimitador, _flujos  # noqa: E402
from sgm.proceso.origen_producto import origenes_producto  # noqa: E402
from sgm.talend_item.arquitectura import cargar_arquitectura  # noqa: E402
from sgm.talend_item.escritura import escribir_job  # noqa: E402
from sgm.talend_item.jobs_conciliacion import CODIGO_NO_CONCILIA, job_conciliacion  # noqa: E402
from sgm.talend_item.jobs_producto import job_producto  # noqa: E402
from sgm.talend_item.jobs_totales import job_totales, variables_fecha  # noqa: E402

PROGRAMA = REPO / "tests" / "fixtures" / "sas" / "client" / "client_large.sas"
DECISIONES = REPO / "decisiones"
ESCENARIOS = ("tal_cual", "planta")
NOMBRES = ("job_producto", "job_totales", "job_conciliacion")
PATRON_NO_CONCILIA = re.compile(
    r"NO CONCILIA (\w+): diferencia de filas (-?\d+), diferencia de saldo (-?[\d.]+)"
)


def emitir(carpeta: Path) -> None:
    """Escribe los tres Jobs con la función de `sgm talend` (mismos parámetros que el CLI)."""
    texto = PROGRAMA.read_text(encoding="utf-8", errors="replace")
    arq = cargar_arquitectura(DECISIONES / "client_large.jobs.yaml")
    origenes = origenes_producto(
        texto, cargar_declaracion(DECISIONES / "client_large.agrupacion.yaml").productos
    )
    flujos, _ = _flujos(texto)
    cuenta, _ = _cuenta(texto)
    variables = tuple(v for _, v in arq.periodo.variables)
    producto = job_producto(
        arq,
        origenes.columnas_comunes,
        variables,
        "totales de origen y de salida (R2-02)",
        _delimitador(origenes),
        validacion=arq.validaciones[0],
        numericas=origenes.numericas_comunes,
        flujos=flujos,
        cuenta=cuenta,
        escribe_totales=True,
    )
    for job in (producto, job_totales(arq, PRODUCTOS), job_conciliacion(arq, PRODUCTOS)):
        escribir_job(job, carpeta)


def parametros_producto(salida: Path, producto: str, origen: Path, insumos: Path) -> list[str]:
    """Parámetros de `job_producto`: el Excel numérico de `insumos` y el periodo de PERIODO."""
    return [
        f"producto={producto}",
        f"ruta_origen={origen.as_posix()}",
        f"sufijo={producto}",
        f"periodo_anio={PERIODO[0]}",
        f"periodo_mes={PERIODO[1]}",
        f"periodo_dia={PERIODO[2]}",
        f"arch_hom_tipo_doc={ARCHIVO_HOMOLOGACION}",
        f"ruta_insumos={insumos.as_posix()}/",
        "hoja_excel=Sheet1",
        f"ruta_resultados={salida.as_posix()}/",
    ]


def _leer(ruta: Path) -> list[list[str]]:
    with ruta.open(encoding="utf-8", newline="") as entrada:
        return [fila for fila in (linea.rstrip("\r\n").split(";") for linea in entrada) if fila]


def _comprobar_totales(
    carpeta: Path, producto: str, esperado: dict, validos_rech: int
) -> list[str]:
    """Diferencias de los dos archivos de `producto` frente al oráculo."""
    diferencias: list[str] = []
    for tipo in ("origen", "salida"):
        archivo = carpeta / f"totales_{tipo}_{producto}.csv"
        if not archivo.is_file():
            diferencias.append(f"no existe {archivo.name}")
            continue
        filas = _leer(archivo)
        if filas[0] != CABECERA_TOTALES or len(filas) != 2:
            diferencias.append(f"{archivo.name}: cabecera o filas inesperadas: {filas}")
            continue
        fila = filas[1]
        valores = dict(zip(CABECERA_TOTALES, fila, strict=False))
        previstos = esperado[tipo]
        if valores["PRODUCTO"] != producto or valores["TIPO"] != tipo:
            diferencias.append(
                f"{archivo.name}: PRODUCTO/TIPO {valores['PRODUCTO']}/{valores['TIPO']}"
            )
        for columna in ("NRO_FILAS", "NRO_SALDOS_NO_VACIOS", "SUMA_SALDO"):
            if not coincide(valores[columna], previstos[columna]):
                diferencias.append(
                    f"{archivo.name} {columna}: {valores[columna]!r} != {previstos[columna]!r}"
                )
        if (
            tipo == "origen"
            and esperado["origen"]["NRO_FILAS"] != esperado["salida"]["NRO_FILAS"] + validos_rech
        ):
            diferencias.append(f"{producto}: origen != válidos + rechazados")
    return diferencias


def _rechazados(carpeta: Path, producto: str) -> int:
    archivo = carpeta / f"doc_incorrectos_{producto}.csv"
    if not archivo.is_file():
        return 0
    return max(len(_leer(archivo)) - 1, 0)


def _comprobar_conciliacion(corrida: dict, carpeta: Path, esperado: dict[str, dict]) -> list[str]:
    """Código, mensaje y archivo de `job_conciliacion` frente a la diferencia del oráculo."""
    diferencias: list[str] = []
    no_concilia = {}
    for producto in PRODUCTOS:
        dif_filas = (
            esperado[producto]["origen"]["NRO_FILAS"] - esperado[producto]["salida"]["NRO_FILAS"]
        )
        dif_saldo = (
            esperado[producto]["origen"]["SUMA_SALDO"] - esperado[producto]["salida"]["SUMA_SALDO"]
        )
        if dif_filas != 0 or abs(dif_saldo) > TOLERANCIA:
            no_concilia[producto] = (dif_filas, dif_saldo)
    codigo_previsto = CODIGO_NO_CONCILIA if no_concilia else 0
    if corrida["exitCode"] != codigo_previsto:
        diferencias.append(f"código {corrida['exitCode']} en lugar de {codigo_previsto}")
    mensajes = {
        m.group(1): m for m in PATRON_NO_CONCILIA.finditer(corrida["stdout"] + corrida["stderr"])
    }
    if set(mensajes) != set(no_concilia):
        diferencias.append(
            f"productos que no concilian: {sorted(mensajes)} en lugar de {sorted(no_concilia)}"
        )
    for producto, (dif_filas, dif_saldo) in no_concilia.items():
        m = mensajes.get(producto)
        if m and (
            int(m.group(2)) != dif_filas or abs(Decimal(m.group(3)) - dif_saldo) > TOLERANCIA
        ):
            diferencias.append(
                f"mensaje {producto}: {m.group(0)} en lugar de {dif_filas}/{dif_saldo}"
            )
    archivo = carpeta / f"conciliacion_{''.join(PERIODO)}.csv"
    if not archivo.is_file():
        return diferencias + ["no existe conciliacion_*.csv"]
    filas = _leer(archivo)
    if filas[0] != ["PRODUCTO", "DIF_FILAS", "DIF_SALDO"] or len(filas) != 3:
        diferencias.append(f"conciliacion: filas inesperadas {filas}")
    return diferencias


def _escenario(
    cliente: MCP, lanzadores: dict[str, Path], nombre: str, trabajo: Path, java_bin: Path | None
) -> int:
    carpeta = trabajo / f"salida_{nombre}"
    carpeta.mkdir(parents=True, exist_ok=True)
    insumos = trabajo / "insumos"
    insumos.mkdir(parents=True, exist_ok=True)
    validos = homologados(homologacion_numerica(insumos))
    origenes = {
        p: preparar_origen(trabajo, p, planta=nombre == "planta" and p == "CTE") for p in PRODUCTOS
    }
    diferencias: list[str] = []
    esperado: dict[str, dict] = {}
    for producto, origen in origenes.items():
        corrida = ejecutar(
            lanzadores["job_producto"],
            "Default",
            parametros_producto(carpeta, producto, origen, insumos),
            java_bin,
        )
        print(f"[{nombre}] job_producto {producto}: código {corrida['exitCode']}")
        print(corrida["stdout"][-1500:])
        if corrida["exitCode"] != 0:
            diferencias.append(f"job_producto {producto} salió con {corrida['exitCode']}")
            print(corrida["stderr"][-600:])
            continue
        esperado[producto] = esperado_totales(origen, validos)
        rechazados = _rechazados(carpeta, producto)
        diferencias += _comprobar_totales(carpeta, producto, esperado[producto], rechazados)
        print(f"  rechazados (doc_incorrectos): {rechazados}")
    if diferencias or len(esperado) != len(PRODUCTOS):
        return _resumen(nombre, diferencias)
    arq = cargar_arquitectura(DECISIONES / "client_large.jobs.yaml")
    variables = variables_fecha(arq)
    fecha = [f"ruta_resultados={carpeta.as_posix()}/"]
    fecha += [f"{variables[k]}={PERIODO[i]}" for i, k in enumerate(("anio", "mes", "dia"))]
    totales = ejecutar(lanzadores["job_totales"], "Default", fecha, java_bin)
    print(f"[{nombre}] job_totales: código {totales['exitCode']}")
    if totales["exitCode"] != 0:
        diferencias.append(f"job_totales salió con {totales['exitCode']}")
    conc = ejecutar(lanzadores["job_conciliacion"], "Default", fecha, java_bin)
    print(f"[{nombre}] job_conciliacion: código {conc['exitCode']}")
    print(f"Comando conciliación: {conc['comando']}")
    if conc["stdout"].strip():
        print("stdout:\n" + conc["stdout"])
    diferencias += _comprobar_conciliacion(conc, carpeta, esperado)
    final = carpeta / f"{arq.archivo_totales}_{''.join(PERIODO)}.csv"
    if final.is_file():
        print(f"Contenido literal de {final.name}:")
        print(final.read_text(encoding="utf-8"))
    else:
        diferencias.append("no existe el archivo final de totales")
    conciliacion = carpeta / f"conciliacion_{''.join(PERIODO)}.csv"
    if conciliacion.is_file():
        print(f"Contenido literal de {conciliacion.name}:")
        print(conciliacion.read_text(encoding="utf-8"))
    return _resumen(nombre, diferencias)


def _resumen(nombre: str, diferencias: list[str]) -> int:
    for d in diferencias:
        print(f"DIFERENCIA: {d}")
    print(f"RESULTADO {nombre}: " + ("OK" if not diferencias else "DIFERENCIAS"))
    return 0 if not diferencias else 1


def validar(
    proyecto: Path, trabajo: Path, sufijo: str, java_bin: Path | None, m2: Path | None
) -> int:
    trabajo.mkdir(parents=True, exist_ok=True)
    proceso = proyecto / "process"
    creada = not proceso.exists()
    proceso.mkdir(exist_ok=True)
    carpeta_emit = trabajo / f"emit_{sufijo}"
    carpeta_emit.mkdir(parents=True, exist_ok=True)
    emitir(carpeta_emit)
    tecnico = re.search(
        r'technicalLabel="([^"]+)"', (proyecto / "talend.project").read_text(encoding="utf-8")
    )
    mapa = renombrar(carpeta_emit, sufijo, tecnico.group(1) if tecnico else proyecto.name)
    cliente = MCP()
    copiados: list[Path] = []
    lanzadores: dict[str, Path] = {}
    destinos: list[Path] = []
    resultado = 1
    try:
        for nombre in NOMBRES:
            for extension in (".item", ".properties"):
                origen = carpeta_emit / f"{mapa[nombre]}_0.1{extension}"
                if origen.exists():
                    destino = proceso / origen.name
                    shutil.copyfile(origen, destino)
                    copiados.append(destino)
        cliente.llamar("talend_bridge_refresh_workspace")
        print("Compilando: " + str([mapa[n] for n in NOMBRES]))
        construir(cliente, [mapa[n] for n in NOMBRES])
        for nombre in NOMBRES:
            destino = crear_destino_build()
            destinos.append(destino)
            lanzadores[nombre] = exportar(cliente, mapa[nombre], destino, m2)
        resultado = 0
        for escenario in ESCENARIOS:
            resultado |= _escenario(cliente, lanzadores, escenario, trabajo, java_bin)
    finally:
        for archivo in copiados:
            archivo.unlink(missing_ok=True)
        for destino in destinos:
            borrar_destino_build(destino)
        if creada and proceso.is_dir() and not any(proceso.iterdir()):
            proceso.rmdir()
        try:
            cliente.llamar("talend_bridge_refresh_workspace")
        except ErrorValidacion:
            pass
        print(f"Limpieza: {len(copiados)} archivos de Jobs borrados de process/ y builds borrados")
    return resultado


def main(argv: list[str] | None = None) -> int:
    for flujo in (sys.stdout, sys.stderr):
        if hasattr(flujo, "reconfigure"):
            flujo.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--proyecto", type=Path, required=True)
    parser.add_argument("--trabajo", type=Path)
    parser.add_argument("--sufijo", help="sufijo nuevo de los Jobs (Studio cachea por id)")
    parser.add_argument("--java-bin", type=Path, help="carpeta bin del JDK de Studio")
    parser.add_argument("--m2", type=Path, help="caché .m2 de Studio")
    args = parser.parse_args(argv)
    if not (args.proyecto / "talend.project").is_file():
        print(f"error: no es un proyecto Talend: {args.proyecto}", file=sys.stderr)
        return 2
    from corpus_lib.studio_validar import sufijo_nuevo

    sufijo = args.sufijo or sufijo_nuevo()
    trabajo = args.trabajo or Path(tempfile.mkdtemp(prefix="prueba-totales-"))
    print(f"Proyecto: {args.proyecto}\nSufijo: {sufijo}\nTrabajo: {trabajo}")
    try:
        return validar(args.proyecto, trabajo, sufijo, args.java_bin, args.m2)
    except ErrorValidacion as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
