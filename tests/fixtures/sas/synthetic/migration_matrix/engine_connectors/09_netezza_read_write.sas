/* priority: P1 */
libname nz netezza server='example.invalid' database=demo schema=public;
data work.nz_balances; set nz.balances; run;
data nz.balance_snapshot; set work.nz_balances; run;
