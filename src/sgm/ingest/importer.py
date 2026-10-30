"""Importación segura de lotes (carpeta o ZIP). Entrada no confiable: nada se ejecuta.

Los archivos aceptados se copian a `dest` (snapshot reproducible) y se registran con sha256.
"""

import hashlib
import os
import re
import stat
import tempfile
import zipfile
from collections.abc import Iterator
from pathlib import Path, PurePosixPath

from sgm.ingest.limits import ImportLimits
from sgm.ingest.models import FileKind, Skipped, SourceFile

EXCLUDED_DIRS = {".git", "node_modules", "__pycache__", ".svn", "__MACOSX"}
KIND_BY_SUFFIX = {
    ".sas": FileKind.SAS,
    ".sh": FileKind.SHELL,
    ".ksh": FileKind.SHELL,
    ".bash": FileKind.SHELL,
    ".log": FileKind.LOG,
    ".md": FileKind.DOC,
    ".txt": FileKind.DOC,
}
TEXT_KINDS = {FileKind.SAS, FileKind.SHELL, FileKind.LOG, FileKind.DOC}

# Los programas se entregan a veces como `.txt`: un `.txt` es SAS si se lee como SAS (varias sentencias propias del
# lenguaje al inicio de linea y un cierre de paso). Una nota que menciona "data" o "proc" en prosa no cumple.
_SAS_STATEMENT = re.compile(
    r"(?im)^\s*(?:proc\s+[a-z]+\b|data\s+[\w.&]+[^;\n]*;|%macro\s+\w+|%let\s+\w+\s*=|libname\s+\w+|%include\b|filename\s+\w+)"
)
_SAS_STEP_END = re.compile(r"(?im)\b(?:run|quit)\s*;|^\s*%mend\b")


def looks_like_sas(text: str) -> bool:
    """Si el texto parece un programa SAS. SAS Studio antepone un carácter invisible (U+200B) al exportar."""
    text = text.lstrip("\u200b\ufeff")
    return len(_SAS_STATEMENT.findall(text)) >= 3 and _SAS_STEP_END.search(text) is not None


class ImportError_(ValueError):
    """Lote rechazado (límites globales, origen inválido)."""


def safe_relpath(name: str) -> str | None:
    """Ruta relativa POSIX segura o None si escapa del directorio, es absoluta o está vacía."""
    n = name.replace("\\", "/")
    if "\0" in n or n.startswith("/") or (len(n) > 1 and n[1] == ":"):
        return None
    parts = [p for p in PurePosixPath(n).parts if p not in ("", ".")]
    if not parts or ".." in parts:
        return None
    return "/".join(parts)


def detect_encoding(data: bytes) -> str | None:
    if b"\0" in data:
        return None
    if data.startswith(b"\xef\xbb\xbf"):
        return "utf-8-sig"
    for enc in ("utf-8", "cp1252"):
        try:
            data.decode(enc)
            return enc
        except UnicodeDecodeError:
            pass
    return "latin-1"


def _entries(
    src: Path, limits: ImportLimits, dest: Path
) -> Iterator[tuple[str, bytes | None, str | None]]:
    """Genera (ruta_relativa, contenido, motivo_omisión). contenido None si se omite."""
    if src.is_dir():
        for root, dirs, files in os.walk(src, followlinks=False):
            # no entrar en carpetas que contienen el destino (el directorio de datos puede estar
            # dentro de la fuente: copiaría la copia recursivamente)
            dirs[:] = sorted(
                d
                for d in dirs
                if d not in EXCLUDED_DIRS and not dest.is_relative_to(Path(root, d).resolve())
            )
            for f in sorted(files):
                p = Path(root, f)
                rel = p.relative_to(src).as_posix()
                if p.is_symlink():
                    yield rel, None, "enlace simbólico"
                elif p.stat().st_size > limits.max_file_bytes:
                    yield rel, None, "supera max_file_bytes"
                else:
                    yield rel, p.read_bytes(), None
    elif zipfile.is_zipfile(src):
        with zipfile.ZipFile(src) as zf:
            infos = zf.infolist()
            if len(infos) > limits.max_zip_members:
                raise ImportError_(f"más de {limits.max_zip_members} miembros ZIP")
            for info in sorted(infos, key=lambda i: i.filename):
                if info.is_dir():
                    continue
                rel = safe_relpath(info.filename)
                if rel is None:
                    yield info.filename, None, "ruta insegura"
                elif stat.S_ISLNK(info.external_attr >> 16):
                    yield rel, None, "enlace simbólico"
                elif info.file_size > limits.max_file_bytes:
                    yield rel, None, "supera max_file_bytes"
                else:
                    with zf.open(info) as fh:
                        data = fh.read(limits.max_file_bytes + 1)
                    if len(data) > limits.max_file_bytes:
                        yield rel, None, "supera max_file_bytes"
                    else:
                        yield rel, data, None
    else:
        raise ImportError_(f"{src} no es una carpeta ni un ZIP válido")


def import_source(
    src: Path, dest: Path, limits: ImportLimits
) -> tuple[list[SourceFile], list[Skipped]]:
    src = Path(src)
    dest = dest.resolve()
    if src.resolve().is_relative_to(dest):
        raise ImportError_(
            "la fuente está dentro de la copia del proyecto; se borraría al reimportar"
        )
    dest.parent.mkdir(parents=True, exist_ok=True)
    files: list[SourceFile] = []
    skipped: list[Skipped] = []
    seen_paths: set[str] = set()
    total = 0
    with tempfile.TemporaryDirectory(dir=dest.parent) as tmp:
        staged = Path(tmp) / "snapshot"
        staged.mkdir()
        for raw, data, reason in _entries(src, limits, staged):
            rel = safe_relpath(raw)
            path_key = rel if rel is not None else raw
            if path_key in seen_paths:
                raise ImportError_(f"ruta duplicada: {raw}")
            seen_paths.add(path_key)
            if data is None or rel is None:
                skipped.append(Skipped(path=raw, reason=reason or "ruta insegura"))
                continue
            # "._x" son metadatos AppleDouble que macOS añade al comprimir, no código
            if PurePosixPath(rel).name.startswith("._"):
                skipped.append(
                    Skipped(path=rel, reason="metadatos auxiliares de macOS; no son código fuente")
                )
                continue
            if any(part in EXCLUDED_DIRS for part in rel.split("/")):
                skipped.append(Skipped(path=rel, reason="directorio excluido"))
                continue
            total += len(data)
            if len(files) + 1 > limits.max_files:
                raise ImportError_(f"más de {limits.max_files} archivos")
            if total > limits.max_total_bytes:
                raise ImportError_(f"más de {limits.max_total_bytes} bytes en total")
            suffix = PurePosixPath(rel).suffix.lower()
            kind = KIND_BY_SUFFIX.get(suffix, FileKind.OTHER)
            if suffix == ".txt" and looks_like_sas(
                data.decode(detect_encoding(data) or "utf-8", errors="replace")
            ):
                kind = FileKind.SAS
            target = staged / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            files.append(
                SourceFile(
                    path=rel,
                    sha256=hashlib.sha256(data).hexdigest(),
                    size=len(data),
                    kind=kind,
                    encoding=detect_encoding(data) if kind in TEXT_KINDS else None,
                )
            )
        backup = Path(tmp) / "previous"
        if dest.exists() or dest.is_symlink():
            dest.rename(backup)
        try:
            staged.rename(dest)
        except OSError:
            if backup.exists():
                backup.rename(dest)
            raise
    return sorted(files, key=lambda f: f.path), skipped
