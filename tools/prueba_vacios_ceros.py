"""R1-04 / hito 86: los filtros de vacíos y ceros de `v02` se ejecutan en Studio.

Las tres reglas salen del propio `v02_vacios_ceros/programa.sas` con
`sgm.proceso.reglas_fila` (el `client_large.sas` real tiene las mismas formas, 3 por producto).
Se traducen a `expressionFilter` con `sgm.talend_item.filtros_fila` y se monta un Job mínimo:

    tFileInputDelimited -> tMap_normalizacion -> tMap_filtros -> 3 tFileOutputDelimited

No es el `job_producto` emitido por `sgm talend`: es un Job aislado construido con los módulos
de producto, igual que los arneses de R1-01/R1-02. La integración en el emisor es el hito 87.
La comparación es fila por fila contra `esperado/`; ver `vacios_ceros_datos.py`.

Uso:
    uv run python tools/prueba_vacios_ceros.py --proyecto <carpeta> \
        [--sufijo v86a] [--trabajo DIR] [--java-bin DIR] [--m2 DIR]

Código de salida 0 solo si los dos productos coinciden fila por fila, el desglose de anomalías
plantadas cuadra y se cumplen las tres invariantes del caso.
"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tools"))

from mcp_cliente import MCP, ErrorValidacion  # noqa: E402
from vacios_ceros_datos import (  # noqa: E402
    CASO,
    COLUMNAS,
    ESQUEMAS,
    PRODUCTOS,
    SALIDAS,
    esperado,
    informe,
    invariantes,
    observado,
)
from validar_en_studio import (  # noqa: E402
    borrar_destino_build,
    construir,
    crear_destino_build,
    ejecutar,
    exportar,
    renombrar,
)

from sgm.proceso.reglas_fila import reglas_fila  # noqa: E402
from sgm.talend_item.escritura import escribir_job  # noqa: E402
from sgm.talend_item.filtros_fila import salidas_filtro  # noqa: E402
from sgm.talend_item.modelo import Columna, Conexion, Job, ParametroContexto  # noqa: E402
from sgm.talend_item.normalizacion import as_text, input_left_wd  # noqa: E402
from sgm.talend_item.plantillas import nodo_desde_plantilla  # noqa: E402
from sgm.talend_item.tmap import EntradaMap, SalidaMap, tmap  # noqa: E402

SAS = CASO / "programa.sas"
_EXTENSIONES = (".item", ".properties")
_FILA = "normalizados"
# `v02` solo demuestra una conversión: NRO_DOC=input(left(NRO_DOC_TXT), 30.). El client_large
# real convierte también TIPO_DOC con 8., pero v02 lo deja como texto TD01..TD04; aplicar los
# 15 informats del programa real aquí borraría esa columna. No se inventan conversiones.
INFORMATS = {"NRO_DOC": (30, 0)}


def reglas():
    """Las tres reglas de `v02`, en el orden del SAS."""
    resultado = reglas_fila(SAS.read_text(encoding="utf-8"))
    if sorted(r.modo for r in resultado) != sorted(ESQUEMAS):
        raise ErrorValidacion(f"v02 no declara las tres reglas esperadas: {resultado}")
    return resultado


def job_vacios_ceros() -> Job:
    """Job mínimo: normaliza `NRO_DOC` y separa tit_cot, fa y válidos con `expressionFilter`."""
    cols = [Columna(c) for c in COLUMNAS]
    normalizadas = {
        c.nombre: (
            as_text(input_left_wd(f"row1.{c.nombre}", *INFORMATS[c.nombre]))
            if c.nombre in INFORMATS
            else f"row1.{c.nombre}"
        )
        for c in cols
    }
    esquemas = {modo: [Columna(c) for c in columnas] for modo, columnas in ESQUEMAS.items()}
    salidas = salidas_filtro(reglas(), esquemas, fila=_FILA)
    nodos = [
        nodo_desde_plantilla(
            "tFileInputDelimited", "tFileInputDelimited_1", 0, 0,
            {
                "FILENAME": "context.ruta_origen",
                "FIELDSEPARATOR": '";"',
                "HEADER": "0",
            },
            columnas=cols,
        ),
        tmap(
            "tMap_normalizacion",
            [EntradaMap("row1", cols)],
            [SalidaMap(_FILA, cols, normalizadas)],
            240, 0,
        ),
        tmap("tMap_filtros", [EntradaMap(_FILA, cols)], salidas, 480, 0),
    ]
    conexiones = [
        Conexion("tFileInputDelimited_1", "tMap_normalizacion", "row1"),
        Conexion("tMap_normalizacion", "tMap_filtros", _FILA),
    ]
    for i, salida in enumerate(salidas, start=1):
        unico = f"tFileOutputDelimited_{i}"
        nodos.append(
            nodo_desde_plantilla(
                "tFileOutputDelimited", unico, 720, (i - 1) * 120,
                {
                    "FILENAME": f'context.ruta_salida + "/{SALIDAS[salida.nombre]}"',
                    "FIELDSEPARATOR": '","',
                    "INCLUDEHEADER": "false",
                    "APPEND": "false",
                },
                columnas=salida.columnas,
            )
        )
        conexiones.append(Conexion("tMap_filtros", unico, salida.nombre))
    contextos = {
        "Default": [ParametroContexto("ruta_origen"), ParametroContexto("ruta_salida")]
    }
    return Job("prueba_vacios_ceros", nodos=nodos, conexiones=conexiones, contextos=contextos)


def _proyecto_tecnico(proyecto: Path) -> str:
    archivo = proyecto / "talend.project"
    if archivo.is_file():
        coincide = re.search(
            r'technicalLabel="([^"]+)"', archivo.read_text(encoding="utf-8", errors="replace")
        )
        if coincide:
            return coincide.group(1)
    return proyecto.name


def _preparar(trabajo: Path) -> None:
    for producto in PRODUCTOS:
        salida = trabajo / "salida" / producto
        salida.mkdir(parents=True, exist_ok=True)
        for nombre in SALIDAS.values():
            (salida / nombre).unlink(missing_ok=True)


def validar(
    proyecto: Path, trabajo: Path, sufijo: str, java_bin: Path | None, m2: Path | None
) -> int:
    """Compila y ejecuta el Job para CTE y AHO; compara contra los esperados del corpus."""
    _preparar(trabajo)
    cliente = MCP()
    proceso = proyecto / "process"
    exportado = crear_destino_build()
    temporal = Path(tempfile.mkdtemp(prefix="jobs-v02-"))
    copiados: list[Path] = []
    resultados: dict[str, dict] = {}
    buenos = 0
    try:
        escribir_job(job_vacios_ceros(), temporal)
        nombre = renombrar(temporal, sufijo, _proyecto_tecnico(proyecto))["prueba_vacios_ceros"]
        for extension in _EXTENSIONES:
            origen = temporal / f"{nombre}_0.1{extension}"
            if origen.is_file():
                destino = proceso / origen.name
                shutil.copyfile(origen, destino)
                copiados.append(destino)
        cliente.llamar("talend_bridge_refresh_workspace")
        construir(cliente, [nombre])
        lanzador = exportar(cliente, nombre, exportado, m2)
        for producto in PRODUCTOS:
            salida = trabajo / "salida" / producto
            parametros = [
                f"ruta_origen={(CASO / 'entradas' / f'DETALLE_{producto}.csv').as_posix()}",
                f"ruta_salida={salida.as_posix()}",
            ]
            corrida = ejecutar(lanzador, "Default", parametros, java_bin)
            print(f"Comando {producto}: {corrida['comando']}")
            print(f"Código de salida {producto}: {corrida['exitCode']}")
            if corrida["exitCode"] != 0:
                print(f"stderr: {corrida['stderr'][-800:]}")
                continue
            obs = observado(salida)
            resultados[producto] = obs
            if informe(producto, esperado(producto), obs):
                buenos += 1
    finally:
        for archivo in copiados:
            archivo.unlink(missing_ok=True)
        shutil.rmtree(temporal, ignore_errors=True)
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
    trabajo = args.trabajo or Path(tempfile.mkdtemp(prefix="prueba-vacios-ceros-"))
    print(f"Proyecto: {args.proyecto}\nSufijo: {sufijo}\nTrabajo: {trabajo}")
    try:
        return validar(args.proyecto, trabajo, sufijo, args.java_bin, args.m2)
    except ErrorValidacion as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
