/* priority: P1 */
proc sql; create table work.latest as select a.id,a.dt from work.orders a where a.dt=(select max(b.dt) from work.orders b where b.id=a.id); quit;
