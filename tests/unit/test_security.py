import re
import zipfile
from pathlib import Path

from sgm.redaction import redact, redact_other, redact_sas

SRC = """libname ora oracle user=scott password="Tiger123" path=PRODDB;
libname d2 db2 user=u pw=Sekret9 database=S;
%let dbpass = TopSecret77;
%let anio = 2025;
proc sql;
  connect to oracle (user=scott password='Tiger123' path=PRODDB);
quit;
data work.y; set ora.t; if pw = 5 then x = 1; run;
"""


def test_redact_sas_masks_credentials_only():
    out = redact_sas(SRC)
    for secret in ("Tiger123", "Sekret9", "TopSecret77"):
        assert secret not in out
    assert "user=scott" in out and "path=PRODDB" in out and "%let anio = 2025" in out
    assert "if pw = 5" in out  # lógica de datos intacta
    assert out.count("\n") == SRC.count("\n")


def test_redact_pwencode_literal_but_not_a_macro_variable():
    """`proc pwencode in='clave'` lleva la clave en texto claro: tampoco puede llegar a ningún análisis."""
    source = "proc pwencode in='Cl4veSecreta*9';\nrun;\nproc pwencode in=&clave;\nrun;\n"
    out = redact_sas(source)

    assert "Cl4veSecreta" not in out
    assert "in=***" in out
    assert "in=&clave" in out  # una macrovariable no es un secreto
    assert out.count("\n") == source.count("\n")


def test_redact_shell_and_dispatch():
    sh = 'export DB_PASSWORD="abc"\nsasgsub -password xyz -sysin a.sas\nAPI_TOKEN=t0k\n'
    out = redact_other(sh)
    assert "abc" not in out and "xyz" not in out and "t0k" not in out
    assert redact("x.sh", "x.sh") == "x.sh" and "***" in redact("libname a db2 pw=a;", "k.sas")




ROOT = Path(__file__).resolve().parents[2]
PWENCODE_STATEMENT = re.compile(r"(?i)proc\s+pwencode\b[^;]*")
PWENCODE_MASKED = re.compile(r"(?i)proc\s+pwencode\s+in\s*=\s*'\*\*\*'")
TEXT_SUFFIXES = {".sas", ".txt", ".sh", ".md", ".json", ".log", ".csv"}


def _text_blobs():
    """Texto de cada fixture y de cada miembro de texto de los ZIP, y de la salida `out/` si existe."""
    for path in sorted((ROOT / "tests").rglob("*")):
        if path.suffix.lower() in TEXT_SUFFIXES and path.is_file():
            yield path.relative_to(ROOT).as_posix(), path.read_text(encoding="utf-8", errors="replace")
        elif path.suffix.lower() == ".zip" and path.is_file():
            with zipfile.ZipFile(path) as archive:
                for member in archive.namelist():
                    if Path(member).suffix.lower() in TEXT_SUFFIXES:
                        blob = archive.read(member).decode("utf-8", errors="replace")
                        yield f"{path.name}!{member}", blob
    out = ROOT / "out"
    if out.exists():
        for path in sorted(out.rglob("*")):
            if path.is_file() and path.suffix.lower() in TEXT_SUFFIXES:
                yield path.relative_to(ROOT).as_posix(), path.read_text(encoding="utf-8", errors="replace")


def test_pwencode_en_fixtures_y_salidas_solo_con_asteriscos():
    """Un `proc pwencode` con cualquier valor distinto de '***' es una contraseña en claro: falla."""
    bad = []
    for name, text in _text_blobs():
        for match in PWENCODE_STATEMENT.finditer(text):
            if not PWENCODE_MASKED.fullmatch(match.group(0).strip()):
                bad.append(f"{name}: {text.count(chr(10), 0, match.start()) + 1}")
    assert not bad, "pwencode sin enmascarar (usar in='***'): " + ", ".join(bad)
