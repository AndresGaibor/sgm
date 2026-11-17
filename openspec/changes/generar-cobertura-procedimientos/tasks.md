> **SUPERADO (17 de noviembre de 2026, tras integrar la serie de Byron):** la tarea `C-22` de
> `docs/superpowers/plans/2026-11-11-mg-c-sql-y-procedimientos.md` (carril de Byron) crea
> `tools/cobertura_procs.py` y genera el mismo documento de cobertura con los 77 procedimientos de la guía,
> no solo con las 9 entradas de `procs-usados.yaml`. Dos herramientas escribiendo `docs/cobertura.md`
> chocarían. **No ejecutar este change**; si `C-22` queda corta, se archiva sin aplicar. Sus 8 pruebas (en
> `tasks.md`) se pueden reutilizar como punto de partida de `C-22`.

## 0. Reglas para quien ejecute esto

> **Hito agrupado:** si se ejecuta dentro de `docs/superpowers/plans/2026-11-17-plan-del-dia.md`, los pasos 3.3 y
> la sección 4 de abajo **no se hacen aquí**: se hacen una vez en el bloque 4 de ese plan. Ciclo rápido: solo
> `tests/unit/test_generar_cobertura.py`, nunca la suite completa.

- Solo se crean `tools/generar_cobertura.py`, `tests/unit/test_generar_cobertura.py` y `docs/cobertura.md`, y se edita `PROGRESS.md`. Nada en `src/`, `rules/` ni `tools/ci.py`.
- Sin Studio ni `talend-mcp`. Comandos con `uv run python -m pytest` (no `uv run pytest`).
- Si un resultado no coincide con el «Esperado», **parar y reportar**.
- El catálogo real tiene 9 entradas: 2 `reconocida` (`sql`, `sort`) y 7 `no_verificada`.

## 1. Pruebas (primero, con TDD)

- [ ] 1.1 Crear `tests/unit/test_generar_cobertura.py` con exactamente este contenido:

```python
"""Pruebas de tools/generar_cobertura.py: docs/cobertura.md sale del catálogo de procedimientos."""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))

import generar_cobertura as gc  # noqa: E402

ENTRADAS = [
    {"id": "sql", "nombre": "PROC SQL", "fuente": "sqlproc.pdf, p. 269", "estado": "reconocida", "nota": "ok"},
    {"id": "delete", "nombre": "PROC DELETE", "fuente": "proc.pdf, p. 837", "estado": "no_verificada", "nota": "limpieza"},
    {"id": "contents", "nombre": "PROC CONTENTS", "fuente": "proc.pdf, p. 541", "estado": "no_verificada"},
]


def test_solo_las_no_reconocidas_en_el_orden_del_catalogo():
    assert [f["nombre"] for f in gc.filas(ENTRADAS)] == ["PROC DELETE", "PROC CONTENTS"]


def test_la_entrada_sin_nota_deja_el_motivo_vacio():
    assert gc.filas(ENTRADAS)[1]["nota"] == ""


def test_catalogo_sin_pendientes_no_tiene_filas_y_lo_dice():
    todas = [{**e, "estado": "reconocida"} for e in ENTRADAS]
    texto = gc.markdown(gc.filas(todas))
    assert gc.filas(todas) == []
    assert "No hay procedimientos sin tratamiento." in texto
    assert "| PROC" not in texto


def test_la_nota_con_barra_vertical_no_rompe_la_tabla():
    filas = [{"nombre": "PROC X", "fuente": "proc.pdf, p. 1", "estado": "no_verificada", "nota": "a|b"}]
    assert "a\\|b" in gc.markdown(filas)


def test_el_estado_se_imprime_tal_cual_y_el_aviso_nombra_el_programa_grande():
    texto = gc.markdown(gc.filas(ENTRADAS))
    assert "| PROC DELETE | proc.pdf, p. 837 | no_verificada | limpieza |" in texto
    assert "`client_large.sas`" in texto


def test_dos_generaciones_son_identicas():
    assert gc.markdown(gc.filas(ENTRADAS)) == gc.markdown(gc.filas(ENTRADAS))


def _catalogo(tmp_path: Path) -> Path:
    ruta = tmp_path / "procs.yaml"
    ruta.write_text(
        "id: x\nkind: catalogo\nversion: 1\ndescription: x\nentries:\n"
        "- {id: a, nombre: PROC A, fuente: 'proc.pdf, p. 1', estado: no_verificada, nota: n}\n",
        encoding="utf-8",
    )
    return ruta


def test_verificar_sale_0_con_el_documento_al_dia_y_no_escribe(tmp_path):
    catalogo, salida = _catalogo(tmp_path), tmp_path / "cobertura.md"
    assert gc._principal(["--catalogo", str(catalogo), "--salida", str(salida)]) == 0
    antes = salida.read_bytes()
    assert gc._principal(["--verificar", "--catalogo", str(catalogo), "--salida", str(salida)]) == 0
    assert salida.read_bytes() == antes


def test_verificar_sale_distinto_de_0_con_el_documento_viejo_y_no_escribe(tmp_path):
    catalogo, salida = _catalogo(tmp_path), tmp_path / "cobertura.md"
    salida.write_text("viejo\n", encoding="utf-8")
    assert gc._principal(["--verificar", "--catalogo", str(catalogo), "--salida", str(salida)] ) != 0
    assert salida.read_text(encoding="utf-8") == "viejo\n"
```

- [ ] 1.2 Correr `uv run python -m pytest -q tests/unit/test_generar_cobertura.py -p no:cacheprovider`.
  Esperado: error de colección `ModuleNotFoundError: No module named 'generar_cobertura'`.

## 2. Implementación

- [ ] 2.1 Crear `tools/generar_cobertura.py` con estas firmas (el cuerpo lo escribe quien ejecute):
  - Docstring de módulo en español: «Documento `docs/cobertura.md` generado desde `rules/sas/catalogo/procs-usados.yaml` (MG-P6-06).» y la línea de uso `uv run python tools/generar_cobertura.py [--verificar]`.
  - Constantes `RAIZ = Path(__file__).resolve().parents[1]`, `CATALOGO = RAIZ / "rules" / "sas" / "catalogo" / "procs-usados.yaml"`, `SALIDA = RAIZ / "docs" / "cobertura.md"`.
  - `def filas(entradas: list[dict]) -> list[dict]`: las de `estado != "reconocida"`, en el mismo orden, cada una como `{"nombre","fuente","estado","nota"}` con `nota` igual a `""` si falta. No cambia ningún valor.
  - `def markdown(filas: list[dict]) -> str`: `# Cobertura de procedimientos SAS`, una línea de aviso que contenga «El catálogo solo cubre `client_large.sas`.», y la tabla `| Procedimiento | Fuente | Estado | Motivo |` con una fila `| {nombre} | {fuente} | {estado} | {nota} |` por entrada; en `nota` se escapa `|` como `\|` y los saltos de línea pasan a espacio. Sin filas, en lugar de la tabla, la línea `No hay procedimientos sin tratamiento.` Termina en un solo `\n`.
  - `def _generar(catalogo: Path) -> str`: lee el YAML con `yaml.safe_load`, toma `entries` y devuelve `markdown(filas(entries))`.
  - `def _principal(argv: list[str] | None = None) -> int` con `argparse`: `--verificar`, `--catalogo` (por omisión `CATALOGO`), `--salida` (por omisión `SALIDA`). Sin `--verificar`: escribe con `salida.write_text(texto, encoding="utf-8", newline="\n")`, imprime la ruta y devuelve 0. Con `--verificar`: lee los bytes del archivo (vacío si no existe), compara con `texto.encode("utf-8")`, imprime «docs/cobertura.md al día» o «docs/cobertura.md desactualizado: corre `uv run python tools/generar_cobertura.py`» y devuelve 0 o 1. Nunca escribe en modo verificación.
  - Cierre del archivo: `if __name__ == "__main__": sys.exit(_principal())`.
- [ ] 2.2 Correr las pruebas de 1.1. Esperado: `8 passed`. Si falla `test_el_estado_se_imprime_tal_cual...`, comparar contra el formato exacto de fila de 2.1.
- [ ] 2.3 `uv run ruff check tools/generar_cobertura.py tests/unit/test_generar_cobertura.py`. Esperado: `All checks passed!`. Si dice `E501` en las líneas largas de la prueba, partirlas; no desactivar la regla.

## 3. Documentación

- [ ] 3.1 `uv run python tools/generar_cobertura.py`. Esperado: escribe `docs/cobertura.md`. Comprobar a ojo que tiene el aviso de `client_large.sas` y **7 filas** (`PROC DELETE`, `PROC CONTENTS`, `PROC UPLOAD`, `PROC EXPORT`, `PROC IMPORT` y las dos que siguen en el catálogo).
- [ ] 3.2 `uv run python tools/generar_cobertura.py --verificar`. Esperado: «al día» y código de salida 0 (`echo $?`).
- [ ] 3.3 Añadir en `PROGRESS.md` el hito (último `## Hito` más uno, letra `m`): qué se hizo, la decisión «el estado `no_verificada` se muestra sin reclasificar», y las 7 filas.

## 4. Cierre

- [ ] 4.1 `uv run ruff check .` en verde.
- [ ] 4.2 `openspec validate generar-cobertura-procedimientos` en verde.
- [ ] 4.3 `uv run python tools/ci.py` en verde.
- [ ] 4.4 Commit `hito N: genera docs/cobertura.md desde el catálogo de procedimientos` con solo los cuatro archivos.
