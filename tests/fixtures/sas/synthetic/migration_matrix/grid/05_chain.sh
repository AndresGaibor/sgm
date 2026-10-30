# priority: P1
# Secuencia condicional: demostración, no invocar.
sasgsub -gridjobname stage_one -gridsubmitpgm /example/jobs/stage_one.sas
if [ $? -eq 0 ]; then
  sasgsub -gridjobname stage_two -gridsubmitpgm /example/jobs/stage_two.sas
fi
