# Design

## Context

`xdist` (`-n auto`, `-n 8` en `tools/ci.py`) reparte pruebas entre procesos. Una prueba con un `for`
de 190 programas (90 s) o de 101 casos (76 s) corre entera en un worker. Los demás terminan y esperan.
La fixture `migrados` es de sesión y vive por worker: cada caso se migra la primera vez que lo pide
ese worker.

## Goals / Non-Goals

**Goals:** repartir esas dos pruebas por caso sin cambiar lo que comprueban.

**Non-Goals:** caché en disco del plan del programa grande (cambio aparte, tras medir); tocar `src/`.

## Decisions

- `@pytest.mark.parametrize` por programa (`ids` = ruta relativa) y por caso (`ids` = nombre), igual
  que `test_ningun_operador_se_pierde`, que ya funciona así.
- La aserción global `con_pendientes == {nombre: lista[nombre]}` se divide en la del caso (si tiene
  pendiente real, está en la lista con el mismo código). La mitad inversa (nombre listado sin
  pendiente) ya la cubre `test_la_lista_no_tiene_casos_resueltos`.
- `tmp_path` por prueba sustituye al `tmp_path / str(posicion)`.

## Ingeniería

- Alternativas descartadas: `pytest-split` (dependencia nueva, fuera de la lista permitida);
  `--dist loadfile` (no divide un archivo); subir workers (medido en el hito 258m: no ayuda).
- Riesgos: más pruebas (~290) y más migraciones repetidas entre workers (cada uno migra los casos
  que le tocan; `migrados` ya hace eso hoy). Un programa grande tarda lo mismo que antes.
- Dependencias: ninguna. Frontera con `src/sgm/backend_talend/`: no se toca.

## Pruebas

- `uv run python -m pytest -q tests/unit/test_migrar_corpus_aceptacion.py` en verde, con el conteo de
  pruebas subiendo de 5 a unas 290.
- Mutación manual: quitar un caso de la lista y ver que falla solo la prueba de ese caso.
- Cierre: `uv run ruff check .` y `uv run python tools/ci.py` en verde; comparar con 202 s.

## Risks / Trade-offs

Si el tiempo no baja de forma apreciable, el cuello es el programa grande y no el reparto: se anota
en `PROGRESS.md` y se pasa a la caché.
