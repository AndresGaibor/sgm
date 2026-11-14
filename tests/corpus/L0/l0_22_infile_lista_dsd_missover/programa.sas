DATA WORK.clientes;
  INFILE '.../entradas/clientes.txt' DLM=';' DSD MISSOVER FIRSTOBS=2;
  INPUT id nombre :$12. saldo;
RUN;
