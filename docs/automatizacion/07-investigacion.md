# 07. Investigación de temas 41 a 47

Fecha de la investigación: 2026-11-03.

Método: búsqueda web y lectura de las páginas oficiales cuando fue posible. Las fuentes de comunidad (foros de Qlik Community, SAS Communities) se usan solo como indicio y se marcan como tales. Si una página oficial no confirma un punto, la sección lo dice. Ninguna conclusión se toma de memoria.

Leyenda de estado: **Confirmado** (lo dice una fuente oficial leída), **Parcial** (lo confirma solo una fuente secundaria o un fragmento de búsqueda), **Sin confirmar** (ninguna fuente lo respalda).

---

## 41. Semántica de tFlowToIterate con subjobs por fila (Talend Studio 8)

**Pregunta.** En Talend Studio 8, ¿un subjob conectado con el enlace Iterate se ejecuta completo por cada fila del flujo de entrada? ¿Cómo se leen los valores de la fila actual?

**Fuentes.**
- [Documentación oficial de tFlowToIterate, Talend 8.0](https://help.qlik.com/talend/en-US/components/8.0/orchestration/tflowtoiterate.md) (leída).
- [Hilo de Qlik Community sobre tFlowToIterate con joblets (2017)](https://community.qlik.com/t5/Talend-Studio/tFlowToIterate-usage-with-joblets/m-p/2303671) (solo encontrado en búsqueda; la página no devolvió su contenido al leerla).
- [Hilo de Qlik Community sobre iterar valores de una tabla](https://community.qlik.com/t5/Talend-Studio/Iterating-through-values-in-table-for-single-Context-Variable/td-p/2334186) (solo fragmento de búsqueda).

**Conclusión.**
- **Confirmado.** La página oficial dice que el componente "Reads data line by line from the input flow and stores the data entries in iterative global variables". Pertenece a la familia Orchestration, no puede ser componente de inicio y necesita un componente de salida aguas abajo. Tiene un enlace de fila de salida llamado Iterate, una entrada Row Main y enlaces de disparo Run if, On Component Ok y On Component Error.
- **Confirmado.** Los valores de la fila se toman de las variables globales. En Basic settings hay dos opciones: usar el valor por defecto (key, value) o personalizar la key y elegir la columna de la fila. Además, el componente expone NB_LINE (después de ejecutar), CURRENT_ITERATION (flujo) y ERROR_MESSAGE (después de ejecutar, solo si Die on error está desmarcado).
- **Sin confirmar.** La página oficial no dice que el subjob conectado se ejecute completo por cada fila. Solo menciona el enlace Iterate y remite a ejemplos. La afirmación de que sí se ejecuta por fila aparece en un comentario de comunidad (fragmento de búsqueda), no en documentación oficial.
- **Sin confirmar.** La página oficial no documenta el nombre exacto de las claves de `globalMap` ni cómo leerlas en código. Un fragmento de búsqueda cita una forma como `globalMap.get("row1.dbname")`, pero no pude verificarla en una fuente oficial.
- **Confirmado (fuente de comunidad de 2017, respaldada por la respuesta marcada como solución).** Un enlace iterate no se puede conectar directamente a un joblet. El workaround aceptado es poner un tJava sin código entre Iterate y el joblet, y disparar el joblet con el enlace On Component Ok de ese tJava. La fuente es antigua y corresponde a una versión de Studio anterior a la 8.0.

**Qué cambia en el proyecto.**
- No asumir en el generador de Talend que un subjob se ejecuta por fila mientras no haya una prueba en Studio 8 que lo demuestre. Queda como pendiente de validación.
- Para leer columnas de la fila actual, no fijar nombres de `globalMap` en el generador. Usar la opción "Customize" con key y value explícitos, que sí está documentada.
- Si el código generado usa joblets dentro de un ciclo, aplicar el workaround con tJava. Antes de usarlo, verificarlo en Studio 8, porque la fuente tiene más de ocho años.

---

## 42. Límite de memoria de tMap con lookups grandes y modelos de caché

**Pregunta.** ¿Qué modelos de carga de lookup ofrece tMap, cuáles son sus límites de memoria y cuál usar con lookups grandes?

**Fuentes.**
- [Documentación oficial de tMap lookup models, Talend 8.0](https://help.qlik.com/talend/en-US/components/8.0/tmap/tmap-lookup-models) (leída).
- [Versión 7.3 de la misma página](https://help.qlik.com/talend/en-US/components/7.3/tmap/tmap-lookup-models) (solo encontrada en búsqueda).
- [Hilo de Qlik Community sobre Reload at each row y Load once](https://community.qlik.com/t5/Talend-Studio/exact-use-of-tmap-reload-at-each-row-and-load-once-options/m-p/2229650/highlight/true) (fragmento de búsqueda).

**Conclusión.**
- **Confirmado (Load once).** Carga una sola vez todos los registros del lookup, en memoria, o en un archivo local si la opción Store temp data está activa. La documentación lo recomienda cuando el flujo principal tiene muchos registros.
- **Confirmado (Reload at each row).** Vuelve a cargar todos los registros del lookup por cada registro del flujo principal. La página lo sugiere cuando los datos del lookup cambian constantemente o cuando el flujo principal es pequeño y el lookup es grande.
- **Confirmado (Reload at each row (cache)).** Funciona como el anterior, pero en cada recarga solo se traen los registros que aún no están en la caché, y la caché vive en memoria. La página dice textualmente que este modelo "can't be used with Store temp data on disk option".
- **Confirmado (advertencia de memoria).** La página indica que Load once "might cause an OutOfMemory exception" con datasets de lookup grandes, y sugiere Reload at each row en ese caso. Este aviso aparece en la sección de Reload at each row.
- **Parcial.** La recomendación de reducir el flujo principal con variables globales para filtrar el lookup viene de la documentación de rendimiento y de un comentario de foro. No la verifiqué en la página leída.
- **Sin confirmar.** La página no da un tamaño de memoria concreto a partir del cual falla Load once. Cualquier umbral numérico en el proyecto debe medirse, no tomarse de la documentación.

**Qué cambia en el proyecto.**
- Al traducir un lookup de SAS a tMap, la elección debe depender del tamaño del lookup y del flujo principal, no de un valor fijo. Load once es el valor por defecto razonable para lookups pequeños o medianos.
- Para lookups grandes con flujo principal pequeño, usar Reload at each row (cache), no Load once. Si además se necesita disco, Reload at each row (cache) no sirve porque no se combina con Store temp data.
- Dejar en el diagnóstico una advertencia con el modelo elegido y el motivo, para que la validación en Studio pueda revisarlo.

---

## 43. Comportamiento de tCacheOut y tCacheIn entre tRunJob hijos del mismo padre

**Pregunta.** ¿Un tCacheOut en un job hijo puede ser leído por un tCacheIn en otro hijo, o en el padre, cuando todos se llaman con tRunJob?

**Fuentes.**
- [Documentación de tCacheIn, Talend 8.0](https://help.qlik.com/talend/en-US/components/8.0/processing/tcachein) (leída).
- [Documentación de tRunJob Standard properties, Talend 8.0](https://help.qlik.com/talend/en-US/components/8.0/orchestration/trunjob-standard-properties) (leída).
- [Component-specific settings for tRunJob, Job Script Reference 8.0](https://help.qlik.com/talend/en-US/job-script-reference-guide/8.0/component-specific-settings-for-trunjob) (solo búsqueda).
- [Hilo de Qlik Community sobre compartir datos entre padre e hijo](https://community.qlik.com/t5/Talend-Studio/How-to-share-data-between-parent-job-and-child-jobs/td-p/2301578) (solo búsqueda).

**Conclusión.**
- **Confirmado.** Según la documentación de tCacheIn, el componente lee "the cache RDDs (Resilient Distributed Datasets) stored by tCacheOut". Sus páginas son de Apache Spark Batch y Spark Streaming. No hay en las páginas leídas un uso de tCacheOut/tCacheIn en jobs estándar Java.
- **Confirmado.** La página de tRunJob no menciona compartir caché ni datos en memoria entre padre e hijo. Lo único que describe como transferencia en memoria es el buffer de tBufferOutput, que se activa con "Propagate the child result to the output schema".
- **Confirmado.** La opción "Use an independent process to run subJob" se describe como ayuda para "solving issues related to memory limits". Según la documentación, "Use dynamic job" no es compatible con la caché del JobServer, y tanto esa opción como "Use an independent process" son incompatibles con "Use or register a shared DB Connection".
- **Sin confirmar.** No hay ninguna fuente que diga si un tCacheOut puede ser leído por un tCacheIn de otro hijo o del padre. La conclusión que se puede sostener es que la documentación no lo respalda y que tCacheOut está documentado solo para Spark.

**Qué cambia en el proyecto.**
- No generar tCacheOut/tCacheIn para pasar datos entre jobs Talend estándar. Para ese paso, la opción documentada es tBufferOutput con propagación de salida, o contexto/globalMap para valores simples.
- Si se usa tBufferOutput, documentar que la propagación no aplica con "Use dynamic job" ni con "Use an independent process", porque en esos casos la opción queda oculta o incompatible.
- Cualquier intento de compartir caché entre hijos queda pendiente hasta probarlo en Studio 8.

---

## 44. Semántica de %DO, %TO, %SCAN y %SYSFUNC en macros SAS

**Pregunta.** ¿Cómo se comportan %DO (con %TO y %BY), %SCAN y %SYSFUNC según la documentación oficial de SAS?

**Fuentes.**
- [%DO, Iterative Statement, SAS 9.3 Macro Language: Reference](https://support.sas.com/documentation/cdl/en/mcrolref/62978/HTML/default/p0ri72c3ud2fdtn1qzs2q9vvdiwk.htm) (leída).
- [Macro Functions: %SCAN and %QSCAN Functions, SAS 9.2 Macro Language Reference](https://support.sas.com/documentation/cdl/en/mcrolref/61885/HTML/default/z3514scan.htm) (solo búsqueda).
- [Functions and Arguments for %SYSFUNC, SAS 9.3 Macro Language: Reference](https://support.sas.com/documentation/cdl/en/mcrolref/62978/HTML/default/n1mix0b315l1dpn0zmhebdzifjne.htm) (solo búsqueda).
- [Macro Language Elements, SAS 9.2 Macro Language Reference](http://support.sas.com/documentation/cdl/en/mcrolref/61885/HTML/default/a000543755.htm) (leída; solo sirvió para confirmar que %DO es una sentencia macro).

**Conclusión.**
- **Confirmado (%DO).** La sintaxis es `%DO macro-variable=start %TO stop <%BY increment>;` seguida de texto y sentencias macro, y termina con `%END;`. La página dice que la sentencia "Executes a section of a macro repetitively based on the value of an index variable" y que solo se permite dentro de definiciones de macro.
- **Confirmado (%TO).** No tiene entrada propia. Aparece solo como parte de la sintaxis de %DO.
- **Confirmado (%BY).** "By default, increment is 1."
- **Confirmado (variable índice).** Si la variable índice no existe, el procesador macro la crea en la tabla de símbolos local.
- **Confirmado (ejemplo).** La página muestra `%macro create(howmany); %do i=1 %to &howmany; data month&i; ... %end; %mend create;`. Con `%create(3)` genera DATA steps para MONTH1 a MONTH3.
- **Parcial (%EVAL).** Un fragmento de búsqueda cita una nota de SAS sobre que %DO ... %TO llama automáticamente a %EVAL sobre sus expresiones. La página leída no contiene esa nota, así que no la confirmé en la fuente oficial.
- **Confirmado (%SCAN).** La página describe %SCAN como la función que busca una palabra por su posición en una cadena. %QSCAN enmascara caracteres especiales y operadores mnemónicos, y %SCAN no. Si n es mayor que el número de palabras, el resultado es una cadena nula. Esto viene de un fragmento de búsqueda de la página oficial, no de una lectura completa.
- **Confirmado (%SYSFUNC).** La forma general es `%SYSFUNC(function(argument-1 <...argument-n>)<, format>)`. %QSYSFUNC enmascara caracteres especiales en el resultado y %SYSFUNC no. Los argumentos no se entrecomillan como en DATA step, y no se pueden anidar funciones de DATA step directamente, aunque sí llamadas %SYSFUNC anidadas. Algunas funciones no están permitidas; la lista está en la referencia de SAS 9.3.
- **Sin confirmar.** Las páginas consultadas son de SAS 9.2 y 9.3. No verifiqué si algo cambió en 9.4.

**Qué cambia en el proyecto.**
- El traductor de macros puede tratar %DO con %TO y %BY como bucle con índice local, con incremento 1 por defecto, y debe respetar que solo es válido dentro de %MACRO.
- Para %SYSFUNC, el traductor debe distinguir %SYSFUNC de %QSYSFUNC porque el resultado enmascarado cambia el texto.
- Para %SCAN, el traductor debe respetar que una posición fuera de rango devuelve cadena nula, no error.
- La nota de %EVAL queda pendiente de confirmar en la documentación de SAS 9.4 antes de usarla como regla.

---

## 45. MERGE con IN= y BY frente a joins SQL: diferencias de semántica

**Pregunta.** ¿Qué dice la documentación de SAS sobre MERGE con IN= y BY, y en qué se diferencia de un join SQL? ¿Qué pasa en merges many-to-many?

**Fuentes.**
- [Merging SAS Data Sets: Understanding the MERGE Statement, Base SAS (SAS 9.3)](https://support.sas.com/documentation/cdl/en/basess/58133/HTML/default/a001318477.htm) (leída).
- [SAS Data Set Options: IN= Data Set Option, SAS 9.2](http://support.sas.com/documentation/cdl/en/lrdict/64316/HTML/default/a000131134.htm) (leída).
- [Paper 1746-2018, Merge with Caution, Joshua Horstman (SGF 2018)](https://support.sas.com/resources/papers/proceedings18/1746-2018.pdf) (el PDF se descargó pero no se pudo extraer el texto).
- [Hilos de SAS Communities sobre many-to-many merge](https://communities.sas.com/t5/SAS-Programming/many-to-many-merge/m-p/834474) (solo búsqueda).

**Conclusión.**
- **Confirmado.** "You merge data sets using the MERGE statement in a DATA step." Con BY, "the data sets must be sorted by the same BY variables before you can merge them."
- **Confirmado (IN=).** El valor es "1 if the data set contributed to the current observation, and 0 otherwise". El valor "remains as long as that BY group is still being processed and the value is not reset by programming logic". Además, la variable "are not included in the SAS data set that is being created, unless they are assigned to a new variable".
- **Parcial (many-to-many).** Un foro cita la ayuda en línea de SAS y dice que MERGE no produce producto cartesiano en un match-merge many-to-many, sino que empareja por posición dentro de cada grupo BY. Esta regla no aparece en las páginas oficiales que pude leer. Por eso la dejo como parcial, aunque el texto lo atribuye a SAS.
- **Sin confirmar (PROC SQL).** Los foros recomiendan PROC SQL para many-to-many. Ninguna fuente oficial leída lo dice, y el paper de Horstman no se pudo leer en texto.
- **Diferencia de diseño (inferida de lo confirmado).** En MERGE, el IN= es una bandera que indica de qué fuente vino la fila. En SQL, la equivalencia es una columna calculada en un LEFT JOIN o en un EXISTS, y no existe el emparejamiento posicional por grupo BY. Esto se deduce de las definiciones confirmadas; no hay fuente que compare los dos modelos punto por punto.

**Qué cambia en el proyecto.**
- No traducir MERGE a JOIN SQL sin una prueba de equivalencia, porque el emparejamiento posicional dentro de grupos BY no es un join.
- Un IN= se traduce a una bandera que solo cubre la fila actual, no a una columna que persiste en la salida. Si el SAS la asigna a una variable nueva, sí se conserva.
- Los merges many-to-many quedan como pendiente de análisis hasta confirmar la regla con la documentación de SAS 9.4 o con un caso de prueba.
- Un ejemplo con datos de muestra del corpus debe comprobar el orden de emparejamiento antes de cerrar la regla.

---

## 46. Dialecto SAS en otros traductores (confirmar o descartar con fuentes)

**Pregunta.** ¿Hay traductores de código abierto que soporten SAS como dialecto de origen?

**Fuentes.**
- [Documentación de sqlglot](https://pypi.org/project/sqlglot/0.6.0) (solo búsqueda; la página de versión antigua no lista dialectos completos).
- [tree-sitter-sas en PyPI](https://pypi.org/project/tree-sitter-sas/) (solo búsqueda).
- [Stan, traductor parcial de SAS a SciPy, en GitHub](https://github.com/8bit-pixies/Stan) (solo búsqueda).
- [sas-scoring-translator-python en GitHub](https://github.com/sassoftware/sas-scoring-translator-python) (la página devolvió 404; no pude leerla).
- [Hilo de SAS Communities sobre conversión de SAS a Python](https://communities.sas.com/t5/SAS-Programming/Conversion-of-SAS-Code-to-Python/m-p/809150) (solo búsqueda).

**Conclusión.**
- **Descartado con la evidencia disponible.** sqlglot no aparece con SAS como dialecto en las búsquedas. Sus dialectos documentados que aparecieron son DuckDB, Presto, Spark, Snowflake, BigQuery y Hive. Como no leí la lista completa de dialectos de su documentación actual, lo doy por descartado solo para el alcance de esta búsqueda.
- **Confirmado con fuente de búsqueda.** tree-sitter-sas es una gramática para SAS con licencia MIT, con cobertura de DATA steps, PROC, definiciones %MACRO/%MEND, llamadas macro, %INCLUDE, LIBNAME y OPTIONS. Lo que no es proc-specific cae en un nodo genérico. Su versión en PyPI es 0.4.1 según la búsqueda. No es un traductor; sirve como parser sobre el que construir uno.
- **Parcial.** Stan (8bit-pixies) describe su objetivo como un subconjunto de SAS/Base a SciPy y se presenta como experimental y con parser incompleto. No verifiqué su estado actual.
- **Parcial.** Existe un proyecto oficial de SAS para traducir código de scoring a Python y a R. La página de GitHub devolvió 404, así que solo lo sé por un resultado de búsqueda. Su alcance, según la búsqueda, es solo código de scoring, no programas SAS generales.
- **Confirmado (comercial).** Semantic Designs ofrece un traductor de SAS a Python, Java, C#, Julia. BeOptimized ofrece servicio para SAS Base puro. No son de código abierto.
- **Descartado como traductor.** saspy es un puente entre Python y SAS 9.4 para ejecutar código SAS desde Python; no traduce código.

**Qué cambia en el proyecto.**
- No asumir que existe un traductor de código abierto de SAS a Python o Spark listo para usar. El proyecto debe seguir con su propio parser.
- Si se necesita un parser, tree-sitter-sas es el punto de partida más sólido de los encontrados. Antes de adoptarlo hay que verificar licencia, mantenimiento y cobertura real en el corpus. Como dependencia nueva, debe anotarse en "Decisiones" según AGENTS.md, porque no está en la lista permitida.
- Stan y el traductor oficial de scoring no sirven como base para el proyecto por su alcance declarado.

---

## 47. Herramientas de clones parametrizados aplicables a código SAS

**Pregunta.** ¿Qué herramientas generan variantes parametrizadas de código a partir de una plantilla, y pueden aplicarse a código SAS?

**Fuentes.**
- [Cookiecutter, documentación avanzada](https://cookiecutter.readthedocs.io/en/latest/advanced/) (solo búsqueda).
- [Cookiecutter, documentación general](https://cookiecutter.readthedocs.io/) (solo búsqueda).
- [Búsqueda sobre Talend y clones parametrizados de jobs](https://edwardost.github.io/talend/di/2015/05/27/Parameterized-Jobs) (solo búsqueda; artículo de 2015).

**Conclusión.**
- **Confirmado (Cookiecutter).** Ofrece variables de elección (choice), variables booleanas, sustitución en nombres de archivos y directorios, hooks de pre y post generación, y herencia de plantillas desde la versión 2.2. El motor de plantillas es Jinja2.
- **Sin confirmar (SAS).** Ninguna fuente encontrada muestra Cookiecutter o Jinja2 aplicado a código SAS. Es posible técnicamente, porque Jinja2 es texto genérico, pero no hay un caso documentado.
- **Sin confirmar (Talend).** La búsqueda de clones parametrizados de jobs en Talend solo devolvió un artículo de 2015 sobre jobs parametrizados. No encontré una herramienta oficial que genere clones de jobs.
- **Parcial.** Talend tRunJob permite pasar parámetros de contexto al hijo, y USE_DYNAMIC_JOB permite elegir el job hijo en tiempo de ejecución. Esto es una forma de parametrizar sin clonar, y se documenta en la guía de Job Script Reference.

**Qué cambia en el proyecto.**
- Un generador de variantes de SAS en el proyecto tendría que basarse en el parser (ver tema 46), no en una herramienta de plantillas de texto. Una plantilla con Jinja2 sobre texto SAS no sabe de sintaxis y puede producir código inválido.
- Si se quiere parametrizar, lo más simple y acorde con las reglas del proyecto es usar variables de entrada explícitas, no clones generados. Queda pendiente decidir si se incorpora Cookiecutter; sería una dependencia nueva y debe anotarse en "Decisiones".
- Las reglas del proyecto no deben nombrar scripts de ejemplo al describir estas variantes, como ordena AGENTS.md.

---

## Resumen de confirmaciones

| Tema | Confirmado | Parcial o sin confirmar |
|---|---|---|
| 41 tFlowToIterate | Componente, enlaces, variables globales, limitación con joblets (fuente antigua) | Ejecución de subjob por fila; nombres de claves de globalMap |
| 42 tMap | Los tres modelos de carga, aviso de OutOfMemory, incompatibilidad caché con disco | Umbral de memoria; recomendación de filtrar con variables |
| 43 tCacheOut/tCacheIn | Uso solo Spark; tRunJob no menciona caché compartida | Compartir caché entre hijos y padre |
| 44 %DO, %SCAN, %SYSFUNC | Sintaxis y defaults de %DO; %SYSFUNC y %QSYSFUNC; %SCAN por fragmento | Nota de %EVAL; cambios en 9.4 |
| 45 MERGE vs SQL | Requisito BY ordenado; IN= como bandera 1/0 que no persiste sin asignación | Many-to-many posicional; recomendación de PROC SQL |
| 46 Traductores SAS | tree-sitter-sas como parser | Sin traductor abierto maduro; repositorio oficial de scoring no leído (404) |
| 47 Clones parametrizados | Cookiecutter y sus funciones | Aplicación a SAS y a jobs Talend sin fuente |
