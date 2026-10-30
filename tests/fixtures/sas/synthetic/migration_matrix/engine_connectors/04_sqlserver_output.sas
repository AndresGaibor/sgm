/* priority: P1 */
libname mssql sqlsvr server='example.invalid' database=demo schema=dbo;
data mssql.monthly_summary; set work.monthly_summary; run;
