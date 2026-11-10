LIBNAME LZ '/data/lz';

PROC SQL;
  CREATE TABLE LZ.salida AS
  SELECT id, saldo * 2 AS doble
  FROM LZ.origen
  WHERE saldo > 10;
QUIT;
