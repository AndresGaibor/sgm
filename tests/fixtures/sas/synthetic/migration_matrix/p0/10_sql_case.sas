/* priority: P0 */
proc sql; create table work.risk as select id,case when ratio>.8 then 'HIGH' else 'LOW' end as band from work.metrics; quit;
