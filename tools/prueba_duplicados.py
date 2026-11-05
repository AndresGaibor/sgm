"""Hito 92 / R1-12: la rama de duplicados (`NODUPKEY`) se ejecuta en Studio con datos.

Se emiten dos Jobs con `flujos_duplicados.job_duplicados`, uno por conjunto de datos porque el
esquema de cada uno es distinto:

* `dup_vectores`: 14 filas de `duplicados_datos.VECTORES` (columnas `CLAVE` y `SALDO`).
* `dup_aho_unicos`: `origen_aho.csv` del caso `L8/totales/01`, con cabecera de 23 columnas y
  `;` como separador. La regla es la de `AHO_UNICOS`, leída de `programa.sas`.

Cada Job se renombra con el sufijo nuevo, se copia al proyecto de Studio, se compila, se exporta
como Build Job y se ejecuta con sus parámetros. Después se compara:

* Vectores: `informe_vectores` (llave, saldo del sobreviviente y número de repetidas).
* AHO: `AHO_UNICOS_<sufijo>.csv` contra `esperado/AHO_UNICOS.csv` (23 columnas, multiconjunto) y
  contra el oráculo `clasificar`, que es el mismo cálculo en Python, con la primera fila de cada
  llave; y el número de repetidas, 7 = 47 - 40.

Los Jobs de prueba se borran del proyecto al terminar, aunque falle. Código de salida 0 solo si
todo coincide.

Uso:
    uv run python tools/prueba_duplicados.py --proyecto <carpeta> [--sufijo v92b] [--trabajo DIR]
        [--java-bin DIR] [--m2 DIR]
"""

from __future__ import annotations

import argparse
import csv
import shutil
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "tools"))

from duplicados_datos import (  # noqa: E402
    caso_esperado,
    caso_origen,
    clasificar,
    informe_vectores,
    leer_csv,
    llave,
    recorte,
    vector_csv,
)
from mcp_cliente import MCP, ErrorValidacion  # noqa: E402
from validar_en_studio import (  # noqa: E402
    borrar_destino_build,
    construir,
    crear_destino_build,
    ejecutar,
    exportar,
    renombrar,
)

COLUMNAS_AHO = (
    "ANIO_PROCESO,MES_PROCESO,CODIGO_OFICINA,RELACION,CODIGO_SUCURSAL,TIPO_CTA,NRO_CTA,"
    "LLAVE_NOMBRE,TIPO_DOC,NRO_DOC,GMF,VAL_CRED_MES,NRO_CRED_MES,PROM_CRED_MES,MED_CRED_MES,"
    "VAL_DEB_MES,NRO_DEB_MES,PROM_DEB_MES,MED_SALDO_CTA,PROM_SALDO_CTA,MAX_SALDO_CTA,"
    "MIN_SALDO_CTA,FIN_SALDO_CTA"
).split(",")
LLAVES_AHO = ("RELACION", "TIPO_CTA", "NRO_CTA", "TIPO_DOC", "NRO_DOC")
NUM_REPETIDAS_AHO = 7  # 47 filas de origen menos 40 llaves únicas (CONTROL_DUPLICADOS_AHO)


def _regla(salida: str, entrada: str, llaves: tuple[str, ...]):
    from sgm.proceso.reglas_duplicados import ReglaDuplicados

    return ReglaDuplicados(entrada=entrada, salida=salida, llaves=llaves, equals=True)


def emitir(nombre: str, regla, columnas: list[str], carpeta: Path) -> Path:
    """Escribe el `.item` del Job de la regla en `carpeta` y devuelve su ruta."""
    from sgm.talend_item.escritura import escribir_job
    from sgm.talend_item.flujos_duplicados import job_duplicados
    from sgm.talend_item.modelo import Columna

    cols = [Columna(c) for c in columnas]
    delimitador = "," if nombre == "dup_vectores" else ";"
    job = job_duplicados(regla, cols, delimitador)
    job.nombre = nombre
    item, _ = escribir_job(job, carpeta)
    return item


def _proyecto_tecnico(proyecto: Path) -> str:
    import re

    archivo = proyecto / "talend.project"
    if archivo.is_file():
        coincide = re.search(
            r'technicalLabel="([^"]+)"', archivo.read_text(encoding="utf-8", errors="replace")
        )
        if coincide:
            return coincide.group(1)
    return proyecto.name


def _csv_con_cabecera(origen: Path, destino: Path, columnas: list[str]) -> Path:
    """Copia el `;` del caso con la cabecera de 23 nombres, sin tocar los valores."""
    destino.parent.mkdir(parents=True, exist_ok=True)
    with origen.open(encoding="utf-8", newline="") as entrada, destino.open(
        "w", encoding="utf-8", newline=""
    ) as salida:
        escritor = csv.writer(salida, delimiter=";", lineterminator="\n")
        escritor.writerow(columnas)
        for fila in csv.reader(entrada, delimiter=";"):
            escritor.writerow(fila)
    return destino


def _validar_job(
    cliente: MCP,
    proyecto: Path,
    nombre_base: str,
    regla,
    columnas: list[str],
    entrada: Path,
    trabajo: Path,
    sufijo: str,
    java_bin: Path | None,
    m2: Path | None,
    copiados: list[Path],
) -> dict:
    """Emite, renombra, compila, exporta y ejecuta un Job; devuelve código y CSV de salida."""
    carpeta = trabajo / f"emit_{nombre_base}"
    carpeta.mkdir(parents=True, exist_ok=True)
    emitir(nombre_base, regla, columnas, carpeta)
    nombre = renombrar(carpeta, sufijo, _proyecto_tecnico(proyecto))[nombre_base]
    proceso = proyecto / "process"
    for extension in (".item", ".properties"):
        origen = carpeta / f"{nombre}_0.1{extension}"
        if origen.is_file():
            destino = proceso / origen.name
            shutil.copyfile(origen, destino)
            copiados.append(destino)
    cliente.llamar("talend_bridge_refresh_workspace")
    construir(cliente, [nombre])
    exportado = crear_destino_build()
    try:
        lanzador = exportar(cliente, nombre, exportado, m2)
        salida = trabajo / f"salida_{nombre}"
        salida.mkdir(parents=True, exist_ok=True)
        params = [
            f"ruta_origen={entrada.as_posix()}",
            f"ruta_resultados={salida.as_posix()}/",
            f"sufijo={sufijo}",
        ]
        corrida = ejecutar(lanzador, "Default", params, java_bin)
        print(f"Comando {nombre}: {corrida['comando']}")
        print(f"Código de salida {nombre}: {corrida['exitCode']}")
        print(f"stdout {nombre}: {corrida['stdout'][-600:]}")
        return {"corrida": corrida, "salida": salida, "nombre": nombre, "regla": regla}
    finally:
        borrar_destino_build(exportado)


def _unicos_y_repetidos(salida: Path, regla, sufijo: str) -> tuple[list[dict], list[dict]]:
    base = f"{regla.salida}"
    unicos = leer_csv(salida / f"{base}_{sufijo}.csv")
    repetidos = leer_csv(salida / f"{base}_DUPLICADOS_{sufijo}.csv")
    return unicos, repetidos


def validar(
    proyecto: Path, trabajo: Path, sufijo: str, java_bin: Path | None, m2: Path | None
) -> int:
    trabajo.mkdir(parents=True, exist_ok=True)
    cliente = MCP()
    copiados: list[Path] = []
    errores: list[str] = []
    try:
        # Vectores propios: 20 filas, columnas CLAVE y SALDO.
        entrada_vec = vector_csv(trabajo / "entradas" / "VECTORES.csv")
        regla_vec = _regla("VECTORES", "VECTORES_ENTRADA", ("CLAVE",))
        r_vec = _validar_job(
            cliente, proyecto, "dup_vectores", regla_vec, ["CLAVE", "SALDO"], entrada_vec,
            trabajo, sufijo, java_bin, m2, copiados,
        )
        if r_vec["corrida"]["exitCode"] != 0:
            errores.append(f"dup_vectores salió con {r_vec['corrida']['exitCode']}")
        else:
            unicos, repetidos = _unicos_y_repetidos(r_vec["salida"], regla_vec, sufijo)
            fallos = informe_vectores(unicos, repetidos)
            errores += [f"vectores: {f}" for f in fallos]
            print(f"Vectores: {len(unicos)} únicas, {len(repetidos)} repetidas; "
                  f"{'OK' if not fallos else 'DIFERENCIA'}")

        # AHO del caso L8/01: cabecera de 23 columnas, `;` como separador.
        entrada_aho = _csv_con_cabecera(
            caso_origen(), trabajo / "entradas" / "origen_aho_cabecera.csv", COLUMNAS_AHO
        )
        regla_aho = _regla("AHO_UNICOS", "AHO_ORDENADO", LLAVES_AHO)
        r_aho = _validar_job(
            cliente, proyecto, "dup_aho_unicos", regla_aho, COLUMNAS_AHO, entrada_aho,
            trabajo, sufijo, java_bin, m2, copiados,
        )
        if r_aho["corrida"]["exitCode"] != 0:
            errores.append(f"dup_aho_unicos salió con {r_aho['corrida']['exitCode']}")
        else:
            unicos, repetidos = _unicos_y_repetidos(r_aho["salida"], regla_aho, sufijo)
            origen = leer_csv(entrada_aho, ";")
            oraculo = clasificar(origen, LLAVES_AHO)
            esperado = caso_esperado("AHO_UNICOS")
            if len(unicos) != len(esperado):
                errores.append(f"AHO únicas: esperadas {len(esperado)}, obtenidas {len(unicos)}")
            if len(repetidos) != NUM_REPETIDAS_AHO:
                errores.append(
                    f"AHO repetidas: esperadas {NUM_REPETIDAS_AHO}, obtenidas {len(repetidos)}"
                )
            obtenido = sorted(tuple(recorte(v) for v in f.values()) for f in unicos)
            ref = sorted(tuple(recorte(f[c]) for c in COLUMNAS_AHO) for f in esperado)
            if obtenido != ref:
                errores.append("AHO únicas: multiconjunto distinto de esperado/AHO_UNICOS.csv")
            if [llave(f, LLAVES_AHO) for f in unicos] != [
                llave(f, LLAVES_AHO) for f in oraculo.unicas
            ]:
                errores.append("AHO únicas: el orden de llaves no coincide con el oráculo")
            print(f"AHO: {len(unicos)} únicas (esperado {len(esperado)}), "
                  f"{len(repetidos)} repetidas (esperado {NUM_REPETIDAS_AHO})")
    finally:
        for archivo in copiados:
            archivo.unlink(missing_ok=True)
        try:
            cliente.llamar("talend_bridge_refresh_workspace")
        except ErrorValidacion:
            pass
        print(f"Limpieza: {len(copiados)} archivos borrados del proyecto")
    if errores:
        print("RESULTADO: DIFERENCIA")
        for e in errores:
            print(f"  - {e}")
        return 1
    print("RESULTADO: vectores y AHO coinciden con el oráculo y con esperado/AHO_UNICOS.csv")
    return 0


def main(argv: list[str] | None = None) -> int:
    for flujo in (sys.stdout, sys.stderr):
        if hasattr(flujo, "reconfigure"):
            flujo.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--proyecto", type=Path, required=True)
    parser.add_argument("--trabajo", type=Path)
    parser.add_argument("--sufijo", required=True, help="sufijo nuevo del Job (v92b, v92c...)")
    parser.add_argument("--java-bin", type=Path)
    parser.add_argument("--m2", type=Path)
    args = parser.parse_args(argv)
    if not (args.proyecto / "talend.project").is_file():
        print(f"error: no es un proyecto Talend: {args.proyecto}", file=sys.stderr)
        return 2
    trabajo = args.trabajo or Path(tempfile.mkdtemp(prefix="prueba-duplicados-"))
    print(f"Proyecto: {args.proyecto}\nSufijo: {args.sufijo}\nTrabajo: {trabajo}")
    try:
        return validar(args.proyecto, trabajo, args.sufijo, args.java_bin, args.m2)
    except ErrorValidacion as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
