/* priority: P1 */
/* Reporte legible: decidir si se conserva como salida, se registra o se descarta. */
proc print data=work.exceptions noobs; var record_id reason detected_date; title 'Synthetic exception report'; run;
