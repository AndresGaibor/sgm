/* priority: P0 | origen: qlikdojo ejemplo-basico */
/* Ejemplo de lectura: filtro y cálculo en DATA step; resumen en PROC SQL. */

data work.personas_filtradas;
  set sashelp.class;
  if age >= 13;
  estatura_cm = height * 2.54;
run;

proc sql;
  create table work.resumen as
  select sex,
         count(*) as personas,
         avg(estatura_cm) as promedio_estatura_cm
  from work.personas_filtradas
  group by sex;
quit;
