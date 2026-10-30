import hashlib
import stat
import zipfile
from pathlib import Path

import pytest

from sgm.ingest.importer import (
    ImportError_,
    import_source,
    looks_like_sas,
    safe_relpath,
)
from sgm.ingest.limits import ImportLimits

ROOT = Path(__file__).parent.parent.parent
FIXTURES = ROOT / "tests" / "fixtures" / "sas"


def cfg(tmp_path, **kw) -> ImportLimits:
    return ImportLimits(**kw)


@pytest.mark.parametrize("bad", ["../x.sas", "/etc/passwd", "a/../../x", "C:\\x.sas", "a\0b", ""])
def test_safe_relpath_rejects(bad):
    assert safe_relpath(bad) is None


def test_safe_relpath_normalizes():
    assert safe_relpath("a\\b/./c.sas") == "a/b/c.sas"


def test_folder_import_hashes_and_skips(tmp_path):
    src = tmp_path / "src"
    (src / ".git").mkdir(parents=True)
    (src / ".git" / "config").write_text("x")
    (src / "a.sas").write_bytes("data x; run; /* ñ */".encode("cp1252"))
    (src / "big.sas").write_bytes(b"x" * 50)
    try:
        (src / "link.sas").symlink_to(src / "a.sas")
    except OSError as exc:
        pytest.skip(f"Windows no permite crear symlinks en este entorno: {exc}")
    files, skipped = import_source(src, tmp_path / "dest", cfg(tmp_path, max_file_bytes=40))
    by = {f.path: f for f in files}
    assert set(by) == {"a.sas"}
    assert by["a.sas"].encoding == "cp1252"
    assert by["a.sas"].sha256 == hashlib.sha256((src / "a.sas").read_bytes()).hexdigest()
    assert {s.path: s.reason for s in skipped} == {
        "big.sas": "supera max_file_bytes",
        "link.sas": "enlace simbólico",
    }
    assert (tmp_path / "dest" / "a.sas").exists()


SAS_EN_TXT = """/* Etiqueta: Programa */
libname lib "/data/x";
%let anio = 2025;
data work.a; set lib.t; run;
proc sql; create table work.b as select * from work.a; quit;
"""


def test_a_txt_file_with_sas_code_is_imported_as_sas(tmp_path):
    """Los programas se entregan a veces como `.txt`: se reconocen por su contenido, no por la extension."""
    src = tmp_path / "src"
    src.mkdir()
    (src / "Cod1.txt").write_text(SAS_EN_TXT, encoding="utf-8")
    (src / "notas.txt").write_text(
        "Reunion del lunes.\nTema: data lake y proc de compras.\nrun de pruebas el viernes.\n",
        encoding="utf-8",
    )
    (src / "LEEME.md").write_text(SAS_EN_TXT, encoding="utf-8")

    files, _ = import_source(src, tmp_path / "dest", cfg(tmp_path))
    kinds = {f.path: f.kind.value for f in files}

    assert kinds == {"Cod1.txt": "sas", "notas.txt": "doc", "LEEME.md": "doc"}


def test_sas_is_recognised_by_content_even_after_an_invisible_character():
    """SAS Studio antepone U+200B al exportar; una nota cualquiera no es SAS."""
    assert looks_like_sas("\u200b" + SAS_EN_TXT)
    assert not looks_like_sas("Una nota cualquiera.\nSin codigo.\n")


def test_zip_slip_and_symlink_rejected(tmp_path):
    z = tmp_path / "b.zip"
    with zipfile.ZipFile(z, "w") as zf:
        zf.writestr("ok/p.sas", "data a; run;")
        zf.writestr("../evil.sas", "x")
        zf.writestr("/abs.sas", "x")
        info = zipfile.ZipInfo("lnk.sas")
        info.external_attr = (stat.S_IFLNK | 0o777) << 16
        zf.writestr(info, "/etc/passwd")
    files, skipped = import_source(z, tmp_path / "dest", cfg(tmp_path))
    assert [f.path for f in files] == ["ok/p.sas"]
    assert {s.reason for s in skipped} == {"ruta insegura", "enlace simbólico"}
    assert not (tmp_path / "evil.sas").exists()


def test_zip_bomb_entry_skipped(tmp_path):
    z = tmp_path / "b.zip"
    with zipfile.ZipFile(z, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("big.sas", "0" * 10_000)
    files, skipped = import_source(z, tmp_path / "dest", cfg(tmp_path, max_file_bytes=100))
    assert not files and skipped[0].reason == "supera max_file_bytes"


def test_zip_member_limit_rejects_archives_with_too_many_skipped_entries(tmp_path):
    z = tmp_path / "many-members.zip"
    with zipfile.ZipFile(z, "w") as archive:
        archive.writestr("../rejected-1.sas", "x")
        archive.writestr("../rejected-2.sas", "x")

    with pytest.raises(ImportError_, match="miembros ZIP"):
        import_source(z, tmp_path / "dest", cfg(tmp_path, max_zip_members=1))


def test_zip_appledouble_metadata_is_skipped(tmp_path):
    z = tmp_path / "mac.zip"
    with zipfile.ZipFile(z, "w") as zf:
        zf.writestr("daily.sas", "data x; run;")
        zf.writestr("._daily.sas", "metadata")
        zf.writestr("__MACOSX/._daily.sas", "metadata")
    files, skipped = import_source(z, tmp_path / "dest", cfg(tmp_path))
    assert [f.path for f in files] == ["daily.sas"]
    assert {s.path: s.reason for s in skipped} == {
        "._daily.sas": "metadatos auxiliares de macOS; no son código fuente",
        "__MACOSX/._daily.sas": "metadatos auxiliares de macOS; no son código fuente",
    }


def test_global_limits_reject_batch(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    for i in range(3):
        (src / f"{i}.sas").write_text("x")
    with pytest.raises(ImportError_):
        import_source(src, tmp_path / "dest", cfg(tmp_path, max_files=2))
    with pytest.raises(ImportError_):
        import_source(tmp_path / "nope", tmp_path / "dest", cfg(tmp_path))
