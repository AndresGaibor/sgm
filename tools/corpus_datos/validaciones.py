"""Generador de entradas de los casos L8 de validaciones: datos ficticios y semilla fija.

Uso (desde la raíz del repositorio):

    uv run python tools/corpus_datos/validaciones.py

Escribe `tests/corpus/L8/validaciones/<caso>/entradas/`: un CSV de 23 columnas por producto (sin
cabecera, separado por `;`), CSV auxiliares de ubicación y los xlsx de homologación, país y DANE.
Imprime los conteos de anomalías por producto para copiarlos a `caso.yaml`. Es reproducible: dos
ejecuciones dan los mismos bytes en los CSV y las mismas celdas en los xlsx.

Cada fila anómala tiene un único defecto, así que los conteos se suman sin solaparse.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
_CARPETA = Path(__file__).resolve().parent
sys.path.insert(0, str(_CARPETA))
sys.path.insert(0, str(REPO / "tools"))

from simular_insumos import escribir_xlsx  # noqa: E402
from validaciones_filas import (  # noqa: E402
    PRODUCTOS,
    fila_detalle,
    fila_ubicacion,
    secuencia,
)

CORPUS_L8 = REPO / "tests" / "corpus" / "L8" / "validaciones"

# Excel de homologación, país y DANE: nombre, cabecera (fila 1) y filas.
EXCEL = {
    "homol_tipo_doc": (
        "Homologacion_tpo_dto.xlsx",
        ["CNAME"],
        [["TD01"], ["TD02"], ["TD03"], ["TD04"]],
    ),
    "homol_nequi": (
        "Homologacion_tpo_dto_Nequi.xlsx",
        ["CNAME"],
        [["TD01"], ["TD02"], ["TD03"], ["TD05"]],
    ),
    "pais": (
        "Cod_pais.xlsx",
        ["Codigo_Pais", "Nombre Pais"],
        [["900", "NACION FICTICIA"], ["902", "PAIS FICTICIO DOS"], ["903", "PAIS FICTICIO TRES"]],
    ),
    "dane": ("CODIGOS_DANE.xlsx", ["CODIGO_DANE"], [["99001"], ["99002"], ["99003"]]),
}

# Conteos por producto: la clave `validos` va al final. Cada caso dice qué Excel usa.
CASOS: dict[str, dict] = {
    "v01_tipo_doc": {
        "productos": {
            "CTE": {"tipo_doc_invalido": 7, "validos": 88},
            "AHO": {"tipo_doc_invalido": 5, "validos": 60},
        },
        "excel": ["homol_tipo_doc"],
    },
    "v02_vacios_ceros": {
        "productos": {
            "CTE": {
                "tit_cot_nro_doc_vacio": 3,
                "tit_cot_nro_doc_cero": 2,
                "fa_nro_doc_vacio": 1,
                "fa_nro_doc_cero": 4,
                "validos": 85,
            },
            "AHO": {
                "tit_cot_nro_doc_vacio": 2,
                "tit_cot_nro_doc_cero": 1,
                "fa_nro_doc_vacio": 2,
                "validos": 70,
            },
        },
        "excel": [],
    },
    "v03_pais_dane": {
        "ubicacion": {
            "CTE": {
                "pais_no_homologado": 2,
                "dane_no_homologado": 3,
                "ubicacion_extranjera_con_codigo": 1,
                "direccion_invalida": 2,
                "validos": 80,
            },
            "AHO": {
                "pais_no_homologado": 1,
                "dane_no_homologado": 2,
                "ubicacion_extranjera_con_codigo": 1,
                "direccion_invalida": 1,
                "validos": 55,
            },
        },
        "excel": ["pais", "dane"],
    },
    "v04_tipo_cta_gmf": {
        "productos": {
            "CTE": {
                "tipo_cta_invalido": 4,
                "gmf_invalido": 2,
                "gmf_fuera_rango": 3,
                "validos": 81,
            },
            "AHO": {
                "tipo_cta_invalido": 6,
                "gmf_invalido": 1,
                "gmf_fuera_rango": 2,
                "validos": 56,
            },
        },
        "excel": [],
    },
    "v05_codex_saldos": {
        "productos": {
            "CTE": {"codex_invalido": 3, "saldo_negativo": 4, "validos": 83},
            "AHO": {"codex_invalido": 2, "saldo_negativo": 5, "validos": 58},
        },
        "excel": [],
    },
    "v06_normalizacion": {
        "productos": {
            "CTE": {
                "nombre_minusculas": 4,
                "nombre_con_enie": 3,
                "nombre_con_tildes": 2,
                "nombre_con_espacios": 5,
                "valor_con_espacios": 3,
                "validos": 77,
            },
            "AHO": {
                "nombre_minusculas": 2,
                "nombre_con_enie": 2,
                "nombre_con_tildes": 1,
                "nombre_con_espacios": 3,
                "valor_con_espacios": 2,
                "validos": 60,
            },
        },
        "excel": [],
    },
    "v07_cadena_completa": {
        "productos": {
            "CTE": {
                "tipo_doc_invalido": 6,
                "tit_cot_nro_doc_vacio": 2,
                "fa_nro_doc_cero": 3,
                "tipo_cta_invalido": 4,
                "validos": 75,
            },
            "AHO": {
                "tipo_doc_invalido": 3,
                "tit_cot_nro_doc_vacio": 1,
                "fa_nro_doc_cero": 2,
                "tipo_cta_invalido": 2,
                "validos": 50,
            },
        },
        "excel": ["homol_tipo_doc"],
    },
    "v08_nequi_cadena": {
        "productos": {
            "NEQUI": {
                "tipo_doc_invalido": 5,
                "tit_cot_nro_doc_vacio": 2,
                "fa_nro_doc_cero": 3,
                "tipo_cta_invalido_no_validado": 2,
                "validos": 70,
            },
        },
        "excel": ["homol_nequi"],
    },
}


def conteos_caso(caso: str) -> dict[str, dict[str, int]]:
    """Conteos de anomalías por producto en minúsculas (lo que va a `caso.yaml`)."""
    spec = CASOS[caso]
    fuente = spec.get("ubicacion", spec.get("productos", {}))
    return {nombre.lower(): dict(conteo) for nombre, conteo in fuente.items()}


def _texto_csv(filas: list[list[str]]) -> bytes:
    """Filas separadas por `;`, sin cabecera, con saltos `\\n` y codificación UTF-8."""
    return ("\n".join(";".join(fila) for fila in filas) + "\n").encode("utf-8")


def escribir_caso(caso: str, carpeta: Path) -> list[Path]:
    """Escribe las entradas de `caso` en `carpeta` y devuelve las rutas escritas."""
    spec = CASOS[caso]
    carpeta.mkdir(parents=True, exist_ok=True)
    escritos: list[Path] = []
    if "ubicacion" in spec:
        for nombre, conteo in spec["ubicacion"].items():
            etiquetas = secuencia(conteo)
            filas = [fila_ubicacion(d, i) for i, d in enumerate(etiquetas)]
            ruta = carpeta / f"UBICACION_{nombre}.csv"
            ruta.write_bytes(_texto_csv(filas))
            escritos.append(ruta)
            # Detalle de 23 columnas: una fila válida por cada llave de ubicación.
            detalle = [fila_detalle("validos", i, PRODUCTOS[nombre]) for i in range(len(etiquetas))]
            ruta = carpeta / PRODUCTOS[nombre].archivo
            ruta.write_bytes(_texto_csv(detalle))
            escritos.append(ruta)
    for nombre, conteo in spec.get("productos", {}).items():
        producto = PRODUCTOS[nombre]
        etiquetas = secuencia(conteo)
        filas = [fila_detalle(d, i, producto) for i, d in enumerate(etiquetas)]
        ruta = carpeta / producto.archivo
        ruta.write_bytes(_texto_csv(filas))
        escritos.append(ruta)
    for clave in spec["excel"]:
        nombre, cabecera, filas = EXCEL[clave]
        ruta = carpeta / nombre
        escribir_xlsx(ruta, cabecera, filas)
        escritos.append(ruta)
    return escritos


def generar_todo(destino: Path = CORPUS_L8) -> dict[str, dict[str, dict[str, int]]]:
    """Escribe los ocho casos y devuelve sus conteos."""
    for caso in CASOS:
        escribir_caso(caso, destino / caso / "entradas")
    return {caso: conteos_caso(caso) for caso in CASOS}


def main() -> int:
    for caso, conteos in generar_todo().items():
        print(caso)
        for producto, conteo in conteos.items():
            print(f"  {producto}: {conteo}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
