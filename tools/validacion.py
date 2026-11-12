"""Candado de cierre: exige la suite completa y `ruff` en verde para el árbol que se va a commitear.

Uso:
    uv run python tools/validacion.py estado
    uv run python tools/validacion.py historial
    uv run python tools/validacion.py exigir          # lo llama el gancho pre-commit
    uv run python tools/validacion.py guardia         # lo llama el gancho de Claude Code

`tools/ci.py` deja el estado en `.cache/validacion/estado.json` cuando termina. El gancho
`pre-commit` (`.githooks/pre-commit`) compara la huella del árbol actual con la que se validó: si no
coinciden, o si algún paso obligatorio quedó en rojo, el commit se rechaza. Cada validación y cada
intento de commit quedan en `.cache/validacion/historial.jsonl`.

La huella cubre el commit base, cada archivo modificado y cada archivo sin seguimiento, con el hash
de su contenido. Así, editar un archivo después de validar invalida el cierre aunque `git status`
muestre el mismo nombre. Los archivos ignorados (`.cache`, `corpus`, `.venv`) no cuentan.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shlex
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import TextIO

REPO = Path(__file__).resolve().parents[1]
PASOS_OBLIGATORIOS = ("pytest", "ruff")
NOMBRE_ESTADO = "estado.json"
NOMBRE_HISTORIAL = "historial.jsonl"


def directorio(base: Path | None = None) -> Path:
    """Carpeta del estado. `SGM_VALIDACION_DIR` permite aislarla en las pruebas."""
    if base is not None:
        return Path(base)
    return Path(os.environ.get("SGM_VALIDACION_DIR") or (REPO / ".cache" / "validacion"))


def _ahora() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


def _commit_base(repo: Path) -> str:
    proceso = _git(repo, "rev-parse", "--verify", "HEAD")
    return proceso.stdout.strip() if proceso.returncode == 0 else ""


def _hash_archivo(ruta: Path) -> str:
    try:
        return hashlib.sha256(ruta.read_bytes()).hexdigest()
    except OSError:
        return "<ilegible>"


def huella_arbol(repo: Path = REPO) -> str:
    """Hash estable de lo que se commitearía: HEAD más el contenido de cada cambio."""
    estado = _git(
        repo,
        "status",
        "--porcelain=v1",
        "-z",
        "--untracked-files=all",
        "--no-renames",
    )
    if estado.returncode != 0:
        raise RuntimeError(estado.stderr.strip() or "git status falló")
    partes = [f"base:{_commit_base(repo)}"]
    for entrada in estado.stdout.split("\0"):
        if len(entrada) < 4:
            continue
        # Formato `XY ruta`: los dos primeros caracteres son el estado y el tercero es el espacio.
        # No se puede usar `partition(" ")`: una modificación sin preparar empieza con un espacio.
        codigo = entrada[:2]
        ruta = entrada[3:]
        archivo = repo / ruta
        if "D" in codigo or not archivo.is_file():
            contenido = "<ausente>"
        else:
            contenido = _hash_archivo(archivo)
        partes.append(f"{codigo}:{ruta}:{contenido}")
    partes.sort()
    return hashlib.sha256("\n".join(partes).encode("utf-8")).hexdigest()


def leer_estado(base: Path | None = None) -> dict:
    ruta = directorio(base) / NOMBRE_ESTADO
    try:
        return json.loads(ruta.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def escribir_estado(estado: dict, base: Path | None = None) -> None:
    carpeta = directorio(base)
    carpeta.mkdir(parents=True, exist_ok=True)
    ruta = carpeta / NOMBRE_ESTADO
    temporal = ruta.with_suffix(".tmp")
    temporal.write_text(json.dumps(estado, ensure_ascii=False, indent=2), encoding="utf-8")
    temporal.replace(ruta)


def _anotar(evento: dict, base: Path | None = None) -> None:
    carpeta = directorio(base)
    carpeta.mkdir(parents=True, exist_ok=True)
    with (carpeta / NOMBRE_HISTORIAL).open("a", encoding="utf-8") as archivo:
        archivo.write(json.dumps(evento, ensure_ascii=False) + "\n")


def registrar(
    paso: str,
    ok: bool,
    resumen: str = "",
    *,
    repo: Path = REPO,
    base: Path | None = None,
    huella: str | None = None,
) -> dict:
    """Anota el resultado de un paso para el árbol actual.

    Si el árbol cambió desde la última anotación, el estado se reinicia: una validación vieja no
    autoriza un commit nuevo.
    """
    actual = huella or huella_arbol(repo)
    estado = leer_estado(base)
    if estado.get("huella") != actual:
        estado = {
            "huella": actual,
            "commit": _commit_base(repo),
            "fecha": _ahora(),
            "pasos": {},
        }
    estado.setdefault("pasos", {})[paso] = {
        "ok": bool(ok),
        "fecha": _ahora(),
        "resumen": resumen.strip()[:500],
    }
    estado["fecha"] = _ahora()
    escribir_estado(estado, base)
    _anotar(
        {
            "fecha": estado["fecha"],
            "evento": "validacion",
            "paso": paso,
            "ok": bool(ok),
            "huella": actual,
            "commit": estado.get("commit", ""),
            "resumen": resumen.strip()[:500],
        },
        base,
    )
    return estado


def evaluar(repo: Path = REPO, base: Path | None = None) -> dict:
    """Decide si el árbol actual puede commitearse y explica por qué no."""
    actual = huella_arbol(repo)
    estado = leer_estado(base)
    resultado = {"permitido": False, "motivo": "", "huella": actual, "pasos": {}}
    if not estado:
        resultado["motivo"] = "No hay ninguna validación registrada para este repositorio."
        return resultado
    if estado.get("huella") != actual:
        resultado["motivo"] = (
            "El árbol cambió después de la última validación: la huella no coincide."
        )
        return resultado
    pasos = estado.get("pasos", {})
    resultado["pasos"] = pasos
    cierre = pasos.get("ci")
    if cierre and not cierre.get("ok"):
        detalle = cierre.get("resumen") or "algún paso obligatorio falló"
        resultado["motivo"] = f"El último cierre de `tools/ci.py` falló: {detalle}."
        return resultado
    if cierre and cierre.get("ok"):
        resultado["permitido"] = True
        resultado["motivo"] = "Cierre completo en verde para el árbol actual."
        return resultado
    faltan = [paso for paso in PASOS_OBLIGATORIOS if not pasos.get(paso, {}).get("ok")]
    if faltan:
        resultado["motivo"] = f"Falta la validación completa: {', '.join(faltan)}."
        return resultado
    resultado["permitido"] = True
    resultado["motivo"] = "Suite completa y `ruff` en verde para el árbol actual."
    return resultado


def mensaje(resultado: dict) -> str:
    return (
        f"Commit bloqueado: {resultado['motivo']}\n\n"
        "Corre el cierre completo y vuelve a intentar:\n"
        "    uv run python tools/ci.py\n\n"
        "El estado queda en .cache/validacion/estado.json y el historial en\n"
        ".cache/validacion/historial.jsonl. No uses `--no-verify`: el gancho existe para que un\n"
        "cierre en rojo no llegue al historial."
    )


def exigir(
    *,
    origen: str = "gancho-git",
    repo: Path = REPO,
    base: Path | None = None,
    salida: TextIO | None = None,
) -> int:
    """Código 0 si el commit puede seguir; 1 si el gancho debe rechazarlo."""
    resultado = evaluar(repo, base)
    _anotar(
        {
            "fecha": _ahora(),
            "evento": "commit",
            "permitido": resultado["permitido"],
            "origen": origen,
            "motivo": resultado["motivo"],
            "huella": resultado["huella"],
            "commit": _commit_base(repo),
        },
        base,
    )
    if resultado["permitido"]:
        return 0
    print(mensaje(resultado), file=salida or sys.stderr)
    return 1


def _es_commit(comando: str) -> bool:
    """Detecta `git commit` como subcomando, no como texto dentro de otro argumento."""
    for tramo in re.split(r"&&|\|\||[;|\n]", comando):
        try:
            partes = shlex.split(tramo, posix=True)
        except ValueError:
            partes = tramo.split()
        for indice, token in enumerate(partes):
            if token != "git":
                continue
            siguiente = indice + 1
            while siguiente < len(partes) and partes[siguiente].startswith("-"):
                opcion = partes[siguiente]
                siguiente += 1
                if opcion in ("-C", "-c", "--git-dir", "--work-tree", "--namespace"):
                    siguiente += 1
            if siguiente < len(partes) and partes[siguiente] == "commit":
                return True
    return False


def guardia(
    entrada: str,
    *,
    repo: Path = REPO,
    base: Path | None = None,
) -> tuple[int, str]:
    """Gancho de Claude Code: bloquea `git commit` sin cierre verde (código 2)."""
    try:
        datos = json.loads(entrada or "{}")
    except json.JSONDecodeError:
        return 0, ""
    if datos.get("tool_name") != "Bash":
        return 0, ""
    comando = str((datos.get("tool_input") or {}).get("command") or "")
    if not _es_commit(comando):
        return 0, ""
    if "--no-verify" in comando:
        motivo = "No uses `git commit --no-verify`: el candado de cierre quedaría saltado."
        _anotar(
            {
                "fecha": _ahora(),
                "evento": "commit",
                "permitido": False,
                "origen": "claude",
                "motivo": motivo,
                "huella": "",
                "commit": _commit_base(repo),
            },
            base,
        )
        return 2, f"Commit bloqueado: {motivo}\n\nCorre `uv run python tools/ci.py`."
    if "tools/ci.py" in comando:
        # El cierre corre antes del commit en el mismo comando y deja el estado; el gancho de git
        # comprueba el resultado justo antes de crear el commit.
        return 0, ""
    resultado = evaluar(repo, base)
    _anotar(
        {
            "fecha": _ahora(),
            "evento": "commit",
            "permitido": resultado["permitido"],
            "origen": "claude",
            "motivo": resultado["motivo"],
            "huella": resultado["huella"],
            "commit": _commit_base(repo),
        },
        base,
    )
    if resultado["permitido"]:
        return 0, ""
    return 2, mensaje(resultado)


def _cmd_estado(repo: Path = REPO, base: Path | None = None) -> int:
    estado = leer_estado(base)
    actual = huella_arbol(repo)
    print(f"Árbol actual: {actual[:12]}")
    if not estado:
        print("Sin validaciones registradas.")
        print("Commit permitido: no (corre `uv run python tools/ci.py`).")
        return 1
    print(f"Validado: {estado.get('fecha', '?')} sobre {estado.get('huella', '')[:12]}")
    print(f"Commit base: {estado.get('commit', '?')[:12] or '(sin commits)'}")
    pasos = estado.get("pasos", {})
    if not pasos:
        print("  (ningún paso anotado)")
    for nombre in sorted(pasos):
        datos = pasos[nombre]
        marca = "OK" if datos.get("ok") else "FALLA"
        resumen = datos.get("resumen") or ""
        print(f"  {nombre:<8} {marca:<5} {resumen}".rstrip())
    resultado = evaluar(repo, base)
    print(f"Commit permitido: {'sí' if resultado['permitido'] else 'no'} ({resultado['motivo']})")
    return 0 if resultado["permitido"] else 1


def _cmd_historial(cantidad: int, base: Path | None = None) -> int:
    ruta = directorio(base) / NOMBRE_HISTORIAL
    try:
        lineas = ruta.read_text(encoding="utf-8").splitlines()
    except OSError:
        print(f"No hay historial en {ruta}.")
        return 1
    for linea in lineas[-cantidad:]:
        try:
            evento = json.loads(linea)
        except json.JSONDecodeError:
            continue
        if evento.get("evento") == "validacion":
            marca = "OK" if evento.get("ok") else "FALLA"
            detalle = f"{evento.get('paso', '?'):<8} {marca:<5} {evento.get('resumen', '')}"
        else:
            marca = "PERMITE" if evento.get("permitido") else "BLOQUEA"
            detalle = f"commit   {marca:<8} {evento.get('motivo', '')}"
        print(f"{evento.get('fecha', '?')}  {detalle}".rstrip())
    return 0


def main(argv: list[str] | None = None) -> int:
    for flujo in (sys.stdout, sys.stderr):
        if hasattr(flujo, "reconfigure"):
            flujo.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    subcomandos = parser.add_subparsers(dest="comando", required=True)
    subcomandos.add_parser("estado", help="qué se validó y si el commit pasaría")
    historial = subcomandos.add_parser(
        "historial", help="últimas validaciones e intentos de commit"
    )
    historial.add_argument("-n", type=int, default=20, help="cuántas líneas mostrar")
    exigir_parser = subcomandos.add_parser("exigir", help="código 1 si el commit debe rechazarse")
    exigir_parser.add_argument("--origen", default="gancho-git")
    subcomandos.add_parser("guardia", help="gancho PreToolUse de Claude Code")
    args = parser.parse_args(argv)
    if args.comando == "estado":
        return _cmd_estado()
    if args.comando == "historial":
        return _cmd_historial(args.n)
    if args.comando == "exigir":
        return exigir(origen=args.origen)
    codigo, aviso = guardia(sys.stdin.read())
    if aviso:
        print(aviso, file=sys.stderr)
    return codigo


if __name__ == "__main__":
    raise SystemExit(main())
