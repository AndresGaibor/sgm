"""Ejecuta un conjunto de Jobs ya emitidos en Talend Studio con las entradas de un caso.

Reutiliza el protocolo de `tools/validar_en_studio.py` (nombre nuevo por intento, hijos antes que
el padre, exportación y lanzador, borrado de los Jobs de prueba al terminar) sin modificarlo.
Aquí se añaden tres cosas: la carpeta de trabajo con las entradas del caso, los parámetros de
contexto que apuntan a ella y la lectura de la salida. El padre no se parchea: las rutas llegan
como `--context_param`.

Hallazgo: `renombrar` lee `<job>_0.1.item`; los Jobs deben tener versión 0.1.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from mcp_cliente import MCP, ErrorValidacion, descargar_poms
from validar_en_studio import construir, ejecutar, renombrar

from .caso import Caso
from .studio_mapa import parametros_contexto
from .studio_trabajo import archivos_salida, preparar_trabajo

_TECNICO = re.compile(r'technicalLabel="([^"]+)"')
_EXTENSIONES = (".item", ".properties")
_RONDAS_POMS = 8


@dataclass
class EjecucionStudio:
    """Resultado de correr el lanzador. `error` no vacío significa que no hubo salida fiable."""

    trabajo: Path
    salida: list[Path]
    exit_code: int | None
    stderr: str = ""
    error: str = ""

    @property
    def ok(self) -> bool:
        return not self.error and self.exit_code == 0


def _proyecto_tecnico(proyecto: Path) -> str:
    """Nombre técnico del proyecto (`technicalLabel` de talend.project), o el de la carpeta."""
    archivo = proyecto / "talend.project"
    if archivo.is_file():
        coincidencia = _TECNICO.search(archivo.read_text(encoding="utf-8", errors="replace"))
        if coincidencia:
            return coincidencia.group(1)
    return proyecto.name


def _copiar_jobs(carpeta_jobs: Path, destino: Path) -> list[str]:
    """Copia los `.item` y `.properties` a `destino` y devuelve los nombres base de los Jobs."""
    items = sorted(carpeta_jobs.glob("*.item"))
    if not items:
        raise ErrorValidacion(f"no hay archivos .item en {carpeta_jobs}")
    for origen in carpeta_jobs.iterdir():
        if origen.suffix in _EXTENSIONES and origen.is_file():
            shutil.copyfile(origen, destino / origen.name)
    return [re.sub(r"_\d+\.\d+\.item$", "", item.name) for item in items]


def _exportar(cliente: MCP, job: str, destino: Path, m2: Path | None) -> Path:
    """Exporta el Build Job y devuelve su lanzador `<job>_run.bat`.

    A diferencia de `validar_en_studio.exportar`, busca el lanzador en todo `destino`: el
    servidor lo deja en una subcarpeta `<destino>/<job>/`. Reintenta hasta 8 rondas
    descargando los poms de Maven que falten en la caché de Studio.
    """
    ultimo = ""
    for _ in range(_RONDAS_POMS):
        try:
            cliente.llamar(
                "talend_deliverables_build_job", {"jobName": job, "destinationDir": str(destino)}
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
    raise ErrorValidacion(f"exportación fallida: {ultimo[:1200]}")


def sufijo_nuevo() -> str:
    """Sufijo distinto en cada intento: Studio guarda en memoria cada Job por su identificador."""
    return "cs" + datetime.now().strftime("%Y%m%d%H%M%S")


def validar_en_studio(
    caso: Caso,
    carpeta_jobs: Path,
    padre: str,
    proyecto: Path,
    *,
    parametros: list[str] | None = None,
    mapa: dict[str, str] | None = None,
    trabajo: Path | None = None,
    cliente: MCP | None = None,
    sufijo: str | None = None,
    contexto: str = "Default",
    java_bin: Path | None = None,
    m2: Path | None = None,
) -> EjecucionStudio:
    """Compila, exporta y ejecuta el padre con las entradas del caso. Borra lo que copió.

    `parametros` son las variables de contexto literales (`clave=valor`); `mapa`, las rutas del
    caso (ver `studio_mapa`). Lanza `ErrorValidacion` si el protocolo falla antes de ejecutar.
    """
    if not (proyecto / "talend.project").is_file():
        raise ErrorValidacion(f"no es un proyecto Talend (falta talend.project): {proyecto}")
    trabajo = preparar_trabajo(caso, trabajo or Path(tempfile.mkdtemp(prefix="corpus-studio-")))
    pares = parametros_contexto(mapa or {}, trabajo, parametros or [])
    cliente = cliente or MCP()
    temporal = Path(tempfile.mkdtemp(prefix="jobs-"))
    exportado = Path(tempfile.mkdtemp(prefix="build-"))
    copiados: list[Path] = []
    try:
        nombres = _copiar_jobs(carpeta_jobs, temporal)
        if padre not in nombres:
            raise ErrorValidacion(f"el padre '{padre}' no está entre los Jobs: {nombres}")
        renombres = renombrar(temporal, sufijo or sufijo_nuevo(), _proyecto_tecnico(proyecto))
        nuevo_padre = renombres[padre]
        proceso = proyecto / "process"
        proceso.mkdir(exist_ok=True)
        for nuevo in renombres.values():
            for extension in _EXTENSIONES:
                origen = temporal / f"{nuevo}_0.1{extension}"
                if origen.exists():
                    destino = proceso / origen.name
                    shutil.copyfile(origen, destino)
                    copiados.append(destino)
        cliente.llamar("talend_bridge_refresh_workspace")
        hijos = [n for viejo, n in renombres.items() if viejo != padre]
        if hijos:
            construir(cliente, hijos)
        construir(cliente, [nuevo_padre])
        lanzador = _exportar(cliente, nuevo_padre, exportado, m2)
        return _ejecutar_lanzador(lanzador, contexto, pares, java_bin, trabajo)
    except ErrorValidacion as fallo:
        return EjecucionStudio(trabajo, [], None, error=str(fallo))
    finally:
        for archivo in copiados:
            archivo.unlink(missing_ok=True)
        shutil.rmtree(temporal, ignore_errors=True)
        try:
            cliente.llamar("talend_bridge_refresh_workspace")
        except ErrorValidacion:
            pass


def _ejecutar_lanzador(
    lanzador: Path,
    contexto: str,
    pares: list[str],
    java_bin: Path | None,
    trabajo: Path,
) -> EjecucionStudio:
    """Corre el lanzador con los parámetros y recoge lo que dejó en `salida/`."""
    try:
        resultado = ejecutar(lanzador, contexto, pares, java_bin)
    except subprocess.TimeoutExpired:
        return EjecucionStudio(trabajo, archivos_salida(trabajo), None, error="tiempo agotado")
    codigo = resultado["exitCode"]
    error = "" if codigo == 0 else f"el Job terminó con código {codigo}"
    return EjecucionStudio(trabajo, archivos_salida(trabajo), codigo, resultado["stderr"], error)
