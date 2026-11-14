DATA WORK.mov;
  INFILE '.../entradas/mov.txt' TRUNCOVER;
  INPUT @1 cuenta $5. @6 sucursal 3. @9 monto 8.2;
RUN;
