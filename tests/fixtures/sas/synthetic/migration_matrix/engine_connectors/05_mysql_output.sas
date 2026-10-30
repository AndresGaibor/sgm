/* priority: P1 */
libname mysql mysql server='example.invalid' database=demo;
data mysql.daily_extract; set work.daily_extract; run;
