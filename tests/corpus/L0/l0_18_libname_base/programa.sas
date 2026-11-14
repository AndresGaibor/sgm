LIBNAME lz IMPALA DSN=IMPALAP SCHEMA=sgmtest_d2;
DATA WORK.caros;
  SET lz.vehiculos;
  WHERE precio > 15;
  KEEP marca precio;
RUN;
LIBNAME lz CLEAR;
