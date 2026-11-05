# Impala 4.5.3 de pruebas (sgmtest_)

Impala real en contenedores locales, con el quickstart de Apache adaptado a 6,4 GiB de memoria.
Sirve para probar Jobs de Talend (`tImpalaConnection`, `tImpalaInput`) contra un Impala de verdad.
No es un cluster de Cloudera ni usa HDFS.

## Arrancar, probar y parar

```powershell
powershell -File tools\contenedores\impala\arrancar.ps1   # o: tools/contenedores/impala/arrancar.sh
uv run python tools/contenedores/cargar_tablas.py --sas tests/fixtures/sas/client/client_large.sas --ejecutar
tools/contenedores/impala/parar.sh                        # Git Bash; con --borrar-datos borra también los volúmenes
```

- HiveServer2 de Impala en `localhost:21050`, sin SASL. En JDBC usar `jdbc:hive2://localhost:21050/default;auth=noSasl`.
- Consulta a mano: `docker run --rm --network sgmtest_impala_red --entrypoint impala-shell apache/impala:4.5.3-impala_quickstart_client -i impalad:21050 -q "show databases"`.
- `parar.sh --borrar-datos` borra también los volúmenes `sgmtest_impala_*` (tablas creadas).

## Memoria

Límites en `docker-compose.yml`: HMS 1 GiB, statestored 256 MiB, catalogd 1 GiB e impalad 2,5 GiB
(con `-mem_limit=2gb`). Medido en reposo tras cargar las tablas de prueba: impalad 347 MiB,
catalogd 275 MiB, hms 260 MiB y statestored 15 MiB (unos 0,9 GiB en total, frente a un tope de 4,75 GiB).

## Decisiones y problemas resueltos

- El HMS va en la red `sgmtest_impala_red` con IP fija `172.30.0.10`, y impalad y catalogd lo
  resuelven con `extra_hosts`. Motivo: el DNS de Docker devuelve el nombre del contenedor
  (`sgmtest_hms`, con guion bajo) y Hive lo rechaza al construir la URI del metastore
  (`URISyntaxException`). Los nombres de contenedor no pueden cambiar porque deben empezar por `sgmtest_`.
- El volumen de almacén nuevo es de root y el HMS corre como `hive`. `arrancar.*` crea
  `managed` y `external` con permisos abiertos, solo dentro del volumen de prueba.
- `quickstart_conf/hive-site.xml` es una copia adaptada de la configuración del quickstart oficial.
- Para Talend, la conexión necesita `IMPALA_ADDITIONAL_JDBC = ";auth=noSasl"` (es un valor del Job,
  no un cambio de plantilla). Sin él el cliente inicia SASL y se queda colgado.
