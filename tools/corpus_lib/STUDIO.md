# Arnés de Studio del corpus

Ejecuta Jobs de Talend ya emitidos con las entradas de un caso del corpus y compara su salida con
`esperado/`. Así cualquier traductor, el actual o uno futuro, se prueba contra el corpus.

Código: `tools/corpus_studio.py` (CLI) y `tools/corpus_lib/studio_*.py`. Plan: sección 6 de
`docs/plan-reescritura/plan-corpus-y-equivalencia.md`.

## Uso

```
# Sin Studio: compara una carpeta de salida ya producida (es lo que va a pytest)
uv run python tools/corpus_studio.py comparar <caso> --salida <carpeta>

# Con Studio: copia las entradas, ejecuta el padre, compara y borra los Jobs de prueba
uv run python tools/corpus_studio.py validar <caso> --jobs <carpeta_jobs> --padre <job_padre> \
    --proyecto <carpeta_del_proyecto> [--mapa mapa.yaml] [--contexto clave=valor ...] \
    [--java-bin <jdk\bin>] [--m2 <.m2>] [--informe <archivo.md>]
```

`--proyecto` acepta también la variable `TALEND_PROJECT`. `--contexto` se puede repetir.

Código de salida: 0 solo si todos los CSV del caso coinciden; 1 si hay diferencias o un error de
Studio; 2 si el uso o un archivo no son válidos.

## Carpeta de Jobs

Contiene el par `<job>_<versión>.item` y `<job>_<versión>.properties` del padre y de sus hijos
(`tRunJob`). La versión puede ser `0.1`, `0.2` o `1.0`: `renombrar` la lee del nombre del archivo
y recalcula los ids del `.properties` con la versión real.

## Mapa de contexto

`mapa.yaml` es un mapa plano de variable de contexto a ruta relativa al caso:

```yaml
ruta_origen: entradas/ventas.csv     # archivo: debe existir en el caso
ruta_clientes: entradas/clientes.csv
ruta_resultados: salida/             # carpeta: termina en / y el Job escribe dentro
```

Las rutas se resuelven dentro de una copia de trabajo (`entradas/` del caso más `salida/`). El
original del repositorio no se toca. Las rutas no pueden ser absolutas ni tener `..`.

## Protocolo de `validar`

1. Copia `entradas/` (y `entradas_preparadas/` si existe) a una carpeta temporal y crea `salida/`.
2. Renombra los Jobs con un sufijo nuevo (`cs` más fecha) y los copia a `process/` del proyecto.
3. Refresca el workspace, compila los hijos, compila el padre, exporta y ejecuta el lanzador con
   `--context_param` para cada variable del mapa.
4. Compara `salida/*.csv` con `esperado/*.csv`. Los nombres se emparejan sin distinguir
   mayúsculas.
5. Borra del proyecto los Jobs de prueba y refresca el workspace, aunque falle.

## Comparación

- Columnas con el mismo nombre y orden. `--ignorar-orden-columnas` acepta otro orden.
- Filas como conjunto, salvo `orden_relevante: true` en `caso.yaml`.
- Números con la `tolerancia` del caso. Texto con blancos finales ignorados. Vacío igual a vacío.
- Diferencias concretas: `fila N, columna 'X': esperado 'a', obtenido 'b'`, más faltantes y
  sobrantes. El número de fila es el de `esperado/`.

## Hallazgos del protocolo

Los cuatro primeros los corrigió el hito 80 (R0-02) en `tools/validar_en_studio.py`, y el arnés
usa esas funciones en vez de una copia (R0-03):

- El servidor deja el lanzador en una subcarpeta, `<destino>/<job>/<job>_run.bat`. `exportar` lo
  busca en todo `<destino>` con `rglob`.
- `renombrar` acepta Jobs de cualquier versión, no solo `0.1`.
- `ejecutar` entrecomilla el lanzador, el contexto y cada `--context_param`, así que las rutas con
  espacios funcionan.
- La carpeta `build-*` de `%TEMP%` se borra al terminar, en el mismo `finally` que borra los Jobs
  de prueba del proyecto. Si hace falta inspeccionar el build, se copia antes: ya no se queda.

Sigue en pie: Studio cachea el modelo de cada Job por su identificador, así que cada intento
necesita un sufijo nuevo (`cs` más la fecha).

## Pruebas

`tests/unit/test_corpus_studio.py` cubre el comparador, el modo `comparar` con una salida copiada
y otra alterada, el mapa y la limpieza, con un doble del cliente MCP y un lanzador falso. No
necesita Studio. `tests/unit/test_tools_validar_en_studio.py` cubre las cuatro correcciones del
protocolo por separado.
