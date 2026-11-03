# Automatización: de un archivo SAS a una especificación de Talend

Estado: **propuesta de diseño**. Se escribe a partir de la propuesta de automatización acordada en la conversación, no del estado actual de ningún archivo del repositorio.

Objetivo: que un archivo SAS, cualquiera, produzca automáticamente un JSON de especificación (jobs, subjobs, componentes, flujos, cachés, contextos, salidas y pendientes) y un Markdown legible, donde cada dato tiene fuente, regla y confianza, o un pendiente con su motivo.

Principio rector: **lo que se extrae del SAS es determinista; lo que se decide sobre cómo se construye en Talend se expresa en reglas YAML versionadas.** Ningún paso consulta bases, APIs ni nombres de programas concretos.

---

## 1. Qué significa "perfecto"

Una traducción totalmente automática y correcta en todos los casos no es posible: el SAS puede generar código en tiempo de ejecución, y la equivalencia de datos solo se prueba con datos. Por eso "perfecto" se define con criterios verificables:

| Propiedad | Criterio | Cómo se verifica |
|---|---|---|
| Trazabilidad | Todo valor del JSON tiene `fuente` (archivo y líneas) o es `pendiente` | Prueba de invariante sobre el JSON |
| Sin invención | Ningún valor sin fuente que no sea `pendiente` | Misma prueba |
| Determinismo | Mismo archivo y mismo conjunto de reglas dan el mismo JSON, byte a byte | Compilar dos veces y comparar hash |
| Cobertura | Toda línea del SAS aparece en un componente, en un `no_migrado` con motivo o en un pendiente | Prueba de cobertura por línea |
| Mejora por datos | Cerrar un caso nuevo se hace con una regla YAML y un caso de prueba, sin cambiar el motor | Revisión de que el cambio es solo de reglas |
| Robustez | Ningún archivo produce excepción; lo que no entiende queda como pendiente | Pruebas con archivos rotos, vacíos y binarios |

**Fuera de alcance:** la equivalencia semántica (que el Job haga exactamente lo mismo que el SAS). Eso solo se demuestra comparando salidas con datos reales.

---

## 2. Arquitectura en capas

```
 archivo .sas
   │
   ▼
 C0  Ingesta         codificación, copia, redacción de secretos
   │
   ▼
 C1  Lectura         nodos (/* Etiqueta */), pasos, macros expandidas en lo constante
   │                 → representación intermedia con evidencia por línea
   ▼
 C2  Hechos          lo que el archivo afirma, sin interpretar
   │
   ▼
 C3  Clasificación   reglas YAML: patrón de hechos → construcción de Talend
   │
   ▼
 C4  Especificación  JSON con fuente, regla, confianza y pendientes
   │
   ├─► C5a Guía Markdown por job
   ├─► C5b Mapa de flujo (ver 02-mapa-de-flujo.md)
   └─► C5c Reporte de cobertura, pendientes y constructos sin regla
```

Regla de dependencia: cada capa solo lee la anterior. C3 no lee el texto del SAS; solo lee hechos. Así cambiar una regla nunca cambia un hecho, y cambiar un hecho exige revisar las reglas que lo usan.

---

## 3. Capa C1: lectura

Qué hace, en orden:

1. **Separación en nodos** por marcadores `/* Etiqueta: ... */`. Cada nodo tiene línea de inicio y de fin. Un nodo sin etiqueta solo existe si tiene contenido.
2. **Pasos dentro de cada nodo:** DATA step, PROC SQL, PROC genérico, definición de macro, llamada de macro, `%let`, `%include`, `libname`, `options`, asignaciones y sentencias globales.
3. **Expansión de macros solo cuando es constante:** `%let` con valor literal, `&var` conocida, `%if` con condición constante, `%do` con límites constantes, llamadas con parámetros literales. Todo lo demás se marca como **dinámico** con su texto original.
4. **Un paso que no entiende** queda como `no_interpretado` con su texto y sus líneas. Nunca se descarta.

Salida de C1: lista de pasos, cada uno con `nodo`, `tipo`, `lineas`, `texto_normalizado` y `dinamico` (sí/no).

Prueba: cero excepciones; cada línea del archivo pertenece a un nodo, a un paso o a una lista de líneas en blanco o comentario.

---

## 4. Capa C2: hechos

### 4.1 Definición

Un hecho es una afirmación observable del archivo, sin reglas de negocio ni de Talend:

```json
{
  "id": "h-000123",
  "tipo": "tabla_escrita",
  "valor": "WORK.<nombre>",
  "alcance": "work",
  "fuente": {"archivo": "programa.sas", "lineas": [2310, 2340]},
  "nodo": "<etiqueta del nodo>",
  "extractor": "sql.create_table"
}
```

### 4.2 Catálogo cerrado de tipos

| Tipo | Se observa en | Campos |
|---|---|---|
| `tabla_leida` | `FROM`, `JOIN`, `SET`, `MERGE`, `UPDATE` | nombre, alcance (`work`, `permanente`, `externo`) |
| `tabla_escrita` | `CREATE TABLE`, `DATA <x>`, `OUT=` | nombre, alcance |
| `tabla_borrada` | `PROC DELETE`, `DROP TABLE` | nombre, alcance |
| `ruta_literal` | cadena con `\\` o `/` | ruta, uso (`lectura` o `escritura`, según la sentencia) |
| `servidor` | `SERVER=`, `server=`, `RSUBMIT` | nombre, puerto si aparece |
| `conexion_base` | `CONNECT TO <motor>`, `LIBNAME` con motor | motor, DSN |
| `credencial` | `PASS=`, `PASSWORD=`, `PROC PWENCODE` | **valor siempre enmascarado** (`'***'`) |
| `macro_definida` | `%macro` | nombre, parámetros, huella del cuerpo |
| `macro_llamada` | `%nombre(...)` | nombre, argumentos |
| `variable_constante` | `%let x = literal` | nombre, valor |
| `variable_dinamica` | `%let x = %sysfunc(...)` u otra expresión | nombre, expresión sin evaluar |
| `rama_por_valor` | `%if &v eq <literal>` | variable, valores, líneas de cada rama |
| `limite_de_bucle` | `%do i = a %to b` | variable, límites (literales o dinámicos) |
| `include_externo` | `%include` | ruta |
| `archivo_externo` | `PROC IMPORT`, `PROC EXPORT`, `PROC UPLOAD`, `PROC DOWNLOAD`, `DATAFILE=` | ruta, dirección, formato |
| `funcion_usada` | llamadas a funciones | nombre, número de argumentos |
| `proc_usado` | `PROC <nombre>` | nombre, opciones |
| `desconocido` | cualquier construcción que el extractor no reconoce con certeza | texto, líneas |

Agregar un tipo es un cambio del catálogo; se documenta con su extractor y su prueba.

### 4.3 Reglas de extracción

- Cada hecho lo produce **un** extractor, nombrado en `extractor`.
- Un extractor no decide si un hecho importa; solo lo observa.
- Lo que no se puede observar con certeza sale como `desconocido`, nunca se omite.
- Orden estable: por archivo, línea y tipo. Mismo archivo, mismos hechos, mismo orden.

### 4.4 Pruebas de C2

- Cada hecho tiene archivo existente y líneas dentro del rango.
- Cada `credencial` tiene el valor reemplazado; ningún valor sensible aparece en la salida de C2.
- Ningún extractor contiene nombres de programas, tablas o columnas de un cliente.

---

## 5. Capa C3: reglas de clasificación

### 5.1 Qué es una regla

Una regla dice cómo se expresa un conjunto de hechos en Talend. Vive en un archivo YAML por regla, con `id`, `version`, `estado`, condiciones (`cuando`), resultado (`produce`) y casos de prueba.

### 5.2 Lenguaje de condiciones (pequeño y cerrado)

Una condición solo puede consultar:

- **Tipo de paso** de C1: `proc_sql`, `data_step`, `macro_if`, `macro_do`, `no_interpretado`, …
- **Hechos del mismo nodo o del archivo**, por tipo y alcance: `tiene(tabla_escrita, alcance=work)`, `cuenta(rama_por_valor) >= 2`.
- **Valores de hechos**: `valor en [D, C, P]`, `valor empieza_con "WORK."`.
- **Relaciones del linaje**: `lectores(tabla) >= 2`, `es_frontera_entre_etapas(tabla)`.

No puede: ejecutar código, leer el texto crudo del SAS, consultar red, ni comparar con nombres concretos.

### 5.3 Ejemplos (genéricos)

```yaml
id: sql.ctas_consumo_unico
version: 1
estado: soportado
cuando:
  paso: proc_sql
  hechos:
    - tipo: tabla_escrita
      alcance: work
      cantidad: 1
  lectores_de_salida: 1
produce:
  componente: tDBRow               # SQL ejecutado en la base
  materializar: false              # se encadena con WITH en la siguiente sentencia
  confianza: alta
  razon: "la salida la consume un solo paso: no hace falta persistirla"
casos:
  - casos/sql-ctas-consumo-unico
```

```yaml
id: ambiente.rama_por_valor
version: 1
estado: soportado
cuando:
  paso: macro_if
  hechos:
    - tipo: rama_por_valor
      valores: [D, C, P]
produce:
  grupo_de_contexto: true          # cada valor es un grupo de contexto
  clave: "{variable}"              # nombre tomado del SAS, marcado como propuesto
  confianza: media
  pendiente_si: "los valores de cada grupo no están en el archivo"
casos:
  - casos/ambiente-rama-por-valor
```

### 5.4 Precedencia y conflictos

- Si dos reglas activas proponen valores distintos para el mismo campo, **no** se elige una. Se crea una decisión con las dos opciones y las reglas que las propusieron.
- `prioridad` es un entero. Sirve solo para desempatar reglas que no chocan; dos reglas de igual prioridad que chocan son un error de validación.
- Una regla sin caso no valida.

### 5.5 Cuando ninguna regla aplica

El paso queda `hueco` con un motivo del catálogo cerrado (sección 6.4). Así un archivo nuevo siempre sale con su lista de huecos.

---

## 6. Capa C4: especificación y pendientes

### 6.1 Forma de cada valor

```json
{
  "valor": "…",
  "fuente": [{"archivo": "…", "lineas": [a, b]}],
  "regla": "id@version",
  "confianza": "alta | media | baja",
  "hechos": ["h-000123"]
}
```

### 6.2 Forma de un pendiente

```json
{
  "valor": null,
  "pendiente": {
    "motivo": "DATO_NO_EN_ARCHIVO",
    "dueno": "usuario",
    "se_cierra_con": "ruta del archivo a crear o editar",
    "nota": "texto en español, sin inventar"
  }
}
```

### 6.3 Qué se deja como pendiente, y qué no se inventa

| Caso | Tratamiento |
|---|---|
| Host, puerto, usuario o ruta que no están en el archivo | `DATO_NO_EN_ARCHIVO`, se cierra con un archivo de entorno |
| Lógica de cálculo sin regla (por ejemplo, un dígito de verificación) | Se incluye el bloque como evidencia; `LOGICA_SIN_REGLA` |
| Expresión que depende de datos en ejecución | `DINAMICO`, con la expresión sin evaluar |
| Contraseña | `SECRETO`; se cierra con vault o metadato cifrado |
| Archivo externo no declarado | `EXTERNO`, se cierra declarándolo |
| Decisión de negocio | `DECISION_HUMANA`, con opciones y su efecto |

### 6.4 Motivos cerrados

`NO_INTERPRETADO`, `SENTENCIA_NO_SOPORTADA`, `PROC_NO_SOPORTADO`, `FUNCION_NO_MAPEADA`, `MACRO_DINAMICA`, `INCLUDE_EXTERNO`, `TIPO_DESCONOCIDO`, `CONSTRUCCION_SIN_REGLA`, `SEMANTICA_DUDOSA`, `DATO_NO_EN_ARCHIVO`, `LOGICA_SIN_REGLA`, `DINAMICO`, `EXTERNO`, `SECRETO`, `DECISION_HUMANA`.

Cada motivo tiene un dueño sugerido y una forma de cerrarse (un archivo de reglas, un archivo de entorno, una decisión o un cambio de código).

### 6.5 Nombres

- **Determinista:** se toma el identificador del SAS, se normaliza (caracteres válidos, minúsculas, sufijo numérico ante colisión) y se marca `propuesto`.
- **Sin significado inventado:** un identificador `X1` produce `x1`, no "saldos".
- **Aprobación:** un nombre que una persona confirma pasa a una decisión o a un override, nunca a una suposición silenciosa.

---

## 7. Bloques repetidos: de copias a un Job parametrizado

Este es el caso que más pesa en archivos grandes y el que más se puede equivocar.

### 7.1 Procedimiento

1. **Huella normalizada** de cada bloque: literales de tabla, ruta y número se reemplazan por marcadores; se calcula un hash del resultado.
2. **Agrupación:** bloques con la misma huella forman grupo. Bloques casi iguales se agrupan por distancia entre la secuencia de **hechos** (no de texto).
3. **Diff por hechos** entre el bloque de referencia y cada copia.
4. **Parámetros:** cada diferencia que sea del mismo tipo de hecho y ocupe la misma posición se vuelve parámetro, con tipo y valores observados. Ejemplo: un hecho de tabla escrita que cambia por bloque es el parámetro `tabla_origen`.
5. **Residuo:** toda diferencia que no encaje como parámetro se marca `SEMANTICA_DUDOSA` con sus líneas. **El grupo no se unifica** mientras haya residuo.

### 7.2 Condición para unificar

Dos bloques se unifican solo si:

- todas sus diferencias son parámetros;
- los valores de cada parámetro están en el archivo (no son dinámicos);
- el residuo es vacío.

Si no se cumple, el reporte dice cuántas diferencias quedan y en qué líneas.

### 7.3 Por qué escala

No depende de nombres. Un archivo con cincuenta bloques se agrupa igual que uno con dos. Lo que cambia es el tamaño del residuo, y eso es lo que el reporte muestra.

---

## 8. Materializar o encadenar

La decisión sale de hechos del linaje, no de criterio manual:

| Condición medida | Decisión |
|---|---|
| Salida con un solo lector, sin ser entregable, sin frontera entre etapas | Encadenar (`WITH` o subconsulta); no se crea tabla |
| Salida con dos o más lectores | Materializar (o caché en memoria si el volumen lo permite) |
| Salida que es entregable (se escribe a archivo o a una tabla permanente) | Materializar |
| Frontera entre etapas (un programa o job termina y otro lee) | Materializar |
| Salida sin lectores | Advertencia: código muerto o salida no declarada |

Esto convierte en regla algo que se decidió a mano. Como referencia, el archivo de este caso crea 348 tablas WORK distintas, 263 se leen con `FROM` y solo 2 se borran explícitamente. La regla dice cuántas se materializan, y la respuesta depende del linaje, no de una opinión.

---

## 9. Reporte por archivo (C5c)

Para cada archivo:

- **Cobertura:** pasos clasificados / total, y líneas cubiertas / total.
- **Pendientes:** lista por motivo, con dueño y `se_cierra_con`.
- **Constructos sin regla:** ranking por frecuencia (archivos afectados, luego ocurrencias). Este ranking decide qué regla escribir después.
- **Bloques repetidos:** grupos, tamaño y residuo.
- **Hash** de las reglas usadas y del JSON resultante.

El ranking se calcula sobre un corpus, no sobre un archivo. Con cientos de archivos similares, el ranking muestra qué patrón justifica la siguiente regla.

---

## 10. Métricas

| Métrica | Dirección | Meta |
|---|---|---|
| Valores del JSON sin fuente ni pendiente | Baja | 0 |
| Pendientes sin motivo, dueño o `se_cierra_con` | Baja | 0 |
| Hechos sin fuente válida | Baja | 0 |
| Líneas sin componente, sin motivo y sin pendiente | Baja | 0 |
| Compilaciones con hash distinto para la misma entrada | Baja | 0 |
| Pasos clasificados por regla | Sube | Se reporta por archivo |
| Residuo de bloques repetidos | Baja | Se reporta |
| Tablas WORK materializadas / creadas | Informativa | Se reporta con su regla |

Regla de avance: una versión de las reglas solo se acepta si ninguna métrica de la lista empeora frente a la anterior en el mismo corpus.

---

## 11. Pruebas

| Prueba | Garantiza |
|---|---|
| Hechos con fuente válida | Cada hecho apunta a líneas que existen |
| Valores con fuente o pendiente | Ningún valor queda sin respaldo |
| Determinismo | Dos compilaciones de la misma entrada dan el mismo JSON |
| Credenciales enmascaradas | Ningún secreto sale en ninguna capa |
| Sin nombres de cliente en código ni reglas | Vigilado por una prueba que busca esos nombres |
| Conflictos de reglas | Dos reglas que chocan producen decisión |
| Cada regla con caso | Una regla sin caso no valida |
| Residuo de bloques | Un bloque con diferencias no explicadas no se unifica |
| Materialización | Con un linaje mínimo, la decisión es la esperada |
| Robustez | Archivos rotos, vacíos, binarios y gigantes no producen excepción |
| Golden de referencia | Salida completa revisada a mano cuando cambia |

---

## 12. Ciclo de mejora

1. Entra un archivo nuevo.
2. Se compila; lo que no entiende queda como hueco o pendiente, nunca como error.
3. El reporte (C5c) muestra el constructo más frecuente sin regla.
4. Se escribe una regla YAML con su caso y el resultado esperado escrito a mano.
5. Se corre todo el corpus y se revisan las métricas.
6. Si nada empeora, la regla entra; si empeora, se corrige o se justifica.

El ciclo no cambia el motor. Mejorar es agregar reglas, casos y, cuando hace falta, nuevos extractores o tipos de hecho con su prueba.

---

## 13. Plan de construcción

| Etapa | Entregable | Criterio de salida |
|---|---|---|
| 1 | Lectura C1 con evidencia por línea | Sin excepciones; cobertura de líneas en un archivo de referencia |
| 2 | Hechos C2 con catálogo cerrado | Cada hecho con fuente; credenciales enmascaradas |
| 3 | Motor de reglas C3 y primeras 10 reglas con casos | Reglas validan; conflictos generan decisión |
| 4 | Especificación C4 con fuente, regla y pendientes | Invariante de trazabilidad en verde; determinismo en verde |
| 5 | Bloques repetidos (sección 7) | Un archivo con copias se agrupa y su residuo queda explicado |
| 6 | Materialización por linaje (sección 8) | Conteo de tablas materializadas reproducible |
| 7 | Reporte C5c con ranking | El ranking identifica la siguiente regla a escribir |
| 8 | Mapa de flujo (02-mapa-de-flujo.md) | Entendible por una persona sin conocer Talend |

---

## 14. Límites y riesgos

| Riesgo | Mitigación |
|---|---|
| Una regla parece correcta y no lo es | Caso con resultado esperado escrito a mano; revisión por otra persona |
| Un bloque "igual" con una diferencia sutil | Diff por hechos, residuo obligatorio |
| El mapa de flujo se toma como verdad | Cada elemento lleva fuente y regla; nota fija de que no es equivalencia |
| Crecimiento de reglas sin control | Versión, estado, caso y hash del conjunto |
| Macros que dependen de datos | `DINAMICO`; nunca se evalúan |
| Confundir automático con correcto | Pendientes visibles y revisión humana; equivalencia solo con datos |

**Lo que este diseño no resuelve:** la equivalencia de datos, y las decisiones de negocio. Esas quedan como decisiones con opciones, nunca como un valor elegido por la herramienta.
