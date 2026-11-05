# Huecos del frontend detectados con los casos L8 de validaciones

Fecha de la comprobación: 4 de noviembre de 2026. Comandos usados:

- `build_flows` (`sgm.flow.model`) sobre cada `programa.sas`: 8 de 8 se analizan sin excepción.
- `sgm proceso` con decisiones de prueba fuera del repositorio: 8 de 8 terminan sin excepción.

Los programas están en `tests/corpus/L8/validaciones/<caso>/programa.sas`. No se corrigió el
frontend: solo se anota.

## H1. `PROC DOWNLOAD` dentro de `RSUBMIT` no tiene lectura ni escritura

- Qué pasó: el paso `PROC DOWNLOAD INFILE='\\servidor_ficticio\...\X.csv' OUTFILE='/work_sasstudio/
  pcfiles/X.csv'` queda como paso `proc` sin lectura y sin escritura. La ruta de origen de red
  no aparece como entrada externa. Sí aparece la copia en `/work_sasstudio/pcfiles/` como entrada
  externa, porque la lee el `PROC IMPORT` posterior.
- Construcción válida: sí, es la forma del original (`client_large.sas`, líneas ~153, 284 y 871).
- Efecto: el linaje pierde el origen real del archivo de producto. Un programa con dos
  descargas por producto muestra entradas incompletas.
- Ocurrencias (líneas de `PROC DOWNLOAD`):
  - v01: 49, 62.
  - v02: 39, 52.
  - v03: 88, 90, 103, 105 (dos descargas por producto dentro de un mismo `RSUBMIT`).
  - v04: 39, 52.
  - v05: 39, 52.
  - v06: 39, 52.
  - v07: 25, 38.
  - v08: 53.

## H2. Pendiente declarado: macro dinámica en la cabecera de v08 (no es un hueco)

- Qué pasó: `FOOTNOTE1` con `%TRIM(%QSYSFUNC(DATE(), NLDATE20.))` queda como pendiente
  "Macro dinámica: %sysfunc sobre datos o valores de ejecución" (`v08_nequi_cadena`, línea 45).
- Es el comportamiento declarado del frontend para `%sysfunc` con valores de ejecución. Se anota
  para que no cuente como fallo. La misma cabecera está en el original.

## Observación de uso (no es del SAS)

- `sgm proceso` falla si no encuentra `decisiones/<programa>.agrupacion.yaml` y
  `decisiones/<programa>.diseno.yaml`, o si no se pasan `--agrupacion` y `--diseno`. El corpus no
  crea esas decisiones (son decisiones del equipo). Para la comprobación se usaron YAML de prueba
  en el scratchpad, fuera del repositorio.
- Con esas decisiones de prueba, `familias` sale en 0 porque cada programa del corpus tiene una
  sola región `%macro ambiente`. Es un efecto de la configuración de prueba, no un hueco.
