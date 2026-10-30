/* priority: P0 */
/* Escenario de extremo a extremo: archivo, filtro, cálculo, orden, agregado y salida. */
filename source '/example/input/sales.csv';
data work.valid_sales; infile source dsd dlm=',' firstobs=2; input region $ customer_id amount; where amount>0; net_amount=amount*0.9; run;
proc sort data=work.valid_sales; by region customer_id; run;
proc sql; create table work.region_totals as select region,sum(net_amount) as total from work.valid_sales group by region; quit;
proc export data=work.region_totals outfile='/example/output/region_totals.csv' dbms=csv replace; run;
