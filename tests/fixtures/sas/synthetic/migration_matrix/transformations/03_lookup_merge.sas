/* priority: P1 */
data work.enriched; merge work.transactions(in=t) work.account_lookup(in=a); by account_id; if t; run;
