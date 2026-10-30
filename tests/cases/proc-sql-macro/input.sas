proc sql;
  %JOB_CONTROL_RD(mbsf,&DA_SCHEMA.);
quit;
