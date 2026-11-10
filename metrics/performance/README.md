# Medición de rendimiento

MG-P12-01 se ejecuta desde la raíz del repositorio:

```powershell
uv run python tools/performance/migrar.py
```

El comando migra por separado `client_large.sas` y los otros 189 `.sas` de `tests/fixtures/sas/`.
Copia temporalmente el lote conservando su estructura; esa preparación no cuenta en `elapsed_seconds`.
Cada ejecución corre en un proceso hijo y sus salidas se eliminan al terminar.

El reporte versionado `mg-p12-01.json` registra la versión de Python, plataforma, cantidad/tamaño de
fuentes, tiempo de pared, memoria residente máxima del árbol de procesos y número de paquetes
producidos. En Windows suma el `WorkingSetSize` actual del lanzador y sus descendientes en cada
muestreo; en Linux suma `VmRSS` de `/proc` para el mismo árbol. Conserva el mayor total observado.
El tiempo incluye el arranque del comando y el coste del muestreo; excluye la preparación/copia de
fuentes y la escritura del reporte. No incluye rutas absolutas, usuario ni nombre del equipo. Los
tiempos y la memoria dependen del hardware y no deben compararse como si fueran una medición de la
misma máquina.

La aceptación exige, en ambos escenarios, código de salida 0, todos los paquetes esperados, menos
de 120 segundos y menos de 1 000 000 000 bytes de memoria residente máxima. `metrics/baseline.json`
se reserva para el trinquete de calidad de compilación y no se altera con este benchmark.
