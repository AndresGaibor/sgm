# Diseño: compuerta de secretos para `sgm migrar`

## Objetivo

Completar MG-P13-01: impedir que `sgm migrar` publique un paquete que el escáner actual marque
como secreto, y ejecutar la misma verificación de forma programada sobre una migración controlada
y sobre `decisiones/`.

## Decisión

La migración se escribe primero en un directorio temporal junto a la salida final. Se escanea tanto
un paquete existente como el paquete recién generado. Solo si ambas revisiones terminan sin
hallazgos se copian al destino los archivos generados. Así se conservan archivos adicionales que el
usuario haya guardado en la carpeta del paquete. Una salida existente con hallazgos, un enlace
simbólico o junction de Windows en la ruta destino o dentro de ella, o un error de lectura bloquean la escritura;
no se imprimen valores
sospechosos.

La compuerta se aplica por paquete. En una migración de carpeta, los paquetes limpios sí se publican,
los paquetes bloqueados se omiten y el comando devuelve código 1 si alguno falló por seguridad.
Los errores normales de traducción siguen documentándose en `pendientes.md` y no cambian su código
de salida.

## Informe del bloqueo

El comando informa ruta relativa, línea y tipo de hallazgo con el valor omitido. Si el escaneo no
puede completarse, informa un motivo genérico sin incluir el error del sistema, porque su texto
podría revelar contenido sensible. La carpeta temporal se elimina al salir, incluidos los informes
de una migración bloqueada.

## Corrida nocturna

Se agrega un workflow de GitHub Actions con `schedule` y `workflow_dispatch`, permiso de solo lectura
al repositorio y acciones fijadas a SHA. El workflow instala dependencias desde `uv.lock`, corre las
pruebas del escáner y del comando, migra un fixture controlado hacia `$RUNNER_TEMP`, y revisa el
paquete y `decisiones/` con `sgm secretos`. No usa Studio, bases de datos ni secretos de CI.

## Límites

La compuerta conserva el alcance del escáner existente: archivos de texto, sus expresiones
regulares y lista blanca documentada. Los binarios no se inspeccionan. Esta tarea no cambia reglas,
no borra secretos del SAS de entrada ni sustituye la revisión humana de credenciales.

## Alternativas consideradas

1. **Escribir directamente y escanear al final:** descarta la generación insegura, pero deja el
   paquete filtrado en disco aunque el comando falle; se rechaza.
2. **Escribir a staging y escanear antes de publicar:** evita que un hallazgo nuevo llegue al
   destino, conserva archivos extra y permite limpiar el staging; elegida.
3. **Reemplazar atómicamente toda la carpeta:** complicaría Windows y borraría archivos agregados
   manualmente; se rechaza.
