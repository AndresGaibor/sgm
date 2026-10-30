proc sql;
  select count(*) into :n from work.a;
quit;
