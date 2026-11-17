# Plan del día de Andres: dos changes en un solo hito, sin Studio y sin correr el corpus entero Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans. Los pasos de cada tarea están en el `tasks.md` de su change; este documento fija el orden, el corte de pruebas y el cierre único.

**Goal:** Dejar en un solo hito (un `tools/ci.py`, un commit) dos mejoras que aceleran todo lo demás: pruebas largas repartidas y B-7 cerrado con `LZ`, más el avance real en la tabla 11b.

**Architecture:** Un bloque por change, cada uno con sus pruebas dirigidas (segundos). La suite completa y el corpus se corren **una vez**, al final, en segundo plano.

**Tech Stack:** Python 3.12 (`uv`, pytest, ruff), OpenSpec 2.1.0.

**Spec:** `openspec/changes/paralelizar-pruebas-largas/` y `openspec/changes/cerrar-b7-lz-y-avance-real/`. El change `generar-cobertura-procedimientos` **no se hace**: lo supera `C-22` de Byron (`tools/cobertura_procs.py` genera `docs/cobertura-procedimientos.md`, que G-17 integra en `docs/cobertura.md`).

## Global Constraints

- Sin Studio ni `talend-mcp`. Pocos componentes. `LZ` es base de datos con datos de prueba inventados (`docs/BLOQUEOS.md`, decisiones del 17 de noviembre).
- **Una sola entrada de `PROGRESS.md` y un solo commit** para los dos changes. El número de hito es **único en todo el repositorio**: se toma el último `## Hito` de `PROGRESS.md`, de cualquier serie, más uno (tras integrar a Byron el más alto es el 270n, así que el siguiente es el 271). En cada `tasks.md`, los pasos «Documentación» y «Cierre» **no se hacen por separado**: se hacen una vez, en el bloque 3 de este plan.
- Durante los bloques 1 y 2 solo se corre el archivo o el `-k` que dice el paso. Prohibido: `pytest` sin ruta, `tests/unit` entero, el corpus entero, `tools/ci.py`.
- El gancho `pre-commit` rechaza el commit si el árbol (contenido o estado de git) cambia después del cierre verde: `git add` y `PROGRESS.md` van **antes** de `tools/ci.py`.
- Si un resultado no coincide con el «Esperado», **parar y reportar**.

## Review Focus

- Un bloque que deja el árbol en rojo contagia al siguiente: cada bloque termina con su prueba dirigida en verde.
- `env/engines.json` es global: declarar `LZ` puede mover otros casos; el paso 1.6 de B-7 lo comprueba y manda parar.
- La cola de pendientes de Studio (108 casos) no se toca hoy; ningún paso la vacía ni la cuenta como validada.
- Los tiempos son estimaciones del plan, no mediciones. La suite completa medida sobre el `main` integrado con Byron: 6262 pruebas, 235,75 s.

---

## Bloque 0: preparación (≈ 10 min)

- [ ] **0.1** `git pull --rebase` (ya integrado hasta el hito 270n) y `git status --short`. Esperado: solo documentos y `openspec/`; nada de `src/` modificado.
- [ ] **0.2** `grep -n "^## Hito" PROGRESS.md | sort -t' ' -k3 -n | tail -3`: confirmar el número libre (271 si nadie subió otro).
- [ ] **0.3** `openspec validate --all`. Esperado: válidos.

## Bloque 1: `paralelizar-pruebas-largas` (≈ 20 min)

- [ ] **1.1** Hacer las tareas 1.1 a 2.5 de `openspec/changes/paralelizar-pruebas-largas/tasks.md`. Dirigido: solo `tests/unit/test_migrar_corpus_aceptacion.py` con `-k` (2.4) y la mutación de 2.5.
- [ ] **1.2** Esperado: `ruff check` del archivo en verde y las pruebas dirigidas verdes.

## Bloque 2: `cerrar-b7-lz-y-avance-real` (≈ 25 min)

- [ ] **2.1** Hacer las tareas 1.1 a 2.3 de `openspec/changes/cerrar-b7-lz-y-avance-real/tasks.md`. Dirigido: `test_push_db.py`, `test_pendientes_sql_l1_l2.py` y el `-k` del paso 1.6. No se toca `src/`: el código de Byron ya pliega `LIBNAME`.
- [ ] **2.2** Esperado: `l2_16` con un solo componente (`tImpalaRow`) y el pendiente `P-CONEXION-BASE`; `tools/avance_creditos.py --verificar` en 0.

## Bloque 3: cierre único (≈ 10 min de trabajo y unos 4 de suite)

La huella del cierre (`tools/validacion.py`, `huella_arbol`) incluye el contenido de **cada** archivo cambiado (también `PROGRESS.md`) y su estado de git (` M` sin preparar y `M ` preparado dan huellas distintas). Por eso el orden es: primero todo lo que cambia el árbol, después `tools/ci.py`, y el commit sin tocar nada más.

- [ ] **3.1** `uv run ruff check .`. Esperado: `All checks passed!`.
- [ ] **3.2** `openspec validate --all`. Esperado: válidos.
- [ ] **3.3** Escribir **una** entrada `## Hito N m` en `PROGRESS.md`: qué hizo cada change, los tiempos de las dos pruebas largas **antes** (89,7 s y 76,0 s; suite completa 202 s antes de integrar a Byron y 235,75 s después de integrarlo), el avance antes (27,8 %) y después, y el supuesto `impala`. El tiempo de la suite **después** de este hito no se escribe aquí: se lee de `uv run python tools/validacion.py historial` y entra en el hito siguiente. No inventar el número.
- [ ] **3.4** `git add` de los archivos de los dos changes y `PROGRESS.md` (no `openspec/changes/`, `.claude/` ni `.agents/` salvo que el usuario lo pida).
- [ ] **3.5** `uv run python tools/ci.py` **en segundo plano** (`run_in_background`) y no tocar ningún archivo mientras corre. Esperado: verde. Si falla, arreglar, volver a preparar (`git add`) y repetir solo este paso.
- [ ] **3.6** `uv run python tools/validacion.py estado`. Esperado: validado sobre la huella actual. Commit inmediato `hito N: paralelizar pruebas largas y B-7 con LZ`, con la línea `Co-Authored-By` que corresponda y sin `--no-verify`.

## Después (si queda día)

- Lo que de verdad falta sin Studio para Andres está en `2026-11-17-andres-cola-sin-studio.md`: **C-1 a C-15 (SQL), F1 e I**. El plan B ya está citado casi entero en los hitos 201m a 255m.
- Byron: `2026-11-17-byron-cola-sin-studio.md`, por hito agrupado.

## Self-review

- Cobertura: los dos changes quedan en bloques con sus pasos y su prueba dirigida; el corpus entero solo corre dentro de `tools/ci.py`.
- Un cierre por hito, no uno por change.
- Riesgo que sigue abierto: si algo cambia entre 3.5 y 3.6 el gancho rechaza el commit y hay que repetir `tools/ci.py` (unos 4 minutos).
