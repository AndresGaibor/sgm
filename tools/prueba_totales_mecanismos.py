"""Hito 97 / R2-01: tres mecanismos para pasar totales entre Jobs, ejecutados en Studio con datos.

Datos: dos archivos de producto `CLAVE;saldo` (CTE: 3 filas, 15.00; AHO: 2 filas, 120.50). Los
totales esperados se calculan a mano aquí, no con Studio. Los jobs están en
`totales_mecanismos_jobs`.

Por mecanismo se comprueba:

* (a) `totales_a_CTE.csv` y `totales_a_AHO.csv` contienen el total de cada hijo (el padre
  recibió las filas por `PROPAGATE_CHILD_RESULT`).
* (b) `totales_origen_CTE/AHO.csv` los escribe el hijo, y `totales_unidos_b.csv` une los dos.
* (c) el padre lee `resultado` y `globalMap` tras cada hijo. Se espera ver el valor inicial: el
  hijo no lo devuelve. Se comprueba en la salida de la ejecución.

Cada Job se renombra con el sufijo nuevo, se compila, se exporta y se ejecuta. Los Jobs se
borran del proyecto al terminar, aunque falle. Código de salida 0 solo si los tres mecanismos dan
lo esperado.

Uso:
    uv run python tools/prueba_totales_mecanismos.py --proyecto <carpeta> --sufijo v97a
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

from mcp_cliente import MCP, ErrorValidacion  # noqa: E402
from totales_mecanismos_jobs import jobs_mecanismos  # noqa: E402
from validar_en_studio import (  # noqa: E402
    borrar_destino_build,
    construir,
    crear_destino_build,
    ejecutar,
    exportar,
    renombrar,
)

DATOS = {"CTE": "1;10.50\n2;4.25\n3;0.25\n", "AHO": "1;100.00\n2;20.50\n"}
ESPERADO = {"CTE": (Decimal("3"), Decimal("15.00")), "AHO": (Decimal("2"), Decimal("120.50"))}
HIJOS = ("mec_a_hijo", "mec_b_hijo", "mec_b_totales", "mec_c_hijo")
PADRES = {"a": "mec_a_padre", "b": "mec_b_padre", "c": "mec_c_padre"}


def _proyecto_tecnico(proyecto: Path) -> str:
    """Etiqueta técnica del proyecto (`technicalLabel` de `talend.project`)."""
    import re

    archivo = proyecto / "talend.project"
    coincide = re.search(
        r'technicalLabel="([^"]+)"', archivo.read_text(encoding="utf-8", errors="replace")
    )
    return coincide.group(1) if coincide else proyecto.name


def _emitir(carpeta: Path, proyecto: str) -> None:
    from sgm.talend_item.escritura import escribir_job

    for mecanismo, jobs in jobs_mecanismos(proyecto).items():
        for job in jobs:
            escribir_job(job, carpeta)
        print(f"Emitidos mecanismo {mecanismo}: {[j.nombre for j in jobs]}")


def _filas(archivo: Path) -> list[tuple[Decimal, Decimal]]:
    """Filas de un CSV `registros;suma_saldo` con cabecera, como pares de decimales."""
    with archivo.open(encoding="utf-8", newline="") as entrada:
        lector = csv.reader(entrada, delimiter=";")
        next(lector)
        return [(Decimal(r[0]), Decimal(r[1])) for r in lector if r]


def _evaluar_fallo(mecanismo: str, corrida: dict) -> list[str]:
    """Con un producto sin archivo, el padre debe salir con error y no seguir con los pasos."""
    errores: list[str] = []
    salida = corrida["stdout"]
    if corrida["exitCode"] == 0:
        errores.append(f"{mecanismo} fallo: el padre salió con 0 sin el archivo de AHO")
    if mecanismo == "b" and "mec_b_totales arranca" in salida:
        errores.append("b fallo: el Job de totales corrió tras el fallo del hijo")
    if mecanismo == "c" and "tras AHO" in salida:
        errores.append("c fallo: el padre siguió tras el fallo del hijo")
    return errores


def _evaluar(mecanismo: str, trabajo: Path, sufijo: str, salida: str) -> list[str]:
    """Diferencias frente a lo esperado; lista vacía si el mecanismo se comporta como se espera."""
    errores: list[str] = []
    if mecanismo == "a":
        for producto in ("CTE", "AHO"):
            archivo = trabajo / f"salida_a_ok_{sufijo}" / f"totales_a_{producto}.csv"
            if not archivo.is_file():
                errores.append(f"a: falta {archivo.name}")
                continue
            filas = _filas(archivo)
            if filas != [ESPERADO[producto]]:
                errores.append(f"a {producto}: obtenido {filas}, esperado [{ESPERADO[producto]}]")
    elif mecanismo == "b":
        carpeta = trabajo / f"salida_b_ok_{sufijo}"
        for producto in ("CTE", "AHO"):
            archivo = carpeta / f"totales_origen_{producto}.csv"
            if not archivo.is_file():
                errores.append(f"b: falta {archivo.name}")
            elif _filas(archivo) != [ESPERADO[producto]]:
                errores.append(f"b {producto}: {_filas(archivo)} != {ESPERADO[producto]}")
        unidos = carpeta / "totales_unidos_b.csv"
        if not unidos.is_file():
            errores.append("b: falta totales_unidos_b.csv")
        elif sorted(_filas(unidos)) != sorted(ESPERADO.values()):
            errores.append(f"b unidos: {sorted(_filas(unidos))}")
    else:
        for etiqueta in ("tras CTE", "tras AHO"):
            if f"mec_c_padre {etiqueta}: resultado=SIN_VALOR globalMap=null" not in salida:
                errores.append(f"c: en '{etiqueta}' el padre sí vio el valor del hijo")
        if "mec_c_hijo fija resultado=HIJO_CTE" not in salida:
            errores.append("c: el hijo no imprimió su resultado")
    return errores


def validar(proyecto: Path, trabajo: Path, sufijo: str, java_bin: Path | None, m2: Path | None):
    trabajo.mkdir(parents=True, exist_ok=True)
    entradas = trabajo / "entradas"
    entradas.mkdir(exist_ok=True)
    rutas = {}
    for producto, texto in DATOS.items():
        ruta = entradas / f"origen_{producto.lower()}.csv"
        ruta.write_text(texto, encoding="utf-8", newline="\n")
        rutas[producto] = ruta.as_posix()
    cliente = MCP()
    copiados: list[Path] = []
    resultados: dict[str, dict] = {}
    try:
        proyecto_tec = _proyecto_tecnico(proyecto)
        carpeta = trabajo / f"emit_{sufijo}"
        carpeta.mkdir(parents=True, exist_ok=True)
        _emitir(carpeta, proyecto_tec)
        mapa = renombrar(carpeta, sufijo, proyecto_tec)
        proceso = proyecto / "process"
        for nombre in mapa.values():
            for extension in (".item", ".properties"):
                origen = carpeta / f"{nombre}_0.1{extension}"
                if origen.exists():
                    destino = proceso / origen.name
                    shutil.copyfile(origen, destino)
                    copiados.append(destino)
        cliente.llamar("talend_bridge_refresh_workspace")
        hijos = [mapa[h] for h in HIJOS]
        print(f"Compilando hijos: {hijos}")
        construir(cliente, hijos)
        padres = {m: mapa[p] for m, p in PADRES.items()}
        print(f"Compilando padres: {list(padres.values())}")
        construir(cliente, list(padres.values()))
        # Escenario `fallo`: el archivo de AHO no existe; el padre debe detenerse
        # (DIE_ON_CHILD_ERROR).
        rutas_fallo = {"CTE": rutas["CTE"], "AHO": (entradas / "no_existe_aho.csv").as_posix()}
        for escenario, rutas_run in (("ok", rutas), ("fallo", rutas_fallo)):
            for mecanismo, padre in padres.items():
                salida = trabajo / f"salida_{mecanismo}_{escenario}_{sufijo}"
                salida.mkdir(parents=True, exist_ok=True)
                destino = crear_destino_build()
                try:
                    lanzador = exportar(cliente, padre, destino, m2)
                    params = [
                        f"ruta_origen_cte={rutas_run['CTE']}",
                        f"ruta_origen_aho={rutas_run['AHO']}",
                        f"ruta_trabajo={salida.as_posix()}/",
                        f"sufijo={sufijo}",
                    ]
                    corrida = ejecutar(lanzador, "Default", params, java_bin)
                finally:
                    borrar_destino_build(destino)
                print(f"--- {escenario} mecanismo {mecanismo} ({padre}) "
                      f"código de salida {corrida['exitCode']}")  # fmt: skip
                print(corrida["stdout"])
                if corrida["stderr"].strip():
                    print("stderr:\n" + corrida["stderr"])
                resultados[f"{mecanismo}_{escenario}"] = corrida
    finally:
        for archivo in copiados:
            archivo.unlink(missing_ok=True)
        try:
            cliente.llamar("talend_bridge_refresh_workspace")
        except ErrorValidacion:
            pass
        print(f"Limpieza: {len(copiados)} archivos borrados del proyecto")
    errores: list[str] = []
    for clave, corrida in resultados.items():
        mecanismo, escenario = clave.split("_")
        if escenario == "fallo":
            errores += _evaluar_fallo(mecanismo, corrida)
        elif corrida["exitCode"] != 0:
            errores.append(f"{mecanismo}: código de salida {corrida['exitCode']}")
        else:
            errores += _evaluar(mecanismo, trabajo, sufijo, corrida["stdout"])
    for error in errores:
        print(f"DIFERENCIA: {error}")
    print("RESULTADO: " + ("OK" if not errores else "DIFERENCIAS"))
    return 0 if not errores else 1


def main(argv: list[str] | None = None) -> int:
    for flujo in (sys.stdout, sys.stderr):
        if hasattr(flujo, "reconfigure"):
            flujo.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--proyecto", type=Path, required=True)
    parser.add_argument("--trabajo", type=Path)
    parser.add_argument("--sufijo", required=True, help="sufijo nuevo del intento (v97a, v97b...)")
    parser.add_argument("--java-bin", type=Path)
    parser.add_argument("--m2", type=Path)
    args = parser.parse_args(argv)
    if not (args.proyecto / "talend.project").is_file():
        print(f"error: no es un proyecto Talend: {args.proyecto}", file=sys.stderr)
        return 2
    trabajo = args.trabajo or Path(tempfile.mkdtemp(prefix="prueba-totales-"))
    print(f"Proyecto: {args.proyecto}\nSufijo: {args.sufijo}\nTrabajo: {trabajo}")
    try:
        return validar(args.proyecto, trabajo, args.sufijo, args.java_bin, args.m2)
    except ErrorValidacion as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
