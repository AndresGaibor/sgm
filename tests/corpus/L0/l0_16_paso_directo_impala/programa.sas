PROC SQL;
  CONNECT TO IMPALA (DSN=IMPALAP);
  CREATE TABLE WORK.por_marca AS
  SELECT * FROM CONNECTION TO IMPALA
  (select marca, COUNT(*) as n, SUM(precio) as total
     from sgmtest_d2.vehiculos where anio = 2026 group by marca);
  DISCONNECT FROM IMPALA;
QUIT;
