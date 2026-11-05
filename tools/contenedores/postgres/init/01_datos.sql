-- Datos ficticios para la prueba de tPostgresqlInput -> tPostgresqlOutput.
-- Tabla de origen con filas evidentemente simuladas (SIM_...).
CREATE TABLE IF NOT EXISTS sgmtest_origen (
    id      integer PRIMARY KEY,
    nombre  varchar(60) NOT NULL,
    saldo   numeric(12, 2)
);

INSERT INTO sgmtest_origen (id, nombre, saldo) VALUES
    (1, 'SIM_nombre_1', 100.50),
    (2, 'SIM_nombre_2', 250.00),
    (3, 'SIM_nombre_3', 0.00);
