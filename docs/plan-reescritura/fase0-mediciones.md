# Fase 0: mediciones sobre `client_large.sas`

Programa: `tests/fixtures/sas/client/client_large.sas` (24.801 líneas, 30 regiones `%macro ambiente`).
Reproducible con `uv run python tools/medir_fase0.py` (unos 8 s). Escribe
`docs/plan-reescritura/fase0-mediciones.json` sin fechas: dos corridas dan el mismo archivo. No toca
`src/`. Los sufijos de producto salen de `decisiones/client_large.agrupacion.yaml`.

## Conclusiones

| Hipótesis | Veredicto | Número que la sostiene |
|---|---|---|
| H1: la mayor parte del programa es fontanería | Confirmada | 41,0 % por patrón de reglas; 68,5 % contando lo que las cargas masivas absorben. Quedan 780 de 6.466 operadores (12,1 %), y unos 607 (9,4 %) son de datos. |
| H2: la mayoría de las tablas WORK son aristas, no persistencias | Confirmada con matices | 640 de 810 escrituras WORK (79 %) se leen solo dentro de su región. Pero hay 30 tablas que el programa sí persiste en la base (22 las relee). |
| H3: sin fontanería las regiones son mucho más parecidas | **Refutada** | La mediana de similitud entre pares baja de 0,75 a 0,20 al quitar la fontanería. |

## H1. Fontanería

Criterio: las categorías de `rules/sas/plumbing.yaml` (pasada 2) más lo que la pasada 3 absorbe en
una carga externa. Universo: los 6.466 operadores del grafo justo después de la pasada 1 (incluye
164 escrituras finales que añade esa pasada). Los 4.808 ítems del programa dan en promedio más de un operador
cada uno, así que el denominador son operadores, no sentencias.

| Concepto | Operadores | % de 6.466 |
|---|---|---|
| Marcados como fontanería por patrón | 2.651 | 41,0 |
| De ellos, quitados sueltos | 1.029 | 15,9 |
| De ellos, absorbidos por una carga externa | 1.622 | 25,1 |
| Absorbidos por una carga sin ser fontanería por patrón | 1.776 | 27,5 |
| Maquinaria total (suma de los dos anteriores) | 4.427 | 68,5 |
| Operadores que quedan al final de la compilación | 780 | 12,1 |
| De ellos, cargas externas (30 de la pasada 3 absorben 3.398 operadores, unos 113 cada una) | 31 | 0,5 |
| De ellos, sentencias de entorno sin traducir (configuración, include, UPLOAD, DOWNLOAD, PWENCODE) | 142 | 2,2 |
| Operadores de datos estimados | 607 | 9,4 |

Por familia (2.651 marcados):

| Familia | Operadores | Categorías |
|---|---|---|
| Log, medición y presentación | 1.078 | `visor_studio` 447, `presentacion` 293, `mensajes` 218, `medicion` 60, `fin_de_paso` 60 |
| Macro: control y configuración | 522 | `control_macro` 240, `configuracion_macro` 222, `variables_control` 60 |
| Sesión remota y paralelismo | 502 | `remoto` 202, `espera` 150, `troceado_lotes` 120, `shell_auxiliar` 30 |
| Conexión y tablas de base | 333 | `conexion` 242, `limpieza_tablas` 91 |
| Limpieza de temporales | 216 | `limpieza_work` 216 |

Lo que absorben las cargas sin marca de patrón: 1.326 `unsupported`, 120 `read`, 90 `derive`, 90
`sort`, 60 `filter`, 30 `dedup`, 30 `set_variable` y 30 `exec_sql`.

Los 164 `unsupported` finales: 85 configuración, 30 include declarado, 22 UPLOAD, 4 DOWNLOAD, 1
PWENCODE y solo 22 con semántica dudosa de PROC SQL.

## H2. Tablas WORK

Fuente: los hechos de texto (`tabla_escrita` y `tabla_leida`) ordenados por línea. Una versión es una
escritura de un nombre, con las lecturas que la siguen hasta la siguiente escritura. Se descartan
150 nombres con macro variable y `data _null_`.

| Medida | Valor |
|---|---|
| Escrituras WORK (versiones) | 810 |
| Nombres WORK distintos | 404 |
| Nombres escritos una sola vez | 332 |
| De ellos, leídos solo en su región (candidatos a arista) | 218 |
| De ellos, leídos desde otra región | 29 |
| De ellos, importados, exportados o sin lector | 85 |
| Nombres reescritos varias veces | 72 (`temporal` 156 veces; tres de la macro de carga, 30 cada uno) |

Versiones por clase: local a la región 640 (79,0 %), sin lector 99, cruzan región 40, exportadas 22,
importadas 9.

| | Medido | Diseño manual |
|---|---|---|
| Fuentes externas | 11: 9 archivos importados (5 Excel y 4 CSV) y 2 tablas de base | 8: 5 Excel y 3 tablas Impala |
| Salidas | 26 nombres (20 sin el sufijo de producto): 22 exportaciones CSV y 8 cargas a la base que nadie relee, con solapes | 5 familias de salida |

Por qué difieren:

- Los 5 Excel coinciden. Los 4 CSV (descargados de un recurso compartido) y las 2 tablas de base
  (`master_customer_data` y otra de canales) no coinciden uno a uno con las 3 tablas Impala del diseño,
  que ya figuran como pendientes de nombre. No se puede afirmar que sean las mismas fuentes.
- Otras 22 lecturas de base no son fuentes: son tablas que el propio programa cargó antes desde un
  WORK (`%scan(WORK.x, ...)` hacia la base) y relee. Son persistencias intermedias que el diseño
  elimina. En total son 30 los WORK cargados a la base; 22 se releen.
- El SAS hace 22 exportaciones CSV distintas. El diseño las reduce a pocas
  familias (sábana válida, rechazados, totales, conciliación, log) y añade salidas que el SAS no tiene
  (conciliación, log estructurado). No se verificó qué exportaciones del SAS cubre cada familia.
- 60 tablas WORK no tienen lector, exportación ni carga: son descartables o diagnóstico.

## H3. Similitud entre las 30 regiones

Método: LCS de tipos de operador por región, con la región asignada por la línea de la invocación
de macro. Similitud estricta = LCS / largo de la más larga. Producto: 11 regiones de un producto, 10
de otro y 3 de otro; 6 sin producto quedan fuera de intra e inter. Todas son 435 pares.

| Variante de la secuencia | Operadores | Mediana de largo por región | Pares: mín / mediana / máx | Frente a la región mayor: mediana / máx | Intra-producto (mediana) | Inter-producto (mediana) |
|---|---|---|---|---|---|---|
| V0 con fontanería | 6.068 | 148,5 | 0,12 / **0,75** / 1,00 | 0,15 / 0,52 | 0,79 | 0,74 |
| V1 sin fontanería | 1.838 | 28 | 0,01 / **0,20** / 1,00 | 0,05 / 0,44 | 0,33 | 0,30 |
| V2 V1 sin lecturas de tablas intermedias | 1.174 | 19 | 0,01 / 0,26 / 1,00 | 0,06 / 0,45 | 0,36 | 0,32 |
| V3 V2 sin tipos consecutivos repetidos | 1.174 | 12 | 0,01 / 0,24 / 1,00 | 0,04 / 0,40 | 0,27 | 0,25 |
| V4 V2 sin `unsupported` | 1.026 | 17 | 0,01 / 0,21 / 1,00 | 0,05 / 0,45 | 0,29 | 0,27 |

Si solo se comparan pares donde ambas regiones tienen 10 o más operadores (sesgo de tamaño
reducido), la mediana sube pero sigue por debajo de la de V0: V0 0,75 (435 pares), V1 0,46 (190), V2
0,43 (190), V3 0,32 (120).

Lectura:

- La hipótesis se refuta. Las regiones se parecen sobre todo por la maquinaria de carga, que se repite
  casi igual en cada una: cada región tiene al menos 116 operadores y 4.230 de los 6.068 (70 %) se
  van al quitar la fontanería. Lo que queda es lo que de verdad cambia entre regiones.
- El mejor caso sin fontanería frente a la región mayor es 0,44 (V1), por debajo de 0,52 con
  fontanería, y la medición previa (0,47 con fontanería adentro) queda en el mismo orden de magnitud.
  No se reproduce exacto porque el script anterior no está en el repositorio.
- El producto casi no separa: intra 0,33 contra inter 0,30 en V1. Diferencia de 0,04: el producto no separa
  las regiones por estructura.
- La contención (LCS / largo de la menor) da mediana 1,0 en todas las variantes, pero con regiones de
  3 operadores es trivial y no se usa como evidencia.

## Hallazgo lateral

Asignar un operador a su región por la línea de su evidencia (como hace `sgm.generador`) da 2.948
operadores en la región 0 y 569 en la última; asignarlo por la línea de la llamada da 251 y 662. 2.923
operadores vienen de una expansión de macro y su evidencia queda en el cuerpo de la primera copia.
El conteo por región de `sgm diseno` puede estar sesgado por esto; no se comprobó en el generador.

## Límites de la medición

- H1 es un rango, no un punto: 41 % es el piso (solo patrones) y 68,5 % es el techo (todo lo que una
  carga absorbe). La absorción es una heurística de crecimiento de región y no se auditó operador por
  operador.
- Los operadores de la IR son más finos que las sentencias SAS (un paso DATA da varios). No hay
  fracción por sentencia; solo por operador.
- H2 usa texto sin ejecutar. El orden es el de las líneas, la lectura dentro de un mismo
  `CREATE TABLE ... AS SELECT` del mismo nombre se confunde, las lecturas de SQL de base salen de una
  expresión regular, y la carga masiva se reconoce por el literal `%scan(WORK.x`. Los 150 nombres con
  macro variable no se pueden resolver.
- Las 30 regiones son copias del mismo código: "se lee solo en su región" es un indicio débil de que
  sea una arista, porque no se sabe si la región se ejecuta una vez o varias.
- H3 compara solo el tipo del operador, sin parámetros ni tablas. Los tipos vienen de la IR tras la
  pasada 1 (un `derive` por asignación). V1 también quita las cargas externas. Algunas regiones
  quedan con 3 operadores, y una similitud estricta penaliza la diferencia de tamaño.
- Nada de esto prueba que un modelo de proceso por linaje sea mejor: solo mide cuánto del programa
  es maquinaria y cuánto se parece entre regiones.
