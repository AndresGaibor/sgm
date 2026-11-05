/* Caso l6_08_nodupkey_llave: PROC SORT con NODUPKEY quita las filas con llave repetida.
   Entradas: entradas/CLIENTES_DUP.csv (sin ordenar). Salida: WORK.CLIENTES_UNICOS. Datos ficticios.
   Pendiente de revision: cual fila se conserva viene de fuentes secundarias. */

PROC IMPORT DATAFILE='.../entradas/CLIENTES_DUP.csv' OUT=WORK.CLIENTES_DUP DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

/* Etiqueta: Una fila por ID */
PROC SORT DATA=WORK.CLIENTES_DUP OUT=WORK.CLIENTES_UNICOS NODUPKEY;
  BY ID;
RUN;

PROC EXPORT DATA=WORK.CLIENTES_UNICOS OUTFILE='.../salida/CLIENTES_UNICOS.csv'
  DBMS=CSV REPLACE;
RUN;
