# Plan de implementación: seguridad del emisor MG-P13-05

## Pasos

1. Añadir pruebas rojas de extremo a extremo para tabla SQL hostil y name literal Java, más pruebas
   unitarias para nombre de contexto y literales Java con controles.
2. Rechazar identificadores SQL no portables en el AST completo antes del lowering; dejar un
   pendiente seguro con motivo explícito y sin emitir operadores ejecutables.
3. Validar name literals, referencias completas y nombres portables de fila/campo al formar
   expresiones del `tMap`; validar de nuevo el esquema y las expresiones en el límite público del
   componente; dejar la asignación no soportada como pendiente.
4. Validar nombres de contexto declarados en decisiones y constructores públicos que los interpolan.
5. Unificar los literales Java del traductor inline, las dos rutas `_jstr` y `jobs_diseno.java`
   mediante un helper común; escapar rutas y validar segmentos de nombres de archivo, rechazar
   escapes Unicode peligrosos y verificar apóstrofes duplicados en SQL.
6. Actualizar la referencia SAS del catálogo si la regla de nombres se registra ahí, el plan maestro
   y `PROGRESS.md`; correr suite completa, Ruff, validador de reglas y diff-check; revisión
   independiente y commit local `hito 135: bloquear identificadores hostiles en emision`.

## Aceptación

- El `name literal` de tabla no puede alterar ni entrar a una consulta generada para la base.
- Un name literal que no sea un campo Java portable queda como pendiente y no produce fragmentos
  de sentencia Java.
- Esquemas y expresiones entregados directamente al generador tMap también pasan validación.
- Las rutas/nombres de archivo generados no pueden cerrar o alterar un literal Java.
- Un árbol SQL mutado después del parseo no elude la validación de identificadores ni de estructura.
- Nombres de contexto con sintaxis no válida fallan antes de escribir código Talend.
- Las cadenas Java conservan su contenido con los controles escapados.
- Una cadena SAS que contiene apóstrofes duplicados sigue siendo un único literal SQL.
- No se ejecuta SQL o Java y no se añaden dependencias.
