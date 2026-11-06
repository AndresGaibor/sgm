# INPUT con informat dinámico

## Intención

Evitar que el traductor emita una conversión numérica candidata cuando SAS no permite determinar el informat de `INPUT`. El resultado debe conservarse como pendiente, con evidencia, antes que sugerir una conversión cuya semántica no está demostrada.

## Alcance y límites

- Un informat que siga siendo macrovariable, columna o expresión no literal produce `Unsupported`; no genera Java candidato y el flujo existente registra el hueco con su origen.
- Los informats que el expansor resuelva a literales compatibles conservan el comportamiento actual. No se cambian las traducciones ni advertencias de informats numéricos literales en este ajuste.
- No se incorporan equivalencias nuevas, dependencias, datos del cliente ni valores sensibles de los adjuntos.
- Se divide el traductor actual en módulos con responsabilidades claras y de menos de 300 líneas, preservando `translate_to_talend` y los imports usados por el resto del proyecto.

## Enfoques considerados

- **Rechazar informats dinámicos y conservar lo demás (elegido):** reduce falsos candidatos con un cambio pequeño y medible, manteniendo la compatibilidad de literales existentes.
- **Mantener `Mathematical.REAL` y solo advertir:** conserva más candidatos, pero permite que un informat dinámico de texto o fecha se trate como numérico.
- **Reescribir todas las conversiones `INPUT` ahora:** permitiría normalizar más informats, pero requiere especificar y validar muchas reglas SAS/Talend no demostradas por este caso.

## Decisión

El parser aceptará solo un informat literal en esta primera mejora; un informat dinámico quedará pendiente. Se añadirán pruebas unitarias y de integración con entradas sintéticas, y se conservará el estado parcial/revisable de los operadores. La refactorización solo reubica código y mantiene el contrato público.

## Verificación

Pruebas sintéticas de informats dinámicos y de literales existentes. El ejemplo adjunto no demuestra un informat dinámico: sus cuatro candidatos `INPUT` usan cada uno un literal numérico de un token. La regresión de compilación en memoria debe conservar sus conteos y huecos; no se copia el contenido. Antes de cerrar el hito: `uv run pytest -q` y `uv run ruff check .`.
