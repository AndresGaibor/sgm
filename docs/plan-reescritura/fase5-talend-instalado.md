# Fase 5: el Talend instalado y la decisión de cómo emitir

Revisado el 4 de noviembre de 2026 en esta máquina (solo lectura).

## Qué hay instalado

| Dato | Valor |
|---|---|
| Ubicación | `C:\Talend\8.0.1\studio` (JDK Zulu 21 en `C:\Talend\8.0.1`) |
| Producto | Talend Studio, marca "Talend Cloud Data Fabric", versión `8.0.1.20260925_1301-patch` (parches 2026-06, 2026-08 y 2026-09) |
| Características | familia `org.talend.lite.*` 8.0.3 (jobs estándar, joblets, big data); sin complementos de Job Script ni de línea de comandos (ningún plugin con `jobscript` o `commandline` entre los 1.382 de `plugins/`) |
| Proyecto de trabajo | `workspace/talendbancolombia-963626413/PRJ_BANCOLOMBIA` (almacenamiento Git, `productVersion` igual al producto) |
| Jobs existentes | decenas de `.item` guardados por Studio en `process/` (orquestadores con `tRunJob`, `tFileInput/OutputDelimited`, `tMap`, `tFixedFlowInput`, `tLogRow`, `tHashInput/Output`, `tDie`, `tJava`, conexiones Impala/HDFS/FTP) |
| Otros | una característica propia (`com.andres.talend.bridge.feature`) que no se usa: `AGENTS.md` prohíbe MCP |

## Decisión

El plan decía: confirmar la versión de Studio y probar cómo se ejecuta un Job Script, con el plan B de
parametrizar un Job exportado. Esta instalación **no trae Job Script ni línea de comandos**, así que el
plan A no es posible aquí. Se elige el plan B en su forma más directa: **escribir los archivos `.item` y
`.properties` que Studio guarda**, copiando la forma de Jobs reales de este mismo Studio.

Motivos:

- Hay ejemplos reales y recientes de la misma versión; el formato se puede comparar byte a byte.
- No se depende de un complemento ni de una función de pago que no está instalada.
- Es reproducible y revisable en Git: el resultado se copia a `process/` del proyecto.

## Qué se hizo (hito 59)

`src/sgm/talend_item/` escribe un Job con `tFixedFlowInput` y `tLogRow`. La prueba
`tests/unit/test_talend_item.py` compara nodos, conexiones y subjobs contra `tests/fixtures/talend/hijo_0.1.item`
(copia de un Job real de este Studio, sin contraseñas ni rutas locales): **son idénticos**. Los 96
parámetros base coinciden en campo y orden.

## Qué no se ha verificado

- **Nunca se abrió un Job emitido en Studio.** Esta sesión no puede abrir Studio. Un Job emitido que
  Studio rechace o "repare" al abrir es un riesgo real. Antes de seguir añadiendo componentes, una
  persona debe abrir un Job emitido (ver abajo).
- El `.properties` omite `item_key` (hash que Studio escribe; no se sabe cómo se calcula) y el
  `.screenshot`. Studio probablemente los regenera, pero no se comprobó.
- Las contraseñas por defecto del Job se emiten vacías (Studio guarda un valor cifrado).
- Solo hay dos componentes con ejemplo real comparado. Para los demás (`tMap`, `tFileInputExcel`,
  `tAggregateRow`, `tUnite`, `tReplicate`, `tRunJob`...) hay que copiar sus parámetros de un Job real
  y añadirlos con su prueba. `tFileInputExcel`, `tAggregateRow`, `tUnite` y `tReplicate` no tienen
  ejemplo en el proyecto: habría que crear uno en Studio y copiarlo.

## Cómo comprobarlo a mano

1. Generar un Job con `sgm.talend_item` (por ahora desde Python: ver la prueba).
2. Copiar `<nombre>/<nombre>_0.1.item` y `.properties` a `PRJ_BANCOLOMBIA/process/<carpeta>/`.
3. En Studio: clic derecho en Repository, "Refresh"; abrir el Job y ejecutarlo.
4. Anotar si Studio lo abre sin errores y qué cambia al guardarlo (comparar el `.item` guardado).
