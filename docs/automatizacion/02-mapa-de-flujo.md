# Mapa de flujo: entender un programa SAS sin traducirlo

Estado: **propuesta de diseño**. Depende de la capa de hechos y de la lectura de `01-automatizacion.md`.

Objetivo: producir, para cada archivo SAS, un documento en español que una persona pueda leer para entender **qué hace el programa, en qué orden, con qué datos y qué depende de qué**, sin conocer Talend ni términos de traducción.

No es una traducción ni una propuesta de Jobs. No decide cómo se construye nada. Solo describe lo que el SAS hace.

---

## 1. Lectores y uso

| Lector | Qué busca | Qué le sirve |
|---|---|---|
| Quien revisa el programa por primera vez | Entender el proceso en pocos minutos | Etapas y datos de entrada y salida |
| Quien va a traducirlo | Saber qué partes son repetidas y qué partes son únicas | Bloques repetidos, ramas de ambiente, dependencias |
| Quien audita | Saber de dónde sale cada afirmación | Fuente y línea en cada punto |
| Negocio | Confirmar que el proceso se entiende bien | Lista de entradas, salidas y decisiones que hay que tomar |

---

## 2. Estructura del documento

Cada mapa tiene siete secciones, en este orden:

### 2.1 Resumen

- Nombre del archivo (sin ruta completa), número de líneas y de nodos.
- Cuántas etapas tiene el proceso y cuántos bloques repetidos.
- Entradas externas (archivos, bases, servidores) y salidas externas.
- Ramas de ambiente detectadas (si las hay).
- Cuántos pendientes hay, por motivo.

Ejemplo de redacción (generada a partir de hechos):

> El programa tiene 610 pasos etiquetados. Lee 5 archivos de Excel desde una carpeta compartida, lee datos de una base y escribe 6 archivos CSV. Contiene 30 bloques casi iguales que procesan una tabla distinta cada uno. Tiene una rama por ambiente con tres valores.

### 2.2 Etapas

Una etapa es un grupo de pasos conectados por datos que se escriben y se leen dentro del programa. Se calcula así:

1. Se construye el grafo de datos: nodo por paso, arista de un paso que escribe un conjunto de datos a un paso que lo lee.
2. Se separan las componentes conectadas por **fronteras externas**: lecturas o escrituras a archivos, bases o servidores.
3. Cada componente es una etapa. Se ordenan por dependencia.

Por etapa, el documento muestra:

- nombre descriptivo tomado de la etiqueta del nodo más frecuente (si no hay etiqueta, se muestra el primer identificador de salida, marcado como tal);
- entradas (qué lee de fuera y qué recibe de otra etapa);
- salidas (qué escribe fuera y qué deja para otra etapa);
- pasos principales, en orden, con su etiqueta y su línea;
- pendientes de la etapa.

### 2.3 Conjuntos de datos

Tabla con un renglón por conjunto de datos:

| Conjunto | Alcance | Escrito en (líneas) | Leído en (cantidad) | Borrado | Nota |
|---|---|---|---|---|---|

- **Alcance**: `trabajo` (temporal del programa), `permanente`, `externo`.
- **Leído en (cantidad)**: número de pasos que lo leen. Es la base de la decisión de materializar.
- **Nota**: "no lo lee nadie", "lo borra un paso", "se usa como entregable", etc.

Para el archivo de referencia, esta tabla muestra que se escriben 405 conjuntos de trabajo distintos, que 347 se leen y que 1 se borra explícitamente (medido con `sgm facts`). El documento no concluye nada de eso; solo lo muestra.

### 2.4 Entradas y salidas externas

Lista con: tipo (archivo, base, servidor, macro externa), ruta o nombre, dirección, pasos que la usan y líneas. Las credenciales aparecen como `***`.

### 2.5 Parámetros y ambiente

- Variables que cambian el comportamiento según su valor (ramas por valor).
- Variables constantes que se usan en varios lugares.
- Variables dinámicas, con su expresión sin evaluar.
- Para cada rama: valores, líneas y qué cambia en cada una (rutas, bases o servidores distintos).

### 2.6 Bloques repetidos

Para cada grupo de bloques casi iguales:

- número de copias y líneas de inicio y fin de cada una;
- qué cambia entre copias, en forma de tabla (valor de referencia contra valor de cada copia);
- cuántas diferencias son parámetros y cuántas quedan como residuo;
- el residuo, con líneas, para revisión.

Este es el apartado que más ayuda a traducir un archivo grande, porque separa lo que es el mismo proceso repetido de lo que es distinto.

### 2.7 Pendientes y preguntas

Lista de pendientes y decisiones, cada una con:

- qué falta o qué hay que decidir;
- por qué (motivo);
- quién debería contestarla (dueño sugerido);
- qué efecto tiene la respuesta sobre el proceso.

---

## 3. Cómo se genera

Todo sale de hechos (`01-automatizacion.md`, capa C2) y del grafo de datos. No se usa el texto libre del SAS para redactar nada.

| Sección | Fuente |
|---|---|
| Resumen | Conteos de nodos, pasos y hechos de entrada y salida |
| Etapas | Grafo de datos + fronteras externas (hechos `archivo_externo`, `conexion_base`, `servidor`) |
| Conjuntos de datos | Hechos `tabla_escrita`, `tabla_leida`, `tabla_borrada` + grado de salida |
| Entradas y salidas | Hechos `ruta_literal`, `archivo_externo`, `servidor`, `conexion_base` |
| Parámetros y ambiente | Hechos `variable_constante`, `variable_dinamica`, `rama_por_valor` |
| Bloques repetidos | Procedimiento de la sección 7 de `01-automatizacion.md` |
| Pendientes | Pendientes de C4, sin cambios |

Cada frase del documento lleva, al final, una referencia a su fuente: archivo y líneas. Un lector puede ir de la afirmación al código.

---

## 4. Lo que el mapa no hace

- No dice si una etapa es correcta ni si el negocio la necesita.
- No propone componentes, Jobs ni contextos. Eso es la capa de traducción.
- No interpreta el propósito de una variable a partir de su nombre. Si el nombre sugiere un significado, el documento lo muestra como nombre, no como significado.
- No evalúa macros dinámicas.

Nota fija al pie de cada mapa: *"Este documento describe lo que el archivo dice. No demuestra que el proceso produzca los mismos datos que una traducción; eso solo se verifica comparando salidas."*

---

## 5. Formato de salida

- **Markdown** en español, con tablas y encabezados. Un archivo por programa.
- **JSON** equivalente, con la misma información, para que otras herramientas lo lean.
- Ambos se generan del mismo modelo interno; no se mantienen a mano.

Ruta sugerida: `out/mapas/<archivo>.md` y `out/mapas/<archivo>.json`. Las salidas no se versionan si contienen rutas o nombres de cliente; se regeneran cuando se necesitan.

---

## 6. Revisión

Un mapa se considera útil cuando:

1. Una persona que no conoce el programa lo entiende en menos de quince minutos.
2. Quien va a traducirlo encuentra en él los bloques repetidos, las ramas y las entradas sin tener que volver al código.
3. Cada afirmación del mapa se puede seguir hasta una línea del archivo.
4. Quien conoce el proceso confirma que las etapas y las salidas son correctas. Esa confirmación se registra como revisión (acta corta), no como verdad automática.

---

## 7. Ejemplo de lo que mostraría con el archivo de referencia

Solo con datos ya medidos en el archivo:

- **Tamaño:** 24.801 líneas y 610 pasos etiquetados.
- **Bloques repetidos:** 30 bloques con la misma secuencia de macros (9 macros distintas repetidas en cada bloque), que se diferencian sobre todo por el nombre de la tabla que procesan.
- **Conjuntos de trabajo:** 405 escritos, 347 leídos, 1 borrado explícitamente (medido con `sgm facts`).
- **Ambiente:** una rama por valor de una variable con tres valores (D, C, P), que cambia el nombre de la base de destino.
- **Entradas externas:** Excel desde una carpeta compartida (cinco archivos distintos) y lectura de una base.
- **Salidas externas:** archivos CSV a una carpeta compartida, y cargas a un servidor remoto mediante sesiones.
- **Credenciales:** hay sentencias de conexión con contraseña en claro. Se muestran como `***`. El número exacto debe medirse con el extractor antes de publicarlo.

Estos datos no son el mapa final; son lo que el mapa tendría que mostrar. Si el extractor da otro número, prevalece el extractor y se revisa esta lista.

---

## 8. Riesgos

| Riesgo | Mitigación |
|---|---|
| Etapas mal separadas por una frontera externa que no se detectó | Las fronteras se listan en el resumen; un extractor faltante aparece como pendiente |
| Un nombre de variable que sugiere un significado falso | Se muestra como nombre, sin interpretación |
| El lector confunde "mapa" con "traducción" | Nota fija y sección 4 visibles en el documento |
| Volumen grande, documento ilegible | Resumen primero; tablas largas al final; el JSON contiene el detalle completo |
