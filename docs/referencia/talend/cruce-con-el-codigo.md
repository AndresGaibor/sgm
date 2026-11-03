# Cruce entre la documentación de Talend y el código de sgm

Revisión de las tareas 13 a 20 de la lista de 50. Cada punto dice qué dice la documentación
descargada, qué hace el código hoy (con archivo y línea) y qué queda pendiente. La documentación
es la de Talend Studio 8.0 R2026-09, la misma versión del inventario (`inventario.sha256`).

## Tarea 16: contextos y joblets

- **Documentación:** `studio-guia-jobs-contextos.md`, temas *Applying a context variable to a
  Joblet* y *Defining context variables*. Un joblet recibe el contexto del Job que lo llama, y las
  variables de contexto se definen en la tabla de contexto.
- **Código:** `src/sgm/generador.py:233`, `contexto_del_encabezado`, construye el joblet de contexto
  con las sentencias de entorno del encabezado (hito 39).
- **Estado:** el joblet de contexto no está conectado al plan ni a la guía. Por decisión de ese
  hito, sigue en la fase de diseño.

## Tarea 17: prueba del diseño de joblets frente a los contextos

- **Pendiente.** Probar que el diseño respeta el contexto exige que el joblet de contexto esté
  conectado al plan, y hoy no lo está (ver tarea 16). Escribir la prueba antes de la conexión
  solo fijaría un diseño incompleto. Se retoma cuando se conecte.

## Tarea 18: orden del Job padre (`tPrejob`, `tPostjob`, `tRunJob`)

- **Documentación:** `tprejob.md` dice "starts the execution of a prejob"; `tpostjob.md` dice
  "starts the execution of a postjob". `trunjob.md` dice que ejecuta el Job llamado "in the frame
  of the context defined".
- **Código:** `src/sgm/generador.py:42-43` trata `tRunJob` como una llamada y no como componente
  (`_SIN_COMPONENTE`). No hay ninguna línea de `src/sgm` que emita `tPrejob` ni `tPostjob` (búsqueda
  en `src/sgm/**/*.py`: cero coincidencias).
- **Brecha:** `docs/conventions.md` (sección 1) describe la estructura con `tPrejob` (conexiones) y
  `tPostjob` (cierre), y el código no la genera. La convención describe el destino, no lo que el
  código hace hoy. Queda registrado como brecha; no se cambia el código en esta revisión.

## Tarea 19: manejo de errores (`tDie`, `tWarn`, `tLogCatcher`, `tLogRow`)

- **Documentación:** `tdie.md` y `twarn.md` dicen que se relacionan con `tLogCatcher` y "generally
  make sense when used alongside a tLogCatcher". `tlogrow.md` dice que muestra datos en la consola
  de ejecución "to monitor data processed".
- **Código:** `src/sgm/emit/conventions/best_practices.py:27` y `:123` exigen manejo de errores
  (`tDie`, `tWarn`, `tLogCatcher` u otro catcher). Coincide con la documentación.
- **`tLogRow`:** `src/sgm/emit/conventions/infra.py:29` lo usa como `COUNT_COMPONENT`, para mostrar el
  conteo de registros. Coincide con su documentación.
- **Brecha (`tDie`):** `infra.py:27` define `ERROR_COMPONENT = "tDie"` para detener el Job ante un
  error. La documentación de `tDie` dice que dispara `tLogCatcher` "for exhaustive log before killing
  the Job". El código usa `tDie` para parar, pero no emite el `tLogCatcher` que la documentación
  describe; el propio `best_practices.py:27` sí lo reconoce como manejo válido. Falta emitirlo junto a
  `tDie` para no perder el registro del error. No se cambia el código en esta revisión.

## Tarea 13: expresiones de `tMap`

- **Pendiente.** `tmap.md` describe el editor, pero no trae el catálogo de funciones de expresión
  (StringHandling, TalendDate, etc.); la palabra "function" aparece solo en frases generales. El
  catálogo está en otras páginas de Talend que no se han descargado. Se necesitan antes de escribir
  `rules/talend/tmap-expresiones.yaml`.

## Tarea 14: motores de `tSQLTemplate`

- **Pendiente.** `tsqltemplate.md` no enumera los motores. Solo menciona MySQL y "access" de paso. La
  lista está en el desplegable *Database Type* de la interfaz, que la documentación no describe con
  nombres.

## Tarea 20: metadatos y conexiones del repositorio

- **Descargado:** tema *Creating a connection* (R2026-09) en `studio-guia-jobs-contextos.md`.
- **Pendiente:** la página *Creating metadata database* vive en otra ruta del sitio
  (`creating-using-metadata-talend-studio/8.0/`). No se descargó porque el descargador solo sigue la
  ruta de la guía de Studio.

## Tarea 15: opciones de `tJDBCConnection`

- **Hecho:** `tjdbcconnection-opciones.yaml`, con 14 propiedades extraídas de sus tablas (Basic
  settings, Advanced settings, Global Variables). Herramienta: `tools/referencia/opciones.py`.
