# Opciones de sistema que cambian el resultado

Una opción de sistema puede cambiar lo que un programa produce sin que se vea en el código: no está
en la sentencia que transforma, está en el entorno. El traductor tiene que decidir qué hace con eso
antes de traducir el primer `MERGE`.

Este documento fija la decisión. Las páginas salen de `docs/referencia/sas/lesysoptsref.pdf`; el
catálogo con las entradas es `rules/sas/catalogo/opciones-resultado.yaml`.

## Las cuatro que importan

| Opción | Página | Qué cambia |
|---|---|---|
| `MERGENOBY` | 265 | Si un `MERGE` sin `BY` avisa (`WARN`, por omisión), falla (`ERROR`) o calla (`NOWARN`). Con `ERROR` el programa no llega a ejecutarse; con `NOWARN`, un cruce cartesiano pasa inadvertido. |
| `MISSING=` | 266 | Qué caracteres cuentan como valor perdido, además del blanco y el punto. Afecta toda comparación y todo `SUM`. |
| `VALIDVARNAME=` | 412 | `V7`, `V6` o `ANY`: qué nombres de columna son válidos y cómo se leen los que traen caracteres raros. |
| `YEARCUTOFF=` | 432 | El siglo de un año de dos dígitos. Por omisión 1920: `yymmdd6.` con `010120` da 2020, pero con otro corte puede dar 1920. |

## Lo que hace el corpus hoy

En `client_large.sas` y en los 129 programas de `tests/corpus/` hay 146 sentencias `OPTIONS`, y
ninguna toca estas cuatro. Son de dos clases, y ninguna transforma filas:

- **Entorno**: `REMOTE=`, `COMAMID=` y `SASCmd=` (41, 41 y 30 usos). Configuran la sesión remota de
  SAS/CONNECT: `connref.pdf` p. 130, 123 y 135.
- **Diagnóstico**: `SYMBOLGEN`, `MLOGIC`, `MPRINT`, `SOURCE`, `SOURCE2` y `NOSYNTAXCHECK`, casi
  siempre con su forma `NO`. Encienden o apagan trazas del log: `mcrolref.pdf` p. 501, 485 y 489, y
  `lesysoptsref.pdf` p. 346, 347 y 381.

El catálogo `opciones-sistema.yaml` lista esas nueve con su página y su clase, y una prueba exige que
cada una aparezca de verdad en el programa grande: si una entrada no se usa, sobra.

## La decisión

1. **Un `OPTIONS` nunca se convierte en una transformación.** No mueve filas ni cambia tipos. Las de
   entorno y diagnóstico se anotan como fontanería y no se emiten en el Job.
2. **Si el programa fija una de las cuatro opciones que cambian el resultado, el paso lleva un
   `Pendiente:` con el nombre de la opción y su página.** No se asume el valor de omisión: el
   programa dice explícitamente lo que quiere, y traducirlo sin decirlo sería inventar.
3. **Si el programa no la fija, no se emite nada.** El valor de omisión del cliente no está en el
   repositorio; suponerlo es exactamente lo que el proyecto prohíbe.
4. **`YEARCUTOFF` tiene una excepción de lectura.** Si aparece un informat de año de dos dígitos
   (`yymmdd6.`, `date7.`, `mmddyy6.`) y el programa no fija `YEARCUTOFF`, la columna queda con
   `Pendiente: fecha de dos dígitos sin YEARCUTOFF` y no se le asigna un siglo.

## Estado

La decisión está escrita y las páginas están localizadas, pero **la regla no está codificada**: hoy
el traductor no mira las sentencias `OPTIONS` en busca de estas cuatro, y por eso el catálogo las
marca `no_verificada`. Implementarla pide tocar la pasada que lee las opciones y el registro de
pendientes; no se hizo en el mismo hito para no mezclar documentación con comportamiento.

Para cerrarla del todo hace falta además algo que el repositorio no tiene: el `autoexec` y los
scripts de lanzamiento del cliente. Sin ellos no se sabe qué valor corre en producción, y con ellos
la decisión 3 se puede afinar («el cliente corre con `YEARCUTOFF=1940`») en vez de dejarla genérica.
