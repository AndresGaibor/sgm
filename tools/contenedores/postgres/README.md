# PostgreSQL 16 de pruebas (sgmtest_)

Base desechable para probar componentes `tPostgresql*` de Talend. Es el respaldo ligero de Impala.

```powershell
cd tools\contenedores\postgres
docker compose -f docker-compose.yml up -d     # arranca en 127.0.0.1:55432
docker compose -f docker-compose.yml down -v   # apaga y borra contenedor y datos
```

- Base `sgmtest_db`, usuario `sgmtest_user`. La contraseña `sgmtest_pw_local` es de este contenedor
  desechable; no es ni debe ser una clave real.
- `init/01_datos.sql` crea `sgmtest_origen` con 3 filas simuladas (`SIM_nombre_n`).
- Límite de memoria: 512 MiB.
