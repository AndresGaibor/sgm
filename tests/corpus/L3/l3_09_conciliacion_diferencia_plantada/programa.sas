/* Caso l3_09_conciliacion_diferencia_plantada: conciliación de origen contra válidos e inválidos. La
   homologación repite CC, así que el INNER JOIN de válidos duplica cada operación con CC. La
   conciliación lo muestra como una diferencia negativa igual al número de operaciones con CC. Esa
   diferencia es la plantada, no un error del programa. Entradas: entradas/operaciones.csv y
   entradas/homologacion_tpo_doc_dup.csv. Salidas: WORK.validos, WORK.invalidos, WORK.cc_operaciones y
   WORK.conciliacion. La ruta '...' es un marcador; el oraculo lee las entradas de la carpeta del caso. */

PROC IMPORT DATAFILE='.../entradas/operaciones.csv' OUT=WORK.OPERACIONES DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

PROC IMPORT DATAFILE='.../entradas/homologacion_tpo_doc_dup.csv'
  OUT=WORK.HOMOLOGACION_TPO_DOC_DUP DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

/* Etiqueta: Validos (INNER JOIN con homologacion con claves repetidas) */
PROC SQL;
  CREATE TABLE WORK.validos AS
  SELECT t.*
  FROM WORK.operaciones t
  INNER JOIN WORK.homologacion_tpo_doc_dup h
  ON ( t.tipo_doc = h.CNAME );
QUIT;

/* Etiqueta: Invalidos (LEFT JOIN e IS MISSING) */
PROC SQL;
  CREATE TABLE WORK.invalidos AS
  SELECT t.*
  FROM WORK.operaciones t
  LEFT JOIN WORK.homologacion_tpo_doc_dup h
  ON ( t.tipo_doc = h.CNAME )
  WHERE h.CNAME IS MISSING;
QUIT;

/* Etiqueta: Operaciones con CC */
PROC SQL;
  CREATE TABLE WORK.cc_operaciones AS
  SELECT t.id_operacion
  FROM WORK.operaciones t
  WHERE t.tipo_doc = 'CC';
QUIT;

/* Etiqueta: Conciliacion origen, validos e invalidos */
PROC SQL;
  CREATE TABLE WORK.conciliacion AS
  SELECT COUNT(*) AS origen,
         (SELECT COUNT(*) FROM WORK.validos) AS validos,
         (SELECT COUNT(*) FROM WORK.invalidos) AS invalidos,
         COUNT(*) - (SELECT COUNT(*) FROM WORK.validos) - (SELECT COUNT(*) FROM WORK.invalidos)
           AS diferencia
  FROM WORK.operaciones;
QUIT;

PROC EXPORT DATA=WORK.conciliacion OUTFILE='.../salida/conciliacion.csv' DBMS=CSV REPLACE;
RUN;
