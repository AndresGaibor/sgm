"""Validador externo: emite un programa, lo compila, lo exporta y lo ejecuta en Talend Studio.

Uso: uv run python tools/validar_en_studio.py <programa.sas> --project <ruta> [--insumos DIR]
     [--productos DIR] [--sufijo v1] [--contexto DEV] [--param clave=valor] [--dry-run]

Convierte el protocolo de `docs/plan-reescritura/tareas-agente.md` (sección 3) en un comando:
emite los Jobs con un nombre nuevo, parchea el padre para correrlo con datos simulados, los copia
al proyecto, refresca el workspace, compila los hijos, luego el padre, exporta y ejecuta el
launcher. **Siempre** borra del proyecto los Jobs de prueba y refresca el workspace al terminar,
aunque falle.

No es parte del producto: vive en `tools/` y habla con talend-mcp por HTTP (`urllib`, sin
dependencias). El servidor debe estar arrancado con permiso de escritura, por ejemplo:

    TALEND_MCP_ALLOW_WRITE=1 TALEND_MCP_ALLOW_EXECUTE=1 bun run start:server

Hallazgos que implementa (no los redescubras): el nombre de Job debe ser nuevo en cada intento
porque Studio cachea el modelo en memoria; compilar los hijos antes que el padre; la exportación
puede pedir poms de Maven que se descargan solos (hasta 8 rondas) en la caché de Studio.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

from mcp_cliente import MCP, ErrorValidacion, descargar_poms

RAIZ = Path(__file__).resolve().parents[1]
_NOMBRE_ITEM = re.compile(r"^(?P<nombre>.+)_(?P<version>\d+(?:\.\d+)*)\.item$")


def emitir(programa: Path, jobs_yaml: Path | None, destino: Path) -> Path:
    """Escribe los Jobs con `sgm talend` y devuelve la carpeta `process/` con los `.item`."""
    comando = [sys.executable, "-m", "sgm.cli", "talend", str(programa), "--out", str(destino)]
    if jobs_yaml:
        comando += ["--jobs", str(jobs_yaml)]
    salida = subprocess.run(comando, cwd=RAIZ, capture_output=True, text=True, check=False)
    if salida.returncode != 0:
        raise ErrorValidacion(f"sgm talend falló: {salida.stderr[-1200:]}")
    carpeta = destino / programa.stem / "talend" / "process"
    if not list(carpeta.glob("*.item")):
        raise ErrorValidacion(f"no se emitió ningún .item en {carpeta}")
    return carpeta


def _id_propiedad(base: str) -> str:
    """Identificador determinista del `.properties`; debe coincidir con el del emisor (T94)."""
    from sgm.talend_item.item import _id

    return _id(f"{base}:id")


def versiones(carpeta: Path) -> dict[str, str]:
    """Nombre base de cada Job y la versión con la que está guardado, leída de su `.item`."""
    encontradas: dict[str, str] = {}
    for archivo in sorted(carpeta.glob("*.item")):
        coincide = _NOMBRE_ITEM.match(archivo.name)
        if coincide:
            encontradas[coincide.group("nombre")] = coincide.group("version")
    return encontradas


def renombrar(carpeta: Path, sufijo: str, proyecto: str) -> dict[str, str]:
    """Renombra los Jobs con sufijo nuevo; reescribe referencias entre `tRunJob` e ids.

    La versión sale del nombre del archivo: Studio guarda `0.1`, `0.2` o `1.0` y no se fija
    ninguna. Los ids del `.properties` se recalculan con la versión real, porque el emisor los
    deriva de `<job>_<versión>`.
    """
    guardadas = versiones(carpeta)
    mapa = {viejo: f"{viejo}_{sufijo}" for viejo in guardadas}
    for viejo, version in guardadas.items():
        nuevo = mapa[viejo]
        base_vieja, base_nueva = f"{viejo}_{version}", f"{nuevo}_{version}"
        item = carpeta / f"{base_vieja}.item"
        texto = item.read_text(encoding="utf-8")
        viejo_id, nuevo_id = _id_propiedad(base_vieja), _id_propiedad(base_nueva)
        texto = texto.replace(f'value="{viejo}"', f'value="{nuevo}"')
        texto = texto.replace(f'value="{proyecto}:{viejo_id}"', f'value="{proyecto}:{nuevo_id}"')
        item.write_text(texto, encoding="utf-8", newline="\n")
        item.rename(carpeta / f"{base_nueva}.item")
        propiedades = carpeta / f"{base_vieja}.properties"
        if not propiedades.exists():
            continue
        texto = propiedades.read_text(encoding="utf-8")
        texto = texto.replace(f'id="{viejo_id}"', f'id="{nuevo_id}"')
        for atributo in ("label", "displayName", "path"):
            texto = texto.replace(f'{atributo}="{viejo}"', f'{atributo}="{nuevo}"')
        texto = texto.replace(f'href="{base_vieja}.item', f'href="{base_nueva}.item')
        propiedades.write_text(texto, encoding="utf-8", newline="\n")
        propiedades.rename(carpeta / f"{base_nueva}.properties")
    return mapa


def _literal(valor: str) -> str:
    return '"' + valor.replace("\\", "\\\\").replace('"', '\\"') + '"'


def parchear_padre(
    carpeta: Path, padre: str, insumos: Path | None, productos: dict[str, Path]
) -> None:
    """Fija `env_nombre=DEV`, la carpeta de insumos y los CSV simulados de cada producto."""
    archivo = carpeta / f"{padre}_0.1.item"
    arbol = ET.parse(archivo)
    raiz = arbol.getroot()
    for parametro in raiz.iter("contextParameter"):
        if parametro.get("name") == "env_nombre":
            parametro.set("value", "DEV")
        elif parametro.get("name") == "ruta_insumos" and insumos is not None:
            parametro.set("value", str(insumos).replace("\\", "/"))
    for nodo in raiz.iter("node"):
        tabla = nodo.find("elementParameter[@name='INTABLE']")
        if tabla is None:
            continue
        celdas = list(tabla)
        for indice, celda in enumerate(celdas):
            valor = celda.get("value")
            producto = next((p for p in productos if valor == _literal(p.upper())), None)
            if producto is None or indice + 1 >= len(celdas):
                continue
            ruta = str(productos[producto]).replace("\\", "/")
            celdas[indice + 1].set("value", _literal(ruta))
    arbol.write(archivo, encoding="UTF-8", xml_declaration=True)


def construir(mcp: MCP, nombres: list[str]) -> None:
    datos = mcp.llamar("talend_job_build_batch", {"jobs": nombres, "parallelism": 4})
    fallos = [j for j in (datos or {}).get("jobs", []) if not j.get("ok")]
    if fallos:
        raise ErrorValidacion(f"no compilan: {json.dumps(fallos, ensure_ascii=False)[:1200]}")


def exportar(mcp: MCP, job: str, destino: Path, m2: Path | None) -> Path:
    """Exporta el Build Job; reintenta hasta 8 rondas descargando los poms que falten.

    El servidor deja el lanzador en una subcarpeta (`<destino>/<job>/<job>_run.bat`), así que se
    busca en todo `destino`; buscarlo solo en la raíz fue el fallo del primer validador.
    """
    ultimo = ""
    for _ in range(8):
        try:
            mcp.llamar(
                "talend_deliverables_build_job",
                {"jobName": job, "destinationDir": str(destino)},
            )
            encontrados = sorted(destino.rglob(f"{job}_run.bat"))
            if encontrados:
                return encontrados[0]
            ultimo = f"no apareció {job}_run.bat en {destino}"
        except ErrorValidacion as error:
            ultimo = str(error)
        faltan = descargar_poms(ultimo, m2)
        if not faltan:
            break
        print(f"  poms descargados: {', '.join(faltan)}")
    raise ErrorValidacion(f"exportación fallida: {ultimo[:1200]}")


def comando_lanzador(lanzador: Path, contexto: str | None, parametros: list[str]) -> str:
    """Línea de comando del lanzador, con cada valor entre comillas.

    Va a `shell=True`: sin comillas, una ruta o un valor con espacios se parte en argumentos y el
    lanzador rechaza la ejecución.
    """
    partes = [f'"{lanzador}"']
    if contexto:
        partes.append(f'--context="{contexto}"')
    partes += [f'--context_param "{p}"' for p in parametros]
    return " ".join(partes)


def ejecutar(
    lanzador: Path, contexto: str | None, parametros: list[str], java_bin: Path | None
) -> dict:
    """Corre el launcher exportado y devuelve salida y código."""
    comando = comando_lanzador(lanzador, contexto, parametros)
    entorno = dict(os.environ)
    if java_bin is not None:
        entorno["PATH"] = str(java_bin) + os.pathsep + entorno.get("PATH", "")
    proceso = subprocess.run(
        comando,
        cwd=lanzador.parent,
        capture_output=True,
        text=True,
        errors="replace",
        timeout=900,
        env=entorno,
        shell=True,
    )
    return {
        "exitCode": proceso.returncode,
        "comando": comando,
        "stdout": proceso.stdout[-4000:],
        "stderr": proceso.stderr[-4000:],
    }


def crear_destino_build() -> Path:
    """Carpeta temporal `build-*` donde el servidor deja el Build Job exportado."""
    return Path(tempfile.mkdtemp(prefix="build-"))


def borrar_destino_build(destino: Path) -> None:
    """Borra la carpeta de build: sin esto quedan `build-*` en `%TEMP%` tras cada validación."""
    shutil.rmtree(destino, ignore_errors=True)


def validar(args: argparse.Namespace) -> dict:
    from sgm.agrupacion import cargar_declaracion
    from sgm.proceso.origen_producto import origenes_producto
    from sgm.talend_item.arquitectura import cargar_arquitectura

    programa: Path = args.programa
    proyecto = Path(args.project)
    if not (proyecto / "talend.project").exists():
        raise ErrorValidacion(f"no es un proyecto Talend (falta talend.project): {proyecto}")
    jobs_yaml = args.jobs or RAIZ / "decisiones" / f"{programa.stem}.jobs.yaml"
    arq = cargar_arquitectura(jobs_yaml)
    productos: dict[str, Path] = {}
    if args.productos:
        texto = programa.read_text(encoding="utf-8", errors="replace")
        declaracion = cargar_declaracion(RAIZ / "decisiones" / f"{programa.stem}.agrupacion.yaml")
        for nombre, origen in origenes_producto(texto, declaracion.productos).por_producto.items():
            productos[nombre] = args.productos / origen.fuente.archivo
    sufijo = args.sufijo or os.environ.get("VALIDAR_SUFIJO", "v1")
    print(f"Proyecto: {proyecto}\nSufijo: {sufijo}\nProductos simulados: {len(productos)}")
    if args.dry_run:
        return {"dryRun": True, "sufijo": sufijo, "productos": sorted(productos)}

    mcp = MCP()
    proceso = proyecto / "process"
    copiados: list[Path] = []
    exportado = crear_destino_build()
    try:
        with tempfile.TemporaryDirectory(prefix="emit-") as temporal:
            carpeta = emitir(programa, jobs_yaml, Path(temporal))
            mapa = renombrar(carpeta, sufijo, arq.proyecto)
            parchear_padre(carpeta, mapa[arq.padre], args.insumos, productos)
            for nombre in mapa.values():
                for extension in (".item", ".properties"):
                    origen = carpeta / f"{nombre}_0.1{extension}"
                    if origen.exists():
                        destino = proceso / origen.name
                        destino.write_bytes(origen.read_bytes())
                        copiados.append(destino)
        mcp.llamar("talend_bridge_refresh_workspace")
        hijos = [n for v, n in mapa.items() if v != arq.padre]
        print(f"Compilando hijos: {', '.join(hijos)}")
        construir(mcp, hijos)
        print(f"Compilando padre: {mapa[arq.padre]}")
        construir(mcp, [mapa[arq.padre]])
        lanzador = exportar(mcp, mapa[arq.padre], exportado, args.m2)
        print(f"Ejecutando {lanzador} (contexto {args.contexto or 'Default'})")
        return ejecutar(lanzador, args.contexto, args.param, args.java_bin)
    finally:
        for archivo in copiados:
            archivo.unlink(missing_ok=True)
        try:
            mcp.llamar("talend_bridge_refresh_workspace")
        except ErrorValidacion:
            pass
        borrar_destino_build(exportado)
        print(f"Limpieza: {len(copiados)} archivos borrados del proyecto y build temporal borrado")


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("programa", type=Path)
    parser.add_argument("--project", required=True, help="Carpeta con talend.project")
    parser.add_argument("--jobs", type=Path, help="YAML de arquitectura de Jobs")
    parser.add_argument("--insumos", type=Path, help="Carpeta con los Excel simulados")
    parser.add_argument("--productos", type=Path, help="Carpeta con los CSV de producto simulados")
    parser.add_argument("--sufijo", help="Sufijo nuevo de los Jobs (por defecto v1)")
    parser.add_argument("--contexto", default="DEV")
    parser.add_argument("--param", action="append", default=[], metavar="CLAVE=VALOR")
    parser.add_argument("--java-bin", type=Path, help="Carpeta bin del JDK de Studio")
    parser.add_argument("--m2", type=Path, help="Caché .m2 de Studio para descargar poms")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    try:
        resultado = validar(args)
    except ErrorValidacion as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(json.dumps(resultado, ensure_ascii=False, indent=2))
    return 0 if resultado.get("exitCode", 0) == 0 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
