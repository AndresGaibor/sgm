/* priority: P1 */
libname db2lib db2 database=EXAMPLE schema=DEMO;
data work.db2_reference; set db2lib.reference_codes; run;
