/* priority: P1 */
/* Herramienta de validación offline; no es una transformación de producción. */
proc compare base=work.reference compare=work.migrated criterion=0.0001; id record_id; var amount score; run;
