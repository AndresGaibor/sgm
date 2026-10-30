#!/bin/bash
# priority: P1 | sintético: script de envío Grid con dependencias entre trabajos
# Los nombres de opciones de sasgsub son ilustrativos; confirmar con los scripts reales.
export FECHA_PROC=${1:-$(date +%Y%m%d)}
JOB1=$(sasgsub -gridsubmitpgm /sas/prog/p0_clientes_activos.sas -gridwaitresults -gridsasoptions "-set FECHA_PROC $FECHA_PROC" -gridjobname carga_clientes)
JOB2=$(sasgsub -gridsubmitpgm /sas/prog/p0_resumen_sql.sas -gridwaitresults -gridjobname resumen_ventas -gridqueue normal)
[ "$?" -eq 0 ] && sasgsub -gridsubmitpgm /sas/prog/p1_merge_first_last.sas -gridjobname pagos_cliente
