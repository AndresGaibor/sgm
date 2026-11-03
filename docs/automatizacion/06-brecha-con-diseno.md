# Brecha entre la salida automática y el diseño de referencia

Medido el 3 de noviembre de 2026 sobre `tests/fixtures/sas/client/client_large.sas`
(24.801 líneas). El diseño de referencia es `docs/diseno-talend-exogena-depositos.md`.

| Métrica | Diseño de referencia | Salida automática hoy |
|---|---|---|
| Jobs | 1 padre + 4 etapas + joblets | 1 Job, 155 Jobs hijos |
| Subjobs | pocos, uno por etapa | 261 |
| Componentes reales | unos 80 | unos 540 |
| `tMap` | pocos, por etapa | 175 |
| `tRunJob` (llamadas) | unas pocas (`tFlowToIterate`) | 153 |
| Joblets | unos pocos | 81 (uno por forma repetida) |
| Contextos | grupos por entorno y parámetros por producto | 1 grupo de ambiente, 0 variables |
| SQL en la base | un `tDBInput` con `WITH` por sabana | 1 operador `exec_sql` |
| Operadores sin traducir | 0 | 164 (`unsupported`) |

## Qué se midió sobre la causa

- **Llamadas repetidas (`tRunJob`):** las instancias de una misma forma se agrupan ahora en todo
  el programa, y un bloque colapsa en un `iterate` mientras no cree un ciclo. Eso bajó 160 a 153.
  El resto no se puede colapsar: las instancias están intercaladas con pasos compartidos, y en el
  orden topológico la secuencia de plantillas no es periódica. Una detección de periodos no sirve.
- **`tMap` (175):** vienen de `derive`, `join` y `map` que no se fusionan en una sola cadena.
- **Operadores sin traducir (164):** sentencias que el traductor no cubre; son huecos reales.

## Qué falta para llegar al diseño

1. **Agrupar por bloque de fuente, no por orden topológico.** En el archivo, las 30 copias del
   bloque son regiones de código con el mismo esquema. Un bloque por región de fuente, comparado
   por forma, da una sola plantilla con 30 contextos.
2. **Un Job por etapa.** Partir el plan por fronteras (`Plan.fronteras`) y por cargas externas.
3. **Fusión a SQL.** Operadores de base consecutivos en un solo `tDBInput` con `WITH`. Requiere
   generar SQL desde la IR para las sentencias que hoy van al flujo.
4. **Contextos.** Rutas, bases y nombres de conjuntos de datos como variables de contexto.

Cada punto se puede medir con la misma tabla. El objetivo es que la tabla de arriba se acerque a
la columna de la izquierda sin tocar el archivo de referencia a mano.

## Mediciones deterministas adicionales (3 de noviembre de 2026)

Estas medidas sustituyen la premisa de "30 bloques idénticos" del diseño de referencia.

- **Regiones por `%macro ambiente`:** 30 regiones, pero solo 6 comparten el mismo multiconjunto de
  tipos de operador, y solo 1 tiene la misma longitud que la primera. La región 0 tiene 82
  operadores y la región 1 tiene 15. No son copias del mismo bloque.
- **Sub-cadenas repetidas de operadores:** con longitud 3 hay 30 tipos de cadena repetida que
  cubren el 62 % de los operadores secuenciales. Como joblet, cada aparición sigue siendo una
  llamada: unas 171 llamadas, no una. No baja los componentes visibles de forma útil.
- **Fusión de cadenas lineales de componentes:** de 330 componentes reales a 210 cadenas. 163 de
  esas cadenas son un solo componente, porque hay puntos de ramificación.

Conclusión medida: con transformaciones deterministas sobre la estructura, el techo para este
archivo está cerca de 200 componentes visibles, no de 80. Llegar a 80 exige unir sabanas
distintas en pocos jobs, y eso es una decisión sobre qué procesos son el mismo proceso. El
archivo no lo dice por estructura.
