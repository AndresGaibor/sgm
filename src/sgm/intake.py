"""`sgm intake` (F1.7): importa un lote, lo deja en UTF-8 sin secretos, compila y registra huecos.

Pasos, en orden:
1. Importa la carpeta o el archivo con `import_source` (copia segura, sin ejecutar nada).
2. Pasa cada texto a UTF-8 y redacta credenciales con `redaction.redact`. El original no se guarda:
   en el lote solo queda la copia limpia.
3. Compila los programas SAS y escribe guía y plan de cada uno en `salida/`.
4. Guarda el inventario de huecos en la base (igual que `compile`: reemplaza el anterior) y lo
   escribe en `huecos.json`.

La carpeta del lote es `corpus/inbox/<fecha>-<hash>/`, con el hash del contenido: el mismo lote
siempre cae en la misma carpeta. `corpus/` no va al repositorio.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import shutil
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from sgm import redaction
from sgm.batch import compile_batch
from sgm.catalog.config import Env, load_env
from sgm.emit.guide_md import render_guide
from sgm.emit.plan_json import plan_to_dict
from sgm.ingest.importer import TEXT_KINDS, detect_encoding, import_source
from sgm.ingest.limits import ImportLimits
from sgm.ingest.models import FileKind
from sgm.store import gaps as gap_store
from sgm.store import overrides as override_store
from sgm.store.db import Store

ROOT = Path(__file__).resolve().parents[2]
INBOX = ROOT / "corpus" / "inbox"


@dataclass
class Resultado:
    carpeta: Path
    archivos: int
    omitidos: int
    lineas_redactadas: int
    codificaciones: dict[str, int] = field(default_factory=dict)
    programas: int = 0
    huecos: int = 0


def _lineas_distintas(antes: str, despues: str) -> int:
    """Líneas que cambiaron. La redacción conserva el número de líneas."""
    return sum(1 for a, b in zip(antes.splitlines(), despues.splitlines(), strict=True) if a != b)


def _normalizar(carpeta: Path, archivos) -> tuple[int, dict[str, int]]:
    """Pasa los textos a UTF-8 y los redacta en sitio. Devuelve líneas redactadas y codificaciones.

    `archivos` son los `SourceFile` de la importación; sus rutas son relativas a `carpeta`.
    """
    lineas = 0
    codificaciones: dict[str, int] = {}
    for archivo in archivos:
        if archivo.kind not in TEXT_KINDS:
            continue
        ruta = carpeta / archivo.path
        data = ruta.read_bytes()
        enc = detect_encoding(data)
        if enc is None:  # binario: no se toca
            continue
        if enc != "utf-8":
            codificaciones[enc] = codificaciones.get(enc, 0) + 1
        texto = data.decode(enc, errors="replace")
        limpio = redaction.redact(texto, archivo.path)
        lineas += _lineas_distintas(texto, limpio)
        ruta.write_bytes(limpio.encode("utf-8"))  # bytes: no convertir saltos de línea
    return lineas, codificaciones


def _escribir_salida(carpeta: Path, compiled: dict) -> None:
    out = carpeta / "salida"
    out.mkdir(parents=True, exist_ok=True)
    for program, result in compiled.items():
        stem = Path(program).with_suffix("").as_posix().replace("/", "__")
        (out / f"{stem}.guide.md").write_text(render_guide(result.plan), encoding="utf-8")
        payload = plan_to_dict(result.plan)
        (out / f"{stem}.plan.json").write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )


def _inventario_de_lotes(inbox: Path) -> list[dict]:
    """Huecos de todos los lotes del inbox, unidos por firma y motivo.

    Así un lote nuevo no borra los huecos de los anteriores: se suman las ocurrencias y se unen
    los archivos.
    """
    unidos: dict[tuple[str, str], dict] = {}
    for ruta in sorted(inbox.glob("*/huecos.json")):
        for fila in json.loads(ruta.read_text(encoding="utf-8")):
            clave = (fila["signature"], fila["reason"])
            if clave not in unidos:
                unidos[clave] = {
                    "signature": fila["signature"],
                    "reason": fila["reason"],
                    "files": [],
                    "occurrences": 0,
                    "example": fila["example"],
                }
            acumulado = unidos[clave]
            acumulado["files"] = sorted(set(acumulado["files"]) | set(fila["files"]))
            acumulado["occurrences"] += fila["occurrences"]
    return sorted(
        unidos.values(), key=lambda r: (-len(r["files"]), -r["occurrences"], r["signature"])
    )


def intake(
    source: Path,
    env: Env | None = None,
    inbox: Path = INBOX,
    limits: ImportLimits | None = None,
) -> Resultado:
    """Importa, normaliza, compila y registra los huecos de un lote. Ver el módulo."""
    source = Path(source)
    if not source.exists():
        raise FileNotFoundError(f"no existe: {source}")
    limits = limits or ImportLimits()
    inbox.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=inbox) as tmp:
        origen = Path(tmp) / "origen"
        if source.is_file():
            origen.mkdir()
            shutil.copy2(source, origen / source.name)
            fuente = origen
        else:
            fuente = source
        importado = Path(tmp) / "importado"
        archivos, omitidos = import_source(fuente, importado, limits)
        # el nombre entra en la huella: dos archivos con el mismo texto son lotes distintos
        digest = hashlib.sha256(
            "".join(f"{a.path}:{a.sha256}" for a in archivos).encode()
        ).hexdigest()[:8]
        carpeta = inbox / f"{dt.date.today().isoformat()}-{digest}"
        if carpeta.exists():  # mismo contenido: se rehace desde cero
            shutil.rmtree(carpeta)
        carpeta.mkdir(parents=True)
        shutil.move(str(importado), str(carpeta / "fuente"))

    lineas, codificaciones = _normalizar(carpeta / "fuente", archivos)
    textos = {
        a.path: (carpeta / "fuente" / a.path).read_text(encoding="utf-8")
        for a in archivos
        if a.kind == FileKind.SAS
    }
    compiled, _ = compile_batch(textos, env=env or load_env())
    _escribir_salida(carpeta, compiled)

    with Store() as store:
        for result in compiled.values():
            override_store.apply(result.plan, store, carpeta.name)
    inventario = gap_store.inventory([r.plan for r in compiled.values()])
    (carpeta / "huecos.json").write_text(
        json.dumps(inventario, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    with Store() as store:
        gap_store.save(store, _inventario_de_lotes(inbox))
    return Resultado(
        carpeta=carpeta,
        archivos=len(archivos),
        omitidos=len(omitidos),
        lineas_redactadas=lineas,
        codificaciones=codificaciones,
        programas=len(compiled),
        huecos=len(inventario),
    )
