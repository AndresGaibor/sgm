# MG-P10-01: aridad de agregados PROC SQL — Plan de implementación

> Ejecutar en línea; un solo hito, sin tocar el emisor Talend.

**Objetivo:** distinguir en el anillo B las funciones numéricas Base SAS de varios argumentos de
los agregados PROC SQL de un argumento, según sqlproc pp. 433 y 435–436 y lefunctionsref pp. 1230,
1233–1234, 1236 y 1580–1581.

**Diseño:** docs/superpowers/specs/2026-11-09-mg-p10-01-aggregate-arity-design.md.

## Task 1: Implementar la aridad documentada de funciones numéricas

## Pasos

1. Escribir regresiones integradas: llamadas multiargumento de SUM/MIN/MAX/MEAN deben conservar
   una fila por entrada; también comprobar MEAN de un argumento como agregado SQL. Los faltantes se
   ignoran y una lista toda faltante produce missing.
2. Confirmar RED porque sqlglot rechaza la aridad SAS de los nombres SQL integrados.
3. Proteger llamadas multiargumento antes del parseo y restaurar sus nombres SAS en las expresiones
   de IR; no proteger AVG multiargumento.
4. Implementar la evaluación numérica por fila de SUM/MIN/MAX/MEAN; mantener MEAN y AVG de un
   argumento como agregados de promedio, y rechazar AVG multiargumento de forma visible.
5. Verificar literales, comas anidadas, comentarios, funciones de un argumento y resultados del
   traductor sin cambiar los esperados.
6. Actualizar PROGRESS.md y el plan maestro con páginas, límites, métricas y estado del emisor.
7. Ejecutar la suite completa, Ruff, rules validate y diff check.
8. Commit local: hito 131: distinguir agregados SQL de funciones por fila.

## Verificación

- La entrada con varios argumentos conserva la cantidad y orden de filas del SAS.
- Las pruebas deben comparar los valores, incluidas filas con faltantes y todos los faltantes.
- La forma AVG de varios argumentos nunca se interpreta como resumen agregado.
- No se afirma equivalencia Talend ni se modifica el golden del corpus.
