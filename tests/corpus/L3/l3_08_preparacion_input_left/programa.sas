/* Caso l3_08_preparacion_input_left: el saldo final llega como texto con blancos iniciales. Un DATA
   step lo convierte con input(left(...), 20.) y luego el PROC SQL suma la columna convertida. Es la
   forma del programa grande (conversión de FIN_SALDO_CTA antes de la suma). El oraculo SQL no ejecuta
   el DATA step: su resultado va declarado en caso.yaml (bloque preparacion) y en
   entradas_preparadas/. Entradas: entradas/columnas_depositos.csv. Salida: WORK.total_saldo_final.
   La ruta '...' es un marcador; el oraculo lee las entradas de la carpeta del caso. */

PROC IMPORT DATAFILE='.../entradas/columnas_depositos.csv' OUT=WORK.COLUMNAS_DEPOSITOS
  DBMS=CSV REPLACE;
  GETNAMES=YES;
RUN;

/* Etiqueta: Convierte FIN_SALDO_CTA a numero */
DATA WORK.FORM_SALDO_CTA_CTE;
  FORMAT FORM_FIN_SALDO_CTA 20.;
  SET WORK.COLUMNAS_DEPOSITOS;
  FORM_FIN_SALDO_CTA=input(left(fin_saldo_cta), 20.);
RUN;

/* Etiqueta: Suma saldo final convertido */
/* Código de query generado para SAS Studio por Common Query Services */

PROC SQL;
CREATE TABLE WORK.total_saldo_final AS
SELECT SUM(FORM_SALDO_CTA_CTE.FORM_FIN_SALDO_CTA) AS suma_saldo_final,
       COUNT(FORM_SALDO_CTA_CTE.FORM_FIN_SALDO_CTA) AS con_saldo
FROM WORK.FORM_SALDO_CTA_CTE FORM_SALDO_CTA_CTE;
QUIT;

PROC EXPORT DATA=WORK.total_saldo_final OUTFILE='.../salida/total_saldo_final.csv'
  DBMS=CSV REPLACE;
RUN;
