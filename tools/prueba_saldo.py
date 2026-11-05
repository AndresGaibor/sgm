"""Hito 90 / R1-07: los saldos negativos del `job_producto` emitido se ejecutan en Studio.

El emisor no produce `job_producto` para `v05_codex_saldos` (su `DETALLE_&sufijo..csv` no se
resuelve a un producto), así que el Job se emite con la misma función que `sgm talend`:

* Columnas, filtros de R1-02, ramas de R1-04 y de R1-06: `client_large.sas` y sus decisiones.
* Regla de saldo negativo: `reglas_saldo` lee `v05_codex_saldos/programa.sas`. El SAS de cliente
  pone los negativos en cero y no tiene esa tabla; eso se publica como pendiente, no se emite.

Se corre tres veces con el mismo `.item`: CTE y AHO contra las entradas de `v05`, y `VECTORES`
con los vectores propios de `saldo_datos.py`. Código de salida 0 solo si los dos productos y los
vectores coinciden y se cumplen las invariantes.

Uso:
    uv run python tools/prueba_saldo.py --proyecto <carpeta> [--sufijo v90a] [--trabajo DIR] \
        [--java-bin DIR] [--m2 DIR]
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
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "tools"))

from mcp_cliente import MCP, ErrorValidacion  # noqa: E402
from prueba_cuenta_real import parametros  # noqa: E402
from saldo_datos import (  # noqa: E402
    ARCHIVOS,
    CASO,
    PRODUCTOS,
    SUFIJO_VECTORES,
    informe,
    informe_vectores,
    invariantes,
    observado,
    vector_csv,
)
from validar_en_studio import (  # noqa: E402
    borrar_destino_build,
    construir,
    crear_destino_build,
    ejecutar,
    exportar,
    renombrar,
)

PROGRAMA = REPO / "tests" / "fixtures" / "sas" / "client" / "client_large.sas"
V05 = CASO / "programa.sas"
DECISIONES = REPO / "decisiones"
EXTENSIONES = (".item", ".properties")
SUFIJOS = (*PRODUCTOS, SUFIJO_VECTORES)


def emitir_producto(carpeta: Path) -> Path:
    """Escribe `job_producto_0.1.item` en `carpeta` con la regla de saldo leída de v05."""
    from sgm.agrupacion import cargar_declaracion
    from sgm.cli_talend import _cuenta, _delimitador, _flujos, _saldo
    from sgm.proceso.origen_producto import origenes_producto
    from sgm.talend_item.arquitectura import cargar_arquitectura
    from sgm.talend_item.escritura import escribir_job
    from sgm.talend_item.jobs_producto import job_producto

    texto = PROGRAMA.read_text(encoding="utf-8", errors="replace")
    arq = cargar_arquitectura(DECISIONES / "client_large.jobs.yaml")
    declaracion = cargar_declaracion(DECISIONES / "client_large.agrupacion.yaml")
    origenes = origenes_producto(texto, declaracion.productos)
    flujos, _ = _flujos(texto)
    cuenta, _ = _cuenta(texto)
    regla_v05 = V05.read_text(encoding="utf-8", errors="replace")
    saldo, avisos = _saldo(regla_v05, cuenta)
    for aviso in avisos:
        print(f"Pendiente: {aviso}")
    variables = tuple(v for _, v in arq.periodo.variables) if arq.periodo else ()
    job = job_producto(
        arq,
        origenes.columnas_comunes,
        variables,
        "saldos negativos (R1-07, regla de v05)",
        _delimitador(origenes),
        validacion=arq.validaciones[0] if arq.validaciones else None,
        numericas=origenes.numericas_comunes,
        flujos=flujos,
        cuenta=cuenta,
        regla_saldo=saldo,
    )
    item, _ = escribir_job(job, carpeta)
    return item


def _proyecto_tecnico(proyecto: Path) -> str:
    archivo = proyecto / "talend.project"
    if archivo.is_file():
        coincide = re.search(
            r'technicalLabel="([^"]+)"', archivo.read_text(encoding="utf-8", errors="replace")
        )
        if coincide:
            return coincide.group(1)
    return proyecto.name


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
        for archivo in ARCHIVOS.values():
            (salida / archivo.format(p=producto)).unlink(missing_ok=True)
    cliente = MCP()
    proceso = proyecto / "process"
    exportado = crear_destino_build()
    copiados: list[Path] = []
    resultados: dict[str, dict] = {}
    buenos = 0
    vectores_ok = False
    try:
        with ExitStack() as pila:
            carpeta = Path(pila.enter_context(tempfile.TemporaryDirectory(prefix="jobs-saldo-")))
            emitir_producto(carpeta)
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
    trabajo = args.trabajo or Path(tempfile.mkdtemp(prefix="prueba-saldo-"))
    print(f"Proyecto: {args.proyecto}\nSufijo: {sufijo}\nTrabajo: {trabajo}")
    try:
        return validar(args.proyecto, trabajo, sufijo, args.java_bin, args.m2)
    except ErrorValidacion as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
