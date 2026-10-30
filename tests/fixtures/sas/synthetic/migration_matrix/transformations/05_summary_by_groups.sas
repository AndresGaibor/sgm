/* priority: P1 */
proc summary data=work.claims nway; class region claim_type; var amount; output out=work.claim_totals sum=total mean=average; run;
