"""Inventario de funciones SAS implementadas por cada motor del migrador."""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

import yaml

_TOOLS = Path(__file__).resolve().parent
if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))


def _tabla_talend() -> dict[str, object]:
    from sgm.expressions.talend_tabla import _FUNCTIONS

    return _FUNCTIONS


def _tabla_oraculo() -> dict[str, object]:
    """Retorna las llaves originales; no atribuye ayudantes a funciones SAS sin equivalencia."""
    from corpus_semantica_funciones import FUNCIONES

    return FUNCIONES


def _tabla_interprete() -> dict[str, object]:
    try:
        from sgm.migrar.interprete_funciones import FUNCIONES
    except ModuleNotFoundError as error:
        if error.name != "sgm.migrar.interprete_funciones":
            raise
        return {}
    return FUNCIONES


def _nombre_sas(nombre: str) -> str:
    """Normaliza el nombre documental; conserva CALL y el nombre de su rutina."""
    partes = nombre.strip().lower().split()
    if not partes:
        return ""
    if partes[0] == "call" and len(partes) > 1:
        return " ".join(partes[:2])
    return partes[0]


def _catalogo(repo: Path) -> dict[str, dict[str, str | None]]:
    """Indexa los dos catálogos de funciones sin ocultar entradas contradictorias."""
    directorio = repo / "rules" / "sas" / "catalogo"
    resultado: dict[str, dict[str, str | None]] = {}
    for nombre_archivo in ("funciones-usadas.yaml", "funciones-guia.yaml"):
        ruta = directorio / nombre_archivo
        if not ruta.is_file():
            continue
        documento = yaml.safe_load(ruta.read_text(encoding="utf-8")) or {}
        for entrada in documento.get("entries", []):
            nombre = _nombre_sas(str(entrada.get("nombre", "")))
            if not nombre:
                continue
            valor = {
                "estado": entrada.get("estado"),
                "fuente": entrada.get("fuente"),
            }
            anterior = resultado.get(nombre)
            if anterior is not None and anterior != valor:
                raise ValueError(f"catálogos de funciones en conflicto para {nombre!r}")
            resultado[nombre] = valor
    return resultado


def _funciones_de_reglas(repo: Path) -> set[str]:
    """Lee el nombre SAS de las reglas de función, no sus alias de archivo."""
    resultado = set()
    for ruta in sorted((repo / "rules" / "sas" / "functions").glob("*.yaml")):
        documento = yaml.safe_load(ruta.read_text(encoding="utf-8")) or {}
        nombre = documento.get("sas")
        if isinstance(nombre, str) and nombre.strip():
            resultado.add(nombre.strip().lower())
    return resultado


def _funciones_del_plan(repo: Path) -> tuple[set[str], set[str]]:
    """Lee nombres y familias de la tabla viva 5.7 del plan maestro."""
    ruta = repo / "docs" / "plan-reescritura" / "plan-migrador-general.md"
    if not ruta.is_file():
        return set(), set()
    contenido = ruta.read_text(encoding="utf-8")
    inicio = re.search(
        r"(?m)^### 5\.7 Funciones, formatos e informats(?: \(tabla viva\))?",
        contenido,
    )
    if inicio is None:
        return set(), set()
    fin = re.search(r"(?m)^## 6\.", contenido[inicio.end() :])
    seccion = (
        contenido[inicio.end() : inicio.end() + fin.start()]
        if fin
        else contenido[inicio.end() :]
    )
    tabla = seccion.split("Cada función:", 1)[0]
    if "| Familia |" not in tabla:
        return set(), set()
    tabla = tabla[tabla.index("| Familia |") :]
    funciones: set[str] = set()
    familias: set[str] = set()
    for token in re.findall(r"`([^`]+)`", tabla):
        for nombre in token.strip().lower().split("/"):
            nombre = nombre.strip()
            if not nombre:
                continue
            if re.fullmatch(r"[a-z_][a-z0-9_]*\*?", nombre) is None:
                continue
            if nombre.endswith("*"):
                familias.add(nombre[:-1])
            else:
                funciones.add(nombre)
    return funciones, familias


def _normalizar_tabla(tabla: dict[str, object]) -> dict[str, object]:
    """Hace insensibles a mayúsculas las llaves de las tablas de cada motor."""
    return {
        str(nombre).strip().lower(): valor
        for nombre, valor in tabla.items()
        if str(nombre).strip()
    }


def inventario(
    repo: Path,
    talend: dict[str, object] | None = None,
    oraculo: dict[str, object] | None = None,
    interprete: dict[str, object] | None = None,
) -> dict[str, dict]:
    """Devuelve por función SAS su cobertura en motores, vectores y catálogo."""
    raiz = Path(repo)
    talend = _tabla_talend() if talend is None else talend
    oraculo = _tabla_oraculo() if oraculo is None else oraculo
    interprete = _tabla_interprete() if interprete is None else interprete
    talend_nombres = _normalizar_tabla(talend)
    oraculo_nombres = _normalizar_tabla(oraculo)
    interprete_nombres = _normalizar_tabla(interprete)

    from corpus_semantica import cargar_vectores

    ruta_vectores = raiz / "tests" / "corpus" / "semantica" / "vectores.yaml"
    cantidad_vectores = Counter(
        str(vector["funcion"]).strip().lower()
        for vector in cargar_vectores(ruta_vectores)
        if vector.get("funcion")
    )
    catalogo = _catalogo(raiz)
    reglas = _funciones_de_reglas(raiz)
    plan, familias = _funciones_del_plan(raiz)
    motores = set(talend_nombres) | set(oraculo_nombres) | set(interprete_nombres)
    candidatos = (
        set(cantidad_vectores)
        | set(catalogo)
        | reglas
        | motores
        | plan
    )
    nombres = candidatos | {
        nombre
        for nombre in plan | motores
        if any(nombre.startswith(prefijo) for prefijo in familias)
    }

    resultado = {}
    for nombre in sorted(nombres):
        entrada = catalogo.get(nombre, {})
        resultado[nombre] = {
            "talend": nombre in talend_nombres,
            "oraculo": nombre in oraculo_nombres,
            "interprete": nombre in interprete_nombres,
            "vectores": cantidad_vectores.get(nombre, 0),
            "catalogo": entrada.get("estado"),
            "pagina": entrada.get("fuente"),
        }
    return resultado


def resumen(
    inv: dict[str, dict], vectores_ejecutados: dict[str, int] | None = None
) -> dict:
    """Cuenta cobertura; el conteo del intérprete requiere ejecuciones explícitas verificadas."""
    ejecutados = vectores_ejecutados or {}
    total_ejecutados = 0
    vistos: set[str] = set()
    for funcion, cantidad in ejecutados.items():
        nombre = funcion.strip().lower()
        if nombre in vistos:
            raise ValueError(f"conteo duplicado tras normalizar el nombre {nombre!r}")
        vistos.add(nombre)
        entrada = inv.get(nombre)
        disponibles = entrada.get("vectores", 0) if entrada is not None else 0
        if not isinstance(cantidad, int) or isinstance(cantidad, bool):
            raise TypeError(f"el conteo de vectores ejecutados debe ser entero: {funcion!r}")
        if entrada is None or not entrada["interprete"]:
            raise ValueError(f"no hay función del intérprete registrada para {nombre!r}")
        if cantidad < 0 or cantidad > disponibles:
            raise ValueError(
                f"conteo de vectores ejecutados fuera de rango para {nombre!r}: "
                f"{cantidad} de {disponibles}"
            )
        total_ejecutados += cantidad
    return {
        "funciones": len(inv),
        "en_talend": sum(bool(item["talend"]) for item in inv.values()),
        "en_oraculo": sum(bool(item["oraculo"]) for item in inv.values()),
        "en_interprete": sum(bool(item["interprete"]) for item in inv.values()),
        "con_vectores": sum(item["vectores"] > 0 for item in inv.values()),
        "vectores_en_interprete": total_ejecutados,
        "sin_catalogo": sorted(nombre for nombre, item in inv.items() if item["catalogo"] is None),
    }


def _sin_catalogo_plan(repo: Path, funciones: dict[str, dict]) -> list[str]:
    """Devuelve solo las funciones nombradas por 5.7 que no tienen ficha de catálogo."""
    plan, familias = _funciones_del_plan(repo)
    motores = {
        nombre
        for nombre, item in funciones.items()
        if item["talend"] or item["oraculo"] or item["interprete"]
    }
    nombres = plan | {
        nombre
        for nombre in plan | motores
        if any(nombre.startswith(prefijo) for prefijo in familias)
    }
    return sorted(
        nombre
        for nombre in nombres
        if funciones.get(nombre, {}).get("catalogo") is None
    )


def main() -> None:
    """Escribe el inventario de la copia actual sin versionar el resultado."""
    repo = Path(__file__).resolve().parents[1]
    funciones = inventario(repo)
    datos = {
        "resumen": resumen(funciones),
        "inventario": funciones,
        "sin_catalogo_plan": _sin_catalogo_plan(repo, funciones),
    }
    salida = repo / "out" / "linea_base_funciones.json"
    salida.parent.mkdir(parents=True, exist_ok=True)
    salida.write_text(
        json.dumps(datos, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    salida_resumen = {
        "resumen": datos["resumen"],
        "sin_catalogo_plan": datos["sin_catalogo_plan"],
    }
    print(json.dumps(salida_resumen, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
