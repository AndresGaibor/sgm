# Tasks

**Reglas (no negociables):** sin Studio ni `talend-mcp`; `uv run python -m pytest` (no `uv run pytest`);
no borrar ni relajar pruebas; si un resultado no coincide con el «Esperado», **para y reporta**.
**Ciclo rápido:** corre solo la prueba que dice cada paso, nunca `tests/unit` entero ni el corpus
entero; `tools/ci.py` se corre una vez, al cierre del hito.

## 1. B-7: LZ como base de datos

Estado verificado el 17 de noviembre de 2026 sobre `main` ya integrado con la serie de Byron: con
`library_engines={"LZ": "impala"}` y `push_to_db`, `l2_16` queda como **un** componente (`tImpalaRow`) y **un**
pendiente, `P-CONEXION-BASE` («configure en Studio el host, puerto, base»). La sentencia `LIBNAME` ya no es
pendiente: Byron la pliega (`_libname_registrado` en `src/sgm/talend_item/desde_plan.py`). Sin `LZ` declarada
siguen 3 pendientes `P-OPERADOR-SIN-SOPORTE`. El host y el puerto son configuración que no se inventa, igual
que en `l0_16_paso_directo_impala`, que ya está en la lista con `P-CONEXION-BASE`. **No hay que tocar `src/`.**

- [ ] 1.1 `uv run python -m pytest -q tests/unit/test_push_db.py tests/unit/test_pendientes_sql_l1_l2.py -p no:cacheprovider`.
  Esperado: verde (línea base).
- [ ] 1.2 En `env/engines.json` cambiar `"libraries": {}` por `"libraries": { "LZ": "impala" }`. No tocar el resto.
- [ ] 1.3 `uv run python -m sgm.cli migrar tests/corpus/L2/l2_16_sql_en_misma_base/programa.sas --out "$TEMP/l216"` y
  leer `$TEMP/l216/programa/pendientes.md`. Esperado: **un solo pendiente**, `P-CONEXION-BASE`. Si hay otro código,
  **parar y reportar** con el contenido del archivo.
- [ ] 1.4 En `tests/corpus/migrar_pendientes.yaml` cambiar la línea
  `l2_16_sql_en_misma_base: P-OPERADOR-SIN-SOPORTE` por `l2_16_sql_en_misma_base: P-CONEXION-BASE`.
- [ ] 1.5 En `tests/unit/test_pendientes_sql_l1_l2.py` cambiar la clave de `CLASIFICACION` a
  `("l2_16_sql_en_misma_base", "P-CONEXION-BASE")` con el valor
  `("entorno", "LZ es una base declarada en env/engines.json; el host y el puerto se configuran en Studio")` y
  reemplazar el comentario de arriba («Decisión pendiente del dueño…») por «Decidido el 17 de noviembre de 2026:
  `LZ` es una base de datos (docs/BLOQUEOS.md, B-7)».
- [ ] 1.6 `uv run python -m pytest -q tests/unit/test_push_db.py tests/unit/test_pendientes_sql_l1_l2.py -p no:cacheprovider`
  y `uv run python -m pytest -q tests/unit/test_migrar_corpus_aceptacion.py -k "solo_los_casos or la_lista_no_tiene" -p no:cacheprovider`.
  Esperado: verde. Si `test_la_lista_no_tiene_casos_resueltos` o `test_solo_los_casos...` fallan por otro caso,
  **parar y reportar**: `engines.json` es global y podría cambiar otros casos que usen `LZ`
  (`grep -l "LZ" tests/corpus/*/*/programa.sas`).

## 2. Avance real

- [ ] 2.1 Leer `docs/plan-reescritura/creditos.yaml` (fases P11, P12, P13) y las entradas 132 a 136 de
  `PROGRESS.md` (`grep -n "^## Hito 13[2-6]" PROGRESS.md`).
- [ ] 2.2 Hoy el YAML da 27,8 % (Byron ya acreditó P2 y P3 hasta el hito 269n). Siguen sin acreditar: P6 (`PROC APPEND`,
  limpiezas y copias: hitos 242n a 246n, `C-20` y `C-21`), P11 (carpetas y cobertura por programa, hito 132), P12
  (medición de `migrar`, hito 133) y P13 (`sgm secretos` integrado, identificadores hostiles, SBOM: hitos 134 a 136). Subir el crédito de esas fases con el método de la sección 11b del plan
  (1 / 0,5 / 0,25 / 0). En `sostiene` de cada fase escribir el hito que lo respalda. No tocar otras
  fases sin evidencia.
- [ ] 2.3 `uv run python tools/avance_creditos.py --actualizar` (existe `--actualizar`: escribe la tabla en
  la sección 11b entre `<!-- avance:inicio -->` y `<!-- avance:fin -->`) y luego
  `uv run python tools/avance_creditos.py --verificar`. Esperado: sale 0. Actualizar a mano la fecha del
  encabezado de 11b.

## 3. Documentación

- [ ] 3.1 Entrada del hito en `PROGRESS.md` (se agrupa con los otros changes del día, ver
  `docs/superpowers/plans/2026-11-17-plan-del-dia.md`): qué se hizo, el avance antes (27,8 %) y después,
  y el motor `impala` como supuesto.

## 4. Cierre (una sola vez para todo el hito del día)

- [ ] 4.1 `openspec validate cerrar-b7-lz-y-avance-real` en verde.
- [ ] 4.2 `uv run ruff check .` y `uv run python tools/ci.py` (ver el plan del día).
