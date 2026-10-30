/* priority: P1 */
libname rs redshift server='example.invalid' database=demo schema=public;
data work.rs_events; set rs.events; run;
data rs.events_snapshot; set work.rs_events; run;
