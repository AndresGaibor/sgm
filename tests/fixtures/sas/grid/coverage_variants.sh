#!/bin/bash
# priority: P1 | sintético: variantes de cobertura de comandos batch y opciones Grid sin mapping
sas -sysin "/sas/prog/program with spaces.sas" -set FECHA_PROC 20241019
sasgsub -grid grid-a -queue normal -name lote -wait -sysin /sas/prog/p0_clientes_activos.sas
bsub -q normal /sas/prog/p0_clientes_activos.sas
bjobs -l 123
sasgsub -gridsubmitpgm /sas/prog/p0_clientes_activos.sas -gridqueue
