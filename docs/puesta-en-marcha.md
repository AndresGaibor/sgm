# Puesta en marcha

Cómo dejar `sgm` funcionando en una máquina limpia y comprobar que quedó igual que en este
repositorio. Cubre lo que se puede reproducir sin el entorno del banco; lo que no, se dice al final.

## 1. Requisitos

| Necesidad | Versión / nota | ¿Obligatorio? |
|---|---|---|
| Python | 3.12 | Sí |
| `uv` | 0.12 o posterior | Sí |
| git | cualquiera reciente | Sí |
| Talend Studio | 8.0.1 con el proyecto `PRJ_BANCOLOMBIA` | Solo para validar Jobs (ver `docs/guia-validacion-studio.md`) |
| JDK de Studio | `zulu21`, el que trae Studio | Solo para ejecutar un Job exportado |
| `talend-mcp` | repositorio aparte, puerto 3927 | Solo para validar Jobs |
| Docker | con las imágenes locales de Impala y PostgreSQL | Solo para probar Jobs contra una base (`tools/contenedores/README.md`) |

La consola por defecto en Windows es PowerShell, pero los comandos de esta guía funcionan igual en
Git Bash. Los scripts del repositorio usan sintaxis POSIX.

## 2. Instalación

```bash
git clone <url-del-repositorio> sgm-v2
cd sgm-v2
uv sync
```

`uv sync` crea `.venv/` e instala las dependencias de `pyproject.toml`, incluidas `sqlglot` y
`jsonschema`, que están fuera de la lista permitida de `AGENTS.md` con la decisión escrita en
`PROGRESS.md` (DC-11, hito 80).

## 3. Comprobar que quedó bien

Un solo comando corre todo lo que el cierre de un hito exige:

```bash
uv run python tools/ci.py
```

Hace, en orden: `ruff check .`, la suite completa (`pytest -q`), los cruces del corpus, el oráculo
del corpus (`tools/corpus.py oraculo todos --verificar`) y el tablero. Termina con una tabla por
paso y sale con código distinto de 0 si algo falla.

En una máquina limpia, la referencia de la línea base es la de
`docs/plan-reescritura/metricas-base.md`: si la suite y el tablero dan otra cosa, algo cambió (no es
un problema del entorno: primero mira `git status`).

Por separado:

```bash
uv run pytest -q                       # suite completa; ~1 minuto con -n auto
uv run pytest --testmon -q -n 4        # ciclos locales: solo lo afectado por el cambio
uv run ruff check .
uv run python tools/tablero.py         # componentes, conformidad y corpus
```

`.testmondata` se crea en la primera pasada de `--testmon` y no se versiona. Antes de cerrar un
hito, la suite se corre completa, sin selección incremental.

## 4. Uso básico

```bash
uv run sgm talend tests/fixtures/sas/client/client_large.sas --out out
uv run sgm proceso tests/fixtures/sas/client/client_large.sas --out out
uv run sgm conformidad tests/fixtures/sas/client/client_large.sas
```

`sgm conformidad <programa.sas> [--decisiones carpeta] [--formato texto|json]` mide cuánto del
diseño manual de referencia sale del SAS. Cada fila recibe un estado: `derivada` (el SAS demuestra
su valor), `declarada` (el valor sale de `decisiones/`), `pendiente` (el migrador aún no la emite o
requiere una persona) o `diferente` (el migrador da otro valor, con el motivo). El comando imprime
los conteos, el porcentaje de derivadas y las diferencias. `--formato json` escribe una fila por
entrada en el orden de la referencia, así que dos corridas con las mismas entradas dan la misma
salida. La línea base medida en el hito 93 sobre `client_large.sas` es 5 derivadas de 118 filas
(4,2 %). La prueba `tests/conformidad/test_linea_base.py` fija esa cifra.

El resto de los comandos está en la tabla del `README.md`. `out/` está ignorado por git: después de
una ejecución completa, `git status` queda limpio.

## 5. Validar en Studio

Sigue `docs/guia-validacion-studio.md`. Resumen: arrancar `talend-mcp` con permiso de escritura y
ejecución, exportar `TALEND_PROJECT` y correr `tools/corpus_studio.py validar` o
`tools/validar_en_studio.py`. Sin Studio no hay forma de saber si un Job ejecuta.

## 6. Problemas conocidos

| Síntoma | Causa y arreglo |
|---|---|
| Tildes y `ñ` salen como `Ã±` en la consola | La consola de Windows no usa UTF-8. Los comandos de `tools/` reconfiguran su salida; si aun así pasa, exporta `PYTHONIOENCODING=utf-8` |
| `pytest --testmon` tarda lo mismo que la suite | Es normal en la primera pasada: está registrando qué archivo usa cada prueba |
| `tools/corpus.py` no ve los casos de `L8` | Se ven todos con `oraculo todos`; los casos de `L8` son capa A o C y el oráculo los omite con motivo (ver `tools/corpus_lib/DIFERENCIAS.md`) |
| La exportación de un Job falla por poms de Maven | Faltan en la caché de Studio; el validador los descarga. El detalle está en `workspace/.metadata/.log` |
| `uv sync` reescribe `uv.lock` | No debería; si pasa, revisa que no hayas tocado `pyproject.toml` y vuelve a `uv lock` |

## 7. Lo que no se reproduce sin el entorno del banco

- Los fixtures de `tests/fixtures/sas/real/` vienen del repositorio viejo, no de un SAS real.
- Los Jobs se validan contra el Studio y el proyecto `PRJ_BANCOLOMBIA` de la máquina del banco;
  las rutas y los usuarios reales por entorno son la tarea R4-06 (decisión DC-07, sin datos).
- Las tablas de Impala reales: en pruebas se usa el contenedor con tablas `sgmtest_`
  (`tools/contenedores/`), nunca una base del banco.
- La corrida paralela contra el SAS (R9-12) necesita el SAS y los insumos reales.
