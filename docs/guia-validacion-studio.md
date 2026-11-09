# Guía de validación en Studio

Cómo comprobar que un Job emitido por `sgm` compila y **ejecuta** en Talend Studio 8.0.1. Compilar
no basta: varias veces compiló y falló al ejecutar, así que la validación termina con las filas de
salida miradas. Esta guía reúne el protocolo, los hechos ya aprendidos y los comandos; el plan de
tareas es `docs/plan-reescritura/ruta-a-produccion.md`.

Si eres nuevo en el proyecto, lee la guía entera antes de tocar Studio. Todo lo que está aquí se
pagó con un fallo real.

## 1. Qué hace falta

| Pieza | Valor de referencia | Nota |
|---|---|---|
| Studio | Talend 8.0.1 con el proyecto `PRJ_BANCOLOMBIA` | Ruta típica `C:/Talend/8.0.1/studio/workspace3/talendbancolombia-963626413/PRJ_BANCOLOMBIA`. **La ruta la decide el Studio abierto, no la carpeta `workspace/`:** pregúntala con `talend_bridge_workspace_state` (campo `location`). En `workspace/` Studio no ve nada y todo da «El job no existe en el repositorio» |
| JDK de Studio | `C:/Talend/8.0.1/zulu21.50.19-ca-jdk21.0.11-win_x64/bin` | El lanzador exportado lo necesita en el `PATH` |
| `talend-mcp` | repositorio aparte, puerto 3927 | Se arranca con `TALEND_MCP_ALLOW_WRITE=1 TALEND_MCP_ALLOW_EXECUTE=1 bun run start:server` |
| Caché de Maven | `C:/Talend/8.0.1/studio/configuration/.m2/repository` | Los poms que falten se descargan solos |

Comprobaciones antes de empezar:

```bash
curl -s http://127.0.0.1:3927/healthz
test -f "<proyecto>/talend.project" && echo "proyecto OK"
```

`talend-mcp` se usa desde `sgm` solo a través de `src/sgm/backend_talend/`: el backend `mcp` habla con
el servidor ya arrancado y el backend `talend` con su CLI. El núcleo no depende de él:
`ArchivosBackend` escribe los Jobs sin Studio.

La librería expone el mismo servidor como backend (`sgm.backend_talend.McpBackend`) y las
herramientas lo usan sin pasar por estas dos: `tools/studio_salud.py --mcp` comprueba la salud y
`tools/corpus_studio.py lote ... --backend mcp` compila en lote. La URL sale de `TALEND_MCP_URL` (por
omisión `http://127.0.0.1:3927/mcp`). `sgm migrar` sigue escribiendo los archivos; compilar es un
paso aparte.

La CLI del producto da las mismas tres operaciones sin escribir Python:

```bash
uv run sgm studio salud
uv run sgm studio compilar JOB [JOB ...] [--refrescar]
uv run sgm studio verificar JOB [--contexto CLAVE=VALOR ...]
```

`--backend mcp` (por omisión) usa el servidor ya arrancado; `--backend talend --talend-dir <carpeta>
--proyecto <proyecto>` usa la CLI, y si faltan las rutas toma `SGM_TALEND_DIR` y
`SGM_TALEND_PROJECT`. `salud` sale 0 solo si Studio responde, deja escribir y no tiene
diálogos; `compilar` imprime `OK`/`FALLA` por Job y sale 1 si alguno no compila; `verificar` imprime
el veredicto y sus hallazgos, y sale 1 solo con `error`.

## 2. Dos comandos, según lo que se valide

Los dos hablan con el servidor por HTTP y borran los Jobs de prueba aunque fallen.

**Un programa completo** (emite, renombra, compila, exporta y ejecuta el padre):

```bash
uv run python tools/validar_en_studio.py tests/fixtures/sas/client/client_large.sas \
    --project "$TALEND_PROJECT" --insumos <carpeta_exceles> --productos <carpeta_csv> \
    --sufijo v1 --contexto DEV --java-bin <jdk>/bin --m2 <caché .m2>
```

**Un caso del corpus, comparando la salida con la esperada** (lo que exige el plan para cerrar una
tarea que genera Jobs):

```bash
uv run python tools/corpus_studio.py validar <caso> --jobs <carpeta_jobs> --padre <job_padre> \
    --proyecto "$TALEND_PROJECT" --mapa mapa.yaml [--contexto clave=valor ...] \
    [--java-bin <jdk>/bin] [--m2 <caché .m2>] [--informe informe.md]
```

Salida 0 solo si todos los CSV del caso coinciden; 1 si hay diferencias o error de Studio; 2 si el
uso no vale. La salida literal (`N casos, M coinciden` y la celda exacta si difiere) se pega en
`PROGRESS.md`: un informe de agente no es evidencia.

Detalle del arnés y del formato de `mapa.yaml`: `tools/corpus_lib/STUDIO.md`.

## 3. Protocolo, paso a paso

1. **Nombre nuevo en cada intento.** Studio guarda en memoria cada Job por su identificador: si
   reemites el mismo nombre con otro contenido, compila la versión vieja aunque refresques el
   workspace. Los dos comandos ponen sufijo solos (`v1`, `v2`, `cs<fecha>`); si lo haces a mano, usa
   uno distinto cada vez.
2. **Copiar** los `.item` y `.properties` a `<proyecto>/process/`.
3. **Refrescar** el workspace (`talend_bridge_refresh_workspace`).
0. **Lotes pequeños.** El puente corta cada llamada a los 25 s: un lote de 85 Jobs lo deja a Studio compilando
   minutos después de que el cliente se rinda, y hasta que termine no contesta ni el refresco. Usa
   lotes de 4 a 8 Jobs, espera a que `comprobar_salud` dé `ok` entre uno y otro, y no borres los
   Jobs mientras Studio sigue compilando.
4. **Compilar los hijos primero** y el padre en una llamada aparte: en paralelo el padre puede
   fallar porque los hijos aún no están compilados. Hay que leer `jobs[...].ok` y el error de javac,
   no solo el código de salida.
5. **Exportar** el Build Job con `talend_deliverables_build_job`. El servidor deja el lanzador en
   `<destino>/<job>/<job>_run.bat`, no en la raíz; `exportar` lo busca en todo el destino.
6. **Ejecutar** el lanzador con el JDK de Studio en el `PATH`, con `--context` y uno o más
   `--context_param clave=valor`. Cada valor va entre comillas: las rutas con espacios, si no, se
   parten y el lanzador rechaza la ejecución. La consola muestra mal las tildes; no es un error.
7. **Borrar** del proyecto los Jobs de prueba y refrescar el workspace, aunque falle. El build
   temporal de `%TEMP%` también se borra (`build-*`): si hace falta inspeccionarlo, se copia antes.

## 4. Hechos de Studio ya aprendidos

No los redescubras; si alguno deja de cumplirse, anótalo en `PROGRESS.md`.

- Una conexión **Run if** con `ACTIVATE=false` está desactivada; si está activa, Studio omite el
  parámetro.
- La plantilla extraída de un componente desactivado no genera código: la extracción descarta
  `ACTIVATE`.
- `tDie` en un Prejob **no** detiene el flujo principal salvo con `EXIT_JVM=true`.
- `tFileInputExcel` con `VERSION_2007` no compila si `PASSWORD` está vacío o vale `***` (Studio lo
  toma como máscara): se pasa un marcador normal.
- `lineStyle` verificados: fila 0, OnSubjobOk 1, OnComponentOk 3, Run if 6, Iterate 7, lookup 8
  (`FLOW_REF`), merge 10, paralelizar 13. `OnSubjobError` y `OnComponentError` no tienen ejemplo
  real todavía (tarea R2-05).
- La fuente de un `OnSubjobOk` es el nodo de inicio del subjob, no el último componente.
- El código `CODE` de `tDie` y `tWarn` es el código de salida numérico, no código Java.
- La exportación pide poms públicos de Maven que pueden faltar en la caché de Studio
  (`logging-parent`, `log4j-bom`…). Se descargan a `<studio>/configuration/.m2/repository`; si
  aparece otro, el error está en `workspace/.metadata/.log` (busca "could not be resolved").
- El validador de `talend-mcp` rechaza salidas de `tReplicate` (toma `MAX_OUTPUT` ausente como 0);
  en Studio no tienen límite. Esas conexiones se escriben directamente.
- **No** uses `talend_job_execute`: no carga los archivos de contexto y el grupo `DEV` no se
  encuentra. **No** uses `talend_job_verify` ni la creación de Jobs en vivo: un diálogo "Network
  Issue" de Studio los bloquea y no hay que cerrarlo. La ruta sin interfaz funciona.
- Con `CONNECTION` de Impala, `IMPALA_ADDITIONAL_JDBC=";auth=noSasl"` es obligatorio en pruebas: sin
  eso el cliente inicia SASL y se cuelga. `PASS` vacío o `""` no compila (Studio genera
  `if ( != null && false)`); se pasa un valor cualquiera y la rama LDAP no se ejecuta.
- Los archivos `.py` de `talend_item` están en CRLF. Al editarlos desde Bash no uses `\n` ni `\b`
  dentro de heredocs (se corrompen): escribe el script a un archivo y cópialo. Revisa
  `git diff --stat` para no reescribir archivos enteros.

## 5. Demostración registrada

Hito 79, caso `l2_01_inner_join_clientes_ventas` con un Job escrito a mano
(`tFileInputDelimited`, `tMap` con lookup `INNER JOIN`, `tFileOutputDelimited`):

```
1 casos, 1 coinciden
```

y, con una salida alterada a propósito (monto 655 por 656):

```
fila 1, columna 'monto': esperado '655', obtenido '656'
```

código de salida 1 y ningún Job de prueba en `process/`.

## 6. Lo que no se puede comprobar sin Studio

- Que un Job emitido por el emisor (no escrito a mano) ejecute: hasta el hito 79 solo se compiló.
- Jobs con hijos (`tRunJob`) y casos con varias salidas en el arnés.
- La tolerancia numérica y `orden_relevante` del comparador, más allá de las pruebas sin Studio.
- El código de salida real del lanzador en PowerShell: en el hito 72 no se capturó.
- La escritura a base (`tPostgresqlOutput`): el generador de Studio falla con un nodo escrito
  offline (`dbType` nulo).

Estas faltas se anotan en `PROGRESS.md` como no verificadas; nunca como verdes.

## 7. Recuperar Studio cuando no responde (Windows, hito 143m)

Síntoma: `sgm studio salud` responde «no se pudo contactar al MCP en http://127.0.0.1:3927/mcp: ...
conexión denegada» aunque Talend Studio esté abierto. Es el caso más frecuente: **Studio puede estar
arriba y el servidor `talend-mcp` apagado.** Son dos procesos distintos.

Diagnóstico en 30 segundos (PowerShell o Git Bash):

```bash
tasklist | grep -i talend                      # Studio: Talend-Studio-win-x86_64.exe
netstat -ano | grep -E ":3927|:3930"           # 3930 = bridge de Studio; 3927 = talend-mcp
curl -s -m 10 http://127.0.0.1:3927/healthz    # debe responder {"ok":true,"service":"talend-mcp",...}
```

- 3930 escuchando y 3927 sin escuchar: el MCP está apagado. Arrancarlo (abajo).
- Ninguno escucha: abrir Talend Studio con el proyecto `PRJ_BANCOLOMBIA` y esperar a que cargue.

Arrancar `talend-mcp` (repositorio aparte, en `C:\Users\USUARIO_BISOLUTION1\code\talend-mcp`). Con
permiso de escritura y ejecución, como exige el protocolo:

```bash
cd /c/Users/USUARIO_BISOLUTION1/code/talend-mcp
TALEND_MCP_ALLOW_WRITE=1 TALEND_MCP_ALLOW_EXECUTE=1 nohup bun run start:server > <log> 2>&1 &
```

Luego espera unos 15 s y comprueba `curl http://127.0.0.1:3927/healthz`. El log debe decir
«Proyecto Talend detectado: C:/Talend/8.0.1/.../PRJ_BANCOLOMBIA». Si el log dice que no encuentra el
proyecto, Studio no está abierto con ese workspace: ábrelo y repite.

El proceso no sobrevive a reinicios ni a cerrar la terminal que lo lanzó. Tras un reinicio, repetir.
No hace falta reinstalar nada: `talend-mcp` tiene sus dependencias en `node_modules` y `bun` está en
`C:\Users\USUARIO_BISOLUTION1\.bun\bin\bun`.

**En este entorno Windows, las órdenes de `uv` y de `sgm` pueden fallar** con «Una directiva de Control
de aplicaciones bloqueó este archivo (os error 4551)». Usar el módulo de Python en su lugar:

```bash
uv run python -m pytest -q               # en lugar de: uv run pytest
uv run python -m sgm.cli studio salud    # en lugar de: uv run sgm studio salud
```

**Validar un programa del corpus en Studio** (`tools/corpus_studio.py validar`), con los errores que ya
costaron tiempo:

1. `--padre` es el nombre del Job sin sufijo de versión: `job_programa`, no `job_programa_0`. El
   archivo se llama `job_programa_0.1.item`, pero el nombre del Job es `job_programa`.
2. Las rutas de contexto del `.item` son marcadores `.../entradas/x.csv`. Sin `--mapa`, el Job falla con
   «java.io.IOException: El sistema no puede encontrar la ruta especificada» en el primer
   `tFileInputDelimited`. Hay que pasar un `mapa.yaml` con cada variable de contexto:

   ```yaml
   ruta_clientes: entradas/clientes.csv
   ruta_clientes_nivel: salida/clientes_nivel.csv
   ```

   El mapa va en un archivo fuera del repositorio (en el scratchpad) y sus rutas son relativas al caso.
3. Rutas de los JDK y de `.m2` de Studio: `--java-bin "C:/Talend/8.0.1/zulu21.50.19-ca-jdk21.0.11-win_x64/bin"`
   y `--m2 "C:/Talend/8.0.1/studio/configuration/.m2/repository"`.
4. El comando exitoso de referencia (caso `l0_07_if_then_else`, hito 143m):

   ```bash
   uv run python tools/corpus_studio.py validar l0_07_if_then_else \
       --jobs <carpeta>/process --padre job_programa \
       --proyecto "C:/Talend/8.0.1/studio/workspace3/talendbancolombia-963626413/PRJ_BANCOLOMBIA" \
       --mapa <mapa.yaml> --java-bin <jdk>/bin --m2 <.m2> --sufijo len2 --informe <informe.md>
   ```

   Resultado: `coincide`, 0 diferencias. Demuestra que `nivel` sale con largo 5 y el Job ejecuta.
