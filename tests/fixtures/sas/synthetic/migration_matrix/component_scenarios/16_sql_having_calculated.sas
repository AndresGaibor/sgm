/* priority: P1 */
proc sql; create table work.high_volume as select account_id,sum(amount) as total from work.transactions group by account_id having calculated total>10000; quit;
