# Cobertura de procedimientos

Generado por `uv run python tools/cobertura_procs.py`. Subinforme de C-22; G-17 lo integra en `docs/cobertura.md` sin sobrescribir este archivo.

El índice local contiene **65 capítulos únicos** de procedimientos. Las menciones sin capítulo se presentan aparte y no aumentan ese denominador.

`traducido` significa que hay una rama o regla ejecutable para un subconjunto, no cobertura completa ni validación en Studio. `reporte` y `limpieza` son políticas condicionadas; `pendiente` conserva código P-; `no_verificado` no tiene equivalencia ni familia asignada. `fuera_de_alcance` es una decisión del producto con motivo y página, no una equivalencia ni permiso para omitir silenciosamente ese PROC.

Fuentes: `docs/referencia/sas/proc.INDEX.md`, `rules/sas/catalogo/procs-usados.yaml`, `procedimientos-migrador.yaml`, `rules/sas/procs/*.yaml` y ramas de `lower_procs.py`/`lower_sql.py`. Las páginas de capítulo localizan documentación; no prueban todas sus opciones. Las equivalencias puntuales se documentan en las reglas y la política.

## Resumen de capítulos

| Estado | Capítulos |
|---|---|
| fuera_de_alcance | 23 |
| limpieza | 2 |
| no_verificado | 26 |
| pendiente | 1 |
| reporte | 4 |
| traducido | 9 |

## Procedimientos de la guía

| Procedimiento | Estado | Página proc.pdf | Motivo y límites |
|---|---|---|---|
| APPEND | traducido | 161 | BASE y DATA estáticos y distintos escriben sobre BASE; las bases nuevas de WORK se crean desde DATA (p. 639). FORCE se requiere cuando DATA añade variables, cambia el tipo o trae una longitud mayor; esas discrepancias y bases permanentes sin fuente quedan pendientes (p. 640). |
| AUTHLIB | fuera_de_alcance | 177 | infraestructura SAS: Catálogos, transporte, versiones, registro o credenciales propios de SAS fuera de la migración de filas (proc.pdf, pp. 62–64). |
| CALENDAR | fuera_de_alcance | 263 | reportes especializados: Presentación de calendarios fuera de la migración de datos (proc.pdf, p. 64). |
| CATALOG | fuera_de_alcance | 357 | infraestructura SAS: Catálogos, transporte, versiones, registro o credenciales propios de SAS fuera de la migración de filas (proc.pdf, pp. 62–64). |
| CHART | fuera_de_alcance | 387 | gráficos: Salida gráfica SAS sin equivalencia de datos del migrador (proc.pdf, pp. 53–54). |
| CIMPORT | fuera_de_alcance | 441 | infraestructura SAS: Catálogos, transporte, versiones, registro o credenciales propios de SAS fuera de la migración de filas (proc.pdf, pp. 62–64). |
| COMPARE | no_verificado | 471 | Sin regla de traducción ni familia de alcance verificada. |
| CONTENTS | reporte | 541 | Sin OUT=: reports=discard omite con aviso; log/csv solo materializan PRINT. WORK._ALL_ OUT=: P-WORK-INTROSPECCION; otras salidas OUT= siguen pendientes. |
| COPY | traducido | 573 | SELECT estático con IN distinto de OUT=WORK; otras formas conservan pendientes. |
| CPORT | fuera_de_alcance | 589 | infraestructura SAS: Catálogos, transporte, versiones, registro o credenciales propios de SAS fuera de la migración de filas (proc.pdf, pp. 62–64). |
| DATASETS | limpieza | 613 | Solo WORK demostrado; bibliotecas persistentes o ambiguas quedan pendientes. |
| DATEKEYS | no_verificado | 779 | Sin regla de traducción ni familia de alcance verificada. |
| DELETE | limpieza | 837 | Solo WORK demostrado; bibliotecas persistentes o ambiguas quedan pendientes. |
| DISPLAY | fuera_de_alcance | 849 | administración de la sesión: Configuración, diagnóstico, impresión o ventanas de la sesión SAS fuera del Job de datos (proc.pdf, pp. 60–63); PROC OPTIONS no es la sentencia OPTIONS. |
| DS2 | no_verificado | 853 | Sin regla de traducción ni familia de alcance verificada. |
| DSTODS2 | no_verificado | 889 | Sin regla de traducción ni familia de alcance verificada. |
| EXPORT | traducido | 901 | Subconjunto de escritura de archivos; formato y destino deben estar demostrados. |
| FCMP | no_verificado | 925 | Sin regla de traducción ni familia de alcance verificada. |
| FEDSQL | no_verificado | 1053 | Sin regla de traducción ni familia de alcance verificada. |
| FMTC2ITM | no_verificado | 1101 | Sin regla de traducción ni familia de alcance verificada. |
| FONTREG | fuera_de_alcance | 1109 | administración de la sesión: Configuración, diagnóstico, impresión o ventanas de la sesión SAS fuera del Job de datos (proc.pdf, pp. 60–63); PROC OPTIONS no es la sentencia OPTIONS. |
| FORMAT | traducido | 1173 | VALUE discreto de carácter y OTHER en el plan/intérprete B (pp. 1173, 1178, 1181); rangos: P-FORMATO-RANGO-SIN-SOPORTE; Talend: P-FORMATO-USUARIO-SIN-EMISOR. |
| FSLIST | no_verificado | 1257 | Sin regla de traducción ni familia de alcance verificada. |
| GROOVY | no_verificado | 1271 | Sin regla de traducción ni familia de alcance verificada. |
| HADOOP | no_verificado | 1285 | Sin regla de traducción ni familia de alcance verificada. |
| HDMD | no_verificado | 1309 | Sin regla de traducción ni familia de alcance verificada. |
| HTTP | no_verificado | 1329 | Sin regla de traducción ni familia de alcance verificada. |
| IMPORT | traducido | 1373 | Lectura de archivos; formato, esquema y opciones deben estar demostrados. |
| JAVAINFO | fuera_de_alcance | 1407 | administración de la sesión: Configuración, diagnóstico, impresión o ventanas de la sesión SAS fuera del Job de datos (proc.pdf, pp. 60–63); PROC OPTIONS no es la sentencia OPTIONS. |
| JSON | no_verificado | 1409 | Sin regla de traducción ni familia de alcance verificada. |
| LUA | no_verificado | 1455 | Sin regla de traducción ni familia de alcance verificada. |
| MEANS | traducido | 1521 | CLASS/VAR/OUTPUT con SUM, MEAN, MIN, MAX, N y NMISS (pp. 1555–1558); faltantes por variable (p. 1571). CLASS exige NWAY y DROP=_TYPE_ _FREQ_ (pp. 1536, 1572–1573). Sin CLASS produce una fila global. STD y opciones no modeladas quedan pendientes; sin OUTPUT conserva la forma declarativa. NMISS se ejecuta en el intérprete; su emisión Talend queda pendiente sin equivalencia de componente demostrada. |
| MIGRATE | fuera_de_alcance | 1617 | infraestructura SAS: Catálogos, transporte, versiones, registro o credenciales propios de SAS fuera de la migración de filas (proc.pdf, pp. 62–64). |
| OPTIONS | fuera_de_alcance | 1639 | administración de la sesión: Configuración, diagnóstico, impresión o ventanas de la sesión SAS fuera del Job de datos (proc.pdf, pp. 60–63); PROC OPTIONS no es la sentencia OPTIONS. |
| OPTLOAD | fuera_de_alcance | 1661 | administración de la sesión: Configuración, diagnóstico, impresión o ventanas de la sesión SAS fuera del Job de datos (proc.pdf, pp. 60–63); PROC OPTIONS no es la sentencia OPTIONS. |
| OPTSAVE | fuera_de_alcance | 1667 | administración de la sesión: Configuración, diagnóstico, impresión o ventanas de la sesión SAS fuera del Job de datos (proc.pdf, pp. 60–63); PROC OPTIONS no es la sentencia OPTIONS. |
| PLOT | fuera_de_alcance | 1675 | gráficos: Salida gráfica SAS sin equivalencia de datos del migrador (proc.pdf, pp. 53–54). |
| PMENU | fuera_de_alcance | 1749 | administración de la sesión: Configuración, diagnóstico, impresión o ventanas de la sesión SAS fuera del Job de datos (proc.pdf, pp. 60–63); PROC OPTIONS no es la sentencia OPTIONS. |
| PRESENV | fuera_de_alcance | 1797 | administración de la sesión: Configuración, diagnóstico, impresión o ventanas de la sesión SAS fuera del Job de datos (proc.pdf, pp. 60–63); PROC OPTIONS no es la sentencia OPTIONS. |
| PRINT | reporte | 1809 | Sin OUT=: reports=discard omite con aviso; log/csv solo materializan PRINT. OUT= no se descarta como reporte. |
| PRINTTO | fuera_de_alcance | 1915 | administración de la sesión: Configuración, diagnóstico, impresión o ventanas de la sesión SAS fuera del Job de datos (proc.pdf, pp. 60–63); PROC OPTIONS no es la sentencia OPTIONS. |
| PRODUCT_STATUS | no_verificado | 1939 | Sin regla de traducción ni familia de alcance verificada. |
| PROTO | no_verificado | 1943 | Sin regla de traducción ni familia de alcance verificada. |
| PRTDEF | fuera_de_alcance | 1971 | administración de la sesión: Configuración, diagnóstico, impresión o ventanas de la sesión SAS fuera del Job de datos (proc.pdf, pp. 60–63); PROC OPTIONS no es la sentencia OPTIONS. |
| PRTEXP | fuera_de_alcance | 1991 | administración de la sesión: Configuración, diagnóstico, impresión o ventanas de la sesión SAS fuera del Job de datos (proc.pdf, pp. 60–63); PROC OPTIONS no es la sentencia OPTIONS. |
| PWENCODE | fuera_de_alcance | 1997 | infraestructura SAS: Catálogos, transporte, versiones, registro o credenciales propios de SAS fuera de la migración de filas (proc.pdf, pp. 62–64). |
| PYTHON | no_verificado | 2009 | Sin regla de traducción ni familia de alcance verificada. |
| QDEVICE | no_verificado | 2043 | Sin regla de traducción ni familia de alcance verificada. |
| RANK | no_verificado | 2093 | Sin regla de traducción ni familia de alcance verificada. |
| REGISTRY | fuera_de_alcance | 2119 | infraestructura SAS: Catálogos, transporte, versiones, registro o credenciales propios de SAS fuera de la migración de filas (proc.pdf, pp. 62–64). |
| REPORT | reporte | 2139 | Sin OUT=: reports=discard omite con aviso; log/csv solo materializan PRINT. OUT= no se descarta como reporte. |
| S3 | no_verificado | 2351 | Sin regla de traducción ni familia de alcance verificada. |
| SCAPROC | fuera_de_alcance | 2385 | administración de la sesión: Configuración, diagnóstico, impresión o ventanas de la sesión SAS fuera del Job de datos (proc.pdf, pp. 60–63); PROC OPTIONS no es la sentencia OPTIONS. |
| SCOREACCEL | no_verificado | 2399 | Sin regla de traducción ni familia de alcance verificada. |
| SOAP | no_verificado | 2435 | Sin regla de traducción ni familia de alcance verificada. |
| SORT | traducido | 2449 | BY/NODUPKEY/NODUPREC/DUPOUT/NOEQUALS; conserva sus pendientes de estabilidad. |
| SQL | traducido | 2505 | Parser y lowering propios de PROC SQL; soporte parcial según sentencia y expresión. |
| SQOOP | no_verificado | 2507 | Sin regla de traducción ni familia de alcance verificada. |
| STANDARD | no_verificado | 2515 | Sin regla de traducción ni familia de alcance verificada. |
| STREAM | no_verificado | 2535 | Sin regla de traducción ni familia de alcance verificada. |
| SUMMARY | traducido | 2549 | Comparte el lowering explícito y los límites de MEANS conforme a la remisión de p. 2549; agregado global sin CLASS con nombres explícitos y DROP de las columnas automáticas. |
| TABULATE | reporte | 2553 | Sin OUT=: reports=discard omite con aviso; log/csv solo materializan PRINT. OUT= no se descarta como reporte. |
| TIMEPLOT | fuera_de_alcance | 2715 | gráficos: Salida gráfica SAS sin equivalencia de datos del migrador (proc.pdf, pp. 53–54). |
| TRANSPOSE | pendiente | 2745 | P-OPERADOR-PIVOTAR: pivote sin componente ni equivalencia completa demostrada. |
| XSL | no_verificado | 2779 | Sin regla de traducción ni familia de alcance verificada. |

## Menciones de catálogo o reglas sin capítulo propio

| Procedimiento | Estado | Página proc.pdf | Motivo y límites |
|---|---|---|---|
| DOWNLOAD | no_verificado | sin página | Sin página verificable en el índice local. Mención sin capítulo propio; no cuenta entre los capítulos. 4 usos; archivos literales se resuelven como alias de ruta (ir/pase_copias_remotas.py); la copia no se materializa; DATA=/OUT=, bibliotecas y catálogos quedan pendientes |
| FREQ | reporte | 89 | Mención sin capítulo propio; no cuenta entre los capítulos. Sin OUT=: reports=discard omite con aviso; log/csv solo materializan PRINT. TABLES OUT=: P-FREQ-OUT-SIN-PAGINA; p. 89 solo documenta MISSPRINT. |
| UPLOAD | no_verificado | sin página | Sin página verificable en el índice local. Mención sin capítulo propio; no cuenta entre los capítulos. 22 usos; archivos literales se resuelven como alias de ruta (ir/pase_copias_remotas.py); la copia no se materializa; DATA=/OUT=, bibliotecas y catálogos quedan pendientes |
