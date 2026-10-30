proc sql;
  create table work.x as select * from connection to impala (select a from t);
quit;
