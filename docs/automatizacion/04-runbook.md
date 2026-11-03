# Runbook: incorporar un programa SAS nuevo

Objetivo: pasar un archivo `.sas` por el proceso y dejar su guía, su mapa y sus pendientes
revisados. Sin ejecutar nada contra bases ni contra Talend.

## 1. Importar

```powershell
uv run python -m sgm.cli intake <carpeta-o-archivo>
```

Copia el lote, pasa el texto a UTF-8 y quita las credenciales. Si el lote trae `pass=` o
`pwencode`, el informe lo dice y el original no se guarda en el lote.

## 2. Mirar los hechos

```powershell
uv run python -m sgm.cli facts <archivo.sas> --out out\hechos.json
uv run python -m sgm.cli mapa <archivo.sas> --out out\mapas
```

El mapa responde: qué conjuntos de datos se escriben y se leen, qué sale y entra del programa,
qué ramas hay por ambiente y qué queda sin interpretar. Revisar esto antes que la guía.

## 3. Ver lo que no se entendió

```powershell
uv run python -m sgm.cli gaps list --top 20
uv run python -m sgm.cli explain <archivo.sas>:<línea>
```

Cada hueco trae firma, motivo, dueño y el archivo que lo cierra (`rules/routing.yaml`).

## 4. Cerrar un hueco con una regla

- Una regla nueva va en `rules/mapping/` con `cuando`, `produce`, `prioridad` y `casos`.
- Su caso va en `tests/cases/<id>/expected.yaml`.
- Validar: `uv run python -m sgm.cli rules validate`.
- Si dos reglas de igual prioridad proponen componentes distintos, el programa lo reporta como
  decisión: no se elige una en silencio.

## 5. Compilar y revisar la guía

```powershell
uv run python -m sgm.cli compile <archivo.sas> --out out\guias
```

Revisar, en este orden:

1. Joblets: porqué, parámetros (su nombre y tipo siguen pendientes) y apariciones.
2. Componentes: regla, confianza y líneas de cada uno.
3. Pendientes: cada uno tiene dueño y cómo se cierra. Un pendiente de secreto o de decisión
   humana bloquea la construcción hasta resolverse.

## 6. Verificar que nada empeora

```powershell
uv run pytest -q
uv run ruff check .
uv run python -m sgm.cli metrics <carpeta> --check
```

El trinquete compara con `metrics/baseline.json`. Si una métrica empeora, el cambio no entra.

## 7. Registrar

Una línea en `PROGRESS.md` con el programa, los huecos cerrados y las métricas antes y después.

## Lo que este runbook no cubre

- La construcción del Job en Talend Studio: se hace a mano, siguiendo la guía.
- La equivalencia de datos con SAS: se valida con datos de prueba en un ambiente con ambos.

## Límites de rendimiento (fase 5.4)

Medido el 3 de noviembre de 2026 sobre `tests/fixtures/sas/client/client_large.sas` (24.801
líneas, 989 operadores):

- Compilación: 26 s.
- Memoria Python en el pico: 29 MB (medido con `tracemalloc`).

Límite vigilado por prueba: 120 s para el archivo de referencia. Por encima, la prueba falla y
hay que revisar qué cambió antes de aceptar el cambio.

## Generar y leer el flujo de un programa nuevo

1. Copia el programa a una carpeta de entrada, o pasa el archivo directamente.
2. Ejecuta `uv run sgm flujo <ruta> --out out`. Escribe un `.flujo.html` por programa en `out/`.
3. Abre el HTML en el navegador. Lee primero el resumen y el diagrama; después la tabla de pasos.
4. Revisa la sección **Pendientes**. Cada pendiente lleva el paso al que se refiere; si la causa es una
   macro dinámica, el flujo de esa parte no se puede seguir sin ejecutar el programa.
5. Si el diagrama es ilegible (más de 200 pasos), usa la vista por sección y baja a la tabla para el detalle.

El HTML es una vista de revisión. Nunca cambia el plan ni la guía, y no se sube a ningún lado.
