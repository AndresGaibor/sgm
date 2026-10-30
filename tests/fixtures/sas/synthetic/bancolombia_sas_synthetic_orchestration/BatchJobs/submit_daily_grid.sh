#!/usr/bin/env bash
# priority: P1 | orquestación sintética de ejemplo para validar SAS Grid.
# Schedule: Weekdays 06:15 | análisis de SAS Grid; no ejecutar durante carga del ZIP.
set -euo pipefail

sasgsub \
  -gridsubmitpgm "BatchJobs/run_daily_portfolio.sas" \
  -gridjobname "BANKING_PORTFOLIO_TEST" \
  -gridqueue "TEST" \
  -gridwaitresults
