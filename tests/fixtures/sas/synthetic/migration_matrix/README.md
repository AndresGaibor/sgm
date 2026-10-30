# Matriz sintética de migración SAS

104 programas SAS originales y 8 ejemplos shell de Grid, escritos para probar análisis, dependencias y generación de planes Talend. Los nombres, datos y rutas son ficticios. No son copias de los ejemplos SAS enlazados ni deben ejecutarse en entornos productivos. La suite no garantiza compilación en todas las versiones SAS ni equivalencia funcional validada.

| Grupo | Cobertura |
| --- | --- |
| P0 | DATA/SET, filtros, ramas, KEEP/DROP/RENAME, SORT, SQL joins/agregaciones/CASE/UNION, macros, DATALINES, LIBNAME. El subgrupo `p0/` tiene 15 casos base; hay más ejemplos en otros grupos. |
| P1 | MERGE/BY, FIRST./LAST., RETAIN, ARRAY, fechas, missing, FORMAT, macros, MEANS, TRANSPOSE, UPDATE, LAG, subconsulta; transformaciones, archivos, bases y escenarios compuestos. |
| P2 | CALL EXECUTE, X/SYSTASK, INCLUDE/nombres dinámicos, indirección macro, SQL dinámico, hash, pass-through externo. Requieren revisión manual. |
| Grid (8) | SASGSUB, espera, parámetros, encadenamiento, batch y comandos LSF no soportados. Analizar estáticamente; no ejecutar. |
| Motores DB (10) | Patrones `LIBNAME` para Oracle, DB2, PostgreSQL, SQL Server, MySQL, Teradata, Redshift, Greenplum, Netezza y ODBC; varios muestran lectura y escritura. |

## Casos adicionales para ampliar componentes Talend

Los siguientes ejemplos ejercitan patrones de entrada/salida y transformaciones que pueden orientar
un diseño Talend. Son **candidatos**, no una promesa de que cada programa produzca automáticamente
un componente. El mapeo depende del análisis, el esquema, la versión instalada y la validación
humana.

| Patrón SAS | Componentes Talend candidatos en las reglas del repo |
| --- | --- |
| `INFILE`, `PROC IMPORT/EXPORT`, `FILE/PUT` | `tFileInputDelimited`, `tFileInputPositional`, `tFileInputExcel`, `tFileOutputDelimited`, `tFileOutputPositional`, `tFileOutputExcel` |
| `DATALINES` / tabla de referencia fija | `tFixedFlowInput` |
| `WHERE`, `IF/THEN`, `KEEP/DROP`, columnas derivadas | `tFilterRow`, `tFilterColumns`, `tMap` |
| `MERGE`, joins SQL, lookup/hash | `tMap` (lookup) o `tJoin`; revisar duplicados y cardinalidad |
| `SET` de entradas compatibles / `UNION ALL` | `tUnite` |
| `PROC SORT`, `PROC MEANS/SUMMARY/FREQ` | `tSortRow`, `tAggregateRow` |
| `ARRAY`, `PROC TRANSPOSE` | `tNormalize` / `tDenormalize` (según dirección y esquema) |
| `LIBNAME` a Oracle, DB2, PostgreSQL, SQL Server, MySQL, ODBC | Componentes de entrada/salida del motor; verificar driver y catálogo disponibles |
| `%MACRO`, `%INCLUDE`, `X`, `SYSTASK` | `tRunJob`, `tSystem` o rediseño de orquestación, sujeto a revisión |
| `PROC PRINT`, `PROC DATASETS`, SQL DML | `tLogRow`, `tDBRow` o ninguna acción; confirmar intención funcional |
| `CALL SYMPUT`, `SELECT INTO :macrovar` | `tSetGlobalVar` o contexto; revisar alcance y momento de evaluación |

Las reglas exactas y sus advertencias están en `rules/mappings/talend-components.json` y
`rules/sas/constructs.json`. No todos los componentes existen en todas las ediciones de Talend.

Más casos ilustrativos de integración de componentes están en `component_scenarios/`. Referencias
Talend revisadas: [tRunJob](https://help.qlik.com/talend/en-US/components/8.0/orchestration/trunjob),
[tSystem](https://help.qlik.com/talend/en-US/components/8.0/system/tsystem),
[tNormalize](https://help.qlik.com/talend/en-US/components/8.0/processing/tnormalize-standard-properties),
[tDenormalize](https://help.qlik.com/talend/en-US/components/8.0/processing/tdenormalize) y
[tHashInput](https://help.qlik.com/talend/en-US/components/8.0/technical/thashinput).

## Ejecución

```bash
uv run sgm import tests/fixtures/sas/synthetic/migration_matrix -n sas-matrix
uv run sgm analyze <project_id>
uv run sgm deps <project_id>
uv run sgm plan <project_id>
uv run pytest tests/unit/test_policy_and_fixtures.py tests/unit/test_parser.py -q
```

El análisis no ejecuta código SAS. Para probar la API, iniciar `uv run sgm dev` y usar
`uv run sgm agent migrate tests/fixtures/sas/synthetic/migration_matrix -n sas-matrix`.

## Referencias oficiales de sintaxis

- [SAS 9.4 MERGE](https://documentation.sas.com/doc/en/lestmtsref/9.4/n1i8w2bwu1fn5kn1gpxj18xttbb0.htm)
- [SAS 9.4 SET](https://documentation.sas.com/doc/en/lestmtsref/9.4/p00hxg3x8lwivcn1f0e9axziw57y.htm)
- [SAS 9.4 Macro Language](https://documentation.sas.com/doc/en/mcrolref/9.4/p1gjh9paxeeq2hn17l8f0irr6d8i.htm)
- [PROC SQL examples](https://documentation.sas.com/doc/en/sqlproc/1.0/n1spf244gkq54cn13bbiy307hknr.htm)
- [SAS Grid Manager SASGSUB](https://documentation.sas.com/doc/en/bicdc/9.4/gridref/p0bjesvjde359nn1bfikmlzfk80b.htm)

Se consultaron para elegir construcciones y validar conceptos, no para redistribuir su código.
