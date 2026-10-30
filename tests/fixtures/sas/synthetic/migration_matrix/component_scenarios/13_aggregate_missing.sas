/* priority: P1 */
/* Conteo de filas vs conteo no missing, sumas y medias. */
proc means data=work.monthly_accounts n nmiss sum mean; class region account_type; var balance; output out=work.balance_stats n=row_count nmiss=missing_count sum=balance_total mean=balance_average; run;
