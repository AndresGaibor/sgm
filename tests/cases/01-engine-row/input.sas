proc sql;
  execute (create table work.x as select 1 as a from y) by impala;
quit;
