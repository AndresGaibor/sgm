# Reparto del plan maestro entre Andres y Byron

Fecha: 6 de noviembre de 2026. Es una **propuesta** de reparto del trabajo que queda de
`plan-migrador-general.md` (719,25 h de agente de las 895 totales; ver su sección 11b). Andres dirige
y Byron colabora. El corte busca dos mitades parecidas **y** dos zonas de código que casi no se pisan.

| | Andres | Byron |
|---|---|---|
| Carril | Pasos, plan lógico, arquitectura de Jobs y emisor | Expresiones, entrada y salida, procedimientos, macros, verificación y seguridad |
| Fases | P1, P4, P5, P8, P9, P14 | P0 (resto), P2, P3, P6, P7, P10, P11, P12, P13 |
| Horas que faltan | **359,0 h** (49,9 %) | **360,25 h** (50,1 %) |
| Horas totales del carril | 458 h, avance 21,6 % | 437 h, avance 17,6 % |

## 0. Antes de repartir: la rama de Byron en el remoto no está integrada

`origin/main` tiene 14 commits de Byron (`hito 20` a `hito 33`, del 3 de noviembre) sobre el hito 19 del
2 de noviembre. El `main` local lleva 144 commits desde ese punto. Por eso **no se puede subir con un
`git push` normal**: la rama divergió (`ahead 144, behind 14`). Hay dos conflictos que se resuelven
antes de repartir:

1. **Código.** Byron partió `expressions/talend_translator.py` en `talend_functions*.py`,
   `talend_lexer.py` y `talend_parser.py`, y arregló `INPUT`, `COMPRESS`, `SCAN` y `LIKE`. El `main`
   local hizo en paralelo `talend_funciones.py` y `talend_tabla.py`, con `COMPRESS` y `SCAN` también
   (hito 107). Es el mismo terreno con dos estructuras. Hay que decidir cuál sobrevive y portar las
   pruebas de Byron (`test_input_informat.py`, `test_talend_compress.py`, `test_talend_scan.py`,
   `test_talend_like.py`) al resultado.
2. **Numeración.** Sus hitos 20 a 33 chocan con los hitos 20 a 33 que ya existen en `PROGRESS.md`.
   Al integrarlos se renombran con la letra de su serie (`20n` a `33n`).

Esta integración es la **tarea 0**: la hace Byron, porque conoce su estructura, con Andres revisando.
No está en las 895 h; hay que estimarla al verla.

## 1. Reglas para no pisarse

- **Letra de serie en `PROGRESS.md` y en los commits.** Andres sigue con `m` (`hito 108m`...). Byron
  usa `n` (`hito 108n`...). Las letras no se reutilizan. `PROGRESS.md` solo se añade al final: si hay
  conflicto, se conservan las dos entradas.
- **Una rama por carril** (`carril-andres`, `carril-byron`) que se une a `main` con
  `git pull --rebase` y commits pequeños, uno por hito. Nada de `push --force`.
- **Dueño de cada zona.** Quien no es dueño no edita la zona sin avisar; pide el cambio al dueño.

| Zona | Dueño |
|---|---|
| `src/sgm/ir/` (plan lógico: `models.py`, `lower*.py`), `src/sgm/passes/` | Andres |
| `src/sgm/talend_item/`, `src/sgm/proceso/`, `src/sgm/emit/`, `src/sgm/backend_talend/` | Andres |
| `src/sgm/expressions/`, `src/sgm/frontend/macros*.py`, `rules/sas/` | Byron |
| `src/sgm/frontend/` (resto: `datastep.py`, `sql*.py`, `steps*.py`) | Andres |
| `src/sgm/migrar/interprete.py` y `semantica.py` (anillo B) | Byron |
| `tests/corpus/` casos L0 a L2 y L4 a L6 | Byron |
| `tests/corpus/` casos L3 y L8 (SQL y totales) | Andres |
| `tools/corpus_*`, `tools/studio_salud.py`, `tools/ciclo_rapido.py`, `tests/studio/` | Byron |

- **Fronteras entre los dos carriles** (los dos puntos donde de verdad se tocan):
  1. *El plan lógico.* Andres define los operadores (`Operator`, `Graph`, `Plan` de `ir/models.py`).
     Si Byron necesita un operador nuevo o un parámetro, lo pide con un caso del corpus que lo exija;
     Andres lo añade con constructor y prueba, y el emisor lo traduce a Talend.
  2. *Las expresiones.* Byron expone una única entrada de traducción de expresiones. Andres la usa sin
     tocarla. Si una expresión no sale, Byron la arregla o la deja como pendiente con su motivo.
- **Studio es un solo recurso.** Antes de un lote C, correr `tools/studio_salud.py`. Avisar cuando se
  usa. No se ejecutan dos lotes a la vez sobre la misma instalación.
- **Mismo protocolo de cierre** que en la sección 13 de `plan-migrador-general.md`: `uv run pytest -q` y
  `uv run ruff check .` en verde, `PROGRESS.md`, commit local `hito N<letra>: ...`.

## 2. Tareas de Andres (359,0 h)

| Fase | Tareas | Horas que faltan | Por qué es de Andres |
|---|---|---|---|
| MG-P1 Modelo y plan lógico | 02 a 06 (tipos de esquema, 14 operadores, SQL a plan, DATA step a plan, PROC a plan) | 29,5 | Es el contrato entre los dos carriles; debe ir primero |
| MG-P4 DATA step | 01 a 09 (`MERGE`, `RETAIN`, `FIRST./LAST.`, `OUTPUT` múltiple, `ARRAY`) | 83 | Construye operadores y emisor |
| MG-P5 `PROC SQL` | 01 a 08 | 68 | Idem, sobre `sql_tree.py` |
| MG-P8 Planificador | 01 a 03, 05 a 07 (04 hecha) | 57 | Decide cómo se organizan los Jobs |
| MG-P9 Emisor | 01 a 10, incluido el joblet (`MG-P9-03`, el mayor riesgo técnico) | 81,5 | Plantillas, joblets y contextos en Studio |
| MG-P14 Producción | 01 a 11 (la parte de personas la lleva Andres con Negocio) | 40 | Responsable del piloto, de las decisiones `MG-D` y del corte |
| **Total** | | **359,0** | |

Orden sugerido: P1-02 a P1-06 y la investigación de joblets (`MG-P9-03`) desde el primer día; luego P5-01
a P5-03 y P4-01 a P4-05; luego P8 con P9; P14 al final. Compuertas que cierra: GM1, GM4 y GM7 a GM8.

## 3. Tareas de Byron (360,25 h)

| Fase | Tareas | Horas que faltan | Por qué es de Byron |
|---|---|---|---|
| Tarea 0 | Integrar la rama `origin/main` (sección 0) | por estimar | Conoce su estructura de expresiones |
| MG-P0 Preparación | 01, 04, 05, 06, 09 (renumeración, ciclo rápido, tablero, documento del IR, tiempo del lote) | 12 | Herramientas de verificación |
| MG-P2 Entrada y salida | 01 a 07 (`XLSX`, `INFILE/INPUT`, informats, `LIBNAME` a bases, `FILENAME`, `RSUBMIT`) | 38 | Lectores y escritores |
| MG-P3 Expresiones y funciones | 01 a 09 (fechas, `PRX`, `PROC FORMAT`, informats, vectores) | 65,5 | Ya trabajó `INPUT`, `COMPRESS`, `SCAN` y `LIKE` |
| MG-P6 Procedimientos | 01 a 07 (`SORT`, `FREQ`, `MEANS`, `TRANSPOSE`, `APPEND`) | 47,5 | Traducción de procedimientos |
| MG-P7 Macros | 01 a 07 | 60 | Frontend de macros y opciones de sistema |
| MG-P10 Verificación | 01 a 09 (intérprete B, casos L7 y L9, generador de SAS, `sgm cobertura`) | 62 | Es su tablero de calidad |
| MG-P11 Experiencia de uso | 01 a 06 (`sgm migrar` de carpeta, `cobertura.md`, mensajes) | 26 | Cara del producto |
| MG-P12 Rendimiento | 01 a 04 | 30 | Medición y escala |
| MG-P13 Seguridad | 01 a 05 (`MG-P13-02` es de persona: 0,5 día) | 19,25 | Auditoría independiente del emisor |
| **Total** (sin la tarea 0) | | **360,25** | |

Orden sugerido: tarea 0; luego P3-01 a P3-03 y P2-01 a P2-03 (alimentan a Andres); P10-01 al compás de lo
que Andres vaya añadiendo; P6 y P7 después; P11 a P13 al final.

## 4. Puntos de encuentro

| Cuándo | Qué se revisa |
|---|---|
| Fin de la tarea 0 | Un solo `main` con las dos líneas de trabajo y la suite en verde |
| Fin de `MG-P1` y `MG-P3-01` | GM1: el plan lógico se construye para el corpus `traducible` sin YAML |
| Cada viernes | Recalcular la fila de cada fase en la sección 11b y reportar el porcentaje |
| Fin de P4, P5, P6 y P7 | GM2 y GM3: `L0` a `L6` traducidos y verificados (B y C) |
| Fin de P8 y P9 | GM4: arquitectura por omisión, joblets o plan B, contextos y límites |
| Después | GM5 a GM8, con Andres al frente del piloto y Byron en la verificación nocturna |

## 5. Lo que este reparto no resuelve

- Los créditos de la sección 11b son un juicio; si Byron los discute, se corrige el número y no el método.
- La estimación de las dos mitades supone que las horas del plan son buenas. `MG-P9-03` (joblets) y la
  tarea 0 pueden mover el equilibrio; se revisa en el primer punto de encuentro.
- Las decisiones `MG-D01` a `MG-D11` y las tareas de personas de `MG-P14` dependen de Negocio y
  Tecnología; el reparto solo dice quién las lleva.
