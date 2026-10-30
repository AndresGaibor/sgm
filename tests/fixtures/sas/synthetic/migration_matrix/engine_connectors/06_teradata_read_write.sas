/* priority: P1 */
libname td teradata server='example.invalid' database=demo;
data work.current_accounts; set td.accounts; where status='OPEN'; run;
data td.account_snapshot; set work.current_accounts; run;
