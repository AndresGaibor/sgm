/* Caso l2_05_lookup_claves_repetidas: la homologación tiene el código CC dos veces. Cada operación
   con CC sale dos veces en el cruce: el LEFT JOIN multiplica filas y eso debe verse en la salida.
   Entradas: entradas/operaciones.csv y entradas/homologacion_tpo_doc_dup.csv. Salidas:
   WORK.operaciones_cruzadas y WORK.operaciones_cc. La ruta '...' es un marcador; el oraculo lee las
   entradas de la carpeta del caso. */

PROC IMPORT DATAFILE='.../entradas/operaciones.csv' OUT=WORK.OPERACIONES DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

PROC IMPORT DATAFILE='.../entradas/homologacion_tpo_doc_dup.csv'
  OUT=WORK.HOMOLOGACION_TPO_DOC_DUP DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

/* Etiqueta: Cruce de operaciones con homologacion (claves repetidas) */
PROC SQL;
  CREATE TABLE WORK.operaciones_cruzadas AS
  SELECT t.id_operacion, t.tipo_doc, h.DESCRIPCION
  FROM WORK.operaciones t
  LEFT JOIN WORK.homologacion_tpo_doc_dup h
  ON ( t.tipo_doc = h.CNAME );
QUIT;

/* Etiqueta: Operaciones con CC, para contar el doble */
PROC SQL;
  CREATE TABLE WORK.operaciones_cc AS
  SELECT t.id_operacion
  FROM WORK.operaciones t
  WHERE t.tipo_doc = 'CC';
QUIT;

PROC EXPORT DATA=WORK.operaciones_cruzadas OUTFILE='.../salida/operaciones_cruzadas.csv'
  DBMS=CSV REPLACE;
RUN;
