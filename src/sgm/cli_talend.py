"""Comando `sgm talend`: escribe los Jobs de Talend (`.item` y `.properties`) de un programa SAS.

Parte de la arquitectura declarada en `decisiones/<programa>.jobs.yaml` y de los productos de
`decisiones/<programa>.agrupacion.yaml`. Los datos que el SAS no demuestra quedan vacíos y se
listan como pendientes. Va aparte de `sgm.cli` para no pasar el límite de 300 líneas.
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from sgm.agrupacion import cargar_declaracion
from sgm.cli_proceso import _decision
from sgm.proceso.insumos import InsumosResueltos, resolver_insumos
from sgm.proceso.origen_producto import origenes_producto
from sgm.proceso.reglas_cuenta_real import reglas_cuenta_real
from sgm.proceso.reglas_fila import flujos_producto
from sgm.proceso.reglas_saldo import PENDIENTE_CERO, negativos_a_cero, reglas_saldo
from sgm.proceso.reglas_ubicacion import reglas_ubicacion
from sgm.proceso.secciones_entrada import cargar_declaradas
from sgm.proceso.validaciones import validaciones
from sgm.talend_item.arquitectura import cargar_arquitectura
from sgm.talend_item.escritura import escribir_job
from sgm.talend_item.jobs_conciliacion import job_conciliacion
from sgm.talend_item.jobs_diseno import ProductoJob, job_padre, jobs_hijos
from sgm.talend_item.jobs_producto import job_producto
from sgm.talend_item.jobs_totales import job_totales
from sgm.talend_item.periodo import contextos_de_periodo, nodos_periodo


def _descripcion_lookups(arq, resueltos: InsumosResueltos) -> str:
    """Los Excel que `job_producto` usará como lookup, con las columnas que el SAS les usa."""
    partes = []
    for clave in arq.lookups:
        insumo = resueltos.insumos.get(clave)
        if insumo:
            partes.append(f"{insumo.archivo} ({', '.join(insumo.columnas) or 'sin columnas'})")
    return f". Lookups: {'; '.join(partes)}" if partes else ""


def _delimitador(origenes) -> str:
    """El delimitador del archivo principal de los productos (el primero; deberían coincidir)."""
    return next(iter(origenes.por_producto.values())).fuente.delimitador


def _confirmar(arq, texto: str) -> list[str]:
    """Contrasta lo declarado con lo que el SAS demuestra, en las dos direcciones."""
    detectadas = {
        (v.columna.casefold(), v.columna_lookup.casefold()): v for v in validaciones(texto)
    }
    declaradas = {
        (v.columna.casefold(), v.columna_lookup.casefold()): v for v in arq.validaciones
    }
    avisos = [
        f"validación declarada ({v.columna} contra {v.columna_lookup}) no aparece en el SAS"
        for clave, v in declaradas.items()
        if clave not in detectadas
    ]
    avisos += [
        f"validación del SAS ({v.columna} contra {v.columna_lookup}, línea {v.linea}) sin declarar"
        for clave, v in detectadas.items()
        if clave not in declaradas
    ]
    return avisos


def _archivo_homologacion(arq, resueltos: InsumosResueltos, producto: str) -> str:
    """Excel de homologación que el padre pasa a ese producto; vacío si el SAS no lo demuestra."""
    for validacion in arq.validaciones:
        insumo = resueltos.insumos.get(validacion.fuente_de(producto))
        if insumo is not None:
            return insumo.archivo
    return ""


def _flujos(texto: str) -> tuple[list, list[str]]:
    """Terna canónica de R1-04; un programa que no la declara íntegra no emite flujos a medias."""
    try:
        return flujos_producto(texto)
    except ValueError as error:
        return [], [f"R1-04: no se emiten flujos de vacíos y ceros: {error}"]


def _cuenta(texto: str) -> tuple[object | None, list[str]]:
    """Pareja de reglas de R1-06 del SAS real; sin la forma completa no se emite la rama."""
    try:
        return reglas_cuenta_real(texto)
    except ValueError as error:
        return None, [f"R1-06: no se emiten los flujos de cuenta y codex: {error}"]


def _saldo(texto: str, cuenta: object | None) -> tuple[object | None, list[str]]:
    """Regla de saldo negativo de R1-07. Sin la cascada de R1-06 tampoco se emite la rama."""
    avisos = [PENDIENTE_CERO] if negativos_a_cero(texto) else []
    try:
        regla, pendientes = reglas_saldo(texto)
    except ValueError as error:
        return None, avisos + [f"R1-07: no se emiten los saldos negativos: {error}"]
    if cuenta is None:
        return None, avisos + ["R1-07: no se emiten los saldos negativos sin la cascada de R1-06"]
    return regla, avisos + pendientes


def _ubicacion(texto: str) -> tuple[object | None, list[str]]:
    """Regla de ubicación de R1-05. Sin la forma del caso v03 no se emite la rama."""
    try:
        regla = reglas_ubicacion(texto)
    except ValueError as error:
        return None, [f"R1-05: no se emite la ubicación: {error}"]
    return regla, list(regla.pendientes)


def talend_command(
    source: Annotated[Path, typer.Argument(help="Archivo .sas del programa.")],
    out: Annotated[Path, typer.Option("--out", help="Carpeta de salida.")] = Path("out"),
    agrupacion: Annotated[
        Path | None, typer.Option("--agrupacion", help="YAML con marcador de región y productos.")
    ] = None,
    jobs_yaml: Annotated[
        Path | None, typer.Option("--jobs", help="YAML con la arquitectura de Jobs.")
    ] = None,
    diseno: Annotated[
        Path | None, typer.Option("--diseno", help="YAML con las fuentes declaradas.")
    ] = None,
) -> None:
    """Escribe en `<out>/<programa>/talend/process/` los Jobs del diseño."""
    if not source.is_file():
        raise typer.BadParameter(f"no es un archivo: {source}")
    declaracion = cargar_declaracion(_decision(agrupacion, source, "agrupacion"))
    arq = cargar_arquitectura(_decision(jobs_yaml, source, "jobs"))
    texto = source.read_text(encoding="utf-8", errors="replace")
    flujos, pendientes_flujos = _flujos(texto)
    cuenta, pendientes_cuenta = _cuenta(texto)
    saldo, pendientes_saldo = _saldo(texto, cuenta)
    ubic, pendientes_ubic = _ubicacion(texto)
    origenes = origenes_producto(texto, declaracion.productos)
    declaradas = cargar_declaradas(_decision(diseno, source, "diseno"), "fuentes")
    claves = [*arq.lookups, *([arq.periodo.fuente] if arq.periodo else [])]
    resueltos = resolver_insumos(texto, declaradas, claves)
    productos = [
        ProductoJob(
            p,
            o.fuente.ruta_origen if (o := origenes.por_producto.get(p)) else "",
            p,
            _archivo_homologacion(arq, resueltos, p),
        )
        for p in declaracion.productos
    ]
    padre = job_padre(
        arq,
        productos,
        periodo=nodos_periodo(arq, resueltos),
        contextos_periodo=contextos_de_periodo(arq, resueltos),
    )
    variables = tuple(v for _, v in arq.periodo.variables) if arq.periodo else ()
    lookups = _descripcion_lookups(arq, resueltos)
    # R2-02: job_producto escribe totales_origen/salida_<sufijo>.csv cuando job_totales los lee.
    escribe_totales = (
        arq.periodo is not None and bool(arq.archivo_totales) and bool(arq.validaciones)
    )
    producto = None
    if origenes.por_producto:
        pendiente = "validaciones, correcciones y salidas del producto" + lookups
        producto = job_producto(
            arq,
            origenes.columnas_comunes,
            variables,
            pendiente,
            _delimitador(origenes),
            validacion=arq.validaciones[0] if arq.validaciones else None,
            numericas=origenes.numericas_comunes,
            flujos=flujos,
            cuenta=cuenta,
            regla_saldo=saldo,
            ubicacion=ubic,
            escribe_totales=escribe_totales,
        )
    totales = None
    conciliacion = None
    if arq.periodo is not None and arq.archivo_totales and productos:
        sufijos = tuple(p.sufijo for p in productos)
        totales = job_totales(arq, sufijos)
        conciliacion = job_conciliacion(arq, sufijos)
    jobs = [
        padre,
        *jobs_hijos(
            arq,
            variables,
            lookups,
            producto_real=producto,
            totales_real=totales,
            conciliacion_real=conciliacion,
        ),
    ]
    destino = out / source.stem / "talend" / "process"
    escritos = [escribir_job(job, destino) for job in jobs]
    for item, _ in escritos:
        typer.echo(str(item))
    typer.echo(f"{len(escritos)} Jobs escritos.")
    sin_origen = [p.producto for p in productos if not p.ruta_origen]
    if sin_origen:
        typer.echo(f"Pendiente: archivo de origen de {', '.join(sin_origen)}.")
    for aviso in _confirmar(arq, texto):
        typer.echo(f"Pendiente: {aviso}")
    for pendiente in origenes.pendientes:
        typer.echo(f"Pendiente: {pendiente}")
    for pendiente in resueltos.pendientes:
        typer.echo(f"Pendiente: {pendiente}")
    for pendiente in pendientes_flujos:
        typer.echo(f"Pendiente: {pendiente}")
    for pendiente in pendientes_cuenta:
        typer.echo(f"Pendiente: {pendiente}")
    for pendiente in pendientes_saldo:
        typer.echo(f"Pendiente: {pendiente}")
    for pendiente in pendientes_ubic:
        typer.echo(f"Pendiente: {pendiente}")
    if totales is not None and not escribe_totales:
        typer.echo(
            "Pendiente: sin validación de producto job_producto no escribe "
            "totales_origen_<producto>.csv ni totales_salida_<producto>.csv."
        )
    if totales is not None:
        typer.echo(
            "Pendiente: la salida de totales son los saldos validados del manual; L8/05 usa "
            "válidos más rechazados. Decisión pendiente (hito 100d)."
        )
    if producto is not None and len(producto.nodos) > 20:
        typer.echo(
            f"Pendiente: job_producto tiene {len(producto.nodos)} componentes; "
            "el límite de G3 es 20. Dividir pendiente."
        )
    if conciliacion is not None:
        typer.echo("Pendiente: tolerancia_conciliacion vale 0 por omisión; confirmar con negocio.")
        typer.echo(
            "Pendiente: la salida de la conciliación del SAS (válidos más rechazados) no es "
            "la salida de totales que hoy escribe el productor de tools/."
        )
        typer.echo(
            "Pendiente: la conciliación de client_large usa fórmulas por producto distintas "
            "de L8/05 (CONCILIACION_REG y CONCILIACION_SALDOS); aún no se decide cuál aplica."
        )
