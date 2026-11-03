# Brecha entre la salida automática y el diseño de referencia

Medido el 3 de noviembre de 2026 sobre `tests/fixtures/sas/client/client_large.sas`
(24.801 líneas). El diseño de referencia es `docs/diseno-talend-exogena-depositos.md`.

| Métrica | Diseño de referencia | Salida automática hoy |
|---|---|---|
| Jobs | 1 padre + 4 etapas + joblets | 1 Job, 155 Jobs hijos |
| Subjobs | pocos, uno por etapa | 261 |
| Componentes reales | unos 80 | unos 540 |
| `tMap` | pocos, por etapa | 175 |
| `tRunJob` (llamadas) | unas pocas (`tFlowToIterate`) | 153 |
| Joblets | unos pocos | 81 (uno por forma repetida) |
| Contextos | grupos por entorno y parámetros por producto | 1 grupo de ambiente, 0 variables |
| SQL en la base | un `tDBInput` con `WITH` por sabana | 1 operador `exec_sql` |
| Operadores sin traducir | 0 | 164 (`unsupported`) |

## Qué se midió sobre la causa

- **Llamadas repetidas (`tRunJob`):** las instancias de una misma forma se agrupan ahora en todo
  el programa, y un bloque colapsa en un `iterate` mientras no cree un ciclo. Eso bajó 160 a 153.
  El resto no se puede colapsar: las instancias están intercaladas con pasos compartidos, y en el
  orden topológico la secuencia de plantillas no es periódica. Una detección de periodos no sirve.
- **`tMap` (175):** vienen de `derive`, `join` y `map` que no se fusionan en una sola cadena.
- **Operadores sin traducir (164):** sentencias que el traductor no cubre; son huecos reales.

## Qué falta para llegar al diseño

1. **Agrupar por bloque de fuente, no por orden topológico.** En el archivo, las 30 copias del
   bloque son regiones de código con el mismo esquema. Un bloque por región de fuente, comparado
   por forma, da una sola plantilla con 30 contextos.
2. **Un Job por etapa.** Partir el plan por fronteras (`Plan.fronteras`) y por cargas externas.
3. **Fusión a SQL.** Operadores de base consecutivos en un solo `tDBInput` con `WITH`. Requiere
   generar SQL desde la IR para las sentencias que hoy van al flujo.
4. **Contextos.** Rutas, bases y nombres de conjuntos de datos como variables de contexto.

Cada punto se puede medir con la misma tabla. El objetivo es que la tabla de arriba se acerque a
la columna de la izquierda sin tocar el archivo de referencia a mano.

## Mediciones deterministas adicionales (3 de noviembre de 2026)

Estas medidas sustituyen la premisa de "30 bloques idénticos" del diseño de referencia.

- **Regiones por `%macro ambiente`:** 30 regiones, pero solo 6 comparten el mismo multiconjunto de
  tipos de operador, y solo 1 tiene la misma longitud que la primera. La región 0 tiene 82
  operadores y la región 1 tiene 15. No son copias del mismo bloque.
- **Sub-cadenas repetidas de operadores:** con longitud 3 hay 30 tipos de cadena repetida que
  cubren el 62 % de los operadores secuenciales. Como joblet, cada aparición sigue siendo una
  llamada: unas 171 llamadas, no una. No baja los componentes visibles de forma útil.
- **Fusión de cadenas lineales de componentes:** de 330 componentes reales a 210 cadenas. 163 de
  esas cadenas son un solo componente, porque hay puntos de ramificación.

Conclusión medida: con transformaciones deterministas sobre la estructura, el techo para este
archivo está cerca de 200 componentes visibles, no de 80. Llegar a 80 exige unir sabanas
distintas en pocos jobs, y eso es una decisión sobre qué procesos son el mismo proceso. El
archivo no lo dice por estructura.

## Fusión de joins en tMap: investigación y resultado (intento revertido)

**Investigación.** Según la documentación de Talend 8.0, un join se modela dentro de `tMap` como
lookup: tiene un modelo de coincidencia (`unique match`, `first match`, `all matches`) y un tipo de
join (inner o left outer). Referencias: [ejemplo de modelos de coincidencia](https://help.qlik.com/talend/en-US/components/8.0/tmap/example-job-implementing-different-match-models?l=de-DE)
y [diferencias entre modelos](https://help.qlik.com/talend/en-US/components/8.0/tmap/differences-between-unique-match-first-match-and-all-matches).
Por tanto, un join sí puede vivir dentro de un `tMap`.

**Medición.** Incluir `join` en la fusión de cadenas (`p06`) baja los `tMap` de 175 a 149 y los
componentes reales de 330 a 296 en `client_large.sas`.

**Por qué se revirtió.** Al fundir el join en un `map`, desaparece como operador suelto y rompe
dos cosas del modelo del proyecto:
- las decisiones por firma: un override `tJoin` ya no puede aplicarse a ese join
  (`tests/unit/test_store.py`, cuatro fallos);
- la detección del patrón de materialización de la pasada 8 (`test_fusion_partition`), y una
  prueba de SQL que espera un join explícito (`test_sql_flujo.py`).

**Decisión pendiente.** Fundir joins solo cuando no hay override ni decisión abierta sobre ese join
exige que la firma del join se conserve dentro del paso del `map`. Es el siguiente cambio que
tendría sentido; requiere tu aprobación porque toca el modelo de decisiones.

## Similitud entre regiones con tolerancia a huecos (3 de noviembre de 2026)

Medida: subsecuencia común más larga (LCS) de tipos de operador entre cada región `%macro ambiente`
y la más grande. Referencia: [Görg, parameterized clone detection](https://dl.gi.de/items/484f854b-061c-4024-9678-5b1dbfc45c12/full)
y [Asta, clones por subárboles repetidos](https://www.microsoft.com/en-us/research/?p=186510).

- Similitud máxima frente a la región de referencia: 0,47.
- La mayoría de las regiones están por debajo de 0,10.

Conclusión: el archivo no contiene 30 copias del mismo proceso ni siquiera con huecos permitidos.
La agrupación "producto ×3" del diseño no se deriva de la estructura. Un generador determinista
puede producir la estructura del diseño solo a partir de una agrupación declarada (por ejemplo en
YAML, con qué regiones forman cada proceso), y esa agrupación es una decisión, no un hecho del SAS.

## Agrupación determinista por producto (3 de noviembre de 2026)

Regla: cada región `%macro ambiente` toma el sufijo dominante (`_CTE`, `_AHO`, `_NEQUI`) de las
tablas que escribe o lee. Medido: 25 de 30 regiones tienen sufijo (11 CTE, 10 AHO, 3 NEQUI); 5 no
tienen ninguno y quedan como pendiente.

Con esa agrupación y contando firmas repetidas una sola vez:
- Firmas de componente distintas: 112 (con nombres y literales).
- Clases gruesas (tipo de operador, componente): 14 en todo el programa, de 6 a 10 por producto.

Esto acerca la salida a la estructura del diseño: un Job por producto con pocas clases de componente
repetidas, en lugar de 30 regiones distintas. Los nombres de producto y sufijos viven en
`decisiones/client_large.agrupacion.yaml` (decisión del equipo), no en `rules/` ni en `src/`.

## Ruta sin pérdida hacia el diseño (3 de noviembre de 2026)

Investigado en la documentación de Talend 8.0: un joblet es una agrupación de diseño cuyo código
queda dentro de la clase del Job padre; un `tRunJob` es una ejecución separada con su propio
contexto ([diferencias entre joblet y tRunJob](https://help.qlik.com/talend/en-US/diffs-between-joblet-trunjob/8.0)).
Por eso, en el canvas, un joblet es un solo nodo aunque tenga muchos componentes dentro.

Método determinista usado (sin sufijos): agrupar regiones por el vocabulario de sus conjuntos de
datos (`sgm.agrupacion`), con Jaccard y palabras comunes descartadas. Resultado en `client_large.sas`:
5 grupos de 2 o más regiones (11, 7, 2, 2, 2) y 6 regiones sueltas.

Medidas:
- Con un cuerpo representativo por grupo: 18 componentes dentro de joblets y 6 sueltos. Pero esto
  pierde las diferencias de los demás miembros; no es equivalente.
- Sin pérdida (unión de firmas de componente distintas por grupo): 89, 14, 5, 2 y 1 firmas; 117 en
  total con las sueltas. Es la cifra honesta: cercana a los unos 80 del diseño. Las firmas distintas
  dentro de un grupo se diferencian sobre todo por nombres y literales, que pasan a contextos.

Pendiente para cerrar la brecha: emitir un joblet por grupo con esas firmas, convertir los
nombres y literales que varían en contextos, y llamar cada joblet con `tFlowToIterate` sobre la
lista de contextos de sus miembros.

## Generador de joblets por grupo (3 de noviembre de 2026)

Implementado en `src/sgm/generador.py`. Regiones: definiciones de la macro más repetida del
programa (sin nombres de cliente). Grupos: `sgm.agrupacion`. Joblet: unión de firmas de componente
distintas de sus miembros. Contextos: por miembro, los conjuntos de datos que usa.

Medido en `client_large.sas`: 5 joblets (11, 7, 2, 2, 2 miembros) con 89, 14, 5, 2 y 1 firmas.

Investigado para la llamada: en Talend, `tFlowToIterate` recorre filas y los valores de cada fila
llegan por `globalMap` a un `tRunJob` con contexto, o a un joblet que lee el contexto del Job padre
([patrón de iteración con tRunJob](https://community.qlik.com/t5/Talend-Studio/Iterating-through-values-in-table-for-single-Context-Variable/td-p/2334186)).
Esa es la forma de llamar un joblet una vez por miembro, en lugar de una vez por región.

Pendiente: los contextos hoy son listas de conjuntos de datos; el diseño necesita roles
(entrada, salida, producto) y la emisión del Job con `tFlowToIterate`.

## Job padre de diseño (3 de noviembre de 2026)

`sgm.generador.diseno_del_job` produce el Job padre: una llamada por joblet de grupo (5), más los
componentes de las regiones sueltas (33). Canvas del padre: 38 nodos. Componentes dentro de los
joblets: 111 firmas.

Investigado: en SAS, repetir sobre una lista se escribe con `%DO i = 1 %TO %SYSFUNC(COUNTW(&lista));`
y `%SCAN` para extraer cada elemento ([guía de macros comunes](https://advance.hub.phuse.global/wiki/x/4xOZAQ)).
El programa de referencia no tiene esa lista: tiene copias. El generador las convierte en la misma
forma (llamada por lista de contextos), que es el equivalente en Talend (`tFlowToIterate` sobre
los contextos de cada joblet).

Brecha restante: los 33 componentes sueltos (6 regiones sin grupo) y los 111 dentro de joblets
siguen por encima de los unos 80 del diseño. Para bajarlos hay que agrupar también las regiones
sueltas (con un umbral más bajo o por sus propias firmas) y que los joblets compartan firmas.

## Medición final de la ronda (3 de noviembre de 2026)

- Los 27 componentes que antes contábamos como "sueltos" son del encabezado del programa (antes de
  la primera región). Son la etapa de preparación: en el diseño pertenecen al Job padre.
- Umbral 0,3: 5 joblets (11, 7, 2, 2, 2), 111 firmas sin pérdida.
- Umbral 0,2: 2 joblets (20 y 4 miembros), 104 firmas sin pérdida. Los sueltos de región bajan a 6.
- Con umbral 0,2 el canvas estimado es 2 llamadas de joblet + 27 componentes del encabezado +
  6 componentes de regiones sueltas = 35 nodos; componentes totales 104 + 33 = 137.

Investigado:
- Talend publica un marco de gestión de contextos basado en joblets que carga las variables al
  inicio de cada Job ([Context Management Framework](https://academy-storage.talend.com/Custom_pages/customers/customer_catalog/4/Content/Solution%20templates/ContextMgmtFramework.htm)).
  Es el patrón para los contextos por entorno del diseño.
- No encontré evidencia independiente de convertidores de SAS a Talend. Las herramientas que aparecen
  son comerciales y cubren otras migraciones.

Brecha restante: 137 componentes frente a unos 80. El siguiente paso medible es partir el
encabezado en joblets de contexto y en Job padre, y mirar si las firmas de 104 se pueden reducir
con sub-cadenas compartidas entre los dos joblets grandes.

## Investigación sobre PROC SQL hacia SQL de motor (3 de noviembre de 2026)

- Traducir PROC SQL a SQL de Spark o Hive es posible para `SELECT`, `GROUP BY` y subconsultas
  simples ([guía de migración de SAS a PySpark](https://digihub.mastechdigital.com/Fabric_Assets/Microsoft%20Fabric%20Asset%20Library/09_Migration_Modernization/MS_Fabric_SAS_to_PySpark_Migration.docx)).
- Diferencia de semántica: en SAS, una columna no agrupada junto a un agregado devuelve un valor;
  en Spark hace falta una función de ventana. Un traductor debe marcar ese caso, no adivinarlo
  ([análisis de conversiones erróneas](https://medium.com/@protmaks/why-ai-cant-correctly-convert-sas-code-to-spark-sql-for-databricks-473552770eb0)).
- `SELECT ... INTO :macrovariable` no es SQL portable: se reconstruye en el programa anfitrión.
- sqlglot traduce entre dialectos SQL (Spark, Hive y otros) ([página de sqlglot](https://pypi.org/project/sqlglot/0.6.0)).
  No confirmé que tenga un dialecto de SAS: hay que verificarlo en su README antes de depender de él.

Consecuencia para la fusión de SQL: cada sentencia pasa a un tDBInput solo si su semántica es
portable. Lo que no lo es (columnas no agrupadas, `INTO :`) queda como pendiente con motivo, no
como SQL inventado.

## Verificación de sqlglot (3 de noviembre de 2026)

Las fuentes consultadas dicen que sqlglot traduce entre unos 31 dialectos SQL (Spark, DuckDB,
Snowflake, BigQuery, entre otros) y permite crear dialectos propios ([repositorio de sqlglot](https://github.com/tobymao/sqlglot)).
No encontré que tenga un dialecto de SAS. Por eso, para PROC SQL, hay que escribir el lector
propio, y sqlglot solo serviría como escritor hacia Impala o Spark. Queda por confirmar en su
README oficial.
