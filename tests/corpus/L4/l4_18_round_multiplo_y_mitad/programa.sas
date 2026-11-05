/* Caso l4_18_round_multiplo_y_mitad: ROUND al multiplo indicado; en el empate va al de mayor
   valor absoluto. Entradas: entradas/MONTOS_L4_18.csv. Salida: WORK.MONTOS_REDONDEADOS.
   Datos ficticios. */

PROC IMPORT DATAFILE='.../entradas/MONTOS_L4_18.csv' OUT=WORK.MONTOS_L4_18 DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

/* Etiqueta: Redondea montos a centavos y a entero */
DATA WORK.MONTOS_REDONDEADOS;
  SET WORK.MONTOS_L4_18;
  MONTO_CENT=round(MONTO, 0.01);
  MONTO_ENTERO=round(MONTO, 1);
RUN;

PROC EXPORT DATA=WORK.MONTOS_REDONDEADOS OUTFILE='.../salida/MONTOS_REDONDEADOS.csv'
  DBMS=CSV REPLACE;
RUN;
