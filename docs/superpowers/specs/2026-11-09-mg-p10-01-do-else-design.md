# MG-P10-01: interpretar `IF ... THEN DO` con `ELSE` en el anillo B

## Intención

El caso `L0/l0_13_do_end` ya tiene un esperado independiente, pero el plan separa el `IF`, las
asignaciones del bloque y el `ELSE` en pasos que el intérprete no puede asociar. El `ELSE` termina
como filtro y el anillo B no calcula el programa.

## Objetivo y límites

- Reconocer el patrón documentado `IF expresión THEN DO;` con asignaciones simples, `END;` y un
  `ELSE` que asigna una variable.
- El parser conserva `IF ... THEN DO` como una sola sentencia `if`; las asignaciones del grupo,
  `END` y `ELSE` son las sentencias siguientes.
- Bajar cada destino a la estructura condicional existente en una sola derivación lógica. La rama
  que no asigna un destino conserva su valor actual del PDV; esto es necesario para `saldo`, leído
  con `SET` y modificado solo cuando la condición es verdadera.
- Solo se acepta el patrón si las variables usadas por la condición no se cambian antes de la última
  asignación del grupo; los consumidores evalúan cada asignación en orden y no guardan una copia de
  la condición evaluada al entrar al grupo.
- Reutilizar las estructuras que ya ejecutan el intérprete y emite Talend; no agregar una excepción
  al intérprete que deje la IR incorrecta.
- En el emisor, una rama alternativa que conserva el destino conserva también el tipo ya demostrado
  por la columna de entrada, que prevalece sobre un tipo intermedio inferido de una asignación
  anterior; si no existe en las entradas, se conserva el tipo previo demostrado.
- Dejar fuera los bloques con otras sentencias, bloques anidados, múltiples alternativas u otras
  formas no cubiertas. Se conservan como parciales o pendientes.

## Enfoques considerados

- Agrupar el patrón en el lowering a una `derive` con asignaciones condicionales. Es el cambio
  elegido porque mantiene el significado en la IR y reutiliza el intérprete y el emisor existentes.
- Enseñar solo al intérprete a reconstruir la rama a partir de `IF`, `DO`, `END` y el filtro `ELSE`.
  Se descarta porque dejaría el plan lógico y el Job emitido con la estructura equivocada.
- Interpretar cualquier sentencia dentro de un bloque `DO`. Se descarta porque sentencias como
  `OUTPUT`, `DELETE` o bloques anidados necesitan semánticas adicionales no demostradas aquí.

## Evidencia y aceptación

La guía define `IF expression THEN statement` y permite que `statement` sea un grupo `DO`; `ELSE`
da la acción alternativa si no se ejecuta `THEN` y debe seguirlo inmediatamente (`lestmtsref.pdf`,
pp. 132-133). La guía del PDV describe cómo las variables leídas se escriben al PDV y cómo se
reinicia en iteraciones posteriores (`lrcon.pdf`, pp. 496-498). Una prueba integrada debe ejecutar
filas negativas, positivas y faltantes, incluyendo el valor de entrada que `ELSE` deja intacto.
Después, el caso deja de ser `xfail` solo si el anillo B coincide con su `esperado/` sin alterar ese
esperado. El hito se cierra con la suite completa y Ruff en verde.
