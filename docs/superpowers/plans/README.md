# Planes ejecutables del migrador general

Los planes de esta carpeta son los que un agente ejecuta tarea por tarea (pruebas primero, commits frecuentes).
El documento de diseño y alcance es `docs/plan-reescritura/plan-migrador-general.md`; este índice los ordena.
Cada plan produce software que funciona y se prueba por sí solo. Se escribe el siguiente cuando el anterior
termina, con las firmas reales que dejó el anterior.

| Plan | Contenido | Depende de | Estado |
|---|---|---|---|
| `2026-11-05-mg-01-fundacion-rapida.md` | Backend de Talend (archivos y CLI de `talend-mcp`), salud de Studio, compilación en lote, ciclo rápido | nada | hecho (compilación real pendiente de repetición según `PROGRESS.md`) |
| `2026-11-05-mg-02-rebanada-vertical.md` | `sgm migrar` sin YAML para `PROC IMPORT`, `PROC SQL` simple y `PROC EXPORT`; contextos; validador; intérprete; corpus `L0` a `L2`; robustez sobre 190 programas | MG-01 (solo la Task 10) | hecho según la validación en Studio reportada en esta sesión; revisar `PROGRESS.md` |
| `2026-11-06-mg-03-expresiones-datastep.md` | Expresiones y funciones SAS→Java con semántica de faltantes; `DATA step` básico | MG-02 | hecho con alcance explícito; lote C compiló y dos casos se ejecutaron contra esperados (hito 106m). Véase `PROGRESS.md` para pendientes fuera del alcance |
| MG-04 (por escribir) | Agregados, subconsultas, conjuntos y procedimientos (`SORT`, `FREQ`, `MEANS`) (MG-P5-03 a 08, MG-P6) | MG-03 | pendiente |
| MG-05 (por escribir) | `MERGE`, `RETAIN`, `FIRST.`/`LAST.`, arrays, `UPDATE` (MG-P4-03 a 07) | MG-03 | pendiente |
| MG-06 (por escribir) | Macros: expansión estática completa y huecos del analizador (MG-P7) | MG-02 | pendiente |
| MG-07 (por escribir) | Arquitectura por omisión: padre, hijos, tamaño, joblets (investigar primero si Studio los carga) y paso de datos entre Jobs (MG-P8, MG-P9-03) | MG-04 | pendiente |
| MG-08 (por escribir) | Entrada y salida avanzada: `INFILE`/`INPUT`, bases (Impala, Postgres), `FILENAME`, `RSUBMIT`; configuración pendiente por entorno (MG-P2) | MG-02 | pendiente |
| MG-09 (por escribir) | Biblioteca de plantillas de componentes, emisor completo y comparación con `talend-mcp` (MG-P9) | MG-02 | pendiente |
| MG-10 (por escribir) | Verificación: generador de programas SAS, corrida nocturna, `sgm cobertura`, casos L7 y L9 (MG-P10) | MG-03 | pendiente |
| MG-11 (por escribir) | Rendimiento, seguridad y experiencia de uso (MG-P11 a MG-P13) | MG-07 | pendiente |
| MG-12 (por escribir) | Producción: empaquetado, piloto, corrida paralela, corte (MG-P14, personas) | todos | pendiente |

Regla de oro de todos los planes (instrucción del usuario): el migrador **no falla nunca**. Si algo no se puede
traducir o falta configuración o credenciales, se omite, se documenta en `pendientes.md` y
`configuracion-pendiente.md`, y el resto se genera al máximo.
