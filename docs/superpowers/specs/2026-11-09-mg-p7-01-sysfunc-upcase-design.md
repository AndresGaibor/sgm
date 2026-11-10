# MG-P7-01: `%SYSFUNC(UPCASE())` estático

## Intención

Resolver en tiempo de análisis la forma demostrada `%SYSFUNC(UPCASE(&variable))` cuando la
macrovariable ya tiene un valor constante. Esto permite expandir el caso L5-06, donde `lealtad` se
convierte en `LEALTAD` antes de formar nombres de tablas.

## Alcance

- Sustituir primero las macrovariables conocidas y evaluar `%SYSFUNC(UPCASE(...))` solo si la llamada
  tiene un único argumento constante y ASCII. El reconocimiento de la sintaxis usa modo ASCII, para
  que la comparación de palabras clave no acepte caracteres Unicode que Python equipara con letras
  ASCII al ignorar mayúsculas y minúsculas.
- Reemplazar `%SYSFUNC` por el resultado para que las referencias posteriores a esa macrovariable se
  expandan y el frontend reconozca los nombres de tabla esperados del caso L5-06.
- Conservar como `MacroDynamic` las funciones no admitidas, valores no constantes, llamadas con
  formato y llamadas cuando el SAS declara `TRANTAB`, `ENCODING`, `LOCALE` u opciones dinámicas.
- La forma implementada se limita a identificadores ASCII simples (`[A-Za-z0-9_]+`). Las pruebas
  existentes de corpus L5 y macros deben conservar su resultado. SAS documenta que `UPCASE` depende
  de `TRANTAB`, `ENCODING` y `LOCALE`; si el proyecto declara esas opciones, la llamada queda
  dinámica. Sus valores externos de sesión todavía no se conocen, así que el resultado se registra
  como avance parcial y no como equivalencia general validada.
- Agregar regresiones para el caso L5-06 y para los límites dinámicos/no admitidos. Ejecutar la prueba
  de corpus L5, la suite completa y Ruff; anotar el hito 125 y el avance medido.

## Fuera de alcance

- Evaluar funciones SAS arbitrarias o expresiones que dependan de tablas, hora, sesión, sistema de
  archivos u otro estado de ejecución.
- Ampliar ahora `%SYSEVALF`, funciones de citado, resolución indirecta `&&var&i` o `%DO` dinámico;
  siguen siendo brechas independientes de MG-P7-01.
- Cambiar la semántica de datos o agregar dependencias.

## Restricciones y decisión

El frontend actual procesa `%LET` y macros en `src/sgm/frontend/macros.py`; hoy marca todo
`%SYSFUNC` dentro de `%LET` como dinámico. El caso de referencia está en
`tests/corpus/L5/l5_06_sysfunc_upcase/`. Se seguirá la regla del repositorio de no inventar
equivalencias: un evaluador general de funciones no es seguro sin reglas individuales, y conservar
todo `%SYSFUNC` como dinámico dejaría L5-06 sin expandir. Por ello se propone una lista permitida
mínima que comience con `UPCASE` y limite la evaluación a texto ASCII constante.

La equivalencia se apoya en `mcrolref.pdf`, p. 372 (`%SYSFUNC`) y `lefunctionsref.pdf`, p. 1638
(`UPCASE`). Se preservan las páginas y motivos de los casos que queden dinámicos.

## Aceptación

1. `analyze_program` analiza el `programa.sas` de L5-06 sin dejar `MacroDynamic` para la llamada
   constante y el SQL reconocido contiene `WORK.RES_LEALTAD` y `WORK.DATOS_LEALTAD`.
2. Un `%SYSFUNC` distinto de la forma permitida, con argumento desconocido o bajo opciones SAS
   explícitas/dinámicas relevantes sigue como dinámico, sin emitir un valor supuesto.
3. Las pruebas existentes de corpus L5 y macros conservan su resultado.
4. `uv run python -m pytest -q` y `uv run ruff check .` terminan correctamente.

## Enfoques considerados

- Evaluar cualquier función de `%SYSFUNC`: descartado porque supondría trasladar semánticas SAS sin
  evidencia individual y podría ejecutar funciones dependientes del entorno.
- Mantener todo `%SYSFUNC` como dinámico: seguro, pero no satisface el vector documentado L5-06.
- Evaluar únicamente `UPCASE` constante ASCII y conservar el resto como dinámico: enfoque propuesto
  por ser el único que cierra el caso probado sin ampliar equivalencias.
