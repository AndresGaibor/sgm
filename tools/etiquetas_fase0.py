"""Fase 0: etiquetas por región de un programa SAS (solo biblioteca estándar).

Uso: uv run python tools/etiquetas_fase0.py [programa.sas] [--agrupacion yaml]

1. Divide el programa en regiones. El marcador es la línea `%macro ambiente;`. La primera
   región va desde el inicio del archivo hasta antes del segundo marcador; las siguientes,
   desde cada marcador hasta el siguiente (la última hasta el final).
2. Extrae por región las etiquetas `/* Etiqueta: <texto> */`, normalizadas: minúsculas,
   sin tildes, sin sufijo de producto y sin números finales.
3. Asigna producto a cada región por el sufijo de producto (_CTE, _AHO, _NEQUI, sin
   distinguir mayúsculas) que más aparece en los nombres de tabla de la región. Si ninguno
   aparece, la región es `sin_producto`. Los sufijos salen del YAML de decisiones.
4. Mide y escribe `docs/plan-reescritura/fase0-etiquetas.json` y `.md` (sin fechas).

No modifica `src/` ni `rules/`. No contiene nombres de scripts del cliente.
"""

from __future__ import annotations

import argparse
import difflib
import json
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROGRAMA_DEFECTO = ROOT / "tests" / "fixtures" / "sas" / "client" / "client_large.sas"
AGRUPACION_DEFECTO = ROOT / "decisiones" / "client_large.agrupacion.yaml"
SALIDA_DIR = ROOT / "docs" / "plan-reescritura"

RE_MARCADOR = re.compile(r"^\s*%macro\s+ambiente\s*;", re.IGNORECASE)
RE_ETIQUETA = re.compile(r"/\*\s*Etiqueta:\s*(.*?)\s*\*/", re.IGNORECASE)
RE_NOMBRE_PRODUCTO = re.compile(r"^\s*-\s*nombre:\s*(\S+)\s*$")
RE_SUFIJOS = re.compile(r"sufijos:\s*\[([^\]]*)\]")
SIN_PRODUCTO = "sin_producto"


def cargar_productos(ruta: Path) -> dict[str, list[str]]:
    """Lee `productos` con su `sufijos` del YAML, sin depender de pyyaml."""
    productos: dict[str, list[str]] = {}
    nombre: str | None = None
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        m_nombre = RE_NOMBRE_PRODUCTO.match(linea)
        if m_nombre:
            nombre = m_nombre.group(1)
            continue
        m_suf = RE_SUFIJOS.search(linea)
        if m_suf and nombre:
            sufijos = [s.strip().strip("'\"") for s in m_suf.group(1).split(",") if s.strip()]
            productos[nombre] = [s.upper() for s in sufijos]
            nombre = None
    if not productos:
        raise SystemExit(f"No se encontraron productos en {ruta}")
    return productos


def quitar_tildes(texto: str) -> str:
    descompuesto = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in descompuesto if not unicodedata.combining(c))


def normalizar_etiqueta(texto: str, sufijos: list[str]) -> str:
    """Minúsculas, sin tildes, sin palabras de producto ni números finales."""
    s = quitar_tildes(texto).lower()
    for suf in sufijos:
        s = re.sub(rf"(?<![a-z0-9]){re.escape(suf.lower())}(?![a-z0-9])", " ", s)
    s = re.sub(r"[\s_\-.:;,]*\d+[\s_\-.:;,]*$", " ", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip(" _-.:;,")


def dividir_regiones(lineas: list[str]) -> list[tuple[int, int, list[str]]]:
    """Devuelve (línea_inicio, línea_fin, líneas) por región, con números 1-based."""
    marcas = [i for i, linea in enumerate(lineas) if RE_MARCADOR.match(linea)]
    if len(marcas) < 2:
        raise SystemExit("Se necesitan al menos dos marcadores `%macro ambiente;`")
    cortes = [0] + marcas[1:]
    regiones = []
    for k, ini in enumerate(cortes):
        fin = cortes[k + 1] if k + 1 < len(cortes) else len(lineas)
        regiones.append((ini + 1, fin, lineas[ini:fin]))
    return regiones


def sufijos_producto(productos: dict[str, list[str]]) -> dict[str, str]:
    """Mapa sufijo -> producto."""
    mapa: dict[str, str] = {}
    for producto, sufijos in productos.items():
        for suf in sufijos:
            mapa[suf] = producto
    return mapa


def asignar_producto(texto: str, productos: dict[str, list[str]]) -> tuple[str, dict[str, int]]:
    """Cuenta ocurrencias de nombres de tabla con sufijo de producto y elige el dominante."""
    todos = sorted({s for sufs in productos.values() for s in sufs}, key=len, reverse=True)
    if not todos:
        return SIN_PRODUCTO, {}
    patron = re.compile(
        r"[A-Za-z0-9]+_(" + "|".join(re.escape(s) for s in todos) + r")(?![A-Za-z0-9])",
        re.IGNORECASE,
    )
    conteo: Counter[str] = Counter()
    for m in patron.finditer(texto):
        conteo[m.group(1).upper()] += 1
    if not conteo:
        return SIN_PRODUCTO, {}
    por_producto: Counter[str] = Counter()
    for suf, n in conteo.items():
        for producto, sufs in productos.items():
            if suf in sufs:
                por_producto[producto] += n
    mejor, n_mejor = por_producto.most_common(1)[0]
    if sum(1 for n in por_producto.values() if n == n_mejor) > 1:
        return "empate", dict(por_producto)
    return mejor, dict(por_producto)


def jaccard(a: set[str], b: set[str]) -> float:
    union = a | b
    return round(len(a & b) / len(union), 4) if union else 0.0


def medir(ruta_sas: Path, ruta_yaml: Path) -> dict:
    productos = cargar_productos(ruta_yaml)
    lineas = ruta_sas.read_text(encoding="utf-8").splitlines()
    # El archivo empieza con U+200B en la línea 1; no afecta a los marcadores.
    lineas = [linea.replace("​", "") for linea in lineas]
    todos_sufijos = [s for sufs in productos.values() for s in sufs]

    regiones = []
    for n, (ini, fin, bloque) in enumerate(dividir_regiones(lineas), start=1):
        texto = "\n".join(bloque)
        crudas = [m.group(1) for m in RE_ETIQUETA.finditer(texto)]
        normalizadas = [normalizar_etiqueta(c, todos_sufijos) for c in crudas]
        producto, conteo = asignar_producto(texto, productos)
        regiones.append(
            {
                "region": n,
                "linea_inicio": ini,
                "linea_fin": fin,
                "producto": producto,
                "conteo_sufijos": dict(sorted(conteo.items())),
                "etiquetas": len(normalizadas),
                "secuencia": normalizadas,
            }
        )

    conjuntos: dict[str, set[str]] = {p: set() for p in productos}
    conjuntos[SIN_PRODUCTO] = set()
    for r in regiones:
        destino = r["producto"] if r["producto"] in productos else SIN_PRODUCTO
        conjuntos.setdefault(destino, set()).update(r["secuencia"])

    todas = {e for r in regiones for e in r["secuencia"]}
    prods = sorted(productos)
    pares = {}
    for i, a in enumerate(prods):
        for b in prods[i + 1 :]:
            pares[f"{a}-{b}"] = jaccard(conjuntos[a], conjuntos[b])

    en_todos = sorted(set.intersection(*(conjuntos[p] for p in prods))) if prods else []

    mayor = {}
    for p in prods:
        candidatas = [r for r in regiones if r["producto"] == p]
        if candidatas:
            r = max(candidatas, key=lambda x: (x["etiquetas"], -x["region"]))
            mayor[p] = {"region": r["region"], "secuencia": r["secuencia"]}

    similitud_secuencias = {}
    nombres = sorted(mayor)
    for i, a in enumerate(nombres):
        for b in nombres[i + 1 :]:
            sa, sb = mayor[a]["secuencia"], mayor[b]["secuencia"]
            sm = difflib.SequenceMatcher(a=sa, b=sb, autojunk=False)
            similitud_secuencias[f"{a}-{b}"] = round(sm.ratio(), 4)

    resumen_productos = {}
    for p in [*prods, SIN_PRODUCTO]:
        rs = [r for r in regiones if r["producto"] == p]
        resumen_productos[p] = {
            "regiones": len(rs),
            "etiquetas": sum(r["etiquetas"] for r in rs),
            "etiquetas_distintas": len(conjuntos.get(p, set())),
        }
    for otro in ("empate",):
        rs = [r for r in regiones if r["producto"] == otro]
        if rs:
            resumen_productos[otro] = {
                "regiones": len(rs),
                "etiquetas": sum(r["etiquetas"] for r in rs),
                "etiquetas_distintas": 0,
            }

    return {
        "programa": ruta_sas.name,
        "agrupacion": ruta_yaml.name,
        "regiones_total": len(regiones),
        "etiquetas_total": sum(r["etiquetas"] for r in regiones),
        "etiquetas_distintas_total": len(todas),
        "productos": resumen_productos,
        "jaccard_entre_productos": pares,
        "etiquetas_en_todos_los_productos": en_todos,
        "etiquetas_en_todos_los_productos_n": len(en_todos),
        "region_mas_grande_por_producto": mayor,
        "similitud_secuencias_region_mayor": similitud_secuencias,
        "regiones": regiones,
    }


def tabla(encabezado: list[str], filas: list[list]) -> list[str]:
    lineas = ["| " + " | ".join(encabezado) + " |", "|" + "---|" * len(encabezado)]
    lineas += ["| " + " | ".join(str(c) for c in f) + " |" for f in filas]
    return lineas


def escribir_md(datos: dict, ruta: Path, conclusion: list[str]) -> None:
    md = [
        "# Fase 0: etiquetas por región de client_large.sas",
        "",
        f"Programa: `{datos['programa']}`. Agrupación: `{datos['agrupacion']}`.",
        "Generado por `tools/etiquetas_fase0.py`. Las cifras salen de ese script.",
        "",
        "## Resumen",
        "",
        f"- Regiones: {datos['regiones_total']}.",
        f"- Etiquetas totales: {datos['etiquetas_total']}.",
        f"- Etiquetas normalizadas distintas: {datos['etiquetas_distintas_total']}.",
        "- Etiquetas presentes en los tres productos: "
        f"{datos['etiquetas_en_todos_los_productos_n']}.",
        "",
        "## Regiones",
        "",
        *tabla(
            ["Región", "Líneas", "Producto", "Sufijos contados", "Etiquetas"],
            [
                [
                    r["region"],
                    f"{r['linea_inicio']}-{r['linea_fin']}",
                    r["producto"],
                    ", ".join(f"{k}={v}" for k, v in r["conteo_sufijos"].items()) or "-",
                    r["etiquetas"],
                ]
                for r in datos["regiones"]
            ],
        ),
        "",
        "## Productos",
        "",
        *tabla(
            ["Producto", "Regiones", "Etiquetas", "Etiquetas distintas"],
            [
                [p, v["regiones"], v["etiquetas"], v["etiquetas_distintas"]]
                for p, v in datos["productos"].items()
            ],
        ),
        "",
        "## Jaccard de etiquetas entre productos",
        "",
        *tabla(["Par", "Jaccard"], [[k, v] for k, v in datos["jaccard_entre_productos"].items()]),
        "",
        "## Etiquetas presentes en los tres productos",
        "",
        f"Total: {datos['etiquetas_en_todos_los_productos_n']}.",
        "",
    ]
    for e in datos["etiquetas_en_todos_los_productos"]:
        md.append(f"- {e}")
    md += [
        "",
        "## Secuencia de la región más grande por producto",
        "",
    ]
    for p, v in datos["region_mas_grande_por_producto"].items():
        md += [
            f"### {p} (región {v['region']}, {len(v['secuencia'])} etiquetas)",
            "",
        ]
        md += [f"{i}. {e}" for i, e in enumerate(v["secuencia"], start=1)]
        md.append("")
    md += [
        "## Similitud de secuencias entre regiones mayores (SequenceMatcher)",
        "",
        *tabla(
            ["Par", "Ratio"],
            [[k, v] for k, v in datos["similitud_secuencias_region_mayor"].items()],
        ),
        "",
        "## Conclusión",
        "",
        *conclusion,
        "",
    ]
    ruta.write_text("\n".join(md), encoding="utf-8")


def conclusion(datos: dict) -> list[str]:
    """Texto de conclusión a partir de las cifras medidas (sin juicio adicional)."""
    j = datos["jaccard_entre_productos"]
    sim = datos["similitud_secuencias_region_mayor"]
    comunes = datos["etiquetas_en_todos_los_productos_n"]
    distintas = datos["etiquetas_distintas_total"]
    jmax = max(j.values())
    smax = max(sim.values())
    vocabulario = (
        "Hay vocabulario compartido: la mayor coincidencia es "
        f"{max(j, key=j.get)} (Jaccard {jmax}), y {comunes} de {distintas} etiquetas "
        "distintas aparecen en los tres productos."
        if jmax >= 0.3
        else "El vocabulario apenas se comparte: el Jaccard máximo es "
        f"{jmax} y solo {comunes} de {distintas} etiquetas distintas aparecen en los tres."
    )
    orden = (
        f"La secuencia de las regiones mayores casi no coincide (similitud máxima {smax}), "
        "así que no hay un orden parecido entre productos."
        if smax < 0.5
        else f"La secuencia de las regiones mayores coincide en parte (similitud máxima {smax})."
    )
    return [
        "Pregunta: ¿las regiones de un mismo producto son etapas consecutivas de un proceso "
        "(vocabulario común y secuencia parecida) o piezas sin relación?",
        "",
        vocabulario,
        "",
        orden,
        "",
        "Lectura honesta: las cifras no demuestran que las regiones sean etapas de un proceso. "
        "Las etiquetas compartidas son genéricas (p. ej. «organizar campos», «sabana final», "
        "«campo apellido»), lo que describe operaciones repetidas y no una secuencia. Además, "
        "las regiones grandes mezclan tablas de varios productos, así que la asignación por "
        "sufijo no separa limpiamente los procesos. Con estos datos la pregunta queda sin "
        "respuesta concluyente: hace falta leer el orden de ejecución de cada región.",
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("programa", nargs="?", type=Path, default=PROGRAMA_DEFECTO)
    parser.add_argument("--agrupacion", type=Path, default=AGRUPACION_DEFECTO)
    parser.add_argument("--salida", type=Path, default=SALIDA_DIR)
    args = parser.parse_args()

    datos = medir(args.programa, args.agrupacion)
    args.salida.mkdir(parents=True, exist_ok=True)
    json_ruta = args.salida / "fase0-etiquetas.json"
    json_ruta.write_text(
        json.dumps(datos, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    escribir_md(datos, args.salida / "fase0-etiquetas.md", conclusion(datos))
    print(
        f"regiones={datos['regiones_total']} etiquetas={datos['etiquetas_total']} "
        f"distintas={datos['etiquetas_distintas_total']} "
        f"jaccard={datos['jaccard_entre_productos']}",
        file=sys.stdout,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
