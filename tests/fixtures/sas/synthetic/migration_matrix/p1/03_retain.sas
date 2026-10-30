/* priority: P1 */
data work.running; set work.transactions; by account_id; retain balance 0; if first.account_id then balance=0; balance+amount; run;
