"""Generadores de F1.6: `case new --from-gap` y `rules new --from-gap`.

Un caso nace de un hueco: se toma el fragmento SAS que lo produce, se anonimiza (tablas y columnas
a `t1`, `c1`...; literales a `texto`; comentarios fuera) y se compila para anotar el estado actual
en `expected.yaml`. El dueño edita después lo que **debería** salir.

Una regla nueva nace prellenada con `status: parcial` (o `component: none` en mapeo) y apunta a ese
caso. Lo que falta está marcado con `PENDIENTE` y no pasa `rules validate` hasta completarse.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from sgm.compile import compile_project

ROOT = Path(__file__).resolve().parents[2]
CASES = ROOT / "tests" / "cases"  # las pruebas lo reemplazan por una carpeta temporal
RULES = ROOT / "rules"

# Tipo de regla -> carpeta donde nace el archivo. `informats` no tiene archivo nuevo: vive en
# `rules/sas/informats.yaml`.
CARPETA = {
    "proc": RULES / "sas" / "procs",
    "statement": RULES / "sas" / "statements",
    "function": RULES / "sas" / "functions",
    "intrinsic": RULES / "sas" / "intrinsics",
    "mapping": RULES / "mapping",
}

# Palabras que el anonimizador no toca: sintaxis de SAS y SQL, no nombres del cliente.
RESERVADAS = frozenset(
    """
    data proc run quit set merge by id var where keep drop rename format informat length label
    output if then else do end to in and or not is null missing select from create table as group
    order having join left right inner outer on union all distinct update delete insert values into
    retain array when otherwise sum count max min mean avg return stop abort link leave continue
    input put options title footnote libname filename ods macro mend let include global local
    class by sorted nodupkey nodup out outer first last explicit noprint print means summary freq
    transpose append base exec execute sql connect using like between exists case end
    """.split()
)
_FORMATO = re.compile(r"\$?[a-z]+\d*\.\d*")
_TOKEN = re.compile(
    r"""'[^']*'|"[^"]*"|&[A-Za-z_]\w*|%?[A-Za-z_][\w.]*|\d+(?:\.\d+)?|\S|\s+""",
)
_TABLA_ANTES = frozenset("set from join merge data into update table modify out".split())
_SECRETO = re.compile(r"pwencode|pass(word)?\s*=|\bpw\s*=", re.IGNORECASE)


def normalizar(firma: str) -> str:
    """Firma en minúsculas, con guiones: nombre de carpeta y de regla."""
    texto = re.sub(r"[^a-z0-9]+", "-", firma.lower()).strip("-")
    if not texto:
        raise ValueError(f"firma vacía tras normalizar: {firma!r}")
    return texto


def _sin_comentarios(text: str) -> str:
    text = re.sub(r"/\*.*?\*/", " ", text, flags=re.DOTALL)
    return "\n".join(
        "" if re.match(r"\s*\*.*;\s*$", linea) else linea for linea in text.splitlines()
    )


def fragmento(texto: str, inicio: int, fin: int, maximo: int = 200) -> str:
    """Líneas `inicio..fin` (1-based). Si el paso o PROC no cierra, sigue hasta `run;`/`quit;`."""
    lineas = texto.splitlines()
    tomadas = lineas[inicio - 1 : fin]
    if tomadas and not any(re.match(r"\s*(run|quit)\s*;", linea) for linea in tomadas):
        for linea in lineas[fin : fin + maximo]:
            tomadas.append(linea)
            if re.match(r"\s*(run|quit)\s*;", linea):
                break
    return "\n".join(tomadas) + "\n"


@dataclass
class _Nombres:
    """Asigna nombres nuevos y estables: el mismo original siempre da el mismo nombre."""

    usados: dict[str, str]
    contadores: dict[str, int]

    def nuevo(self, original: str, prefijo: str) -> str:
        clave = f"{prefijo}:{original.lower()}"
        if clave not in self.usados:
            self.contadores[prefijo] = self.contadores.get(prefijo, 0) + 1
            self.usados[clave] = f"{prefijo}{self.contadores[prefijo]}"
        return self.usados[clave]


def anonimizar(sas: str) -> str:
    """Quita comentarios, renombra identificadores y oculta literales. Conserva palabras de SAS."""
    sas = _sin_comentarios(sas)
    nombres = _Nombres(usados={}, contadores={})
    tokens = [t for t in _TOKEN.findall(sas) if t]
    salida: list[str] = []
    anterior = ""
    for i, token in enumerate(tokens):
        siguiente = tokens[i + 1] if i + 1 < len(tokens) else ""
        bajo = token.lower()
        if token[0] in "'\"":
            salida.append(f"{token[0]}texto{token[0]}" if token[1:-1] else token)
        elif token.startswith("&") and len(token) > 1:
            salida.append("&" + nombres.nuevo(token[1:], "v"))
        elif token.startswith("%") and len(token) > 1:
            salida.append(token if bajo[1:] in RESERVADAS else "%" + nombres.nuevo(token, "m"))
        elif re.match(r"[A-Za-z_]", token):
            raiz = bajo.split(".")[0]
            if siguiente == "(" or raiz in RESERVADAS or _FORMATO.fullmatch(bajo):
                salida.append(token)
            elif "." in token:
                lib, _, resto = token.partition(".")
                if lib.lower() in ("work", "sashelp"):
                    salida.append(f"{lib}.{nombres.nuevo(resto, 't')}")
                else:
                    salida.append(nombres.nuevo(token, "t"))
            elif anterior in _TABLA_ANTES:
                salida.append(nombres.nuevo(token, "t"))
            else:
                salida.append(nombres.nuevo(token, "c"))
        else:
            salida.append(token)
        if token.strip():
            anterior = bajo
    texto = "".join(salida)
    if _SECRETO.search(texto):
        raise ValueError("el fragmento anonimizado aún contiene un secreto; no se escribe")
    return texto


def _compilar(texto: str) -> list[str]:
    """Motivos de huecos que produce el fragmento con el entorno por defecto."""
    compiled, _ = compile_project({"caso.sas": texto})
    return sorted(g.reason for g in compiled["caso.sas"].plan.gaps)


def _leer_fuente(fuente: Path, archivo: str) -> str:
    ruta = fuente if fuente.is_file() else fuente / archivo
    if not ruta.exists():
        raise FileNotFoundError(f"no encuentro el programa de origen: {ruta}")
    return ruta.read_text(encoding="utf-8", errors="replace")


def _mostrar(ruta: Path) -> str:
    """Ruta relativa a la raíz del repo si está dentro; si no, la ruta tal cual."""
    try:
        return ruta.relative_to(ROOT).as_posix()
    except ValueError:
        return str(ruta)


def crear_caso(firma: str, fuente: Path, cases: Path | None = None) -> Path:
    """Crea `tests/cases/<firma>/` a partir del primer ejemplo del hueco guardado."""
    from sgm.store import gaps as gap_store
    from sgm.store.db import Store

    with Store() as store:
        filas = [r for r in gap_store.top(store, 100000) if r["signature"] == firma]
    if not filas:
        raise ValueError(f"no hay un hueco con la firma {firma}; compila primero")
    fila = filas[0]
    ejemplo = fila["example"]
    if not ejemplo:
        raise ValueError(f"el hueco {firma} no tiene ejemplo con líneas")
    carpeta = (CASES if cases is None else cases) / normalizar(firma)
    if carpeta.exists():
        raise FileExistsError(f"ya existe el caso {_mostrar(carpeta)}")
    original = _leer_fuente(fuente, ejemplo["file"])
    texto = anonimizar(fragmento(original, ejemplo["line_start"], ejemplo["line_end"]))
    obtenido = _compilar(texto)
    carpeta.mkdir(parents=True)
    (carpeta / "input.sas").write_text(texto, encoding="utf-8")
    descripcion = (
        f"Hueco {fila['reason']} anonimizado. Lo que sale hoy está en `expect`; "
        "el dueño lo ajusta a lo que debería salir."
    )
    gaps_yaml = "\n".join(f"    - {g}" for g in obtenido) if obtenido else "    []"
    (carpeta / "expected.yaml").write_text(
        f'description: "{descripcion}"\n'
        "input: input.sas\n"
        "env: default\n"
        "expect:\n"
        "  gaps:\n"
        f"{gaps_yaml}\n",
        encoding="utf-8",
    )
    (carpeta / "README.md").write_text(
        f"# {normalizar(firma)}\n\n"
        f"- Firma del hueco: `{firma}`\n"
        f"- Motivo: `{fila['reason']}`\n"
        f"- Dueño: {fila['owner'] or 'sin asignar'}\n"
        f"- Se cierra con: {fila['fix_with'] or 'sin arreglo registrado'}\n\n"
        "Fragmento anonimizado: tablas y columnas renombradas, literales sustituidos, comentarios\n"
        "quitados. `expected.yaml` lleva el estado actual; el dueño lo cambia a lo que debe "
        "salir.\n",
        encoding="utf-8",
    )
    return carpeta


def _nombre_de_funcion(firma: str) -> str:
    return firma.rsplit("/", 1)[-1] if "/" in firma else "PENDIENTE"


def _plantilla(tipo: str, identificador: str, firma: str) -> str:
    caso = f"tests/cases/{normalizar(firma)}"
    cabecera = f"id: {identificador}\nkind: {tipo}\nversion: 1\nstatus: parcial\n"
    if tipo == "proc":
        cuerpo = (
            "proc: PENDIENTE  # nombre del PROC\n"
            "ops:  # operaciones de la IR; ver 04-puntos-de-extension.md\n"
            "  - op: PENDIENTE\n"
        )
    elif tipo == "statement":
        cuerpo = (
            "statement: PENDIENTE\n"
            "action: unsupported  # plumbing, context, set_variable o unsupported\n"
        )
    elif tipo == "function":
        cuerpo = f"sas: {_nombre_de_funcion(firma)}\n"
    elif tipo == "intrinsic":
        # Patrón `^sgm\.`: el módulo se crea después, en src/sgm/passes/intrinsics/.
        cuerpo = "implementation: sgm.passes.intrinsics.PENDIENTE\n"
    else:
        raise ValueError(f"tipo sin plantilla: {tipo}")
    return f"{cabecera}{cuerpo}tests:\n  - {caso}\n"


def _mapeo(identificador: str, firma: str) -> str:
    return (
        f"id: {identificador}\n"
        "version: 1\n"
        "rung: 2\n"
        'description: "PENDIENTE: qué operación cubre esta regla."\n'
        "match:\n"
        "  kind: PENDIENTE\n"
        "emit:\n"
        "  component: none  # sin componente hasta decidirlo; `none` no pasa a componente\n"
        "confidence: baja\n"
        "alternatives: []\n"
        "tests:\n"
        f"  - tests/cases/{normalizar(firma)}\n"
    )


def crear_regla(tipo: str, firma: str, fuente: Path | None) -> Path:
    """Crea el archivo de reglas prellenado para el tipo y apunta al caso (lo crea si falta)."""
    if tipo == "informats":
        raise ValueError(
            "informats no tiene archivo nuevo: edita rules/sas/informats.yaml "
            "o env/schemas/ según el motivo"
        )
    if tipo not in CARPETA:
        raise ValueError(f"tipo desconocido: {tipo}. Tipos: {', '.join(sorted(CARPETA))}")
    identificador = f"{tipo}-{normalizar(firma)}"
    destino = CARPETA[tipo] / f"{identificador}.yaml"
    if destino.exists():
        raise FileExistsError(f"ya existe {destino.relative_to(ROOT).as_posix()}")
    caso = CASES / normalizar(firma)
    if not (caso / "expected.yaml").exists():
        if fuente is None:
            raise ValueError("el caso del hueco no existe; pasa --fuente para crearlo")
        crear_caso(firma, fuente)
    contenido = (
        _mapeo(identificador, firma)
        if tipo == "mapping"
        else _plantilla(tipo, identificador, firma)
    )
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(contenido, encoding="utf-8")
    return destino
