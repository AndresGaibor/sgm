/* priority: P1 */
proc import datafile='/example/data/reference.xlsx' out=work.reference dbms=xlsx replace; sheet='Codes'; getnames=yes; run;
