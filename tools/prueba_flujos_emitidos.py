"""R1-04 / hito 87: el `job_producto` **emitido** separa los tres flujos con datos reales.

A diferencia del hito 86, aquí no se construye un Job a mano: se emite con `sgm talend` sobre
`client_large.sas`, se toma solo `job_producto`, se compila y se exporta en Studio, y se corre para
CTE y AHO contra las entradas de `v02_vacios_ceros`. Los tres CSV que escribe el Job se comparan
con los `esperado/` del corpus.

**Qué se compara y por qué.** El emisor normaliza las 15 columnas que el SAS real declara
numéricas (R1-02). Dos columnas del caso `v02` son texto no numérico (`TIPO_DOC=TDxx` y
`LLAVE_NOMBRE=LLVxxxxx`) y quedan vacías con `input(..., w.d)`: es la salvedad ya medida en el
hito 85, no una decisión de R1-04. Por eso la comparación usa solo las columnas estables bajo esa
normalización (`RELACION`, `TIPO_CTA`, `NRO_CTA`, `NRO_DOC` y `FIN_SALDO_CTA`); `NRO_CTA` es
única por fila, así que la igualdad de multisets sigue siendo fila por fila. No se rellena ni se
transforma el esperado, y no se comparan `TIPO_DOC` ni `LLAVE_NOMBRE`.

Uso:
    uv run python tools/prueba_flujos_emitidos.py --proyecto <carpeta> \
        [--sufijo v87a] [--trabajo DIR] [--java-bin DIR] [--m2 DIR]

Código de salida 0 solo si los dos productos coinciden, el desglose de anomalías plantadas cuadra
y se cumplen las tres invariantes del caso.
"""

from __future__ import annotations

import argparse
import csv
import re
import shutil
import sys
import tempfile
from collections import Counter
from contextlib import ExitStack
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tools"))

from mcp_cliente import MCP, ErrorValidacion  # noqa: E402
from vacios_ceros_datos import (  # noqa: E402
    ARCHIVOS,
    CASO,
    PRODUCTOS,
    anomalias_plantadas,
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
V01 = REPO / "tests" / "corpus" / "L8" / "validaciones" / "v01_tipo_doc" / "entradas"
EXTENSIONES = (".item", ".properties")
MODOS = ("tit_cot", "fa", "valido")
# Columnas que sobreviven a la normalización R1-02 del emisor; ver el docstring del módulo.
ESTABLES = {
    "tit_cot": ("RELACION", "TIPO_CTA", "NRO_CTA", "NRO_DOC"),
    "fa": ("RELACION", "TIPO_CTA", "NRO_CTA", "NRO_DOC"),
    "valido": ("RELACION", "TIPO_CTA", "NRO_CTA", "NRO_DOC", "FIN_SALDO_CTA"),
}


def _csv(ruta: Path) -> list[tuple[str, ...]]:
    with ruta.open(encoding="utf-8", newline="") as archivo:
        return [tuple(fila) for fila in csv.reader(archivo, delimiter=",")]


def _proyectar(ruta: Path, columnas: tuple[str, ...]) -> list[tuple[str, ...]]:
    """Filas de un CSV con cabecera, reducidas a `columnas` por **nombre**."""
    filas = _csv(ruta)
    if not filas:
        raise ErrorValidacion(f"CSV vacío: {ruta}")
    cabecera = filas[0]
    faltan = [c for c in columnas if c not in cabecera]
    if faltan:
        raise ErrorValidacion(f"{ruta.name} no trae las columnas {faltan}: {cabecera}")
    indices = [cabecera.index(c) for c in columnas]
    return [tuple(fila[i] for i in indices) for fila in filas[1:] if fila]


def esperado(producto: str, modo: str) -> list[tuple[str, ...]]:
    return _proyectar(
        CASO / "esperado" / ARCHIVOS[modo].format(p=producto), ESTABLES[modo]
    )


def observado(salida: Path, producto: str, modo: str) -> list[tuple[str, ...]]:
    return _proyectar(salida / ARCHIVOS[modo].format(p=producto), ESTABLES[modo])


def _proyecto_tecnico(proyecto: Path) -> str:
    archivo = proyecto / "talend.project"
    if archivo.is_file():
        coincide = re.search(
            r'technicalLabel="([^"]+)"', archivo.read_text(encoding="utf-8", errors="replace")
        )
        if coincide:
            return coincide.group(1)
    return proyecto.name


def parametros(salida: Path, producto: str) -> list[str]:
    """El Excel de homologación sale de `v01`; el CSV de origen, de `v02`."""
    return [
        f"producto={producto}",
        f"ruta_origen={(CASO / 'entradas' / f'DETALLE_{producto}.csv').as_posix()}",
        f"sufijo={producto}",
        "periodo_anio=2026",
        "periodo_mes=10",
        "periodo_dia=01",
        "arch_hom_tipo_doc=Homologacion_tpo_dto.xlsx",
        f"ruta_insumos={V01.as_posix()}/",
        "hoja_excel=Sheet1",
        f"ruta_resultados={salida.as_posix()}/",
    ]


def informe(
    producto: str, obs: dict[str, list[tuple[str, ...]]]
) -> bool:
    """Compara los tres flujos y el desglose vacío/cero plantado en `caso.yaml`."""
    bueno = True
    for modo in MODOS:
        esp, obtenido = sorted(esperado(producto, modo)), sorted(obs[modo])
        cuadra = esp == obtenido
        bueno &= cuadra
        print(
            f"{producto} {modo}: esperadas {len(esp)} filas, obtenidas {len(obtenido)}; "
            f"{'OK' if cuadra else 'DIFERENCIA'}"
        )
        if not cuadra:
            print(f"  solo en esperado: {sorted(Counter(esp) - Counter(obtenido))[:3]}")
            print(f"  solo en obtenido: {sorted(Counter(obtenido) - Counter(esp))[:3]}")
    desglose = {}
    for modo in ("tit_cot", "fa"):
        conteo = Counter("vacio" if f[3] == "" else "cero" if f[3] == "0" else "otro"
                         for f in obs[modo])
        desglose[f"{modo}_vacio"] = conteo["vacio"]
        desglose[f"{modo}_cero"] = conteo["cero"]
    desglose["validos"] = len(obs["valido"])
    plantado = anomalias_plantadas()[producto]
    cuadra = desglose == plantado
    bueno &= cuadra
    print(f"{producto} anomalías plantadas {plantado}; obtenidas {desglose}; "
          f"{'OK' if cuadra else 'DIFERENCIA'}")
    return bueno


def invariantes(resultados: dict[str, dict[str, list[tuple[str, ...]]]]) -> bool:
    """Las tres invariantes del caso, medidas sobre los flujos que escribió el Job emitido."""
    sabana = {p: len(_csv(CASO / "esperado" / f"SABANA_{p}.csv")) - 1 for p in PRODUCTOS}
    rechazos = {p: len(resultados[p]["tit_cot"]) + len(resultados[p]["fa"]) for p in PRODUCTOS}
    uno = all(sabana[p] == len(resultados[p]["valido"]) + rechazos[p] for p in PRODUCTOS)
    conteos = sum(
        int(fila[1]) for nombre in ("CONTEO_NRO_DOC_TIT_COT.csv", "CONTEO_NRO_DOC_FA.csv")
        for fila in _csv(CASO / "esperado" / nombre)[1:]
    )
    dos = conteos == sum(rechazos.values())
    suma = sum(int(fila[4]) for fila in resultados["CTE"]["valido"])
    esperada = int(_csv(CASO / "esperado" / "SUMA_SALDO_CTE_VALIDAS.csv")[1][0])
    tres = suma == esperada
    print(
        f"Invariantes: sábana=válidos+rechazos {'sí' if uno else 'NO'}; "
        f"conteos={conteos} frente a rechazos={sum(rechazos.values())} {'sí' if dos else 'NO'}; "
        f"suma saldo CTE={suma} frente a {esperada} {'sí' if tres else 'NO'}"
    )
    return uno and dos and tres


def validar(
    proyecto: Path, trabajo: Path, sufijo: str, java_bin: Path | None, m2: Path | None
) -> int:
    salida = trabajo / "salida"
    salida.mkdir(parents=True, exist_ok=True)
    for producto in PRODUCTOS:
        for modo in MODOS:
            (salida / ARCHIVOS[modo].format(p=producto)).unlink(missing_ok=True)
    cliente = MCP()
    proceso = proyecto / "process"
    exportado = crear_destino_build()
    copiados: list[Path] = []
    resultados: dict[str, dict] = {}
    buenos = 0
    try:
        with ExitStack() as pila:
            emision = Path(pila.enter_context(tempfile.TemporaryDirectory(prefix="emision-v02-")))
            carpeta = Path(pila.enter_context(tempfile.TemporaryDirectory(prefix="jobs-v02-")))
            emitido = emitir(PROGRAMA, None, emision)
            for extension in EXTENSIONES:
                shutil.copyfile(
                    emitido / f"job_producto_0.1{extension}",
                    carpeta / f"job_producto_0.1{extension}",
                )
            nombre = renombrar(carpeta, sufijo, _proyecto_tecnico(proyecto))["job_producto"]
            for extension in EXTENSIONES:
                origen = carpeta / f"{nombre}_0.1{extension}"
                if origen.is_file():
                    destino = proceso / origen.name
                    shutil.copyfile(origen, destino)
                    copiados.append(destino)
            cliente.llamar("talend_bridge_refresh_workspace")
            construir(cliente, [nombre])
            lanzador = exportar(cliente, nombre, exportado, m2)
            for producto in PRODUCTOS:
                corrida = ejecutar(lanzador, "Default", parametros(salida, producto), java_bin)
                print(f"Comando {producto}: {corrida['comando']}")
                print(f"Código de salida {producto}: {corrida['exitCode']}")
                if corrida["exitCode"] != 0:
                    print(f"stderr: {corrida['stderr'][-800:]}")
                    continue
                obs = {m: observado(salida, producto, m) for m in MODOS}
                resultados[producto] = obs
                if informe(producto, obs):
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
    todo = buenos == len(PRODUCTOS) and len(resultados) == len(PRODUCTOS)
    if todo:
        todo = invariantes(resultados)
    print(f"RESULTADO: {buenos} de {len(PRODUCTOS)} productos coinciden fila por fila")
    return 0 if todo else 1


def main(argv: list[str] | None = None) -> int:
    for flujo in (sys.stdout, sys.stderr):
        if hasattr(flujo, "reconfigure"):
            flujo.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--proyecto", type=Path, required=True)
    parser.add_argument("--trabajo", type=Path)
    parser.add_argument("--sufijo", help="sufijo nuevo del Job (por defecto con fecha)")
    parser.add_argument("--java-bin", type=Path, help="carpeta bin del JDK de Studio")
    parser.add_argument("--m2", type=Path, help="caché .m2 de Studio para descargar poms")
    args = parser.parse_args(argv)
    if not (args.proyecto / "talend.project").is_file():
        print(f"error: no es un proyecto Talend: {args.proyecto}", file=sys.stderr)
        return 2
    from corpus_lib.studio_validar import sufijo_nuevo

    sufijo = args.sufijo or sufijo_nuevo()
    trabajo = args.trabajo or Path(tempfile.mkdtemp(prefix="prueba-flujos-emitidos-"))
    print(f"Proyecto: {args.proyecto}\nSufijo: {sufijo}\nTrabajo: {trabajo}")
    try:
        return validar(args.proyecto, trabajo, sufijo, args.java_bin, args.m2)
    except ErrorValidacion as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
