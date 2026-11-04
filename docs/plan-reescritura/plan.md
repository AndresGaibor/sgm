# Plan de reescritura: de agrupar operadores a un modelo de proceso

Meta del usuario (4 de noviembre de 2026): que la salida del migrador sea idéntica, o lo más parecida
posible, al diseño hecho a mano (`docs/diseno-talend-exogena-depositos.md`). Se autorizó rehacer o
borrar lo que haga falta, usar subagentes (con `model: "haiku"` para el trabajo mecánico) e investigar
en internet. Este documento reemplaza al plan que se discutió en la conversación y lleva el estado real.

## Por qué hoy no coincide

El generador anterior agrupa operadores SAS y llega a 388 componentes; el diseño manual describe
procesos de negocio en unos 80. Una mejora estructural más no cierra esa distancia: falta una capa que
entienda qué hace cada parte del programa. El destino (Talend, dbt, Python) no cambia la causa: sin
decidir cuáles tablas son persistencia y cuáles solo aristas, 400 tablas WORK dan cientos de pasos.

## Arquitectura nueva

1. **Frontend** (`frontend/`): lee el SAS y deja sentencias y hechos. Se conserva.
2. **Grafo de linaje de datasets** (`flow/model.py`, `flow/pasos_archivo.py`, `frontend/sql_fuentes.py`):
   cada dataset sabe quién lo escribe y quién lo lee.
3. **Modelo de proceso** (`proceso/`): regiones, familias por producto, fuentes y salidas, etapas,
   fontanería, pendientes con motivo. Es el centro nuevo.
4. **Emisores**: leen del modelo y no deciden nada: documento de diseño de ocho secciones, Job Script de
   Talend, mapa de flujo.

Lo que depende del nombre del cliente va a `decisiones/<programa>.*.yaml`, nunca a `src/` ni `rules/`.

## Estado por fase

| Fase | Qué es | Estado | Dónde |
|---|---|---|---|
| 0 | Medir y fijar la meta | **Hecha** (hito 50) | `fase0-*.md`, `tests/conformidad/` |
| 1 | Grafo de linaje | **Hecha, con pendientes** (hito 51) | ver abajo |
| 2 | Modelo de proceso | **En curso** (hitos 52 a 54) | `fase2-familias.md`, `src/sgm/proceso/` |
| 3 | Emisor del documento de diseño | **En curso** (hitos 55 y 56): secciones 1.1, 1.4 y 6 | `proceso/diseno_doc.py` |
| 4 | Joblets por sub-cadena compartida | Sin empezar | |
| 5 | Emisión de Jobs de Talend | **Empezada** (hitos 59 a 61): Jobs del diseño generados desde el modelo y validados ejecutando en Studio real; padre completo, hijos esqueleto | `fase5-talend-instalado.md`, `src/sgm/talend_item/` |
| 6 | Segundo programa e informe de complejidad | Sin empezar | |

### Lo que cambió respecto al plan original

- **H3 corregida.** Se creyó refutada con la mediana de todos los pares. Al comparar cada región con su
  copia más cercana tras normalizar el sufijo de producto, hay 7 familias con parecido de 0,87 a 1,0
  (`fase0-correccion-h3.md`, `fase2-familias.md`).
- **Nequi no tiene copias** y las regiones grandes (2, 5, 29) son procesos completos. Que haya "un
  `job_producto` para tres productos" (D3/D6) no lo respalda el texto del SAS para Nequi: sigue siendo
  decisión humana (P6).
- **Una familia de 10 regiones es la persistencia de una tabla WORK a la base.** Es lo que D1 elimina;
  se detecta por parecido, sin nombres del cliente.
- **Fuentes medidas:** de 40 entradas externas, 12 son fuentes reales (5 Excel, 4 CSV, 3 tablas de base),
  22 son persistencias propias del programa y 6 quedan pendientes con motivo.
- **Los nombres del manual no están en el SAS** (`ruta_insumos`, `arch_hom_tpo_doc`, `cache_hom_doc`):
  los puse yo al diseñar. Por eso la conformidad se mide en dos niveles (estructura derivada y nombres
  declarados en YAML) y no se pasan filas copiando el manual al YAML.

### Pendientes de la fase 1

- `infile`/`file` con fileref sin comillas (resolver `FILENAME`).
- 3 WORK que se leen antes de crearse (`SABANA_SIN_*`) y nombres con macrovariable (`&tabla_origen.`).
- `sql_tree` falla con subconsultas en `FROM` (código viejo que se tirará).
- Las 4 CSV de entrada no coinciden con las 3 tablas Impala del diseño; no se afirma que lo sean.

## Fases que faltan

- **Fase 3 (sigue).** Render a Markdown con las secciones emitidas y un comando de la CLI. Filas
  estructurales de la sección 6 (familias, tablas WORK eliminadas, exportaciones). Secciones 2 a 5, 7 y 8
  desde los hechos y las convenciones del emisor. Medida de conformidad: cuánto sale derivado y cuánto
  declarado.
- **Fase 4.** Cadenas repetidas entre etapas se vuelven joblets con parámetros. Meta del manual: unos 6
  joblets y 80 a 100 componentes.
- **Fase 5.** Empezada (hitos 59 a 61): los Jobs se emiten como `.item`, y el Job padre del diseño se genera desde el modelo y se ejecuta en Studio real; los hijos son esqueletos. Faltan traducir los hijos y la lógica de producto (lectura de insumos, validación, totales y conciliación), y tMap. Procedimiento en `fase5-talend-instalado.md`.
- **Fase 6.** Correr todo sobre los otros programas de `tests/fixtures/sas` y emitir un informe de
  complejidad y de huecos al estilo de Lakebridge (Analyzer, Converter, Reconcile).

## Lo que no se va a poder igualar

- Decisiones humanas: D2 (un archivo de rechazos o ocho), D6, la equivalencia de las copias (P6) y los
  valores de negocio (tolerancia de conciliación). El emisor las marca pendientes y las lee de un YAML.
- Los riesgos técnicos de Talend (R1 a R4, como `tCacheIn` con `tRunJob`): son del componente, no del SAS.
- La redacción: el resultado será parecido en estructura y contenido, no idéntico en el texto.
- Un LLM no se usa para deducir: choca con la regla de no inventar de `AGENTS.md` y no es reproducible.

## Investigación en internet

No existe un traductor abierto y maduro de SAS a otro lenguaje; lo comercial es por patrones, reglas o
IA (afirmaciones de proveedores, no verificadas). Se tomó de Databricks Lakebridge (BladeBridge) la
estructura de tres fases (Analyzer, Converter, Reconcile). Talend Job Script permite emitir Jobs sin
tocar el XML `.item`, pero no se verificó cómo se ejecuta. `tree-sitter-sas` (MIT) deja lo interno de cada
PROC como nodo genérico y no mejora el frontend propio.

## Del plan anterior

`docs/plan-sgm-v2/` (reparto del equipo, contratos, ciclo de huecos) no se borra: el README y
`src/sgm/motivos.py` lo citan, y sus contratos y su reparto siguen vigentes para el equipo. Lo que
queda superado es solo su secuencia de fases del generador por operadores; la secuencia vigente es la de
este documento.
