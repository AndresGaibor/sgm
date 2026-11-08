# Registro de cambios

Todos los cambios notables de `sgm` se documentan en este archivo.

El formato sigue [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/) y la versión sigue
[Versionado semántico](https://semver.org/lang/es/). La versión vive en `pyproject.toml`; el resto
del código la lee de ahí.

## [Sin publicar]

### Añadido

- Compuerta de liberación `tools/liberacion.py` (MG-P14-02): `ruff`, suite, oráculo del corpus,
  determinismo byte a byte, secretos sobre la salida y coherencia de versión.
- Backend MCP del producto (`src/sgm/backend_talend/mcp.py`): habla con `talend-mcp` por HTTP
  JSON-RPC, acepta JSON o SSE, negocia sesión cuando el servidor la pide y comparte el mapeo de
  respuestas con la CLI (`comun.py`). Lo usan la librería y las herramientas de validación
  (`studio_salud.py --mcp`, `corpus_studio.py lote --backend mcp`).
- `docs/produccion.md`: qué falta para producir, con la compuerta, el avance y los bloqueos.
- `sgm studio salud|compilar|verificar`: la CLI del producto usa el backend MCP o la CLI de
  `talend-mcp` para comprobar Studio, compilar un lote y leer un veredicto, sin pasar por `tools/`.

### Corregido

- El mapeo de `talend_job_build_batch` y `talend_job_verify` reconoce el detalle anidado en
  `data.result.jobs` y en `data`, no solo la forma plana de la CLI.
- El backend MCP se probó contra el servidor real: la salud lee el sobre `data`, y un corte de
  conexión (`IncompleteRead`) se informa como `BackendNoDisponible` en vez de una traza.
- `tools/mcp_cliente.py` ya no duplica el protocolo MCP: usa el backend del producto y conserva
  `ErrorValidacion` para los validadores.
- Expresiones: se portaron a la estructura local los arreglos de COMPRESS, SCAN, LIKE e INPUT.
  Un informat dinámico queda pendiente y el mensaje ya no repite el texto del programa.
- Los huecos de expresiones citan el archivo y las líneas de la ocurrencia concreta, no los del paso
  completo.
- La comparación de la longitud de un arreglo con un literal no se confunde con una comparación de
  orden de SAS.

## [0.2.0]

Primera versión etiquetada del compilador. Lo que hay en esta versión sale de `PROGRESS.md` y del
historial de commits (`hito 0` a `hito 110m`).

### Añadido

- Frontend de SAS: nodos por etiqueta, pasos, expansor de macros con evaluación parcial, PROC SQL y
  DATA step básico.
- Pasadas 1 a 8 de la IR hacia la guía y el plan JSON (`compile`).
- Comandos de la CLI `sgm`:
  - `compile`: escribe `<programa>.guide.md` y `<programa>.plan.json`.
  - `metrics`: métricas, línea base y trinquete (`--check`).
  - `lineage`: oleadas de ejecución según las tablas permanentes.
  - `explain`: operadores, pasadas, huecos y notas de una línea.
  - `intake`: importa un lote a `corpus/inbox` (UTF-8, sin secretos, con sus huecos).
  - `facts` y `mapa`: hechos del programa y mapa de flujo sin traducir.
  - `diseno` y `proceso`: diseño de Jobs y documento del proceso en Markdown.
  - `talend`: escribe los Jobs del diseño en la carpeta de salida.
  - `migrar`: migra un programa a Jobs de Talend, con `process/`, contextos e informes.
  - `flujo`: HTML estático de revisión de un programa.
  - `conformidad`: estado de cada fila del diseño manual.
  - `comparar`: compara la exportación de SAS con la de Talend.
  - `secretos`: busca contraseñas, tokens y claves en claro.
  - `decisions` y `gaps`: decisiones del usuario por firma y alcance, e inventario de huecos.
  - `rules` (`new`, `validate`), `case new` y `env import-describe`: reglas, casos y esquemas de
    entorno.
- Catálogo de referencia SAS en `docs/referencia/` con páginas citadas por regla.
- Caché por proyecto y lotes en paralelo para `compile`.

### Seguridad

- Las credenciales de los programas de ejemplo se enmascaran como `'***'` (`proc pwencode` y
  `pass=` de `signon`). Una prueba vigila que no vuelvan a fixtures ni salidas.
