/* priority: P1 */
proc import datafile='/example/data/events.psv' out=work.events dbms=dlm replace; delimiter='|'; getnames=yes; run;
