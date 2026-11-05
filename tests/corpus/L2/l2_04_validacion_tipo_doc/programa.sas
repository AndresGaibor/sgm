/* Caso l2_04_validacion_tipo_doc: patrón de validación con lookup, como en el programa grande.
   Válidos: INNER JOIN con la homologación del tipo de documento. Inválidos: LEFT JOIN y WHERE con
   IS MISSING sobre la clave de la homologación. Un tipo vacío también es inválido.
   Entradas: entradas/operaciones.csv y entradas/homologacion_tpo_doc.csv. Salidas: WORK.operaciones_validas
   y WORK.operaciones_invalidas. La ruta '...' es un marcador; el oraculo lee las entradas de la
   carpeta del caso. */

PROC IMPORT DATAFILE='.../entradas/operaciones.csv' OUT=WORK.OPERACIONES DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

PROC IMPORT DATAFILE='.../entradas/homologacion_tpo_doc.csv' OUT=WORK.HOMOLOGACION_TPO_DOC
  DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

/* Etiqueta: Validos por tipo de documento */
PROC SQL;
  CREATE TABLE WORK.operaciones_validas AS
  SELECT t.id_operacion, t.tipo_doc, t.monto
  FROM WORK.operaciones t
  INNER JOIN WORK.homologacion_tpo_doc h
  ON ( t.tipo_doc = h.CNAME );
QUIT;

/* Etiqueta: Invalidos por tipo de documento */
PROC SQL;
  CREATE TABLE WORK.operaciones_invalidas AS
  SELECT t.id_operacion, t.tipo_doc, t.monto
  FROM WORK.operaciones t
  LEFT JOIN WORK.homologacion_tpo_doc h
  ON ( t.tipo_doc = h.CNAME )
  WHERE h.CNAME IS MISSING;
QUIT;

PROC EXPORT DATA=WORK.operaciones_validas OUTFILE='.../salida/operaciones_validas.csv'
  DBMS=CSV REPLACE;
RUN;

PROC EXPORT DATA=WORK.operaciones_invalidas OUTFILE='.../salida/operaciones_invalidas.csv'
  DBMS=CSV REPLACE;
RUN;
