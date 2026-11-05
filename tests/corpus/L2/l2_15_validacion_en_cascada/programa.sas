/* Caso l2_15_validacion_en_cascada: validación en dos etapas. La etapa 1 valida el tipo de documento
   contra la homologación (INNER JOIN). La etapa 2 valida el canal contra la lista de canales válidos.
   Aceptadas son las que pasan las dos. Rechazadas son las demás, con NOT IN sobre las aceptadas.
   Entradas: entradas/operaciones.csv, entradas/homologacion_tpo_doc.csv y
   entradas/canales_validos.csv. Salidas: WORK.aceptadas y WORK.rechazadas. La ruta '...' es un
   marcador; el oraculo lee las entradas de la carpeta del caso. */

PROC IMPORT DATAFILE='.../entradas/operaciones.csv' OUT=WORK.OPERACIONES DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

PROC IMPORT DATAFILE='.../entradas/homologacion_tpo_doc.csv' OUT=WORK.HOMOLOGACION_TPO_DOC
  DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

PROC IMPORT DATAFILE='.../entradas/canales_validos.csv' OUT=WORK.CANALES_VALIDOS
  DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

/* Etiqueta: Etapa 1, tipo de documento con homologacion */
PROC SQL;
  CREATE TABLE WORK.paso_tipo_doc AS
  SELECT t.*
  FROM WORK.operaciones t
  INNER JOIN WORK.homologacion_tpo_doc h
  ON ( t.tipo_doc = h.CNAME );
QUIT;

/* Etiqueta: Etapa 2, canal valido */
PROC SQL;
  CREATE TABLE WORK.aceptadas AS
  SELECT p.*
  FROM WORK.paso_tipo_doc p
  INNER JOIN WORK.canales_validos c
  ON ( p.canal = c.CANAL );
QUIT;

/* Etiqueta: Rechazadas, las que no pasaron las dos etapas */
PROC SQL;
  CREATE TABLE WORK.rechazadas AS
  SELECT t.*
  FROM WORK.operaciones t
  WHERE t.id_operacion NOT IN (
    SELECT a.id_operacion FROM WORK.aceptadas a
  );
QUIT;

PROC EXPORT DATA=WORK.rechazadas OUTFILE='.../salida/rechazadas.csv' DBMS=CSV REPLACE;
RUN;
