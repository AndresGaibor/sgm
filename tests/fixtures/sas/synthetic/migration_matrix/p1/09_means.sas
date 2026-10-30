/* priority: P1 */
proc means data=work.claims n sum mean; class claim_type; var amount; output out=work.stats sum=total; run;
