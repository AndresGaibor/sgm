"""Hito 89 / R1-06: el `job_producto` **emitido** separa cuenta y codex con la forma del SAS real.

No se construye un Job a mano: se emite con `sgm talend` sobre `client_large.sas`, se toma solo
`job_producto`, se compila y se exporta en Studio, y se corre tres veces:

* CTE y AHO contra las entradas de `v05_codex_saldos`, comparando con `esperado/`.
* `VECTORES`, un CSV propio con las anomalías que `v05` no planta (tipo de cuenta fuera de 1..5,
  `RELACION <> 1000` exento, GMF faltante y una fila que viola las dos reglas a la vez).

`v05` solo separa el codex; R1-07 (saldos negativos) no está en el Job emitido. Por eso
`SABANA_CODEX_VALIDO_*` no se compara con `SABANA_VALIDA_*`: `cuenta_real_datos.invariantes`
comprueba en cambio que esas filas siguen en el flujo válido. Detalle de columnas estables en el
docstring de `cuenta_real_datos.py`.

Uso:
    uv run python tools/prueba_cuenta_real.py --proyecto <carpeta> \
        [--sufijo v89a] [--trabajo DIR] [--java-bin DIR] [--m2 DIR]

Código de salida 0 solo si los dos productos coinciden, los vectores coinciden y las tres
invariantes se cumplen.
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

from cuenta_real_datos import (  # noqa: E402
    ARCHIVOS,
    CASO,
    MODOS,
    PRODUCTOS,
    SUFIJO_VECTORES,
    informe,
    informe_vectores,
    invariantes,
    observado,
    vector_csv,
)
from mcp_cliente import MCP, ErrorValidacion  # noqa: E402
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
SUFIJOS = (*PRODUCTOS, SUFIJO_VECTORES)


def _proyecto_tecnico(proyecto: Path) -> str:
    archivo = proyecto / "talend.project"
    if archivo.is_file():
        coincide = re.search(
            r'technicalLabel="([^"]+)"', archivo.read_text(encoding="utf-8", errors="replace")
        )
        if coincide:
            return coincide.group(1)
    return proyecto.name


def parametros(salida: Path, sufijo: str, origen: Path) -> list[str]:
    """El Excel de homologación sale de `v01`; el CSV de origen, de `v05` o de los vectores."""
    return [
        f"producto={sufijo}",
        f"ruta_origen={origen.as_posix()}",
        f"sufijo={sufijo}",
        "periodo_anio=2026",
        "periodo_mes=10",
        "periodo_dia=01",
        "arch_hom_tipo_doc=Homologacion_tpo_dto.xlsx",
        f"ruta_insumos={V01.as_posix()}/",
        "hoja_excel=Sheet1",
        f"ruta_resultados={salida.as_posix()}/",
    ]


def origenes(trabajo: Path) -> dict[str, Path]:
    return {
        **{p: CASO / "entradas" / f"DETALLE_{p}.csv" for p in PRODUCTOS},
        SUFIJO_VECTORES: vector_csv(trabajo / "DETALLE_VECTORES.csv"),
    }


def validar(
    proyecto: Path, trabajo: Path, sufijo: str, java_bin: Path | None, m2: Path | None
) -> int:
    salida = trabajo / "salida"
    salida.mkdir(parents=True, exist_ok=True)
    for producto in SUFIJOS:
        for modo in MODOS:
            (salida / ARCHIVOS[modo].format(p=producto)).unlink(missing_ok=True)
    cliente = MCP()
    proceso = proyecto / "process"
    exportado = crear_destino_build()
    copiados: list[Path] = []
    resultados: dict[str, dict] = {}
    buenos = 0
    vectores_ok = False
    try:
        with ExitStack() as pila:
            emision = Path(pila.enter_context(tempfile.TemporaryDirectory(prefix="emision-v05-")))
            carpeta = Path(pila.enter_context(tempfile.TemporaryDirectory(prefix="jobs-v05-")))
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
            for producto, origen in origenes(trabajo).items():
                corrida = ejecutar(
                    lanzador, "Default", parametros(salida, producto, origen), java_bin
                )
                print(f"Comando {producto}: {corrida['comando']}")
                print(f"Código de salida {producto}: {corrida['exitCode']}")
                if corrida["exitCode"] != 0:
                    print(f"stderr: {corrida['stderr'][-800:]}")
                    continue
                if producto == SUFIJO_VECTORES:
                    vectores_ok = informe_vectores(salida)
                    continue
                obs = observado(salida, producto)
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
    todo = buenos == len(PRODUCTOS) and len(resultados) == len(PRODUCTOS) and vectores_ok
    if todo:
        todo = invariantes(resultados)
    print(
        f"RESULTADO: {buenos} de {len(PRODUCTOS)} productos coinciden fila por fila; "
        f"vectores {'OK' if vectores_ok else 'DIFERENCIA'}"
    )
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
    trabajo = args.trabajo or Path(tempfile.mkdtemp(prefix="prueba-cuenta-real-"))
    print(f"Proyecto: {args.proyecto}\nSufijo: {sufijo}\nTrabajo: {trabajo}")
    try:
        return validar(args.proyecto, trabajo, sufijo, args.java_bin, args.m2)
    except ErrorValidacion as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
