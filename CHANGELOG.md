# Registro de cambios

Todos los cambios notables de `sgm` se documentan en este archivo.

El formato sigue [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/) y la versión sigue
[Versionado semántico](https://semver.org/lang/es/). La versión vive en `pyproject.toml`; el resto
del código la lee de ahí.

## [Sin publicar]

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
