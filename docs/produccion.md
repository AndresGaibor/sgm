# Estado de producción

Este documento responde una sola pregunta: **¿se puede poner `sgm` a producir hoy?** La respuesta
corta es **no**. La compuerta técnica puede estar en verde y la herramienta seguir sin cubrir el
corpus del cliente ni haber ejecutado un Job. Aquí se separa lo que ya está demostrado de lo que
falta, con la misma evidencia que usa el plan maestro.

## 1. Qué significa "producción" en este proyecto

`docs/automatizacion/03-plan-produccion.md` fija cinco condiciones verificables:

1. Suite verde y sin regresión: pruebas, `ruff` y el trinquete de métricas.
2. Invariantes en todo el corpus: trazabilidad, sin invención, determinismo, credenciales
   enmascaradas y cobertura de líneas.
3. Robustez: ningún archivo produce una excepción; lo que no se entiende queda como pendiente.
4. Guías revisadas por una persona para cada programa del cliente, con acta corta.
5. Un programa validado de extremo a extremo: construido en Studio y comparado con SAS con datos
   de prueba.

Las condiciones 4 y 5 no las puede cerrar un agente: necesitan al dueño del proceso, un ambiente
con SAS, Talend y datos, y un acta de aceptación.

## 2. Compuerta de liberación (MG-P14-02)

Un solo comando decide si el código se puede publicar:

```bash
uv run python tools/liberacion.py
```

Corre, en orden:

| Paso | Qué comprueba |
|---|---|
| `ruff check .` | Estilo y errores estáticos |
| `pytest -q -n 4` | Suite completa, con los anillos A y B del corpus |
| `tools/corpus.py oraculo todos --verificar` | El esperado de cada caso se regenera y coincide |
| `sgm migrar` dos veces | Mismos archivos y mismos bytes: anillo D |
| `sgm secretos` sobre esa salida | Cero credenciales en claro |
| Versión | `pyproject.toml`, paquete instalado y `CHANGELOG.md` coinciden |

Sale con 0 solo si todos los pasos pasan. `--sin-suite` sirve para iterar; `--sin-tablero` omite
la fotografía informativa. La suite se corre con cuatro workers a propósito: con `-n auto` esta
máquina lanzó decenas de workers y algunos fallaron al importar por recursos, un fallo intermitente
del entorno que no debe confundirse con una prueba rota.

`tools/ci.py` sigue siendo el cierre de cada hito; `tools/liberacion.py` es la compuerta de la
versión y añade determinismo, secretos y versión.

## 3. Avance medido

La cifra del plan maestro es el termómetro principal: **27,1 % de las 895 horas de agente** en el
hito 126m (sin cambio de crédito), con C7 (producción con personas) en 0 %. Ningún criterio C1 a C6
está cumplido.

| Termómetro | Valor | Qué falta para producción |
|---|---|---|
| Anillo A (`L0` a `L6` sin pendientes de traducción) | 84 de 101 (83 %) | Los 17 casos con pendiente y los niveles `L7` a `L9` |
| Anillo B (intérprete contra el esperado) | 86 de 93 elegibles (92 %) | 7 `xfail` y los casos fuera de `L0` a `L6` |
| Studio | 85 de 85 Jobs compilan tras los arreglos del hito 125m | **Ningún Job se ejecutó ni se comparó con su esperado** |
| `PROC SQL` | 46 % de la fase | Auto-`JOIN`, subconsulta escalar, `full`/`right` |
| DATA step | 23 % de la fase | Emisor de `MERGE`, `BY`, `OUTPUT` múltiple y `ARRAY` |
| Macros | 13 % de la fase | `%sysfunc`, `SELECT INTO`, macros generadoras |
| Entrada y salida | 24 % de la fase | XLSX, bases, `FILENAME`, `RSUBMIT` |
| Rendimiento (P12) | 0 % | Medición del programa de 800 KB y de los Jobs con volumen |
| Seguridad (P13) | 4 % | Lista de columnas sensibles, SBOM, pruebas con entradas hostiles |
| Producción (P14) | 0 % | Empaquetado verificado, piloto, UAT, corrida paralela, corte |

## 4. Bloqueos que impiden llamarlo producción

1. **Cobertura de traducción.** Un 17 % de los casos `L0` a `L6` sigue con pendiente y los niveles
   altos no están cubiertos. Migrar un programa real puede dejar bloques sin traducir.
2. **Nada se ejecutó en Studio.** Compilar prueba que el `.item` abre y que el Java compila; no
   prueba el resultado. Siguen sin verificar el `COUNT(DISTINCT)`, los grupos de nulos en `sum`, el
   orden de `tUnite` y el orden de nulos de `tSortRow`.
3. **Sin corrida paralela.** No hay comparación SAS contra Talend con los mismos datos y la
   tolerancia acordada (MG-P14-06). Sin eso no hay equivalencia demostrada.
4. **Piloto, UAT y acta.** MG-P14-04, 05 y 10 dependen de Negocio y Tecnología, no del repositorio.
5. **Operación.** No hay monitoreo, alertas ni plan de reversa (MG-P14-07 y 08).
6. **Rendimiento y seguridad incompletos.** P12 está en 0 % y P13 en 4 %; falta el SBOM y la
   revisión de inyección en literales SQL y expresiones Java.

## 5. Qué sí está listo

- La suite queda en verde: **2 601 pruebas pasan, 27 se saltan y 145 quedan en `xfail`**, con las
  expresiones de Byron portadas a la estructura local (COMPRESS, SCAN, LIKE e INPUT con informat
  dinámico pendiente y sin repetir el texto del programa).
- La compuerta se verificó el 7 de noviembre de 2026: oráculo de 117 casos sin fallas, 11 archivos
  de una migración idénticos byte a byte, 0 hallazgos de secretos y versión 0.2.0 coherente.
- `sgm --version`, la versión única y el changelog están comprobados por prueba.
- El emisor no filtra credenciales y `sgm secretos` lo vigila; la compuerta lo vuelve a comprobar
  sobre una migración real.
- La migración es determinista byte a byte sobre el caso de la compuerta.
- `sgm migrar` no falla ante entradas hostiles: deja pendientes con archivo y línea.

## 6. Lista de verificación antes de publicar

1. `uv run python tools/liberacion.py` en verde.
2. `uv run python tools/tablero.py` revisado: sin regresión de componentes ni de conformidad.
3. Un lote de Studio con los Jobs del cambio, compilando y ejecutando los casos representativos.
4. Piloto de tres programas reales con revisión del equipo de Talend (MG-P14-04).
5. Corrida paralela de un ciclo completo con diferencias explicadas o cero (MG-P14-06).
6. Acta de UAT y corte firmada por Negocio y Tecnología (MG-P14-05 y 10).
7. Plan de reversa y estabilización de dos a cuatro semanas (MG-P14-08 y 11).

Mientras los pasos 4 a 7 no estén firmados, la herramienta es un Release Candidate técnico, no un
producto en producción.
