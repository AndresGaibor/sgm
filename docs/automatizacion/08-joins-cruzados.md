# Joins cruzados de client_large.sas (3 de noviembre de 2026)

Pregunta: ¿los 29 joins marcados como `cross` son un error del parser (falta un `ON`)?

Respuesta medida:

- No es un error del parser. Un `LEFT JOIN` o `INNER JOIN` con `ON` en la línea siguiente sí
  se reconoce (prueba directa con `sgm.ir.sql_tree.build`: tipo `left`, condición completa).
- Los casos marcados como `cross` son listas de `FROM` separadas por comas, sin condición de unión.
  Ejemplo: línea 4060 (`CONCILIACION_PROCESAR_DEP_AHO`), que une tablas de conteo y suma.
- Son productos cartesianos reales. Si cada tabla tiene una sola fila, el resultado es una fila
  y la unión es correcta. Si alguna tiene varias filas, el resultado multiplica filas.

Pendiente para cerrar: comprobar que cada tabla de esos joins produce exactamente una fila. Eso
requiere datos (ver `05-validacion-extremo-a-extremo.md`). Hasta entonces, la advertencia del
tMap (`tipo de unión cross ... revisar antes de migrar`) se mantiene.
