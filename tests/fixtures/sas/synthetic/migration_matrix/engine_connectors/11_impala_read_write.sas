/* priority: P1 */
libname impsrc impala server=impala01 port=21050 schema=sample;
data work.impala_reference; set impsrc.reference_data; run;
data impsrc.reference_snapshot; set work.impala_reference; run;
