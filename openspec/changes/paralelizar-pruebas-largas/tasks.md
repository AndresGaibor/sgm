# Tasks

> **Hito agrupado:** si se ejecuta dentro de `docs/superpowers/plans/2026-11-17-plan-del-dia.md`, las secciones
> «Documentación» y «Cierre» de abajo **no se hacen aquí**: se hacen una vez en el bloque 4 de ese plan.

**Reglas para quien ejecute esto (no negociables):**
- Solo se edita `tests/unit/test_migrar_corpus_aceptacion.py`, `PROGRESS.md` y este `tasks.md`
  (marcar `[x]`). Nada en `src/`, `rules/`, `tools/` ni otras pruebas.
- No se borra ni se relaja ninguna aserción ni el límite de 60 s.
- Comandos con `uv run python -m pytest` (no `uv run pytest`, lo bloquea el sistema).
- Si un resultado no coincide con el «Esperado», **para y reporta**; no improvises.

## 1. Línea base

- [ ] 1.1 **No corras la línea base**: ya está medida (17 de noviembre de 2026, suite completa de 202 s):
  `test_robustez_sobre_todo_el_repositorio` 89,7 s y `test_solo_los_casos_listados_tienen_pendientes` 76,0 s.
  Solo anota esos dos números en el hito. Ahorras unos 3 minutos.

## 2. Pruebas (en este orden)

- [ ] 2.1 Reemplazar la función `test_robustez_sobre_todo_el_repositorio` completa (hoy líneas 113-124; se busca por
  nombre porque las líneas se mueven) por exactamente esto:

```python
PROGRAMAS = sorted(FIXTURES.rglob("*.sas"))


def test_los_programas_de_referencia_siguen_en_el_repositorio():
    assert len(PROGRAMAS) >= 190, "los programas de referencia del repositorio desaparecieron"


@pytest.mark.parametrize(
    "programa", PROGRAMAS, ids=[p.relative_to(FIXTURES).as_posix() for p in PROGRAMAS]
)
def test_robustez_sobre_todo_el_repositorio(programa, tmp_path):
    inicio = time.perf_counter()
    resultado = migrar(programa, tmp_path / "salida")
    assert time.perf_counter() - inicio < 60, f"{programa} tardó más de un minuto"
    if resultado.fallo_seguridad is None and not resultado.hallazgos_seguridad:
        assert (resultado.carpeta / "pendientes.md").is_file(), programa
    else:
        assert not resultado.escritos, programa
```

- [ ] 2.2 Reemplazar la función `test_solo_los_casos_listados_tienen_pendientes` completa (hoy líneas 148-157) por
  exactamente esto:

```python
@pytest.mark.parametrize("caso", CASOS, ids=[caso.name for caso in CASOS])
def test_solo_los_casos_listados_tienen_pendientes(caso, migrados):
    reales = _reales(migrados(caso))
    if reales:
        assert _lista().get(caso.name) == reales[0].codigo
```

  La mitad inversa (un caso listado que ya no tiene pendientes) la sigue cubriendo
  `test_la_lista_no_tiene_casos_resueltos`; no se toca.
- [ ] 2.3 `uv run ruff check tests/unit/test_migrar_corpus_aceptacion.py` → `All checks passed!`.
  Si dice que `time` o algo queda sin usar, no lo quites: sigue usándose.
- [ ] 2.4 Comprobar que se recolectan sin correrlas (segundos):
  `uv run python -m pytest --collect-only -q tests/unit/test_migrar_corpus_aceptacion.py -p no:cacheprovider | tail -3`.
  Esperado: unas 290 pruebas (190 programas + 101 casos + el resto). Luego correr **solo dos de cada una**:
  `uv run python -m pytest -q tests/unit/test_migrar_corpus_aceptacion.py -k "los_programas_de_referencia or (robustez and 001) or (solo_los_casos and l0_01)" -p no:cacheprovider`
  (si algún `-k` no selecciona nada, mira los ids con la recolección anterior y ajusta). Esperado: `passed`.
  La corrida completa del archivo la hace `tools/ci.py` una sola vez, al cierre.
- [ ] 2.5 Mutación (y se revierte): borrar **una** línea de entrada de
  `tests/corpus/migrar_pendientes.yaml`, correr
  `uv run python -m pytest -q tests/unit/test_migrar_corpus_aceptacion.py -k solo_los_casos`.
  Esperado: falla **una sola** prueba, con el nombre del caso en el id. Revertir con
  `git checkout tests/corpus/migrar_pendientes.yaml` y comprobar que `git status` ya no lo lista.

## 3. Documentación

- [ ] 3.1 Buscar el último `## Hito` de `PROGRESS.md` (`grep -n "^## Hito" PROGRESS.md | tail -3`).
  Si el último es 259m, el nuevo es **260m**; si no, suma uno. Añadir la entrada con: fecha, qué se
  hizo, tiempo antes/después de este archivo y de la suite completa, pruebas.

## 4. Cierre

- [ ] 4.1 `uv run ruff check .` → `All checks passed!`.
- [ ] 4.2 `uv run python tools/ci.py` → verde. Anotar el tiempo de la suite completa en la entrada
  del hito (referencia: 202 s antes del cambio).
- [ ] 4.3 `git add tests/unit/test_migrar_corpus_aceptacion.py PROGRESS.md` y commit con el mensaje
  `hito 260m: paraleliza las pruebas largas del corpus`. No incluir `openspec/changes/` ni `.claude/`.
