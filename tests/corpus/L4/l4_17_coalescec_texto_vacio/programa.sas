/* Caso l4_17_coalescec_texto_vacio: un texto vacio o solo de blancos cuenta como faltante y
   COALESCEC toma el siguiente. Entradas: entradas/CLIENTES_L4_17.csv. Salida:
   WORK.CLIENTES_CIUDAD. Datos ficticios. */

PROC IMPORT DATAFILE='.../entradas/CLIENTES_L4_17.csv' OUT=WORK.CLIENTES_L4_17 DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

/* Etiqueta: Ciudad con valor por defecto */
DATA WORK.CLIENTES_CIUDAD;
  SET WORK.CLIENTES_L4_17;
  CIUDAD_OK=coalescec(CIUDAD, 'SIN CIUDAD');
RUN;

PROC EXPORT DATA=WORK.CLIENTES_CIUDAD OUTFILE='.../salida/CLIENTES_CIUDAD.csv'
  DBMS=CSV REPLACE;
RUN;
