/* priority: P1 */
/* Dos salidas para flujo aceptado y rechazo funcional. */
data work.accepted work.rejected; set work.incoming; if missing(record_id) or amount<0 then output work.rejected; else output work.accepted; run;
