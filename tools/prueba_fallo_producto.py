"""Hito 98d / R2-07: el `job_producto` emitido falla si no lee su archivo de origen (DIE_ON_ERROR).

Emite `job_producto` con el mismo emisor que `prueba_saldo.py` y lo ejecuta en Studio con
`ruta_origen` apuntando a un archivo que no existe. Con `DIE_ON_ERROR=true` en el lector, el Job
sale con código distinto de 0 y el error queda en la salida. Sin esa opción, Studio solo registra
el error y el Job puede terminar bien (medido en el hito 97d con `tFileInputDelimited`).

Uso:
    uv run python tools/prueba_fallo_producto.py --proyecto <carpeta> --java-bin DIR --m2 DIR
        [--sufijo v98c] [--trabajo DIR]
"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "tools"))

from mcp_cliente import MCP, ErrorValidacion  # noqa: E402
from prueba_cuenta_real import parametros  # noqa: E402
from prueba_saldo import emitir_producto  # noqa: E402
from validar_en_studio import (  # noqa: E402
    borrar_destino_build,
    construir,
    crear_destino_build,
    ejecutar,
    exportar,
    renombrar,
)

EXTENSIONES = (".item", ".properties")


def _proyecto_tecnico(proyecto: Path) -> str:
    archivo = proyecto / "talend.project"
    coincide = re.search(r'technicalLabel="([^"]+)"', archivo.read_text(encoding="utf-8"))
    return coincide.group(1) if coincide else proyecto.name


def validar(proyecto: Path, trabajo: Path, sufijo: str, java_bin, m2) -> int:
    salida = trabajo / "salida"
    salida.mkdir(parents=True, exist_ok=True)
    origen = trabajo / "no_existe_origen.csv"  # deliberadamente ausente
    cliente = MCP()
    copiados: list[Path] = []
    destino_build = crear_destino_build()
    try:
        carpeta = trabajo / "emit"
        carpeta.mkdir(exist_ok=True)
        emitir_producto(carpeta)
        nombre = renombrar(carpeta, sufijo, _proyecto_tecnico(proyecto))["job_producto"]
        for extension in EXTENSIONES:
            origen_item = carpeta / f"{nombre}_0.1{extension}"
            if origen_item.is_file():
                destino = proyecto / "process" / origen_item.name
                shutil.copyfile(origen_item, destino)
                copiados.append(destino)
        cliente.llamar("talend_bridge_refresh_workspace")
        construir(cliente, [nombre])
        lanzador = exportar(cliente, nombre, destino_build, m2)
        corrida = ejecutar(lanzador, "Default", parametros(salida, "CTE", origen), java_bin)
    finally:
        borrar_destino_build(destino_build)
        for archivo in copiados:
            archivo.unlink(missing_ok=True)
        try:
            cliente.llamar("talend_bridge_refresh_workspace")
        except ErrorValidacion:
            pass
        print(f"Limpieza: {len(copiados)} archivos borrados del proyecto")
    print(f"Comando: {corrida['comando']}")
    print(f"Código de salida: {corrida['exitCode']}")
    print("stdout:\n" + corrida["stdout"])
    if corrida["stderr"].strip():
        print("stderr:\n" + corrida["stderr"])
    if corrida["exitCode"] == 0:
        print("RESULTADO: DIFERENCIA, el Job terminó con 0 aunque falta el origen")
        return 1
    print("RESULTADO: OK, el Job falla con código distinto de 0 al faltar el origen")
    return 0


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
    trabajo = args.trabajo or Path(tempfile.mkdtemp(prefix="prueba-fallo-"))
    print(f"Proyecto: {args.proyecto}\nSufijo: {args.sufijo}\nTrabajo: {trabajo}")
    try:
        return validar(args.proyecto, trabajo, args.sufijo, args.java_bin, args.m2)
    except ErrorValidacion as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
