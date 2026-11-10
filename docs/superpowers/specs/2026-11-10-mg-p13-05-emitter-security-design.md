# Diseño: cerrar inyección en el emisor (MG-P13-05)

## Objetivo

Corregir los riesgos concretos de la auditoría independiente del emisor y probar que entradas
hostiles no se convierten en SQL ejecutable ni en sentencias Java dentro de un `tMap`.

## Hallazgos y decisiones

1. **Identificadores en SQL de base:** `sql_tree` quita las comillas del AST y el push a base
   concatena tablas, alias y proyecciones como SQL. Un name literal con sintaxis SQL adicional
   puede cambiar la consulta. Antes del lowering se validarán todos los identificadores del AST
   SQL, incluidos fuente, destino, alias de tabla y alias/columnas proyectadas. Se aceptará la
   gramática portable `[A-Za-z_][A-Za-z0-9_]*`; lo demás quedará como pendiente sin reproducir el
   nombre en la nota. El árbol conserva el nombre para análisis sintáctico, pero lowering y render
   validan antes de emitir. Se reutiliza el motivo contractual `SQL_NO_SOPORTADO` con nota específica,
   sin ampliar la lista cerrada de motivos. No se inventa quoting para motores que no se ejecutan aquí.
2. **Name literal SAS en Java:** la expresión del traductor construye `input_row.<nombre>` y puede
   dejar texto Java después de un prefijo de columna. Solo se aceptan nombres literales que sean un
   identificador portable de campo Java/Talend. Además, el resolvedor rechazará referencias
   parciales, nombres de fila/campos no portables del esquema y separadores de sentencias fuera de
   literales Java. También se rechazan escapes Unicode que Java procesa antes de analizar la
   expresión. La serialización del traductor inline y la del traductor de rutinas Talend deben usar
   el mismo helper de cadenas para que ninguna deje controles crudos.
3. **Nombres de contexto:** los nombres declarados en YAML pueden acabar en `context.<nombre>`.
   Se validarán al leer la decisión y en los constructores que los escriben; un nombre inválido
   aborta la generación con un error de configuración sin incluirlo como código.
4. **Literales Java:** `jobs_diseno.java()`, el traductor inline y `_jstr` de las rutas de expresiones
   tienen escapes distintos e incompletos. Se moverá el escape a una función compartida y todos esos
   caminos la usarán para comillas, barras, controles y caracteres no ASCII.
5. **Límites públicos del emisor:** las columnas y expresiones recibidas por `tMap`, las plantillas,
   los esquemas de entrada/salida y los nombres derivados se vuelven a validar al generar, incluso
   cuando el llamador no usa `sgm migrar`.
6. **Rutas interpoladas:** los constructores directos y los generadores de totales/conciliación
   escapan rutas y validan segmentos de nombre antes de insertar una cadena en Java.
7. **SQL mutado tras parseo:** el renderer valida los identificadores vivos del árbol y analiza
   nuevamente el SQL renderizado antes de transpilarlo; los árboles manipulados no eluden la
   comprobación que hizo el parser inicialmente.

La guía `lepg`, pp. 67–68, y `lrcon`, pp. 54–56, documenta que SAS name literals permiten espacios,
caracteres nacionales y otros nombres que no cumplen el formato V7, y que requieren las opciones
de sistema correspondientes. La salida Talend no tiene un mapeo demostrado para todos esos nombres;
se deja pendiente cuando no se puede representar de forma segura.

## Verificación

Las pruebas usan nombres y cadenas inventados. Cubren tabla, alias, proyección y árbol SQL mutado
con `push_to_db`, un `name literal` con separadores y escapes Unicode Java en una asignación del DATA
step, esquemas tMap hostiles, nombres de contexto y rutas hostiles, controles dentro de literales Java
tanto de expresiones como de Jobs, y cadenas SQL con apóstrofes duplicados. No se conecta a una base,
no se compila ni ejecuta Java y no se usa Studio.

## Fuera de alcance

No se intentará ejecutar los payloads, no se añadirá quoting específico de Impala/Talend y no se
validarán equivalencias no documentadas. La corrección de PII (MG-P13-03), el SBOM (MG-P13-04) y
la confirmación humana de credenciales (MG-P13-02) siguen separados.
