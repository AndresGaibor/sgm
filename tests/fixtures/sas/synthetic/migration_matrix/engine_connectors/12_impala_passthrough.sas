/* priority: P1 */
proc sql;
connect to impala (server=impala01 port=21050 schema=sample);
execute (create table sample.resumen_diario as select fecha, count(*) as n from sample.eventos group by fecha) by impala;
disconnect from impala;
quit;
