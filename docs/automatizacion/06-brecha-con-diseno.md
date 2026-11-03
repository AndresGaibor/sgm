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
tablas que escribe o lee. Medido: 24 de 30 regiones tienen sufijo (11 CTE, 10 AHO, 3 NEQUI); 6 no
tienen ninguno y quedan como pendiente. (Corregido el 3 de noviembre de 2026: la versión anterior
decía 25 y 5, y la suma no cuadraba.)

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

## Joblet de contexto del encabezado y umbral fijado (3 de noviembre de 2026)

**Decisión de umbral.** Queda en 0,2 (`sgm.generador.UMBRAL_DE_AGRUPACION`), tras la revisión humana
del 3 de noviembre de 2026. Con 0,3 la estructura agrupa más fino (5 joblets en vez de 2), pero deja
7 firmas de componente más y 3 nodos más en el Job padre, y el archivo no demuestra que esos grupos
sean procesos distintos.

**Joblet de contexto.** `sgm.generador.contexto_del_encabezado` separa del encabezado las sentencias
de entorno: macrovariables (`%let`), opciones de sesión remota (`OPTIONS REMOTE=`), transferencias
(`PROC DOWNLOAD`, `RSUBMIT`) y codificación de contraseña (`PROC PWENCODE`). Medido en
`client_large.sas`:

- 14 operadores de entorno se van a `jl_contexto`, que ocupa un solo nodo del Job padre.
- 7 variables de contexto declaradas: `servidor_remoto`, `base_de_datos` y `credencial` con el valor
  observado en el archivo (la credencial siempre como `***`); `anio`, `mes`, `dia` y `mday` quedan
  como pendiente `DATO_NO_EN_ARCHIVO`, porque los fija la tabla de validación de fecha en cada
  ejecución.
- 1 pendiente más: 14 rutas literales cuyo papel (insumo o resultado) el archivo no distingue.
- Los 27 componentes de datos del encabezado se quedan en el Job padre, según la decisión tomada.

**Job padre.** 36 nodos: 2 llamadas de joblet, el nodo de contexto, 27 componentes del encabezado y
6 de las regiones sueltas. Firmas de componente distintas en todo el programa: 112 (101 de los
dos joblets, 13 del encabezado y 2 de las sueltas, con 2 compartidas entre encabezado y joblets).
Instancias: 137.

**Qué no cambió.** El joblet de contexto no baja el conteo de componentes: sus 14 operadores son
sentencias pendientes, no componentes. La brecha de 137 frente a unos 80 sigue igual. Tampoco se
resuelven las sub-cadenas compartidas: los dos joblets comparten 3 firmas, así que unirlos en uno
solo ahorraría 3 de las 104. El resto exige unir regiones que la estructura no demuestra que sean el
mismo proceso (similitud máxima 0,47, ya medida arriba).

Estas cifras se midieron sin la política de `env/project.json`. Con la política canónica cambian; la
medición vigente está en la sección "Diseño como artefacto de CLI" al final del archivo.

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

## Diseño como artefacto de CLI (3 de noviembre de 2026)

**Qué hay ahora.** `uv run sgm diseno <archivo.sas> --out out/` escribe
`out/<programa>.diseno.json` con los joblets por grupo, sus contextos, el joblet de contexto y el Job
padre. El diseño deja de existir solo como función del generador: se revisa como archivo, igual que
el plan y la guía. Compila con la misma configuración que `sgm compile` (`env/`), redacta el texto
antes de extraer hechos y no modifica el plan ni la guía.

**Medición vigente** en `client_large.sas`, con `env/project.json` (`placement_strategy:
push_to_db`), que es lo que usa la CLI:

| Métrica | Valor |
|---|---|
| Operadores del plan | 780 |
| Componentes reales | 388 |
| Joblets por grupo (umbral 0,2) | 2 (20 y 4 regiones), con 109 y 12 firmas |
| Firmas de componente distintas | 131 |
| Componentes del encabezado | 56 |
| Componentes de regiones sueltas | 6 |
| Nodos del Job padre | 65 |
| Operadores de contexto | 14 |
| Variables de contexto | 7 (3 con valor, 4 pendientes) |

**Por qué no coinciden con las secciones anteriores.** La política `push_to_db` cambia la fusión y
el empalme a la base: sin ella el plan tiene 955 operadores, el encabezado 27 componentes, 2 joblets
con 98 y 6 firmas, 112 firmas distintas y un Job padre de 36 nodos. Las mediciones anteriores de este
archivo se hicieron sin la política; desde esta sección se reporta la configuración canónica, que es
la que produce la CLI. Con `push_to_db` el encabezado crece porque pasos que antes se fusionaban en
el flujo quedan como componentes.

**Agrupación declarada.** `decisiones/<programa>.agrupacion.yaml` ya se lee. El comando busca ese
archivo junto al programa y, si no está, en `decisiones/`; `--agrupacion <ruta>` manda sobre ambos.
El modo usado queda en `agrupacion` del JSON (`declarada` o `similitud` con su umbral) y los joblets
llevan `regiones`, la lista de índices de región que los forman.

Medido en `client_large.sas` con su YAML: 24 regiones con producto y 6 sin producto, que quedan
sueltas. Salen 3 joblets, uno por producto, como en el diseño:

| Joblet | Regiones | Firmas de componente |
|---|---|---|
| `jl_grupo_01` (producto 1) | 11 | 64 |
| `jl_grupo_02` (producto 2) | 10 | 38 |
| `jl_grupo_03` (producto 3) | 3 | 57 |

Job padre: 66 nodos (3 llamadas, 1 contexto, 56 del encabezado, 6 sueltas). Firmas distintas en todo
el programa: 131, las mismas que con similitud, porque son las mismas regiones. Lo que cambia es el
reparto: la suma de firmas por joblet sube de 121 a 159, así que la agrupación declarada arma los tres
procesos del diseño a cambio de más variedad dentro de cada joblet. El conteo de componentes no baja
por declarar productos; lo que cambia es qué se ve como un solo nodo del padre.

**Qué sigue pendiente.** El diseño no entra en el plan ni en la guía: son artefactos separados. Meter
los joblets y el Job padre en `plan.jobs` toca el modelo de decisiones y las pruebas de firmas, así
que es una decisión aparte. La brecha de fondo tampoco se mueve: 131 firmas distintas frente a los
unos 80 del diseño, y las 6 regiones sin producto siguen requiriendo una decisión: asignarles un
producto o tratarlas como procesos propios.
