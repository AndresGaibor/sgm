# MG-P7-01: `%SYSFUNC(UPCASE())` — plan de implementación

> **Para agentes de implementación:** SUBHABILIDAD OBLIGATORIA: usar `superpowers:executing-plans` para implementar este plan tarea por tarea. Los pasos usan casillas (`- [ ]`) para seguir el avance.

**Objetivo:** Expandir un `%SYSFUNC(UPCASE(...))` constante y documentado dentro de `%LET`, para que la macrovariable del caso L5-06 produzca los nombres de tabla esperados en mayúsculas.

**Arquitectura:** La evaluación se mantiene en el frontend de macros existente. Primero se sustituyen las macrovariables conocidas y luego se aplica un evaluador estático estrecho para `UPCASE` de un argumento ASCII; toda otra forma incierta conserva la ruta actual de `MacroDynamic`. La prueba recorre `analyze_program` sobre el SAS real del caso L5-06.

**Tecnologías:** Python 3, dataclasses del frontend actual, pytest y Ruff; sin dependencias nuevas.

**Diseño:** `docs/superpowers/specs/2026-11-09-mg-p7-01-sysfunc-upcase-design.md`

## Restricciones globales

- No agregar dependencias fuera de `networkx`, `typer`, `pyyaml`, `pydantic` opcional; desarrollo usa `pytest`, `pytest-xdist` y `ruff`.
- Código e identificadores en inglés; comentarios, docstrings, mensajes al usuario y documentación en español.
- No inventar equivalencias SAS: una llamada no admitida o no constante queda pendiente con su texto y motivo.
- No modificar `migrador-sasgrid-qlik`, conectarse a bases, agregar API web/frontend ni hacer push a GitHub.
- Cerrar el hito solo si pasan `uv run python -m pytest -q` y `uv run ruff check .`; registrarlo en `PROGRESS.md` y hacer un commit local con `hito 125: <resumen>`.

## Revisión prioritaria

1. Un valor de macro conocido con letras ASCII en minúscula debe pasar a mayúsculas y llegar al nombre del dataset; se fija con la regresión del frontend para L5-06.
2. Una referencia de macro sin resolver dentro de `UPCASE` no debe parecer constante; se fija con una aserción de `MacroDynamic`.
3. Una entrada no ASCII, incluidas letras Unicode que Python puede confundir con ASCII al ignorar mayúsculas, queda dinámica hasta probar su comportamiento según la codificación SAS; se fija con aserciones de `MacroDynamic`.
4. Un formato de `%SYSFUNC` o argumentos mal formados/múltiples no debe aceptarse como la forma de un argumento; se fija con casos de fallback dinámico.
5. Otra función, como `TODAY` o `LOWCASE`, permanece dinámica; se conserva o amplía la regresión dinámica `%SYSFUNC` existente.

## Archivos y responsabilidades

- `src/sgm/frontend/macros.py`: sustituir variables conocidas, reconocer la forma estática acotada y conservar el fallback dinámico actual.
- `tests/unit/test_macros.py`: regresiones unitarias positivas y negativas para los límites del evaluador.
- `tests/unit/test_corpus_l4l6.py`: ejecutar el SAS L5-06 real mediante `analyze_program` y comprobar los nombres expandidos del SQL.
- `rules/sas/catalogo/funciones-macro.yaml`: describir la cobertura acotada de `%SYSFUNC` y el comportamiento dinámico restante.
- `docs/plan-reescritura/plan-migrador-general.md`: registrar MG-P7-01 como avance parcial medido, no como tarea terminada.
- `PROGRESS.md`: documentar hito 125, decisiones, verificaciones, métricas y brechas de P7-01 aún abiertas.

## Task 1: evaluar la forma documentada de `UPCASE` constante

**Interfaz:** `_static_sysfunc(text: str) -> str | None` recibe la expresión `%SYSFUNC` después de sustituir las macrovariables conocidas. Devuelve el valor en mayúsculas solo para la forma admitida de `UPCASE` con un identificador ASCII simple; `None` significa conservar la llamada como dinámica.

- [x] **Paso 1: agregar la regresión positiva del frontend de producción.** En `tests/unit/test_corpus_l4l6.py`, analizar `tests/corpus/L5/l5_06_sysfunc_upcase/programa.sas` con `analyze_program`; comprobar que no hay elementos `MacroDynamic` y que el texto de las sentencias `ProcSql.statements` expandió `RES_LEALTAD` y `DATOS_LEALTAD`.
- [x] **Paso 2: agregar regresiones de límites.** En `tests/unit/test_macros.py`, cubrir argumento sin resolver, no ASCII y cuatro letras Unicode confundibles, formato opcional, argumentos mal formados/múltiples, otra función y opciones `TRANTAB`/`ENCODING`/`LOCALE`; las formas inciertas siguen como `MacroDynamic`. También se comprueba que `OPTIONS NODATE` no bloquee la expansión y que opciones macro dinámicas sí la bloqueen.
- [x] **Paso 3: ejecutar la regresión positiva y confirmar RED.** Ejecutar `uv run python -m pytest tests/unit/test_corpus_l4l6.py::test_l5_06_sysfunc_upcase_expands_in_frontend -q`; falló porque `%SYSFUNC` dentro de `%LET` quedaba dinámico.
- [x] **Paso 4: implementar el evaluador mínimo.** En `%LET`, sustituir primero las macrovariables conocidas; evaluar con modo ASCII solo la forma permitida. Antes de guardar el resultado, si alguna fuente declara `OPTIONS TRANTAB/ENCODING/LOCALE` o una opción dinámica, conservar `MacroDynamic` y dejar desconocida la macrovariable asignada. No usar `eval` de Python ni evaluar otra función SAS.
- [x] **Paso 5: ejecutar regresiones focales.** `uv run python -m pytest tests/unit/test_macros.py tests/unit/test_corpus_l4l6.py -q`: 154 pasaron y 25 se omitieron; incluye opciones explícitas/dinámicas y aserción sensible a mayúsculas.
- [x] **Paso 6: actualizar catálogo y avance.** El catálogo especifica el subconjunto estático y las dependencias `TRANTAB`/`ENCODING`/`LOCALE`; MG-P7-01 queda parcial, con crédito 0,25. Los valores externos de sesión no se infieren.
- [x] **Paso 7: verificar el estado final.** `uv run python -m pytest -q`: 2601 passed, 26 skipped, 144 xfailed; `uv run ruff check .`: limpio; `uv run python -m sgm.cli rules validate`: válido; `git -c core.whitespace=cr-at-eol diff --check`: limpio. Suite focal: 154 passed, 25 skipped.
- [x] **Paso 8: hacer commit local del hito.** Agregar diseño, plan, implementación, pruebas, catálogo, estado del plan maestro y `PROGRESS.md`; el commit local se registrará como `hito 125: expandir SYSFUNC UPCASE constante`. No hacer push.

## Autorrevisión

- Cobertura del diseño: evaluar `UPCASE` ASCII constante, fallback seguro de las formas no admitidas/dinámicas, análisis integrado de L5-06, documentación, medición y commit local están asignados arriba.
- Granularidad: agregar pruebas, observar RED, implementar, ejecutar pruebas focales, actualizar estado, verificar la suite completa y hacer commit son pasos con resultados observables.
- Consistencia de tipos: la firma del evaluador se usa desde `_let`; `None` es la señal explícita para usar el fallback.
- Revisión prioritaria: valores no constantes, entradas Unicode confusables, opciones relevantes, formatos, argumentos mal formados y funciones no admitidas cuentan con regresiones explícitas en los pasos 1 y 2.
- Proporción: una tarea de implementación coincide con el incremento de una función aprobado en el diseño; no declara MG-P7-01 terminada.
