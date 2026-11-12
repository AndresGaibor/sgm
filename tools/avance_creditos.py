"""Tabla 11b del plan maestro, calculada desde `docs/plan-reescritura/creditos.yaml` (G-4).

El YAML es la fuente de los créditos (juicio humano); la tabla del plan es la salida.
Uso: uv run python tools/avance_creditos.py (--importar | --imprimir | --actualizar | --verificar)
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

import yaml

RAIZ = Path(__file__).resolve().parents[1]
YAML_POR_DEFECTO = RAIZ / "docs" / "plan-reescritura" / "creditos.yaml"
PLAN_POR_DEFECTO = RAIZ / "docs" / "plan-reescritura" / "plan-migrador-general.md"
MARCA_INICIO = "<!-- avance:inicio -->"
MARCA_FIN = "<!-- avance:fin -->"
ENCABEZADO = "| Fase | Horas | Crédito | % de la fase | Qué sostiene la cifra |"
SEPARADOR = "|---|---|---|---|---|"


@dataclass(frozen=True)
class Fase:
    id: str
    nombre: str
    horas: float
    credito_sin_desglosar: float
    tareas: tuple[tuple[str, float, float], ...]
    sostiene: str


def credito(fase: Fase) -> float:
    return fase.credito_sin_desglosar + sum(horas * fraccion for _, horas, fraccion in fase.tareas)


def porcentaje(horas: float, credito_: float) -> int:
    if horas <= 0:
        return 0
    valor = Decimal(str(credito_)) * 100 / Decimal(str(horas))
    return int(valor.quantize(Decimal(1), rounding=ROUND_HALF_UP))


def formato_credito(valor: float) -> str:
    entero, _, decimales = f"{round(valor, 2):.2f}".partition(".")
    decimales = decimales.rstrip("0") or "0"
    return f"{entero},{decimales}"


def _formato_horas(horas: float) -> str:
    return str(int(horas)) if float(horas).is_integer() else formato_credito(horas)


def cargar(ruta: Path) -> tuple[Fase, ...]:
    datos = yaml.safe_load(Path(ruta).read_text(encoding="utf-8")) or {}
    fases: list[Fase] = []
    ids_fase: set[str] = set()
    ids_tarea: set[str] = set()
    for item in datos.get("fases", []):
        fid = str(item["id"])
        if fid in ids_fase:
            raise ValueError(f"id de fase repetido: {fid}")
        ids_fase.add(fid)
        tareas = []
        for t in item.get("tareas") or []:
            tid = str(t["id"])
            fraccion = float(t["fraccion"])
            if tid in ids_tarea:
                raise ValueError(f"id de tarea repetido: {tid}")
            if not 0 <= fraccion <= 1:
                raise ValueError(f"fracción fuera de [0,1] en {tid}")
            ids_tarea.add(tid)
            tareas.append((tid, float(t["horas"]), fraccion))
        horas = float(item["horas"])
        if sum(h for _, h, _ in tareas) > horas:
            raise ValueError(f"{fid}: las tareas suman más horas que la fase")
        fases.append(
            Fase(
                id=fid,
                nombre=str(item["nombre"]),
                horas=horas,
                credito_sin_desglosar=float(item["credito_sin_desglosar"]),
                tareas=tuple(tareas),
                sostiene=str(item.get("sostiene", "")),
            )
        )
    return tuple(fases)


def _porcentaje_total(horas: float, credito_: float) -> str:
    valor = Decimal(str(credito_)) * 100 / Decimal(str(horas))
    return f"{valor.quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)}".replace(".", ",")


def tabla_markdown(fases: tuple[Fase, ...]) -> str:
    filas = [ENCABEZADO, SEPARADOR]
    for f in fases:
        c = credito(f)
        filas.append(
            f"| {f.id} {f.nombre} | {_formato_horas(f.horas)} | {formato_credito(c)} | "
            f"{porcentaje(f.horas, c)} % | {f.sostiene} |"
        )
    horas = sum(f.horas for f in fases)
    total = sum(credito(f) for f in fases)
    filas.append(
        f"| **Total** | **{_formato_horas(horas)}** | **{formato_credito(total)}** | "
        f"**{_porcentaje_total(horas, total)} %** | |"
    )
    return "\n".join(filas)


def importar(plan: Path) -> str:
    lineas = Path(plan).read_text(encoding="utf-8").splitlines()
    if ENCABEZADO not in lineas:
        raise ValueError("no hay tabla 11b en el plan")
    inicio = lineas.index(ENCABEZADO) + 2
    fases = []
    for linea in lineas[inicio:]:
        if not linea.startswith("|") or "**Total**" in linea:
            break
        celdas = [c.strip() for c in linea.strip().strip("|").split("|")]
        fid, _, nombre = celdas[0].partition(" ")
        fases.append(
            {
                "id": fid,
                "nombre": nombre,
                "horas": float(celdas[1].replace(",", ".")),
                "credito_sin_desglosar": float(celdas[2].replace(",", ".")),
                "tareas": [],
                "sostiene": celdas[4],
            }
        )
    return yaml.safe_dump({"fases": fases}, allow_unicode=True, sort_keys=False)


def _eol(texto: str) -> str:
    return "\r\n" if "\r\n" in texto else "\n"


def actualizar_plan(plan: Path, tabla: str) -> bool:
    ruta = Path(plan)
    texto = ruta.read_bytes().decode("utf-8")
    i = texto.find(MARCA_INICIO)
    j = texto.find(MARCA_FIN)
    if i < 0 or j < 0 or j < i:
        return False
    eol = _eol(texto)
    nuevo = (
        texto[: i + len(MARCA_INICIO)] + eol + tabla.replace("\n", eol) + eol + texto[j:]
    )
    ruta.write_bytes(nuevo.encode("utf-8"))
    return True


def verificar(yaml_ruta: Path, plan: Path) -> bool:
    texto = Path(plan).read_text(encoding="utf-8")
    i = texto.find(MARCA_INICIO)
    j = texto.find(MARCA_FIN)
    if i < 0 or j < 0 or j < i:
        return False
    actual = texto[i + len(MARCA_INICIO) : j].strip("\r\n").replace("\r\n", "\n")
    return actual == tabla_markdown(cargar(yaml_ruta))


def _principal(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Tabla 11b desde creditos.yaml")
    parser.add_argument("--yaml", type=Path, default=YAML_POR_DEFECTO)
    parser.add_argument("--plan", type=Path, default=PLAN_POR_DEFECTO)
    modo = parser.add_mutually_exclusive_group(required=True)
    modo.add_argument("--importar", action="store_true")
    modo.add_argument("--imprimir", action="store_true")
    modo.add_argument("--actualizar", action="store_true")
    modo.add_argument("--verificar", action="store_true")
    args = parser.parse_args(argv)

    if args.importar:
        args.yaml.write_text(importar(args.plan), encoding="utf-8")
        print(f"escrito: {args.yaml}")
        return 0
    fases = cargar(args.yaml)
    if args.imprimir:
        print(tabla_markdown(fases))
        restante = sum(f.horas for f in fases) - sum(credito(f) for f in fases)
        print(f"\nrestante = horas - crédito = {formato_credito(restante)} h")
        return 0
    if args.actualizar:
        if not actualizar_plan(args.plan, tabla_markdown(fases)):
            print("el plan no tiene las marcas de avance", file=sys.stderr)
            return 1
        print("plan actualizado")
        return 0
    if verificar(args.yaml, args.plan):
        print("la tabla del plan sale del YAML")
        return 0
    print("la tabla del plan NO coincide con el YAML", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(_principal())
