/* priority: P0 */
proc sql; create table work.priority as select case when balance<0 then 'DEBIT' when balance=0 then 'ZERO' when balance<1000 then 'NORMAL' else 'HIGH' end as category,account_id from work.accounts; quit;
