#!/usr/bin/env bash
# Apaga y borra los contenedores y la red sgmtest_impala.
# Con --borrar-datos borra también los volúmenes sgmtest_impala_* (tablas creadas).
# Uso: tools/contenedores/impala/parar.sh [--borrar-datos]
set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

if [[ "${1:-}" == "--borrar-datos" ]]; then
  docker compose -f docker-compose.yml down -v
else
  docker compose -f docker-compose.yml down
fi
