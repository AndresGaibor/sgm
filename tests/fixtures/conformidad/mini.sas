/* Programa pequeño para las pruebas de sgm conformidad. Ningún dato real. */

/* Etiqueta: importar paises */
PROC IMPORT DATAFILE='&ruta_insumos.\Cod_pais.xlsx' DBMS=EXCELCS OUT=WORK.PAISES REPLACE;
RUN;

DATA WORK.SALIDA_CTE;
  SET WORK.PAISES;
RUN;

/* Etiqueta: escribir sabana */
PROC EXPORT DATA=WORK.SALIDA_CTE OUTFILE='&ruta_salida.\sabana_validada_cte.csv' DBMS=CSV REPLACE;
RUN;
