# Diseño: medición de rendimiento de `sgm migrar`

## Objetivo

Medir MG-P12-01 con dos entradas reproducibles: el programa de estrés `client_large.sas` y un
directorio con los otros 189 programas SAS versionados en `tests/fixtures/sas/`. Registrar tiempo
de pared, memoria residente máxima y paquetes generados para comparar contra los límites de 120
segundos y 1 000 000 000 bytes.

## Hallazgo de partida

`metrics/baseline.json` mide tiempo de compilación, pero no la memoria máxima de `sgm migrar`. El
directorio de fixtures contiene 190 `.sas`: 189 al excluir `client_large.sas`, que se mide aparte.
El programa de estrés tiene 835 630 bytes. El reporte actual no mide migraciones individuales ni
de carpetas.

## Enfoque

- Agregar un ejecutor en `tools/performance/migrar.py` con biblioteca estándar. Copia los 189
  fuentes a un directorio temporal conservando sus rutas; la preparación queda fuera del tiempo
  medido. Ejecuta cada escenario en un proceso hijo y escribe resultados en
  `metrics/performance/mg-p12-01.json`.
- Medir el máximo residente observado del árbol de procesos: en cada muestreo se suma el
  `WorkingSetSize` del lanzador y sus descendientes en Windows, o el `VmRSS` de `/proc` en Linux.
  El JSON identifica la métrica de sistema usada, versión de Python, plataforma, tamaño/cantidad de
  fuentes, tiempo, código de salida y paquetes obtenidos. No registra nombre de equipo, usuario ni
  rutas absolutas.
- Considerar aprobado solo si cada ejecución termina con código 0, genera el número esperado de
  paquetes, tarda menos de 120 segundos y se mantiene bajo 1 000 000 000 bytes.
- Si una medición incumple el límite, investigar y optimizar el migrador con pruebas de regresión
  antes de asignar crédito a MG-P12-01. No cambiar `metrics/baseline.json`, que sigue siendo el
  trinquete de calidad de compilación.

## Límites

Este hito mide `sgm migrar`; no valida velocidad de Jobs Talend en ejecución, volumen de filas,
configuración JVM, ni caché. Esas tareas corresponden a MG-P12-02, 03 y 04. No se usan Studio, SAS,
bases de datos ni dependencias nuevas.

## Pruebas

Probar la selección y exclusión del programa de estrés, la conservación de rutas al preparar
fuentes, la captura real de tiempo y de memoria de un proceso hijo que reserva y toca 32 MB, y las
condiciones estrictas del límite. La medición de corpus queda fuera de la suite automatizada para que
las pruebas no dependan del hardware.
