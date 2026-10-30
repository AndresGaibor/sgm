/* priority: P1 */
libname odbcsrc odbc dsn=DEMO schema=sample;
data work.odbc_reference; set odbcsrc.reference_data; run;
data odbcsrc.reference_snapshot; set work.odbc_reference; run;
