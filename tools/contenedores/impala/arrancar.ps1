# Arranca el Impala 4.5.3 de pruebas (sgmtest_*) y espera a que acepte consultas en 21050.
# Uso: powershell -File tools\contenedores\impala\arrancar.ps1
# Equivalente a arrancar.sh (Git Bash). Requiere Docker Desktop encendido.
$ErrorActionPreference = "Stop"
Set-Location -LiteralPath $PSScriptRoot

docker compose -f docker-compose.yml up -d
if ($LASTEXITCODE -ne 0) { throw "docker compose up falló" }

# El volumen de almacén se crea como root y el HMS corre como usuario hive: hay que preparar
# los directorios de managed y external antes de la primera consulta de DDL.
docker exec -u root sgmtest_hms sh -c "mkdir -p /user/hive/warehouse/managed /user/hive/warehouse/external && chmod -R 777 /user/hive/warehouse"

for ($i = 1; $i -le 30; $i++) {
    docker run --rm --network sgmtest_impala_red --entrypoint impala-shell apache/impala:4.5.3-impala_quickstart_client -i impalad:21050 -q "select 1" *> $null
    if ($LASTEXITCODE -eq 0) {
        Write-Output "Impala listo en localhost:21050 (HiveServer2)."
        exit 0
    }
    Start-Sleep -Seconds 10
}
throw "Impala no respondió tras 5 minutos. Revisa: docker logs sgmtest_impalad"
