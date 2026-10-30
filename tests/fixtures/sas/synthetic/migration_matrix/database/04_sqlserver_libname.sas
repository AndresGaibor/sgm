/* priority: P1 */
libname mssql sqlsvr server='example.invalid' database=demo schema=dbo;
data work.daily_extract; set mssql.daily_extract; run;
