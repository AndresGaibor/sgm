#!/usr/bin/env bash
# Arranca el Impala 4.5.3 de pruebas (sgmtest_*) y espera a que acepte consultas en 21050.
# Uso: tools/contenedores/impala/arrancar.sh
set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

docker compose -f docker-compose.yml up -d

# El volumen de almacén se crea como root y el HMS corre como usuario hive: hay que preparar
# los directorios de managed y external antes de la primera consulta de DDL.
docker exec -u root sgmtest_hms sh -c \
  'mkdir -p /user/hive/warehouse/managed /user/hive/warehouse/external && chmod -R 777 /user/hive/warehouse'

for _ in $(seq 1 30); do
  if docker run --rm --network sgmtest_impala_red --entrypoint impala-shell \
      apache/impala:4.5.3-impala_quickstart_client -i impalad:21050 -q 'select 1' \
      >/dev/null 2>&1; then
    echo "Impala listo en localhost:21050 (HiveServer2)."
    exit 0
  fi
  sleep 10
done

echo "Impala no respondió tras 5 minutos. Revisa: docker logs sgmtest_impalad" >&2
exit 1
