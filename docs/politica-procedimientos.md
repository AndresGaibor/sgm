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

## Reportes y `PROC CONTENTS`

El valor predeterminado `reports=discard` omite la salida impresa con un aviso. Solo `PROC PRINT`
tiene equivalencia implementada para los modos `log` y `csv`; `REPORT`, `TABULATE` y las salidas
`OUT=` de `CONTENTS` permanecen pendientes cuando no se demuestra que el resultado coincide.
Alternativa: escoger `reports=log` o `reports=csv` para `PROC PRINT`; el cambio es materializar las
filas o escribirlas a un archivo configurado. Los demás formatos requieren una regla respaldada por
la documentación SAS y pruebas con un resultado verificable.

## `DROP` y `DELETE FROM`

La misma cautela se aplica a `DROP` y `DELETE FROM` de `PROC SQL`: las tablas de `WORK` se pueden
omitir cuando su alcance es estático y está demostrado; las bibliotecas persistentes quedan
pendientes como `P-DML-PERSISTENTE`. Una acción `DROP` persistente solo se habilitaría mediante una
decisión explícita del programa; el Job resultante destruiría datos en el destino.
