# Política para procedimientos con efectos laterales

Esta política conserva el efecto demostrable del SAS y evita que el migrador genere acciones que
puedan borrar o sobrescribir datos persistentes. Las equivalencias se limitan a las formas citadas;
las demás quedan pendientes con un código y una causa.

## Limpieza de `WORK`

`PROC DELETE DATA=` se omite con el aviso `A-PROC-LIMPIEZA-OMITIDO` solo cuando el texto demuestra
que cada miembro afectado pertenece a `WORK`. La documentación de `PROC DELETE` describe el uso
implícito de `WORK` cuando se omite `LIBRARY=` (`proc.pdf`, pp. 839, 847). `PROC DATASETS DELETE` y
`KILL` se omiten solo con `LIBRARY=WORK` explícito; sin biblioteca, la guía dice que se usa la
biblioteca predeterminada actual, normalmente `WORK`, por lo que el migrador no asume ese valor y
emite `P-DELETE-BIBLIOTECA-SIN-DEMOSTRAR` (`proc.pdf`, pp. 616, 627). Un libref literal distinto de
`WORK` queda como `P-DELETE-PERSISTENTE`; un libref dinámico también queda sin demostrar.
`PROC CONTENTS DATA=WORK.<miembro>` sin `OUT=` se registra como aviso solo cuando
`reports=discard`; con `reports=log/csv` permanece pendiente porque el resultado de metadatos no es
una equivalencia de filas (`proc.pdf`, pp. 541, 547).

Las formas persistentes quedan pendientes como `P-DELETE-PERSISTENTE` y las ambiguas como
`P-DELETE-BIBLIOTECA-SIN-DEMOSTRAR`. No se generan
`DROP TABLE`, `tFileDelete` ni limpieza por configuración: el SAS no demuestra que destruir la tabla
de destino sea seguro. La alternativa sería permitir una decisión explícita por programa en
`decisiones/<programa>.*.yaml`; cambiaría el Job al habilitar un borrado persistente revisable.

## `PROC COPY`

`PROC COPY IN=<libref> OUT=WORK; SELECT <miembros>;` se convierte en lectura y escritura por cada
miembro estático seleccionado. La sintaxis de `IN=`, `OUT=` y `SELECT` está en `proc.pdf`, pp.
573–575. Sin una lista estática se emite `P-COPY-SIN-LISTA`, porque la biblioteca puede contener
miembros que el migrador no conoce en ejecución. Si el destino no es `WORK`, se emite
`P-COPY-PERSISTENTE`; no se sobrescribe una biblioteca persistente sin decisión específica. Si
`IN=` y `OUT=` nombran la misma biblioteca, se emite `P-COPY-MISMA-BIBLIOTECA` porque el flujo no
modela copiar un miembro sobre sí mismo. Una alternativa sería enumerar y resolver las bibliotecas
durante la ejecución; eso requiere acceso al catálogo de origen y podría copiar miembros ajenos al
alcance esperado, así que no se activa automáticamente. Las opciones, banderas y nombres dinámicos
no modelados quedan pendientes.

## `PROC APPEND`

Con `BASE=` y `DATA=` estáticos y distintos, el operador escribe el resultado sobre `BASE=`; las
llamadas sucesivas actualizan versiones encadenadas de esa misma tabla (`proc.pdf`, pp. 161, 639).
Si una base nueva pertenece a `WORK` y no tiene escritor previo en el programa, se copia el flujo
de `DATA=` a ese nombre. Una base permanente sin escritor ni lector demostrable queda como
`P-APPEND-BASE-EXTERNA-SIN-FUENTE`: no se asume que exista ni se omite su contenido inicial.

No se emite la variante con `FORCE`. Si los esquemas conocidos muestran una columna adicional en
`DATA=`, el migrador deja `P-APPEND-COLUMNAS-DISTINTAS`; si el tipo difiere o la columna de
`DATA=` supera la longitud de `BASE=`, deja `P-APPEND-ATRIBUTOS-DISTINTOS`. SAS documenta esas
condiciones para `FORCE` en `proc.pdf`, p. 640. Cuando los nombres existen en ambos lados pero no
se puede demostrar el orden compatible que requiere el emisor, la unión también queda pendiente.
Las opciones de dataset, opciones PROC, sentencias adicionales, referencias dinámicas y la
autocopia de una tabla sobre sí misma conservan sus pendientes existentes; no se convierten a una
unión genérica.

## Reportes y `PROC CONTENTS`

Decisión C-22: la política predeterminada `reports=discard` omite `PRINT`, `REPORT`, `TABULATE`
y `FREQ` sin `OUT=` con `A-REPORTE-OMITIDO`. El aviso conserva archivo y líneas del SAS en
`not_migrated`; el reporte no se convierte en una transformación. PRINT imprime observaciones
(`proc.pdf`, p. 1810); REPORT combina presentación y cálculos (p. 2140); TABULATE presenta
estadísticos en tablas (p. 2554). Las páginas 1809, 2139 y 2553 localizan los capítulos, pero son
sus índices, no evidencia de cada opción.

La alternativa es un `tLogRow` por reporte: con miles de filas por ejecución, aumenta el volumen
y el coste del log y dificulta usarlo para diagnóstico. Se mantiene como opción explícita
`"reports": "log"` en `env/project.json`; solo `PROC PRINT` tiene equivalencia de filas implementada.
`reports=csv` también existe solo para PRINT. REPORT, TABULATE, FREQ y CONTENTS conservan el hueco
`REPORTE` con log/csv; sus resultados no se sustituyen por filas crudas. FREQ con `TABLES OUT=`
conserva `P-FREQ-OUT-SIN-PAGINA`: p. 89 no demuestra sus columnas ni su contenido.

`CONTENTS` sin OUT= se descarta con la misma política; sobre un miembro explícito de WORK
conserva el aviso específico `A-PROC-LIMPIEZA-OMITIDO`. Las salidas OUT= no se consideran
reportes descartables; `WORK._ALL_ OUT=` conserva `P-WORK-INTROSPECCION`.

## ODS, títulos y opciones

ODS es una sentencia global (`proc.pdf`, p. 75). La guía describe su presentación de resultados
(p. 122) y demuestra que ODS OUTPUT puede crear un dataset (p. 1525); esa página no demuestra
el esquema de una tabla arbitraria. Por eso `ODS OUTPUT tabla=dataset` siempre conserva
`Pendiente: P-ODS-OUTPUT-DATASET`, sus líneas de origen y ninguna salida inventada, incluso con
`reports=discard`. Si está dentro de un PROC, PROC SQL o DATA step, se conserva el bloque
completo como pendiente con su rango de líneas: el AST no mantiene todas las posiciones individuales.
No se materializa una parte del bloque suponiendo que la salida ODS no importa. Un signo igual dentro de un literal no prueba una asignación.

Con discard, los destinos de presentación conocidos HTML/HTML5/RTF/PDF/LISTING, SELECT/EXCLUDE,
RESULTS y OUTPUT CLOSE/CLEAR se registran como avisos, sin generar componentes. `lepg.pdf`, p. 707,
demuestra HTML y LISTING como destinos; las demás formas mantienen la política de omisión de
presentación, sin equivalencia de filas. Con log/csv se mantiene el comportamiento conservador:
ODS no se declara reproducido por Talend. Un ODS desconocido queda pendiente. TITLE y FOOTNOTE
se registran como presentación (`lestmtsref.pdf`, pp. 362, 123).

Esta decisión **no omite globalmente OPTIONS**. `docs/opciones-de-sistema.md` sigue siendo
la fuente autoritativa: MERGENOBY, MISSING, VALIDVARNAME y YEARCUTOFF pueden cambiar resultados.
La detección general de estas cuatro sigue pendiente de MG-P7-07; C-22 no la implementa ni le
atribuye equivalencia. Hoy YEARCUTOFF sigue como CONFIGURACION/reemplazado, sin aviso ni pendiente
específico; se conserva ese límite existente y no se cuenta como aceptación de OPTIONS.

## Inventario generado

`uv run python tools/cobertura_procs.py` escribe `docs/cobertura-procedimientos.md`. Clasifica los
65 capítulos reales del índice local y separa las menciones sin capítulo, sin inflar el denominador.
La prueba de frescura obliga a regenerarlo al cambiar sus fuentes. Una familia desconocida queda
`no_verificado`; `fuera_de_alcance` exige motivo de familia y página verificable. El inventario no
es una orden de omisión ni una afirmación de equivalencia completa o de ejecución en Studio.
G-17 lo integra en `docs/cobertura.md`; este generador nunca escribe el documento general.

## `DROP` y `DELETE FROM`

La misma cautela se aplica a `DROP` y `DELETE FROM` de `PROC SQL`: las tablas de `WORK` se pueden
omitir cuando su alcance es estático y está demostrado; las bibliotecas persistentes quedan
pendientes como `P-DML-PERSISTENTE`. Una acción `DROP` persistente solo se habilitaría mediante una
decisión explícita del programa; el Job resultante destruiría datos en el destino.
