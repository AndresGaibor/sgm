/* Caso l0_08_concatenar: arma una etiqueta "nombre (ciudad)" con || y TRIM, que quita los blancos
   finales que PROC IMPORT deja en los textos mas cortos. LENGTH evita que la etiqueta se corte.
   Entrada: entradas/clientes.csv. Salida: WORK.etiquetas.
   Las rutas '...' son marcadores; el ejecutor no las usa. */

PROC IMPORT DATAFILE='.../entradas/clientes.csv' OUT=WORK.clientes DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

DATA WORK.etiquetas;
  SET WORK.clientes;
  LENGTH etiqueta $ 60;
  etiqueta = TRIM(nombre) || ' (' || TRIM(ciudad) || ')';
  KEEP id_cliente etiqueta;
RUN;

PROC EXPORT DATA=WORK.etiquetas OUTFILE='.../salida/etiquetas.csv' DBMS=CSV REPLACE;
RUN;
