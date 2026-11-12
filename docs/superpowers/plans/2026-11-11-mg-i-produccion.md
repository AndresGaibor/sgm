# MG-I: Producción Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. Las tareas marcadas **(personas)** no las ejecuta un agente: son protocolos para el equipo del cliente; el agente solo hace lo que se lista en «Lo que prepara el agente» y deja su prueba.

**Goal:** Llevar `sgm` de «Release Candidate técnico» a producción medible: un paquete instalable en una máquina limpia que trae sus propios datos (`rules/`, `schemas/`, `env/`), una compuerta de liberación que con **un comando** decide si se libera, documentos de despliegue y operación, monitoreo con alertas, y las herramientas y protocolos para el piloto con programas reales, el UAT de Negocio, la corrida paralela SAS contra Talend, la reversa, la capacitación, el corte firmado y la estabilización. Cierra MG-P14 y las compuertas GM7 (piloto y corrida paralela con diferencias explicadas) y GM8 (corte firmado), y con ellas el criterio C7 del plan maestro.

**Architecture:** Dos tipos de trabajo. (1) De agente, en `sgm-v2`: `src/sgm/rutas.py` (resolución de datos empaquetados), `tools/liberacion.py` ampliada, `tools/publicar_version.py`, `tools/instalacion_limpia.py`, y una carpeta nueva `tools/produccion/` (verificador de documentos, alertas, piloto, corrida paralela, paquete de corte, defectos) con sus plantillas en `docs/produccion/`. Nada de esto toca el traductor: lee sus salidas (`trace.json`, `pendientes`, informes de la compuerta). (2) De personas: protocolos con quién, entradas, pasos, evidencia y criterio de aceptación; cada uno nombra qué deja preparado el agente. El núcleo de `sgm` sigue funcionando sin Studio abierto: Studio entra solo en el paso opcional de la compuerta (I-7) y en la validación del piloto.

**Tech Stack:** Python 3.12, pytest, ruff, `uv` 0.12 (`uv build`, `uv tool install`, `uv_build` como backend), `typer`, `pyyaml`; biblioteca estándar para todo lo nuevo (CSV, hashlib, zipfile, email). `uv run python -m pytest` y `uv run python -m sgm.cli` (en este Windows `uv run pytest` puede bloquearse por Control de aplicaciones).

**Spec:** `docs/plan-reescritura/plan-migrador-general.md` (MG-P14-01 a MG-P14-11, sección 1 criterios C6 y C7, sección 10 compuertas GM7 y GM8, decisiones MG-D01 a MG-D11) y `docs/plan-reescritura/ruta-a-produccion.md` (fase F9, subordinada). Estado de partida: `docs/produccion.md` (compuerta técnica verde el 7 de noviembre de 2026; «Release Candidate técnico, no un producto en producción»).

**Horas del plan maestro cubiertas:** MG-P14 agente 40 h (la parte de personas, unos 40 días, es de ellas y no se acredita al agente).

**Series de hitos:** `m` (carril de Andres, I-1 a I-18 e I-Gate). La letra va en el título de la entrada de `PROGRESS.md` y en el mensaje del commit. I-Gate lo cierra Andres con la corrida de Byron (Planes G y H) ya integrada.

## Global Constraints

- Sin `git push`, sin `--amend`. Un commit local por hito: `hito N m: <resumen>`, terminado con la línea `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`. Antes de escribir, buscar el último `## Hito` de `PROGRESS.md` (al redactar este plan era el 198) y sumar uno; si otra sesión ya tomó el número, tomar el siguiente. No renumerar entradas publicadas.
- No tocar `tools/ci.py`, `tools/validacion.py`, `tools/instalar_ganchos.py`, `README.md` ni `.githooks/` (son del Plan A y estaban sin commitear al redactar). La compuerta de este plan **no** importa de ellos y deja su evidencia en `out/liberacion/` (no versionada), no en `.cache/validacion/`. Si el Plan A ya los integró cuando se ejecute una tarea, se puede enlazar la compuerta con el candado de commit, pero solo en una tarea aparte.
- Nada de nombres de scripts de ejemplo (`cod1`, `cod2`, `cars_poc`, `exogena`, `split2`, `split3`, `executeBulkload`, `waitForBulkLoads`, `bulkload_generic`) en `src/` ni `rules/`; lo vigila `tests/unit/test_no_script_specific_names.py`. Nada de lo que depende del nombre del cliente va a `src/` ni a `rules/`: va a `decisiones/<programa>.*.yaml` o a `docs/produccion/`. Este plan **no lee ni cita** archivos con contraseñas en claro (por ejemplo el `Cod2.txt` de Descargas); el piloto trabaja sobre copias ya redactadas por `sgm intake` / `redaction.py`.
- No guardar secretos. Las plantillas de acta, los informes y los correos de alerta no llevan valores de columnas sensibles ni contraseñas: solo conteos, nombres y sumas de control. `sgm secretos` se corre sobre todo lo que se entrega.
- No inventar datos. Los umbrales de alerta, las tolerancias y los plazos de escalamiento que no estén decididos quedan como `PENDIENTE-DECISION` en el YAML con su decisión `MG-Dnn` o `DI-nn`; ninguna herramienta usa un valor supuesto sin decirlo en su salida.
- No borrar ni debilitar pruebas. Un paso de la compuerta que hoy falla se arregla en su causa; no se quita de la lista.
- Archivos de menos de 300 líneas. `tools/liberacion.py` tiene 205: I-6 extrae sus pasos a `tools/produccion/pasos_liberacion.py` antes de sumar pasos.
- Código e identificadores en inglés (los nombres ya existentes en español de `tools/` se conservan); comentarios, docstrings, mensajes de usuario y documentación en español.
- Después de cada tarea: `uv run python -m pytest -q` y `uv run ruff check src tests tools` en verde. Para iterar se corre solo el archivo de la tarea (`-p no:cacheprovider`); la suite completa se corre al cerrar cada tarea. La suite completa de esta serie la corre también `tools/liberacion.py` (I-Gate).
- Studio: se usa en dos puntos y nada más: el paso opcional de la compuerta (I-7) y el lote de cierre (I-Gate). Si `sgm studio salud` no conecta, no reinstalar nada ni cambiar `talend-mcp` (ver `docs/guia-validacion-studio.md`, sección 7: casi siempre es el servidor MCP del puerto 3927 apagado con Studio corriendo). El paso queda como `omitido: Studio no disponible` con su motivo, y **no se cuenta como pasado**.
- Las pruebas que construyen un wheel o instalan en un entorno temporal (I-2, I-5) llevan `pytest.mark.skipif(shutil.which("uv") is None, ...)` y escriben solo en `tmp_path`.
- Lo que depende de personas no se simula: una tarea de personas queda «preparada por el agente» cuando sus plantillas, scripts y pruebas están en verde, y «cerrada» solo cuando la persona entrega la evidencia que el protocolo nombra, en la ruta que nombra.

## Review Focus

- **«Un comando decide» no puede ser un verde engañoso:** la compuerta distingue tres veredictos (`LIBERABLE`, `VERDE SIN STUDIO`, `NO SE LIBERA`) y un paso omitido nunca cuenta como pasado. Hoy `tools/liberacion.py` no tiene pruebas propias (I-1) y no compila nada en Studio, de modo que su verde de noviembre no prueba que los Jobs funcionen (`docs/produccion.md`, sección 4, punto 2). Tests en I-1, I-6 e I-7.
- **El wheel hoy no funciona fuera del árbol:** 15 módulos de `src/sgm/` ubican `rules/`, `schemas/` y `env/` con `Path(__file__).resolve().parents[n]`; en un wheel esas carpetas no existen. `sgm --version` ya pasa limpio, pero `sgm migrar` en una máquina limpia fallaría. Tests en I-2, I-3 e I-5 (el de I-5 migra desde un entorno virgen y compara bytes con la migración del árbol).
- **Equivalencia sin SAS en el repositorio:** el oráculo real de la corrida paralela son exportaciones de SAS hechas por el cliente. El formato de entrega y el comparador tienen que rechazar entregas incompletas (sin manifiesto, sin conteo, con columnas distintas) en vez de compararlas a medias. Tests en I-12 y I-13.
- **Una diferencia explicada no es una diferencia ignorada:** cada diferencia lleva una causa de una lista cerrada, un responsable y, si es un defecto de `sgm`, un caso en el corpus que la reproduce. «Equivalente» se declara solo con cero diferencias sin explicar y ninguna causada por un defecto abierto. Test en I-14.
- **Las alertas no inventan umbrales:** sin umbral decidido (MG-D07 para tolerancias, `DI-02` para conteos), la herramienta informa «sin umbral» y no alerta en silencio. Test en I-9.
- **Corte reversible:** SAS no se apaga hasta que el criterio de reversa esté cumplido y firmado (I-15, I-17).

## Decisiones del plan maestro que bloquean (MG-D01 a MG-D11)

Estado según la tabla de la sección 8 del plan maestro. La opción por omisión es la que toma este plan si nadie decide antes; qué cambia dice qué tarea se redirige.

| Decisión | Bloquea | Opción por omisión que toma este plan | Qué cambia si el usuario o el cliente decide otra |
|---|---|---|---|
| MG-D01 versión de SAS del cliente | I-12 (qué sintaxis de exportación se admite), I-13 | 9.4 (edición 3.5), lo de las guías | Si el cliente usa 9.3, la plantilla de exportación de I-12 (`PROC EXPORT`, `ODS`) se prueba contra esa versión; el comparador no cambia |
| MG-D03 datasets `.sas7bdat` permanentes | I-12 (el oráculo de SAS exporta a CSV) | archivo de preparación con aviso | Si pasan a tabla de base, el manifiesto de I-12 gana `origen: base` y la corrida paralela exige además conteos por consulta; la persona los trae |
| MG-D04 código dinámico (`CALL EXECUTE`) | I-10 (criterios de selección del piloto) | pendiente con motivo | El piloto excluye programas con ese pendiente; si se decide reescribir a mano, se añade como hallazgo y no entra en los 3 |
| MG-D05 destino de bases | I-12, I-13 | Impala, Postgres y archivos | La corrida paralela compara solo esos destinos; otro destino queda fuera del alcance firmado y se anota en el acta |
| MG-D06 almacén de secretos | I-8 (runbook, sección de contextos) | variable de entorno del lanzador y contexto vacío | Si el cliente usa un gestor corporativo, el runbook cambia la sección de credenciales y I-9 no cambia; el producto no guarda secretos en ningún caso |
| MG-D07 tolerancia de comparación | I-13, I-14 | `0.005` por columna numérica o la del caso (el manifiesto puede fijarla por columna) | Una tolerancia distinta se escribe en el manifiesto; el código no cambia. Sin decisión firmada del cliente, GM7 no se declara |
| MG-D08 programas reales del cliente (quién y cuándo) | I-10, I-12, I-Gate (GM7) | sin programas reales: solo corpus | Sin programas reales, el piloto se ensaya con tres programas del corpus L9 (I-10, paso 5) y GM7 queda «ensayo»: **no** se firma |
| MG-D09 validación de `PROC IMPORT`/`EXPORT` en SAS real | I-14 | casos marcados `pendiente_revision` | La corrida paralela no declara equivalente una salida que dependa de un caso `pendiente_revision` hasta que Negocio lo valide |
| MG-D10 plataforma de despliegue | I-8, I-9, I-15 | Build Job exportado (el Job se ejecuta con el planificador del cliente) | TMC o Remote Engine: el runbook gana la sección de publicación y programación de planes; I-9 deja de leer registros del lanzador y lee los conteos de TMC (se redefine el origen en `docs/produccion/alertas.yaml`) |
| MG-D02, MG-D11 | ninguna | MG-D02 ya aprobada; MG-D11 decidida (b), `talend-mcp` opcional | MG-D11: la compuerta usa Studio solo si está disponible (I-7) |

Decisiones nuevas de este plan, a registrar en `PROGRESS.md` («Decisiones») con su alternativa:

- **DI-01 (I-2):** los datos del paquete (`rules/`, `schemas/`, `env/`) se publican en el wheel por la sección de datos de `uv_build` y se resuelven con `sgm.rutas`; alternativa descartada: mover esas carpetas bajo `src/sgm/datos/` (rompería rutas en tests, herramientas y documentación).
- **DI-02 (I-9):** los umbrales de alerta de conteos son relativos al conteo de la última corrida validada, con valor por omisión `PENDIENTE-DECISION`; los acuerda Negocio durante el piloto (I-10).
- **DI-03 (I-6):** códigos de salida de la compuerta: `0` liberable con Studio, `3` verde sin Studio, `1` falla, `2` uso inválido.

---

### Task I-1: Pruebas propias de la compuerta de liberación (MG-P14-02, parte 1; serie `m`)

`tools/liberacion.py` (205 líneas) decide hoy la liberación y **no tiene ninguna prueba**: solo la citan `docs/produccion.md` y el Plan G. Antes de ampliarla se fija su comportamiento.

**Files:**
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_liberacion.py`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\liberacion.py` (solo si una prueba revela un defecto; el cambio va en su propio paso)

**Interfaces:**
- Consumes (de `tools/liberacion.py`): `Resultado(nombre: str, codigo: int, segundos: float, detalle: str = "")` con la propiedad `marca` (`"OK"` o `"FALLA"`); `_version() -> str` (lanza `AssertionError` con los problemas separados por `; `); `_bytes(carpeta: Path) -> dict[str, bytes]`; `_pasos(sin_suite: bool) -> list[tuple[str, str | Callable[[], str]]]`; `_informe(resultados) -> str`; `main(argv: list[str] | None = None) -> int`; la constante de módulo `REPO`.
- Produces: la prueba, importando el módulo con `importlib.util.spec_from_file_location("liberacion", REPO / "tools" / "liberacion.py")` (`tools/` no es paquete).

- [ ] **Step 1: Write the failing tests** en `test_liberacion.py`. (a) `_bytes` de una carpeta con `a.txt` = `b"x"` y `sub/b.txt` = `b"y"` devuelve `{"a.txt": b"x", "sub/b.txt": b"y"}`. (b) `_version` con `liberacion.REPO` apuntando a un `tmp_path` cuyo `pyproject.toml` declara `version = "9.9.9"` y cuyo `CHANGELOG.md` solo trae `## [Sin publicar]` lanza `AssertionError` y el mensaje contiene `CHANGELOG.md no tiene la sección 9.9.9`. (c) `main(["--sin-suite"])` con `_pasos` reemplazado por `[("bien", lambda: "ok"), ("mal", lambda: (_ for _ in ()).throw(AssertionError("boom")))]` devuelve `1`, imprime en stderr `No se libera: falla mal.` y la tabla trae `| mal | FALLA |`. (d) Con los dos pasos en `lambda: "ok"` devuelve `0` e imprime `Compuerta verde: la versión se puede publicar.`. (e) `_pasos(True)` no contiene `"suite"` y `_pasos(False)` sí, en la posición 1.
- [ ] **Step 2: Run tests to verify they fail or pass honestly.** `uv run python -m pytest tests/unit/test_liberacion.py -q -p no:cacheprovider`. Lo esperado es que (a) a (e) pasen sin tocar el código; si alguna falla, anotar el defecto en `PROGRESS.md` («Hallazgos») y arreglarlo en el paso 3. Una prueba que pasa a la primera se deja: documenta el contrato.
- [ ] **Step 3: Implement** solo lo que una prueba rota exija (por ejemplo, que `main` imprima la cola de un paso fallido). Sin cambios de comportamiento si todo pasó.
- [ ] **Step 4: Run tests to verify they pass**, luego `uv run python tools/liberacion.py --sin-suite` y comparar con la tabla de `docs/produccion.md` (mismos cuatro pasos en OK).
- [ ] **Step 5: Run** `uv run ruff check src tests tools`. **Commit** `hito N m: pruebas propias de la compuerta de liberacion` (con la línea `Co-Authored-By`).

---

### Task I-2: Los datos del paquete viajan en el wheel (MG-P14-01, parte 1; serie `m`)

**Hallazgo de partida:** `src/sgm/catalog/config.py:26` (`ENV_DIR`), `src/sgm/expressions/expressions_base.py:9` (`FUNCTIONS_DIR`), `src/sgm/ir/types_code.py:29` (`INFORMATS_YAML`) y otros 12 módulos resuelven `rules/`, `schemas/` y `env/` con `Path(__file__).resolve().parents[n]`, que apunta al repositorio. Instalado con `uv tool install`, esas carpetas no existen y `sgm migrar` falla. `sgm --version` no lo nota porque no las lee.

**Files:**
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\rutas.py`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\pyproject.toml` (sección de datos de `uv_build`)
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_rutas.py`

**Interfaces:**
- Consumes: el patrón a reemplazar, tal cual está hoy, `Path(__file__).resolve().parents[3] / "rules" / "sas" / "functions"` (`expressions_base.py:9`); `[build-system] requires = ["uv_build>=0.12.24,<0.13.0"]`.
- Produces:
  ```python
  CARPETAS_DE_DATOS = ("rules", "schemas", "env")

  def raiz_de_datos() -> Path:
      """Carpeta que contiene `rules/`, `schemas/` y `env/`. Orden: variable `SGM_DATOS`; el árbol
      fuente (la carpeta que está dos niveles sobre este archivo, si trae las tres); la
      ubicación de datos del paquete instalado. Lanza `FileNotFoundError` nombrando los tres
      sitios si no la halla."""

  def datos(*partes: str) -> Path:
      """`raiz_de_datos() / partes...`; `datos("rules", "sas", "functions")`."""
  ```

- [ ] **Step 1: Investigar (una vez, sin cambiar código).** `uv build --wheel -o <scratch>/dist` y listar el contenido con `python -m zipfile -l <wheel>`. Anotar en `PROGRESS.md` qué carpetas trae (se espera: solo `sgm/` y metadatos, sin `rules/`). Leer en la ayuda de `uv build` y en la documentación de `uv_build` la clave de datos del backend (`[tool.uv.build-backend] data = {...}`: **verificar al ejecutar** el nombre exacto de la clave y a qué ruta del entorno instala cada destino) y decidir el destino de los datos del paquete (DI-01). Si `uv_build` no puede empaquetar carpetas fuera del módulo, la alternativa es mover las tres carpetas bajo `src/sgm/datos/` y es una decisión del usuario: parar y registrarla como bloqueo, no moverlas en esta tarea.
- [ ] **Step 2: Write the failing tests** en `test_rutas.py`: (a) con el árbol fuente, `datos("rules", "sas", "functions").is_dir()` es verdadero; (b) con `monkeypatch.setenv("SGM_DATOS", str(tmp_path))` y las tres carpetas creadas vacías, `raiz_de_datos() == tmp_path`; (c) con `SGM_DATOS` apuntando a una carpeta sin `rules/`, lanza `FileNotFoundError` y el mensaje contiene `SGM_DATOS`; (d) con el árbol fuente ausente (parchear la ubicación del módulo) y sin variable, el mensaje nombra el sitio de la instalación; (e) prueba con `skipif` de `uv`: construir el wheel en `tmp_path`, abrirlo con `zipfile` y comprobar que contiene un archivo bajo `rules/sas/functions/` y `schemas/` y `env/schemas.json` (la ruta interna exacta se fija en el paso 1).
- [ ] **Step 3: Run tests to verify they fail.** `uv run python -m pytest tests/unit/test_rutas.py -q -p no:cacheprovider`; esperado: no existe `sgm.rutas`.
- [ ] **Step 4: Implement** `rutas.py` (menos de 60 líneas, solo biblioteca estándar) y la sección de datos de `pyproject.toml` según el paso 1.
- [ ] **Step 5: Run tests to verify they pass**, `uv run ruff check src tests tools`. **Commit** `hito N m: los datos del paquete viajan en el wheel y se resuelven con sgm.rutas`.

---

### Task I-3: Los 15 módulos dejan de adivinar la raíz del repositorio (MG-P14-01, parte 2; serie `m`)

**Files:**
- Modify: los módulos que `grep -rln "parents\[[0-9]\]" src/sgm --include=*.py` lista (15 al redactar; entre ellos `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\src\sgm\catalog\config.py`, `catalog\describe.py`, `catalog\talend.py`, `compile.py`, `expressions\expressions_base.py`, `generadores.py`, `intake.py`, `ir\proc_rules.py`, `ir\sql_portability.py`, `ir\sql_semantics.py`, `ir\types_code.py`, `motivos.py`)
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_sin_raices_adivinadas.py`

**Interfaces:**
- Consumes: `sgm.rutas.datos(*partes) -> Path` (I-2).
- Produces: ninguna firma nueva; cada constante de módulo (`ENV_DIR`, `FUNCTIONS_DIR`, `INFORMATS_YAML`, `ROOT`...) conserva su nombre y su tipo `Path`, ahora definida con `datos(...)`. Los módulos que usan `ROOT` para algo que **no** es dato (por ejemplo una carpeta de salida) se dejan y se anotan en el test como excepción con su motivo.

- [ ] **Step 1: Write the failing test.** `test_sin_raices_adivinadas.py` recorre con `ast` todos los `.py` de `src/sgm/` y recoge las asignaciones de módulo cuyo valor contiene `Path(__file__)` y `parents` y cuya cadena de `/` incluye `"rules"`, `"schemas"` o `"env"`. Esperado: lista vacía. Hoy falla con los módulos de arriba. Excepciones permitidas: una tupla `EXCEPCIONES` con ruta y motivo (vacía al terminar, o cada una con su motivo escrito).
- [ ] **Step 2: Run test to verify it fails.** `uv run python -m pytest tests/unit/test_sin_raices_adivinadas.py -q -p no:cacheprovider`; esperado: falla nombrando los módulos.
- [ ] **Step 3: Implement** módulo por módulo, un commit si el conjunto es grande no hace falta: basta el commit final, pero tras **cada** módulo correr `tests/unit/test_golden.py tests/unit/test_golden_equivalencia.py` (cero cambios de firma ni de bytes). Sin lógica nueva: solo cambia de dónde sale la ruta.
- [ ] **Step 4: Run** el test nuevo en verde, la suite completa `uv run python -m pytest -q` y `uv run ruff check src tests tools`. La suite debe quedar con las mismas pasadas, `xfail` y saltadas que antes (anotar el conteo antes y después en `PROGRESS.md`).
- [ ] **Step 5: Commit.** `hito N m: los modulos usan sgm.rutas en vez de adivinar la raiz del repositorio`.

---

### Task I-4: Versión semántica y registro de cambios con una sola orden (MG-P14-01, parte 3; serie `m`)

`sgm --version`, `sgm.__version__` y `pyproject.toml` ya coinciden (`tests/unit/test_version.py`) y `CHANGELOG.md` sigue Keep a Changelog con la sección `## [Sin publicar]`. Falta lo que evita que una persona edite tres sitios a mano al liberar: una herramienta que sube la versión y mueve «Sin publicar» a su sección fechada.

**Files:**
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\publicar_version.py`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_publicar_version.py`

**Interfaces:**
- Consumes: la regla de `tools/liberacion.py::_version` (el `CHANGELOG.md` debe tener `## [<versión de pyproject>]` y `## [Sin publicar]`); la línea `version = "0.2.0"` de `pyproject.toml`.
- Produces:
  ```python
  def siguiente(version: str, nivel: str) -> str:
      """`nivel` en {"mayor", "menor", "parche"}; "0.2.0" + "menor" -> "0.3.0"; "1.4.9" + "parche" -> "1.4.10"."""

  def publicar(raiz: Path, nivel: str, fecha: str) -> str:
      """Reescribe `pyproject.toml` y mueve el contenido de `## [Sin publicar]` a
      `## [<nueva>] - <fecha>` dejando una `## [Sin publicar]` vacía arriba. Devuelve la versión
      nueva. Lanza `ValueError` si `Sin publicar` está vacía (no se publica nada) o si el nivel
      no vale. No hace commit ni etiqueta."""
  ```

- [ ] **Step 1: Write the failing tests.** `siguiente("0.2.0", "menor") == "0.3.0"`, `siguiente("1.4.9", "parche") == "1.4.10"`, `siguiente("1.4.9", "mayor") == "2.0.0"`, `siguiente("1.4", "parche")` lanza `ValueError`. Con una raíz en `tmp_path` (pyproject con `version = "0.2.0"` y changelog con `## [Sin publicar]`, `### Añadido` y una viñeta), `publicar(raiz, "menor", "2026-11-20")` devuelve `"0.3.0"`, el changelog queda con `## [Sin publicar]`, luego `## [0.3.0] - 2026-11-20` con la viñeta, y el pyproject dice `0.3.0`. Con `Sin publicar` sin viñetas lanza `ValueError`.
- [ ] **Step 2: Run tests to verify they fail.** `uv run python -m pytest tests/unit/test_publicar_version.py -q -p no:cacheprovider`.
- [ ] **Step 3: Implement** con expresiones regulares sobre texto (sin dependencias nuevas); `argparse` con `--nivel`, `--fecha` (por omisión la de hoy) y `--ejecutar`: **sin `--ejecutar` solo imprime lo que cambiaría** (un cambio de versión no se hace por accidente).
- [ ] **Step 4: Run tests to verify they pass.** Correr `uv run python tools/publicar_version.py --nivel parche` (sin `--ejecutar`) sobre el repositorio real y comprobar que solo imprime. No ejecutar la publicación real en esta tarea: la versión de liberación la sube I-Gate.
- [ ] **Step 5: Run** `uv run ruff check src tests tools`. **Commit** `hito N m: publicar_version sube la version y mueve el registro de cambios`.

---

### Task I-5: Instalación en entorno virgen, automatizada, y su verificación por una persona (MG-P14-01, parte 4; serie `m`)

La aceptación de MG-P14-01 es «instala en una máquina limpia (persona verifica una vez)». El agente deja listo todo lo automatizable y la persona repite el recorrido una sola vez en una máquina que nunca tuvo el repositorio.

**Files:**
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\instalacion_limpia.py`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\docs\produccion\plantillas\verificacion-instalacion.md`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_instalacion_limpia.py`

**Interfaces:**
- Consumes: `uv build --wheel -o <carpeta>`, `uv venv <carpeta>`, `uv pip install --python <venv>\Scripts\python.exe <wheel>` (en Windows el ejecutable del entorno está en `Scripts\`; **verificar al ejecutar**); `sgm.cli_migrar.migrar(programa: Path, salida: Path)` (lo usa `tools/liberacion.py::_salida`); `tools/liberacion.py::_bytes(carpeta) -> dict[str, bytes]`.
- Produces:
  ```python
  def instalar_en_limpio(raiz: Path, trabajo: Path, ejecutar=subprocess.run) -> dict:
      """Construye el wheel de `raiz`, crea un entorno virgen en `trabajo`, instala el wheel y
      corre dentro de él `sgm --version` y `sgm migrar <caso de la compuerta> <salida>`.
      Devuelve {"wheel": str, "sha256": str, "version": str, "archivos": int,
      "coincide_con_arbol": bool, "diferencias": list[str]}. `coincide_con_arbol` compara byte a
      byte la salida instalada con la de `migrar` desde el árbol. `ejecutar` se inyecta para
      probar sin red ni `uv`."""
  ```
  Salida del script: JSON en `out/instalacion_limpia/<versión>.json` (no versionado) y código 0 solo si `coincide_con_arbol` y `version` es la de `pyproject.toml`.

**Lo que prepara el agente para la persona:** `verificacion-instalacion.md`, una lista de verificación de una página con casillas y los comandos exactos del protocolo de abajo.

- [ ] **Step 1: Write the failing tests.** Con `ejecutar` falso que registra los comandos y devuelve código 0: `instalar_en_limpio` los invoca en el orden `uv build`, `uv venv`, `uv pip install`, `sgm --version`, `sgm migrar`, y devuelve `coincide_con_arbol=False` y una lista `diferencias` con el nombre del archivo cuando la salida instalada difiere en un byte de una carpeta preparada en el test. Un `ejecutar` que devuelve código 1 en `uv pip install` lanza `RuntimeError` con la cola de la salida. Una prueba real con `skipif` de `uv`: corre `instalar_en_limpio` sobre el repositorio y exige `coincide_con_arbol is True` (**es la prueba que hoy fallaría por el hallazgo de I-2: la que demuestra que I-2 e I-3 sirven**).
- [ ] **Step 2: Run tests to verify they fail.** `uv run python -m pytest tests/unit/test_instalacion_limpia.py -q -p no:cacheprovider`.
- [ ] **Step 3: Implement.** Todo en `tmp_path` o en la carpeta de trabajo; el entorno virgen no hereda `PYTHONPATH` ni `VIRTUAL_ENV` (limpiar el entorno del subproceso) y la salida se lee, nunca se ejecuta.
- [ ] **Step 4: Run tests to verify they pass** con I-2 e I-3 ya integradas. Pegar en `PROGRESS.md` el JSON resultante (versión, sha256 del wheel, archivos).
- [ ] **Step 5: Run** `uv run ruff check src tests tools`. **Commit** `hito N m: instalacion en entorno virgen automatizada y lista de verificacion de persona`.

**Protocolo P14-01b: verificación de instalación en máquina limpia (personas)**

- **Quién:** una persona de Tecnología del cliente (o de Qlik Consulting) con una estación que nunca tuvo el repositorio ni Python del proyecto. Ejecuta una vez por versión candidata.
- **Entradas:** el wheel `sgm-<versión>-py3-none-any.whl` y su `sha256` (de `out/instalacion_limpia/<versión>.json`); `uv` instalado; la carpeta de ejemplo `tests/corpus/L2/l2_01_inner_join_clientes_ventas/programa.sas` copiada aparte.
- **Pasos:** (1) comprobar el `sha256` del wheel (`Get-FileHash`); (2) `uv tool install <wheel>`; (3) `sgm --version` debe imprimir `sgm <versión>`; (4) `sgm --help` lista `migrar`, `secretos`, `comparar` y `studio`; (5) `sgm migrar <programa.sas> <carpeta-de-salida>` termina con código 0 y escribe los archivos del paquete; (6) `sgm secretos <carpeta-de-salida>` da 0 hallazgos; (7) repetir el paso 5 en otra carpeta y comparar (`Compare-Object` de los hashes de cada archivo): mismos bytes; (8) `uv tool uninstall sgm` y comprobar que `sgm` ya no responde.
- **Evidencia que se guarda:** `docs/produccion/evidencia/instalacion-<versión>.md` con la plantilla rellenada (equipo, sistema operativo, versión de `uv`, `sha256`, salida literal de los pasos 3 a 7, fecha y nombre de quien verifica). Sin capturas con rutas de usuario.
- **Criterio de aceptación:** los ocho pasos pasan sin editar nada a mano, sin acceso al repositorio y sin variables de entorno especiales. Un fallo se registra como hallazgo en `docs/produccion/evidencia/hallazgos.csv` (plantilla de I-10) con prioridad alta y bloquea la liberación.

---

### Task I-6: La compuerta decide con un comando y distingue «verde» de «verde sin Studio» (MG-P14-02, parte 2; serie `m`)

Hoy `tools/liberacion.py` corre `ruff`, suite, oráculo, anillo D sobre **un** caso y versión. Faltan: anillos A y B explícitos, determinismo ampliado (Plan G, G-3), cobertura medida (G-17), SBOM al día (hito 136), la instalación en limpio (I-5), que el árbol esté commiteado, y que el resultado quede guardado y no se pueda leer como «liberable» si Studio no corrió.

**Files:**
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\liberacion.py`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\produccion\__init__.py`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\produccion\pasos_liberacion.py`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_liberacion.py` (creada en I-1: se amplía) y `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_pasos_liberacion.py`

**Interfaces:**
- Consumes: `Resultado`, `_subproceso`, `_en_proceso`, `_informe`, `_pasos`, `_ejecutar` de `tools/liberacion.py`; el comando de I-5 (`tools/instalacion_limpia.py`); de los planes hermanos, si ya existen: `tools/determinismo.py` (G-3), `python -m sgm.cli cobertura --verificar` (G-17), `tools/seguridad/generar_sbom.py --check` (hito 136).
- Produces:
  ```python
  @dataclass(frozen=True)
  class Resultado:                       # se amplía el existente
      nombre: str; codigo: int; segundos: float; detalle: str = ""
      omitido: str = ""                  # motivo; "" si el paso corrió
      @property
      def marca(self) -> str: ...        # "OK" | "FALLA" | "OMITIDO"

  def veredicto(resultados: list[Resultado], exige_studio: bool = True) -> tuple[str, int]:
      """("LIBERABLE", 0) si todo OK y el paso `Studio` corrió y pasó;
      ("VERDE SIN STUDIO", 3) si todo lo demás OK y solo `Studio` está OMITIDO;
      ("NO SE LIBERA", 1) si algún paso FALLA u otro paso está OMITIDO.
      Un paso cuya herramienta no existe es FALLA con detalle `no existe <ruta> (<plan, tarea>)`."""

  def guardar_evidencia(resultados, veredicto, raiz: Path, carpeta: Path) -> Path:
      """Escribe `<carpeta>/<versión>-<commit corto>.json` con pasos, veredicto, commit completo,
      `arbol_limpio: bool`, versión y sha256 del wheel (si I-5 lo produjo)."""
  ```
  CLI: `--sin-suite`, `--sin-studio` (omite explícitamente y marca el paso `OMITIDO: pedido por el usuario`), `--permitir-arbol-sucio` (para iterar; con árbol sucio el veredicto máximo es `VERDE SIN STUDIO` y se escribe `arbol_limpio: false`).

- [ ] **Step 1: Extraer.** Mover `_version`, `_bytes` y `_salida` a `tools/produccion/pasos_liberacion.py` y dejarlos importados (sin cambio de comportamiento; `test_liberacion.py` de I-1 debe seguir verde). `tools/liberacion.py` queda en menos de 200 líneas. Como `tools/` no es paquete, `liberacion.py` añade `tools/` a `sys.path` como ya hace `tools/ci.py`.
- [ ] **Step 2: Write the failing tests.** `veredicto([...])` con tres `Resultado` OK y uno de nombre `Studio` con `omitido="Studio no disponible"` devuelve `("VERDE SIN STUDIO", 3)`; con uno en `codigo=1` devuelve `("NO SE LIBERA", 1)` aunque el de Studio esté omitido; con otro paso (no Studio) omitido devuelve `("NO SE LIBERA", 1)`; con todo OK incluido `Studio` devuelve `("LIBERABLE", 0)`. Un paso con herramienta inexistente (`tools/no_existe.py`) produce `Resultado` con `codigo=1` y detalle que empieza por `no existe`. `main` con pasos falsos, `--permitir-arbol-sucio` y árbol sucio simulado devuelve 3 a lo sumo. `guardar_evidencia` escribe un JSON con las claves `pasos`, `veredicto`, `commit`, `arbol_limpio`, `version`, y no contiene valores de variables de entorno.
- [ ] **Step 3: Run tests to verify they fail.** `uv run python -m pytest tests/unit/test_liberacion.py tests/unit/test_pasos_liberacion.py -q -p no:cacheprovider`.
- [ ] **Step 4: Implement.** Pasos nuevos, tras los actuales: `anillos A y B` (`pytest -q -n0 tests/unit/test_migrar_corpus_aceptacion.py tests/unit/test_migrar_corpus_anillo_b.py`), `determinismo ampliado` (`tools/determinismo.py`), `cobertura medida` (`python -m sgm.cli cobertura --verificar`), `SBOM al día`, `instalación en limpio` (I-5), `secretos en toda la salida` (el paso de determinismo y secretos de hoy usa un solo caso: se extiende a todos los casos de `tests/corpus/` que no estén en `migrar_pendientes.yaml`, con la salida de I-7 como carpeta compartida), `árbol limpio` (`git status --porcelain` vacío) y, al final, `Studio` (I-7). Registrar DI-03 en `PROGRESS.md` con la alternativa descartada: un solo código 0/1 (rechazada porque haría pasar por verde algo que no probó nada en Studio).
- [ ] **Step 5: Run tests to verify they pass**, luego `uv run python tools/liberacion.py --sin-suite --sin-studio --permitir-arbol-sucio` (debe imprimir `VERDE SIN STUDIO` y salir con 3; si falta una herramienta del Plan G o H, debe salir con 1 nombrándola) y `uv run ruff check src tests tools`. **Commit** `hito N m: la compuerta de liberacion distingue verde de verde sin Studio y guarda su evidencia`.

---

### Task I-7: Paso opcional de Studio: `talend_job_build_batch` de toda la salida (MG-P14-02, parte 3; serie `m`)

Es lo único que prueba que los Jobs abren y compilan; lo que **ejecuta y coincide** va aparte (lote C de cada plan y la corrida paralela). Con Studio no disponible el paso se omite con su motivo y el veredicto es `VERDE SIN STUDIO`.

**Files:**
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\produccion\compilar_toda_la_salida.py`
- Modify: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\liberacion.py` (registrar el paso `Studio`)
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_compilar_toda_la_salida.py`

**Interfaces:**
- Consumes (de `src/sgm/backend_talend/base.py`): `escribir(self, jobs: list[Job], carpeta: Path) -> list[Path]`, `compilar_lote(self, nombres: list[str]) -> ResultadoLote` con `compilan` y `no_compilan: dict[str, str]`, `refrescar(self) -> None`; `BackendNoDisponible` (de `sgm.backend_talend`); `sgm.cli_migrar.migrar`; `tools/corpus_studio.py lote` (el lote de los planes anteriores; este módulo no lo reemplaza).
- Produces:
  ```python
  def compilar_toda_la_salida(casos: list[Path], backend, jobs_dir: Path, tamano_lote: int = 25) -> dict:
      """Migra cada caso (los que `migrar_pendientes.yaml` no lista), copia sus Jobs a `jobs_dir`,
      compila por lotes de `tamano_lote` y devuelve {"jobs": int, "compilan": int,
      "no_compilan": {nombre: motivo}, "casos_sin_jobs": list[str], "omitido": str}.
      Si `backend` lanza `BackendNoDisponible`, devuelve `omitido` con el motivo y nada más."""
  ```

- [ ] **Step 1: Write the failing tests** con un backend falso: 3 casos, 7 Jobs en total, `compilar_lote` devuelve 6 compilados y `no_compilan={"J7": "error de Java"}`; el resultado es `{"jobs": 7, "compilan": 6, "no_compilan": {"J7": "error de Java"}, ...}`; con `tamano_lote=3` se hacen 3 llamadas a `compilar_lote`; un backend cuya primera llamada lanza `BackendNoDisponible("sin MCP")` devuelve `omitido == "Studio no disponible: sin MCP"` y no lanza. El paso `Studio` de la compuerta es `OMITIDO` en ese caso y `FALLA` si hay un `no_compilan` no vacío (un Job que no compila bloquea).
- [ ] **Step 2: Run tests to verify they fail.** `uv run python -m pytest tests/unit/test_compilar_toda_la_salida.py -q -p no:cacheprovider`.
- [ ] **Step 3: Implement.** Los nombres de Job salen de los `*.item` que `migrar` escribe (**verificar al ejecutar** la disposición real de la carpeta en `src/sgm/cli_migrar.py`); la carpeta de trabajo es `out/liberacion/jobs/` (no versionada) y se vacía al empezar. El proyecto de Studio sale de `--proyecto` (por omisión el del entorno de `sgm studio`).
- [ ] **Step 4: Run tests to verify they pass.** Con Studio disponible (`uv run python -m sgm.cli studio salud` conecta): corrida real `uv run python tools/liberacion.py --sin-suite` y pegar en `PROGRESS.md` `Jobs: N, compilan: M, no compilan: K` con su lista. Sin Studio: «lote C pendiente» con el motivo de `sgm studio salud` y la referencia a la sección 7 de `docs/guia-validacion-studio.md`; no se declara cerrada la parte de Studio y la compuerta queda en `VERDE SIN STUDIO`.
- [ ] **Step 5: Run** `uv run ruff check src tests tools`. **Commit** `hito N m: la compuerta compila en Studio toda la salida cuando Studio esta disponible`.

---

### Task I-8: Guía de despliegue y runbook de operación: contenido verificable (MG-P14-03; serie `m`)

El documento Word se genera aparte con la habilidad `qlik-documentos` (portada, historial de versiones, tabla de contenido, secciones numeradas, procedimientos con pasos y marcadores de capturas). **Esta tarea no genera el Word**: deja el contenido y la estructura en YAML, y una herramienta que comprueba que lo que el documento promete existe (cada comando citado, cada ruta, cada sección obligatoria). Así el Word no puede afirmar un comando que `sgm` no tiene.

**Files:**
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\docs\produccion\guia-despliegue.estructura.yaml`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\docs\produccion\runbook.estructura.yaml`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\produccion\verificar_docs.py`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_verificar_docs.py`

**Interfaces:**
- Consumes: `sgm.cli.app` (el objeto `typer.Typer`; los subcomandos registrados se leen con `typer.main.get_command(app).commands`, hoy entre otros `migrar`, `secretos`, `comparar`, `studio`, `conformidad`, `explicar` si H-8 ya está); `sgm.seguridad.escaner_secretos.escanear_ruta(ruta) -> Escaneo` con `.hallazgos` y `.revisados`.
- Produces:
  ```python
  def verificar(estructura: Path, raiz: Path, secciones_obligatorias: tuple[str, ...]) -> list[str]:
      """Problemas encontrados ([] si todo bien): sección obligatoria ausente (`id`), sección sin
      `contenido`, comando `sgm <sub>` cuyo `<sub>` no está registrado, ruta citada en `rutas`
      que no existe bajo `raiz`, y cualquier hallazgo de `escanear_ruta` sobre el YAML."""
  ```
  Formato de cada sección del YAML: `id`, `titulo`, `contenido` (lista de párrafos o pasos, en español), `comandos` (lista de líneas que empiezan por `sgm ` o `uv `), `rutas` (archivos del repositorio citados), `evidencia` (qué se guarda al ejecutarla, o vacío).

**Contenido de la guía de despliegue** (opción por omisión de MG-D10: **Build Job exportado**, el Job se ejecuta con el planificador del cliente; si el cliente elige TMC o Remote Engine, se añade la sección `publicacion-tmc` con su procedimiento y se anota en `PROGRESS.md`). Secciones obligatorias, en este orden: `alcance` (plataforma elegida y lo que queda fuera), `requisitos` (sistema operativo, JDK que exige el Job compilado, `uv`; el JDK exacto es **verificar al ejecutar** con el Build Job real del piloto), `instalacion` (I-5: `uv tool install`, `sgm --version`, desinstalación), `migracion` (`sgm migrar` sobre cada programa y lectura de `pendientes`), `revision` (qué mira el equipo de Talend: contextos, rutas, tipos, grupos de nulos), `construccion` (Studio o `sgm studio compilar` y exportación del Build Job), `contextos-y-secretos` (MG-D06: variable de entorno del lanzador, contexto vacío, nunca una contraseña en un archivo), `programacion` (cómo el planificador invoca el script del Job, códigos de salida), `verificacion-posterior` (`sgm comparar`, conteos de I-9), `reversa` (resumen y remisión a I-15), `anexos` (versiones, contactos, SBOM `docs/sbom.md`).

**Contenido del runbook de operación** (secciones obligatorias): `operacion-diaria` (qué se mira, a qué hora, dónde), `lectura-de-conteos` (formato de `corridas.jsonl`, I-9), `alertas-y-escalamiento` (tabla de severidad, correo, nivel 1/2/3, tiempos; los valores son los de `docs/produccion/alertas.yaml`), `fallas-conocidas` (síntoma, causa, acción; se alimenta de `pendientes.md` y de los hallazgos cerrados del piloto), `reproceso` (reiniciar un Job, ventana, doble carga: qué comprobar antes), `cambios` (cómo se cambia una decisión en `decisiones/`, cómo se actualiza `sgm` con `CHANGELOG.md` y la compuerta de I-6), `contactos`.

- [ ] **Step 1: Write the failing tests.** Una estructura mínima en `tmp_path` con una sola sección `alcance` y `secciones_obligatorias=("alcance", "requisitos")` devuelve un problema que contiene `requisitos`; una sección con `comandos: ["sgm inventado --x"]` devuelve un problema que contiene `inventado`; una con `rutas: ["no/existe.md"]` devuelve uno que contiene `no/existe.md`; una con la línea de contenido `password=Abc123456789` devuelve un problema de secretos (y el mensaje **no** contiene `Abc123456789`); una estructura correcta devuelve `[]`.
- [ ] **Step 2: Run tests to verify they fail.** `uv run python -m pytest tests/unit/test_verificar_docs.py -q -p no:cacheprovider`.
- [ ] **Step 3: Implement** `verificar_docs.py` (CLI: `python tools/produccion/verificar_docs.py <estructura> --obligatorias a,b,c`, sale 1 si hay problemas) y escribir los dos YAML con las secciones de arriba, con contenido real (comandos y rutas que existan hoy; lo que depende de una decisión pendiente lleva la marca `PENDIENTE-DECISION MG-Dnn` en el texto y no se inventa). Añadir a `test_verificar_docs.py` una prueba que corre `verificar` sobre los dos YAML reales con las listas de secciones de arriba y exige `[]`.
- [ ] **Step 4: Run tests to verify they pass**; `uv run python tools/produccion/verificar_docs.py docs/produccion/guia-despliegue.estructura.yaml --obligatorias alcance,requisitos,instalacion,migracion,revision,construccion,contextos-y-secretos,programacion,verificacion-posterior,reversa,anexos`.
- [ ] **Step 5: Run** `uv run ruff check src tests tools`. **Commit** `hito N m: guia de despliegue y runbook como contenido verificable`.

**Protocolo P14-03b: Word firmado de despliegue y operación (personas)**

- **Quién:** el agente (o Andres) genera el Word con `qlik-documentos` a partir de los dos YAML; **firma** el responsable de Tecnología del cliente.
- **Entradas:** los dos YAML con `verificar_docs.py` en verde; las capturas de pantalla de Studio y de la consola del planificador que los marcadores piden (las toma el equipo de Talend).
- **Pasos:** (1) generar los dos Word; (2) el equipo operador ejecuta la guía de despliegue **siguiendo solo el documento** sobre el piloto de I-10; (3) cada paso que no se pudo seguir se anota como hallazgo; (4) se corrige el YAML y se regenera; (5) firma.
- **Evidencia:** `docs/produccion/evidencia/guia-despliegue-<versión>.docx` y `runbook-<versión>.docx` (o enlace a su ubicación si el cliente no permite versionarlos) y el acta de lectura firmada (`acta-despliegue.md`, formato de I-11, tipo `uat`).
- **Criterio de aceptación:** el equipo operador completó el despliegue del piloto sin ayuda externa y con cero pasos sin poder seguir; documento firmado por Tecnología.

---

### Task I-9: Monitoreo y alertas: códigos de salida, conteos publicados, correo y escalamiento (MG-P14-07; serie `m`)

Los Jobs que emite `sgm` llevan `tDie` y `tLogRow` de cierre (`src/sgm/emit/conventions/infra.py` define `ERROR_COMPONENT = "tDie"`). La opción por omisión de MG-D10 (Build Job con planificador del cliente) deja la vigilancia en un registro de corridas que escribe el lanzador; esta tarea define su formato y la herramienta que lo evalúa.

**Files:**
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\produccion\alertas.py`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\docs\produccion\alertas.yaml`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_alertas.py`

**Interfaces:**
- Consumes: el registro de corridas, una línea JSON por corrida en `corridas.jsonl` con `{"job": str, "inicio": "AAAA-MM-DDTHH:MM:SS", "fin": str, "codigo_salida": int, "filas_leidas": int | null, "filas_escritas": int | null}` (el lanzador lo escribe; **verificar al ejecutar** cómo el Job publica sus conteos: el `tLogRow` de cierre de `desde_plan.py` / `componentes.py` y el código de salida de `tDie` en el script del Build Job).
- Produces:
  ```python
  @dataclass(frozen=True)
  class Alerta:
      severidad: str      # "critica" | "alta" | "info"
      job: str
      regla: str          # "codigo_salida" | "corrida_ausente" | "conteo_fuera_de_umbral" | "escritura_vacia" | "sin_umbral"
      detalle: str
      escalar_a: str      # "N1" | "N2" | "N3" (del YAML)

  def evaluar(registros: list[dict], config: dict, ahora: datetime) -> list[Alerta]
  def redactar_correo(alertas: list[Alerta], config: dict) -> EmailMessage
  ```
  Reglas: `codigo_salida != 0` es `critica`; `filas_escritas == 0` con `filas_leidas > 0` es `critica`; sin corrida desde hace más de `frecuencia_horas * 1.5` es `alta`; conteo que se desvía más que `umbral_relativo` del `conteo_referencia` del Job es `alta`; si el Job no tiene `umbral_relativo` decidido (`PENDIENTE-DECISION`), emite `info` con regla `sin_umbral` y **no** una alerta de conteo (DI-02). `alertas.yaml` trae por Job `frecuencia_horas`, `conteo_referencia` (el de la última corrida validada, lo fija la corrida paralela de I-14), `umbral_relativo`, y la ruta de escalamiento: N1 (equipo operador, respuesta en `PENDIENTE-DECISION` minutos), N2 (equipo Talend), N3 (Qlik Consulting / dueño del proceso en Negocio) con `correo` de cada nivel como marcador de posición, nunca direcciones inventadas.

- [ ] **Step 1: Write the failing tests** con `ahora = 2026-11-20T08:00:00`: un registro con `codigo_salida=1` produce una `Alerta(severidad="critica", regla="codigo_salida", escalar_a="N1")`; `filas_leidas=100, filas_escritas=0` produce `escritura_vacia`; con `conteo_referencia=1000`, `umbral_relativo=0.02` y `filas_escritas=1030` produce `conteo_fuera_de_umbral` (3 % de desvío) y con `1010` no produce alerta; un Job con `frecuencia_horas=24` cuya última corrida terminó el `2026-11-18T07:00:00` produce `corrida_ausente`; un Job con `umbral_relativo: PENDIENTE-DECISION` produce `sin_umbral` con severidad `info` y ninguna alerta de conteo; `redactar_correo` devuelve un `EmailMessage` cuyo asunto empieza por `[sgm] CRITICA` si hay una crítica, cuyo cuerpo lista Job, regla y detalle, y que no contiene ningún valor de columna (solo conteos). Un YAML con un nivel sin `correo` falla con `ValueError`.
- [ ] **Step 2: Run tests to verify they fail.** `uv run python -m pytest tests/unit/test_alertas.py -q -p no:cacheprovider`.
- [ ] **Step 3: Implement.** CLI `python tools/produccion/alertas.py --corridas <jsonl> --config docs/produccion/alertas.yaml --salida <carpeta>`: escribe `<carpeta>/alerta-<fecha>.eml` y sale 0 sin alertas altas o críticas, 1 con alguna, 2 si el uso o el YAML no valen. Envío SMTP solo con `--enviar` (el servidor sale de la variable de entorno `SGM_SMTP`, sin contraseña en archivo: MG-D06; la función recibe una fábrica de conexión para probarla sin red).
- [ ] **Step 4: Run tests to verify they pass.** Prueba de humo con un `corridas.jsonl` fabricado en `tmp_path`.
- [ ] **Step 5: Run** `uv run ruff check src tests tools`. **Commit** `hito N m: evaluador de alertas de operacion con correo y ruta de escalamiento`.

**Protocolo P14-07b: pruebas de alerta en preproducción (personas)**

- **Quién:** equipo operador (provoca y recibe) y Tecnología (aprueba). Una vez, antes del corte (I-17).
- **Entradas:** el planificador de preproducción con los 3 Jobs del piloto, `alertas.yaml` con los correos reales de N1 a N3 y los umbrales acordados con Negocio durante el piloto (DI-02), un buzón de prueba.
- **Pasos:** (1) provocar un fallo de un Job (renombrar su archivo de entrada) y comprobar `codigo_salida`: correo crítico a N1 en menos del plazo escrito; (2) provocar una carga vacía y comprobar `escritura_vacia`; (3) detener el planificador un ciclo y comprobar `corrida_ausente`; (4) cargar un archivo con 5 % más filas que la referencia y comprobar `conteo_fuera_de_umbral`; (5) no atender un correo de N1 durante el plazo y comprobar que sale el aviso a N2; (6) restaurar y comprobar que el siguiente ciclo no alerta.
- **Evidencia:** `docs/produccion/evidencia/alertas-<fecha>.md` con, por cada prueba, hora de provocación, hora del correo recibido (encabezados, no cuerpo con datos) y quién lo recibió.
- **Criterio de aceptación:** las seis pruebas dan el resultado esperado en el plazo escrito; cualquier alerta que no llegó es un hallazgo crítico en `hallazgos.csv`.

---

### Task I-10: Piloto: selección, hallazgos y lista cerrada (MG-P14-04, herramientas del agente; serie `m`)

**Files:**
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\produccion\hallazgos.py`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\produccion\seleccion_piloto.py`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\docs\produccion\plantillas\hallazgos.csv`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_hallazgos.py` y `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_seleccion_piloto.py`

**Interfaces:**
- Consumes: `sgm.cli_migrar.migrar(programa, salida)` (devuelve un objeto con `.carpeta`; **verificar al ejecutar** de dónde sale la lista de pendientes: `pendientes.md` o `trace.json` en esa carpeta); el catálogo de construcciones de `rules/sas/catalogo/*.yaml`.
- Produces:
  ```python
  COLUMNAS = ("id", "programa", "origen", "prioridad", "descripcion", "causa", "estado",
              "caso_corpus", "commit", "evidencia", "responsable", "fecha_apertura", "fecha_cierre")
  ESTADOS = ("abierto", "en_correccion", "cerrado", "no_aplica")
  PRIORIDADES = ("critica", "alta", "media", "baja")
  CAUSAS = ("defecto_sgm", "decision_pendiente", "dato_distinto", "regla_de_negocio", "ambiente", "documentacion")

  def verificar_cierre(filas: list[dict], raiz: Path) -> list[str]:
      """Problemas que impiden decir «lista cerrada»: fila abierta o en_correccion; cerrada sin
      `evidencia` o con una ruta que no existe; `defecto_sgm` cerrado sin `caso_corpus` existente
      bajo `tests/corpus/` ni `commit`; `no_aplica` sin `descripcion`; valores fuera de las listas."""

  def puntuar(programa: Path, migrar=...) -> dict:
      """{"programa": str, "lineas": int, "construcciones": list[str], "pendientes": int,
      "usa_codigo_dinamico": bool, "elegible": bool, "motivo": str}."""

  def seleccionar(candidatos: list[dict], cuantos: int = 3) -> list[dict]:
      """Elige `cuantos` elegibles que cubran familias distintas (SQL, DATA step por grupos o
      MERGE, macros), empatando por menos pendientes y por tamaño mediano. Si no hay `cuantos`
      que cubran tres familias, devuelve los que hay y `motivo` lo dice."""
  ```

- [ ] **Step 1: Write the failing tests.** `verificar_cierre` con una fila `estado=abierto` devuelve un problema con su `id`; con `estado=cerrado, causa=defecto_sgm, caso_corpus=""` devuelve un problema; con `estado=cerrado, causa=dato_distinto, evidencia="no/existe.md"` devuelve un problema; con todo en regla devuelve `[]`. `seleccionar` de 5 candidatos (dos solo-SQL, uno con `CALL EXECUTE`, uno DATA con MERGE, uno con macros) elige los tres de familias distintas y deja fuera el del código dinámico (MG-D04), con `cuantos=3`; con solo dos familias disponibles devuelve 2 y un `motivo` que contiene `familias`.
- [ ] **Step 2: Run tests to verify they fail.** `uv run python -m pytest tests/unit/test_hallazgos.py tests/unit/test_seleccion_piloto.py -q -p no:cacheprovider`.
- [ ] **Step 3: Implement** con `csv` y `argparse` (`hallazgos.py verificar <csv>` sale 1 con problemas). La plantilla `hallazgos.csv` trae solo la cabecera.
- [ ] **Step 4: Run tests to verify they pass.**
- [ ] **Step 5: Run** `uv run ruff check src tests tools`. **Commit** `hito N m: herramientas del piloto: seleccion y lista de hallazgos cerrada`.

**Protocolo P14-04: piloto con 3 programas reales del cliente (personas; depende de MG-D08)**

- **Quién:** Tecnología del cliente (propone y entrega los programas; dueño de MG-D08), equipo de Talend (revisa los Jobs), Negocio (dueño de cada proceso, valida salidas), Qlik Consulting (corrige defectos; Andres o Byron según el carril).
- **Entradas:** 6 a 8 programas SAS candidatos con su dueño de negocio nombrado, ya **redactados** (sin contraseñas ni `pwencode` en claro: `sgm intake` los deja con `'***'`); un ambiente de preproducción de Talend con datos de prueba aprobados por Negocio; los criterios de abajo. Los programas y datos reales **no se versionan**: viven en `corpus/` (ignorada por git) o en la ubicación del cliente.
- **Pasos:** (1) correr `seleccion_piloto.py` sobre los candidatos y proponer 3 que cubran SQL, DATA step por grupos o `MERGE` y macros, con un dueño de negocio cada uno, sin `CALL EXECUTE` (MG-D04) y con la menor cantidad de pendientes; Tecnología firma la selección; (2) `sgm migrar` de cada programa y lectura conjunta de `pendientes`: los pendientes de alcance se aceptan o se corrigen, los de defecto se abren como hallazgo; (3) sesión de revisión de los Jobs con el equipo de Talend (checklist: contextos, rutas y nombres, tipos y longitudes, orden y nulos en agrupaciones y uniones, escritura y codificación de archivos, y un recorrido del `trace.json` de los nodos que el equipo no entienda); (4) compilar y ejecutar en preproducción (`sgm studio compilar`, ejecución con el planificador de prueba); (5) cada diferencia entre lo que produjo el Job y lo que Negocio espera es un hallazgo con causa de la lista cerrada; (6) corrección de los `defecto_sgm` con caso nuevo en el corpus (nunca solo un parche al programa del cliente); (7) repetir 4 a 6 hasta que `hallazgos.py verificar` dé `[]`.
- **Evidencia que se guarda:** `docs/produccion/evidencia/piloto/seleccion.json`; por programa, `docs/produccion/evidencia/piloto/<programa>/hallazgos.csv` y `acta-revision.md` (fecha, asistentes, decisiones; formato de I-11, tipo `uat` con rol Talend); el hash del `trace.json` y de la versión de `sgm` usada. Nada con valores reales de datos.
- **Criterio de aceptación:** los 3 programas migran, compilan y ejecutan en preproducción; `hallazgos.py verificar` sobre los tres CSV devuelve `[]` (ninguno abierto, cada defecto con caso de corpus y commit); cero hallazgos críticos o altos sin cerrar; el acta de revisión firmada por el equipo de Talend. **Sin programas reales (opción por omisión de MG-D08):** se ensaya el mismo protocolo con tres programas de `tests/corpus/L9/` (o `L6` si `L9` no existe) y el resultado se registra como «ensayo»; **GM7 no se declara** con un ensayo.

---

### Task I-11: Acta de aceptación: plantilla y verificador (MG-P14-05, herramientas del agente; serie `m`)

**Files:**
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\produccion\acta.py`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\docs\produccion\plantillas\acta-uat.md`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_acta.py`

**Interfaces:**
- Consumes: `yaml.safe_load` (PyYAML, ya dependencia); el acta es Markdown con un bloque YAML al inicio entre líneas `---`.
- Produces:
  ```python
  ROLES_UAT = ("Negocio",)
  ROLES_CORTE = ("Negocio", "Tecnologia")

  def verificar_acta(ruta: Path, tipo: str, raiz: Path) -> list[str]:
      """`tipo` en {"uat", "corte"}. Problemas: falta un campo del bloque (`tipo`, `programa` o
      `alcance`, `version_sgm`, `fecha`, `criterios`, `firmantes`); un criterio sin `resultado`
      en {"aceptado", "rechazado", "condicional"} o con `evidencia` inexistente bajo `raiz`;
      un resultado `rechazado` o `condicional` en un acta que se declara cerrada; falta un
      firmante de un rol obligatorio (ROLES_UAT / ROLES_CORTE); firmante sin `fecha` o sin
      `firma_ref`; `sha256` de `firma_ref` que no coincide con el archivo si existe; el texto
      `PENDIENTE` en cualquier parte."""
  ```

- [ ] **Step 1: Write the failing tests.** Un acta `uat` con un criterio `aceptado` con evidencia existente y un firmante `Negocio` con fecha y `firma_ref` devuelve `[]`; sin el firmante devuelve un problema que contiene `Negocio`; con un criterio `condicional` devuelve uno que contiene el `id` del criterio; con `PENDIENTE` en el cuerpo devuelve uno; un acta `corte` con solo `Negocio` devuelve uno que contiene `Tecnologia`; `sha256` equivocado de `firma_ref` devuelve uno.
- [ ] **Step 2: Run tests to verify they fail.** `uv run python -m pytest tests/unit/test_acta.py -q -p no:cacheprovider`.
- [ ] **Step 3: Implement** y escribir `acta-uat.md` con el bloque YAML vacío comentado y las secciones: alcance (programas y versión de `sgm`), criterios de aceptación (por cada salida: qué se espera, quién lo valida, resultado, evidencia), diferencias aceptadas y su explicación, condiciones, firmas.
- [ ] **Step 4: Run tests to verify they pass.**
- [ ] **Step 5: Run** `uv run ruff check src tests tools`. **Commit** `hito N m: plantilla y verificador de actas de aceptacion`.

**Protocolo P14-05: UAT de Negocio sobre los resultados del piloto (personas)**

- **Quién:** el dueño de negocio de cada uno de los 3 programas del piloto (acepta); Tecnología (convoca y registra); Qlik Consulting (explica diferencias).
- **Entradas:** las salidas de los Jobs del piloto en preproducción; los informes de `sgm comparar` y de I-13 contra la exportación de SAS (si ya existe, ver P14-06); `hallazgos.csv` de I-10; la plantilla `acta-uat.md`.
- **Pasos:** (1) Negocio define con Tecnología, **antes** de mirar resultados, qué criterio acepta por salida (conteo, sumas por columna, muestra de filas, formato de archivo); (2) Qlik presenta resultados y diferencias explicadas; (3) Negocio revisa una muestra de filas elegida por Negocio y no por Qlik; (4) cada criterio queda `aceptado`, `rechazado` o `condicional` con su evidencia; (5) un `rechazado` o `condicional` abre un hallazgo (I-10) y el UAT se repite sobre lo corregido; (6) Negocio firma.
- **Evidencia:** `docs/produccion/evidencia/uat/<programa>.acta.md` más el PDF firmado fuera del repositorio con su `sha256` en `firma_ref`.
- **Criterio de aceptación:** `acta.py verificar --tipo uat` devuelve `[]` para los 3 programas: todos los criterios `aceptado`, firma de Negocio con fecha.

---

### Task I-12: Formato de entrega del oráculo de SAS, plantilla de exportación y lector (MG-P14-06, parte 1; serie `m`)

El oráculo real de la corrida paralela son los resultados que SAS produjo con los datos congelados del cliente: el repositorio no los tiene ni los puede generar (no hay SAS). Esta tarea fija **cómo se entregan** y rechaza una entrega incompleta antes de compararla.

**Formato de entrega** (una carpeta por corrida, `entrega-<programa>-<corrida>/`):

- `manifiesto.yaml`:
  ```yaml
  version_formato: 1
  corrida: {id: "2026-12-01", ciclo: "2026-12", programa: "<nombre>", sas_version: "9.4", fecha_ejecucion: "2026-12-01"}
  insumos: {<archivo>: <sha256>}        # los datos de entrada congelados que usó SAS
  faltante_texto: ""                   # cómo aparece un faltante en el CSV (vacío por omisión)
  tablas:
    - nombre: ventas_mes
      archivo: ventas_mes.csv
      filas: 12345                     # conteo que SAS declara (PROC SQL COUNT(*) o NOBS)
      sha256: <del CSV>
      clave: [cliente_id, periodo]     # columnas que identifican una fila; sin repetidos
      columnas:
        - {nombre: cliente_id, tipo: caracter}
        - {nombre: saldo, tipo: numerico, tolerancia: 0.005, sensible: false}   # MG-D07
        - {nombre: fecha_corte, tipo: fecha}
  ```
- Un CSV por tabla: UTF-8 sin BOM, separador `,`, texto entre comillas, punto decimal, **sin separador de miles**, fechas ISO `AAAA-MM-DD`, cabecera igual a `columnas`, una fila por registro.
- `exportar_oraculo.sas` (plantilla para el equipo SAS del cliente, en `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\produccion\plantillas\exportar_oraculo.sas`): por cada tabla, `PROC EXPORT` a CSV con la opción de comillas de la guía (`proc.pdf`, ubicar la sección en `docs/referencia/sas/proc.INDEX.md`, **verificar la página y la sintaxis de cada opción antes de fijarla**), un `PROC SQL` que deja el conteo en una variable de macro y un `DATA _NULL_` que escribe el `manifiesto.yaml` con `FILE`/`PUT`. Lo que no se pueda demostrar con una página de las guías queda como comentario `Pendiente:` en la plantilla; el equipo SAS la prueba en su ambiente y reporta (MG-D01).

**Files:**
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\produccion\entrega_sas.py`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\produccion\plantillas\exportar_oraculo.sas`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_entrega_sas.py`

**Interfaces:**
- Consumes: `yaml.safe_load`, `csv`, `hashlib`. No reutiliza `sgm.verify._numero`, que cambia la coma por punto y falla con miles; el formato de arriba lo evita.
- Produces:
  ```python
  @dataclass(frozen=True)
  class Columna: nombre: str; tipo: str; tolerancia: float | None; sensible: bool
  @dataclass(frozen=True)
  class Tabla: nombre: str; archivo: Path; filas: int; clave: tuple[str, ...]; columnas: tuple[Columna, ...]
  @dataclass(frozen=True)
  class Entrega: corrida: dict; faltante_texto: str; insumos: dict[str, str]; tablas: tuple[Tabla, ...]

  def leer_entrega(carpeta: Path) -> Entrega:
      """Lanza `EntregaInvalida` (con la lista de problemas) si: no hay `manifiesto.yaml`; falta
      un CSV; `filas` declarado difiere de las filas reales; `sha256` no coincide; la cabecera
      no es igual a `columnas`; una columna `numerico` tiene un valor que no es número ni el
      faltante; una columna de `clave` tiene repetidos; falta `version_formato` o es distinta
      de 1; una columna `numerico` sin `tolerancia` y sin tolerancia por omisión declarada."""
  ```

- [ ] **Step 1: Write the failing tests** con una entrega mínima en `tmp_path` (tabla `t` de 3 filas: `id,saldo` con `1,100.50`, `2,200.00`, `3,`): `leer_entrega` devuelve 1 tabla con `filas=3`; con `filas: 4` en el manifiesto lanza `EntregaInvalida` y el mensaje contiene `filas` y `t`; con un `sha256` cambiado lanza con `sha256`; con `saldo` = `1.234,5` (miles) lanza con `saldo`; con el `id` repetido lanza con `clave`; sin `manifiesto.yaml` lanza con `manifiesto`. Además, una prueba de que la plantilla `.sas` existe, no contiene la palabra `password` ni nombres de scripts de ejemplo, y trae al menos un comentario `Pendiente:` o una cita `proc.pdf, p. N` cuyo `N` esté en `docs/referencia/sas/proc.INDEX.md`.
- [ ] **Step 2: Run tests to verify they fail.** `uv run python -m pytest tests/unit/test_entrega_sas.py -q -p no:cacheprovider`.
- [ ] **Step 3: Implement** `entrega_sas.py` (menos de 200 líneas) y escribir la plantilla `.sas`.
- [ ] **Step 4: Run tests to verify they pass.**
- [ ] **Step 5: Run** `uv run ruff check src tests tools`. **Commit** `hito N m: formato de entrega del oraculo de SAS con manifiesto y lector estricto`.

---

### Task I-13: Comparador de la corrida paralela: conteos, sumas de control por columna y muestra de filas (MG-P14-06, parte 2; serie `m`)

`sgm comparar` (`src/sgm/verify.py`) compara dos CSV: filas, sumas de columnas totalmente numéricas (igualdad exacta tras `round(.., 6)`) y una huella SHA-256 de todas las filas ordenadas. Sirve para un caso; no tiene tolerancia por columna (MG-D07), ni clave, ni muestra, ni cuenta de faltantes por columna, y la huella global falla con cualquier redondeo. Este comparador no lo reemplaza: lo complementa para la corrida paralela, y Plan H (H-9) añade a `sgm comparar` las pistas hacia el SAS.

**Files:**
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\produccion\comparar_corrida.py`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_comparar_corrida.py`

**Interfaces:**
- Consumes: `entrega_sas.leer_entrega(carpeta) -> Entrega` (I-12); la carpeta de Talend con un CSV por tabla, con el **mismo nombre de archivo** que declara el manifiesto, en el mismo formato.
- Produces:
  ```python
  NIVELES = ("tabla", "filas", "columnas", "faltantes", "suma", "distintos", "muestra", "clave")

  @dataclass(frozen=True)
  class Diferencia:
      tabla: str; nivel: str; columna: str; sas: str; talend: str; detalle: str

  def comparar_entrega(entrega: Entrega, talend: Path, tolerancia_defecto: float = 0.005,
                       muestra: int = 200) -> list[Diferencia]:
      """Por tabla: (1) que exista el CSV de Talend; (2) conteo de filas; (3) columnas y su orden;
      (4) por columna, cantidad de faltantes (igualdad exacta); (5) por columna numérica, la suma:
      se acepta |suma_sas - suma_talend| <= tolerancia * filas (cota de la suma de errores de cada
      valor, ver decisión DI-04); (6) por columna de texto, cantidad de valores distintos y
      huella de la multiconjunto de valores, ambas sin espacios finales (en SAS los espacios
      finales no cuentan en la comparación de cadenas: **verificar en `lrcon`** y citar la
      página); (7) muestra determinista: filas cuya SHA-256 de la clave módulo `k` sea 0, con
      `k = max(1, filas // muestra)`, misma selección en ambos lados, comparadas por clave: texto
      igual, número dentro de la tolerancia de su columna; (8) claves de la muestra presentes en
      un lado y no en el otro. Columnas `sensible: true`: `sas` y `talend` salen como `***`."""

  def informe(diferencias: list[Diferencia], entrega: Entrega) -> dict:
      """{"corrida": id, "tablas": n, "filas": {tabla: n}, "diferencias": [...],
      "coincide": bool}. Sin valores de filas: solo conteos, sumas, nombre de columna y la
      clave en hash (primeros 12 hex)."""
  ```
  CLI: `python tools/produccion/comparar_corrida.py --sas <entrega> --talend <carpeta> --salida <carpeta>`; escribe `informe.json` (agregados, apto para versionar) y `diferencias-detalle.json` (con valores de no sensibles, **no versionado**, en `out/paralela/`); sale 0 sin diferencias, 1 con diferencias, 2 si la entrega no es válida.

- [ ] **Step 1: Write the failing tests** con entrega y carpeta de Talend en `tmp_path` (tabla `t`, clave `id`, `saldo` numérico con `tolerancia: 0.005`, `nombre` texto): (a) iguales: lista vacía y `informe(...)["coincide"] is True`; (b) Talend con `saldo` 100.004 donde SAS tiene 100.00: sin diferencias (dentro de tolerancia, 3 filas, cota 0.015); con 100.006: una `Diferencia(nivel="muestra", columna="saldo")` y ninguna de `suma` (0.006 < 0.015); con 100.02: diferencias de `suma` y de `muestra`; (c) Talend con una fila menos: `nivel="filas"`, `sas="3"`, `talend="2"`; (d) `nombre` con `"Ana "` en un lado y `"Ana"` en el otro: sin diferencia (espacios finales); con `"ana"`: diferencia de `distintos` o de huella; (e) un faltante en `saldo` de Talend donde SAS tiene valor: `nivel="faltantes"` y `muestra`; (f) columna `sensible: true`: la diferencia trae `***` y no el valor; (g) la selección de la muestra es la misma en dos llamadas y no depende del orden de las filas; (h) clave ausente en Talend: `nivel="clave"` con el hash de la clave y no la clave.
- [ ] **Step 2: Run tests to verify they fail.** `uv run python -m pytest tests/unit/test_comparar_corrida.py -q -p no:cacheprovider`.
- [ ] **Step 3: Implement** en menos de 300 líneas (si pasa, `comparar_corrida_muestra.py` para el punto 7). Registrar en `PROGRESS.md` la decisión **DI-04**: tolerancia de la suma = tolerancia por valor multiplicada por las filas; alternativa descartada: la misma tolerancia sobre la suma (rechazada porque una tabla grande con redondeos legítimos de 0.004 por fila fallaría la suma). MG-D07 la confirma el cliente: si decide otra, cambia solo el cálculo en un lugar y se documenta.
- [ ] **Step 4: Run tests to verify they pass.** Prueba de humo con dos CSV reales del corpus de `tests/corpus/L2/` (esperado como «SAS» y copia como «Talend»): cero diferencias.
- [ ] **Step 5: Run** `uv run ruff check src tests tools`. **Commit** `hito N m: comparador de la corrida paralela con tolerancia por columna, clave y muestra`.

---

### Task I-14: Registro de diferencias y veredicto de equivalencia del ciclo (MG-P14-06, parte 3; serie `m`)

Una diferencia explicada no es una diferencia ignorada. Cada `Diferencia` de I-13 se cruza con un registro que la persona escribe y con los hallazgos de I-10; el veredicto lo calcula la herramienta, no una opinión.

**Files:**
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\produccion\diferencias.py`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\docs\produccion\plantillas\diferencias.yaml`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_diferencias.py`

**Interfaces:**
- Consumes: `comparar_corrida.Diferencia` e `informe` (I-13); `hallazgos.verificar_cierre` y el CSV de hallazgos (I-10).
- Produces:
  ```python
  CAUSAS = ("precision_numerica", "formato_de_texto", "faltante_vs_vacio", "regla_de_negocio_aceptada",
            "defecto_sgm", "dato_de_entrada_distinto")
  REQUIEREN_ACEPTACION = ("precision_numerica", "faltante_vs_vacio", "regla_de_negocio_aceptada")

  def veredicto(diferencias: list[Diferencia], registro: list[dict], hallazgos: list[dict]) -> dict:
      """{"equivalente": bool, "sin_explicar": [clave...], "bloqueos": [str...], "aceptadas": int}.
      Cada entrada de `registro`: {tabla, nivel, columna, causa, explicacion, responsable,
      hallazgo (id o ""), aceptada_por ("Nombre, AAAA-MM-DD" o "")}. Equivalente solo si: toda
      diferencia tiene entrada; la causa está en CAUSAS; las de REQUIEREN_ACEPTACION traen
      `aceptada_por` de Negocio; `defecto_sgm` tiene `hallazgo` con estado `cerrado` y `caso_corpus`;
      ninguna es `dato_de_entrada_distinto` (se repite la corrida con los mismos datos: no se acepta)."""

  def declarar_ciclo(carpeta: Path, esperadas: list[str]) -> dict:
      """Lee `<carpeta>/<corrida>.veredicto.json`. {"ciclo_completo": bool, "equivalente": bool,
      "faltan": [corridas esperadas sin veredicto], "no_equivalentes": [corridas]}. Equivalente
      solo con ciclo completo y todas las corridas equivalentes."""
  ```

- [ ] **Step 1: Write the failing tests.** Una `Diferencia(tabla="t", nivel="suma", columna="saldo", ...)` sin entrada en el registro: `equivalente=False` y `sin_explicar == ["t/suma/saldo"]`; con entrada `precision_numerica` sin `aceptada_por`: bloqueo que contiene `aceptada_por`; con `aceptada_por="Ana Perez, 2026-12-03"`: `equivalente=True, aceptadas=1`; con `defecto_sgm` y un hallazgo `abierto`: bloqueo; con `dato_de_entrada_distinto`: bloqueo que contiene `repetir`; sin diferencias: `equivalente=True`. `declarar_ciclo` con `esperadas=["c1","c2","c3"]` y solo `c1` y `c2` con veredicto: `ciclo_completo=False`, `faltan=["c3"]`, `equivalente=False`; con las tres equivalentes: `True`; con `c2` no equivalente: `no_equivalentes=["c2"]`.
- [ ] **Step 2: Run tests to verify they fail.** `uv run python -m pytest tests/unit/test_diferencias.py -q -p no:cacheprovider`.
- [ ] **Step 3: Implement** y escribir `diferencias.yaml` (plantilla con una entrada de ejemplo comentada y la lista de causas con su definición en una línea).
- [ ] **Step 4: Run tests to verify they pass.**
- [ ] **Step 5: Run** `uv run ruff check src tests tools`. **Commit** `hito N m: registro de diferencias y veredicto de equivalencia por ciclo`.

**Protocolo P14-06: corrida paralela de SAS contra Talend durante un ciclo completo (personas + herramientas)**

- **Quién:** dueño del proceso en Negocio (congela y aprueba los datos de entrada), equipo SAS del cliente (ejecuta SAS y exporta el oráculo), equipo de Talend/operación (ejecuta los Jobs migrados), Qlik Consulting (compara, explica, corrige defectos), Tecnología (aprueba la tolerancia MG-D07 y custodia la evidencia).
- **Entradas:** los 3 programas del piloto cerrados (P14-04); MG-D07 firmada (tolerancia por columna) y escrita en cada manifiesto; calendario del **ciclo completo** (el periodo de negocio del proceso: por ejemplo un cierre mensual con todas sus corridas diarias; se define con Negocio y se escribe en `docs/produccion/evidencia/paralela/<ciclo>/calendario.yaml` con la lista `esperadas`); versión de `sgm` congelada para el ciclo (un parche solo con acta y repitiendo las corridas afectadas); entradas congeladas con su `sha256` en `insumos` del manifiesto.
- **Pasos por corrida:** (1) congelar entradas y calcular `sha256`; (2) el equipo SAS corre el programa original con esas entradas y la plantilla `exportar_oraculo.sas` y entrega la carpeta del formato de I-12 (si `leer_entrega` la rechaza, se devuelve y no se compara); (3) el equipo de operación corre el Job migrado con **las mismas entradas** (mismo `sha256`) y deja los CSV de salida; (4) `comparar_corrida.py` produce `informe.json` y el detalle; (5) cada diferencia se anota en el registro (`diferencias.yaml`) con una causa de la lista cerrada, responsable y, si es `defecto_sgm`, un hallazgo con caso nuevo en `tests/corpus/` y su commit; (6) `diferencias.py` calcula el veredicto de la corrida; (7) Negocio acepta por escrito (`aceptada_por`) las diferencias de precisión o de regla; (8) se repite hasta cubrir todas las corridas de `esperadas`; (9) `declarar_ciclo` decide.
- **Evidencia que se guarda y dónde:** `docs/produccion/evidencia/paralela/<ciclo>/<corrida>.informe.json` y `<corrida>.veredicto.json` y el registro de diferencias (agregados, sin filas ni valores sensibles); el detalle con valores va a `out/paralela/` (no versionado) y a la custodia de Tecnología; `calendario.yaml`; el acta de la corrida paralela (formato de I-11, tipo `uat`, alcance «corrida paralela», firma de Negocio).
- **Criterio de aceptación (GM7, parte de corrida paralela):** `declarar_ciclo` devuelve `ciclo_completo=True` y `equivalente=True`; cero diferencias sin explicar; cero causadas por un defecto de `sgm` abierto; ninguna `dato_de_entrada_distinto`; tolerancia MG-D07 firmada y la misma en todos los manifiestos del ciclo; acta firmada. Una diferencia explicada se cuenta como explicada **solo** si trae su registro; «cero» diferencias es aceptable y no exige explicación.
- **Qué no se acepta:** comparar con datos de entrada distintos; comparar una corrida sin oráculo de SAS (no hay esperado de reemplazo); ajustar la tolerancia después de ver las diferencias sin acta.

---

### Task I-15: Plan de contingencia y reversa: SAS en paralelo hasta el corte (MG-P14-08; serie `m`)

**Files:**
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\produccion\estado_corte.py`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\docs\produccion\plantillas\plan-contingencia.md`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\docs\produccion\estado-corte.yaml` (una entrada por programa, con `PENDIENTE-DECISION` donde falte un dato)
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_estado_corte.py`

**Interfaces:**
- Consumes: `yaml.safe_load`; `estabilizacion.estado_estabilizacion` (I-18) para el criterio de apagado.
- Produces:
  ```python
  def verificar_reversa(entrada: dict, hoy: date, estabilizacion_minima_dias: int = 14) -> list[str]:
      """`entrada`: {programa, sas_activo: bool, sas_programado: bool, talend_activo: bool,
      fecha_corte: "AAAA-MM-DD" | "PENDIENTE-DECISION", fecha_apagado_sas: str | None,
      ultimo_respaldo_sas: "AAAA-MM-DD", destino_reversa: str, responsable_reversa: str,
      criterios_de_reversa: list[str]}. Problemas: antes de `fecha_corte` con `sas_activo` o
      `sas_programado` en falso; `fecha_apagado_sas` anterior a `fecha_corte` +
      `estabilizacion_minima_dias`; sin `criterios_de_reversa`; sin `responsable_reversa` o
      `destino_reversa`; `ultimo_respaldo_sas` con más de 7 días de antigüedad respecto de `hoy`;
      `fecha_corte` en `PENDIENTE-DECISION` con `talend_activo` verdadero."""
  ```

**Contenido del plan de contingencia** (`plan-contingencia.md`): principio (SAS sigue programado y con sus datos hasta que Negocio y Tecnología firmen el cierre de la estabilización; ningún programa se apaga en el corte); criterios de reversa por proceso (al menos: un defecto crítico abierto más tiempo que el plazo acordado, una alerta crítica repetida dos ciclos seguidos, conteo fuera de umbral dos ciclos seguidos, o petición de Negocio); procedimiento de reversa paso a paso (detener el planificador de Talend, reactivar los consumidores sobre la salida de SAS, verificar con un conteo, avisar por la ruta de escalamiento de I-9); datos de reversa (qué se respalda de SAS y dónde); quién decide (Negocio) y quién ejecuta (operación); tiempo máximo de reversa (`PENDIENTE-DECISION`, lo fija Negocio); simulacro.

- [ ] **Step 1: Write the failing tests** con `hoy = 2026-12-10` y una entrada completa con `fecha_corte="2026-12-15"`, `sas_activo=True`, `sas_programado=True`, `fecha_apagado_sas="2027-01-15"`, `ultimo_respaldo_sas="2026-12-08"`: devuelve `[]`; con `sas_programado=False` devuelve un problema que contiene `sas_programado`; con `fecha_apagado_sas="2026-12-20"` devuelve uno que contiene `fecha_apagado_sas`; con `criterios_de_reversa=[]` devuelve uno que contiene `criterios`; con `ultimo_respaldo_sas="2026-11-20"` devuelve uno que contiene `respaldo`; con `fecha_corte="PENDIENTE-DECISION"` y `talend_activo=True` devuelve uno que contiene `fecha_corte`. Una prueba lee `estado-corte.yaml` real y exige que cada entrada tenga todas las claves (los valores `PENDIENTE-DECISION` son válidos mientras no sea el día del corte).
- [ ] **Step 2: Run tests to verify they fail.** `uv run python -m pytest tests/unit/test_estado_corte.py -q -p no:cacheprovider`.
- [ ] **Step 3: Implement** `estado_corte.py` y escribir las dos plantillas.
- [ ] **Step 4: Run tests to verify they pass.**
- [ ] **Step 5: Run** `uv run ruff check src tests tools`. **Commit** `hito N m: plan de contingencia y verificador de reversa antes del corte`.

**Protocolo P14-08: simulacro de reversa y aprobación del plan (personas)**

- **Quién:** operación (ejecuta), Negocio (define el tiempo máximo y los criterios), Tecnología (aprueba).
- **Entradas:** `plan-contingencia.md` completo, `estado-corte.yaml` sin `PENDIENTE-DECISION` en las claves de reversa, el piloto corriendo en preproducción con SAS aún programado.
- **Pasos:** (1) Negocio fija el tiempo máximo de reversa y los umbrales; (2) operación ejecuta el procedimiento de reversa en preproducción cronometrando cada paso; (3) se verifica con un conteo que los consumidores volvieron a leer la salida de SAS; (4) se restaura Talend y se repite una vez más para comprobar que es repetible; (5) las fallas del procedimiento se anotan como hallazgos y se corrige el documento.
- **Evidencia:** `docs/produccion/evidencia/reversa-simulacro-<fecha>.md` (hora de inicio y fin de cada paso, quién, resultado) y el plan firmado por Negocio y Tecnología.
- **Criterio de aceptación:** reversa completada dentro del tiempo máximo, dos veces seguidas; `verificar_reversa` devuelve `[]` para cada programa del alcance.

---

### Task I-16: Capacitación: material verificable y evaluación práctica (MG-P14-09; serie `m`)

**Files:**
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\docs\produccion\capacitacion\sesiones.estructura.yaml`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_verificar_docs.py` (se amplía: es la herramienta de I-8)

**Interfaces:**
- Consumes: `verificar_docs.verificar(estructura, raiz, secciones_obligatorias) -> list[str]` (I-8); el runbook de I-8 y los casos de `tests/corpus/` como ejercicios.
- Produces: el YAML con las secciones obligatorias `s1-operacion-y-alertas`, `s2-leer-jobs-y-pendientes`, `s3-reproceso-y-reversa`, `evaluacion`. Cada sesión trae `audiencia`, `duracion_min`, `objetivos`, `ejercicios` (con `rutas` a un caso del corpus o a una plantilla), `comandos` y `criterio` (qué demuestra el asistente). Tres ejercicios mínimos de evaluación: interpretar una alerta de `alertas.py` y decidir el nivel de escalamiento; leer los pendientes de una migración con `sgm explicar` (o `pendientes.md` si H-8 no está) y decir cuáles bloquean; ejecutar el procedimiento de reversa de I-15 en el simulacro.

- [ ] **Step 1: Write the failing test.** `verificar(sesiones.estructura.yaml, RAIZ, ("s1-operacion-y-alertas", "s2-leer-jobs-y-pendientes", "s3-reproceso-y-reversa", "evaluacion")) == []`; hoy falla porque el archivo no existe.
- [ ] **Step 2: Run test to verify it fails.** `uv run python -m pytest tests/unit/test_verificar_docs.py -q -p no:cacheprovider -k capacitacion`.
- [ ] **Step 3: Implement** el YAML con contenido real; los ejercicios citan casos que existan (`tests/corpus/L2/l2_01_inner_join_clientes_ventas`).
- [ ] **Step 4: Run test to verify it passes.**
- [ ] **Step 5: Run** `uv run ruff check src tests tools`. **Commit** `hito N m: material de capacitacion verificable`.

**Protocolo P14-09: sesiones de capacitación al equipo operador (personas)**

- **Quién:** Qlik Consulting dicta; asisten operación (N1), equipo de Talend (N2) y un delegado de Negocio. Tecnología convoca.
- **Entradas:** `sesiones.estructura.yaml`, el runbook firmado (P14-03b), el piloto en preproducción, el material generado con `qlik-documentos` o diapositivas a partir del YAML.
- **Pasos:** tres sesiones (operación y alertas; lectura de Jobs y pendientes; reproceso y reversa) y una evaluación práctica individual con los tres ejercicios.
- **Evidencia:** `docs/produccion/evidencia/capacitacion-<fecha>.md` con asistentes (nombre y rol, no datos personales adicionales), resultado de cada ejercicio por persona y el material entregado.
- **Criterio de aceptación:** el 100 % de los operadores N1 y al menos un N2 resuelven los tres ejercicios sin ayuda; el material queda entregado en la ubicación que Tecnología indique.

---

### Task I-17: Paquete de corte y acta de corte (MG-P14-10, herramientas del agente; serie `m`)

El corte no se firma sobre una conversación: se firma sobre un paquete de evidencia completo, con índice y huellas, que la herramienta se niega a armar si falta algo.

**Files:**
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\produccion\paquete_de_corte.py`
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\docs\produccion\plantillas\acta-corte.md`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_paquete_de_corte.py`

**Interfaces:**
- Consumes: `acta.verificar_acta(ruta, "corte" | "uat", raiz)` (I-11); `hallazgos.verificar_cierre` (I-10); `diferencias.declarar_ciclo` (I-14); `estado_corte.verificar_reversa` (I-15); la evidencia de la compuerta `out/liberacion/<versión>-<commit>.json` (I-6) y de la instalación (I-5).
- Produces:
  ```python
  def requisitos(raiz: Path, version: str, programas: list[str], ciclo: str) -> dict[str, list[str]]:
      """Por requisito, los problemas (lista vacía = cumplido): `liberacion` (veredicto
      `LIBERABLE` y `arbol_limpio` en la evidencia de esa versión), `instalacion`
      (`evidencia/instalacion-<versión>.md` existe), `piloto` (`verificar_cierre` en [] para cada
      programa), `uat` (acta `uat` en [] por programa), `paralela` (`declarar_ciclo` equivalente
      para el ciclo), `alertas` y `reversa` y `capacitacion` (archivos de evidencia presentes),
      `documentos` (guía y runbook firmados), `reversa-datos` (`verificar_reversa` en [] por
      programa), `acta-corte` (`verificar_acta(..., "corte")` en [])."""

  def armar_paquete(raiz: Path, version: str, programas: list[str], ciclo: str, destino: Path) -> dict:
      """Si algún requisito tiene problemas: {"completo": False, "faltantes": {...}} y no escribe
      nada. Si no: copia la evidencia a `destino`, escribe `indice.json` con la ruta y el SHA-256
      de cada archivo y la versión, y devuelve {"completo": True, "indice": Path}."""
  ```

- [ ] **Step 1: Write the failing tests** con una raíz de pruebas en `tmp_path` armada por un ayudante que escribe los archivos mínimos válidos de cada requisito: con todo presente, `armar_paquete(...)["completo"] is True`, `indice.json` lista cada archivo con su SHA-256 de 64 caracteres y la versión; quitando la evidencia de alertas devuelve `completo False` con `faltantes` que contiene `alertas` y **no** crea `destino`; con la evidencia de liberación con `veredicto = "VERDE SIN STUDIO"` devuelve un problema en `liberacion` que contiene esa cadena; con un hallazgo abierto en el piloto devuelve un problema en `piloto`; con el acta de corte firmada solo por `Negocio` devuelve un problema que contiene `Tecnologia`.
- [ ] **Step 2: Run tests to verify they fail.** `uv run python -m pytest tests/unit/test_paquete_de_corte.py -q -p no:cacheprovider`.
- [ ] **Step 3: Implement** y escribir `acta-corte.md` (alcance, versión, paquete de evidencia con el `sha256` de `indice.json`, decisión go/no-go, condiciones, firmas de Negocio y Tecnología con `firma_ref`).
- [ ] **Step 4: Run tests to verify they pass.**
- [ ] **Step 5: Run** `uv run ruff check src tests tools`. **Commit** `hito N m: paquete de corte con requisitos verificables y acta de corte`.

**Protocolo P14-10: corte a producción y firma (personas)**

- **Quién:** firman **Negocio** (dueño del proceso) y **Tecnología** (responsable de la plataforma); asisten operación, equipo de Talend y Qlik Consulting (no firma por el cliente).
- **Entradas:** `armar_paquete` con `completo: True` y su `indice.json`; `estado-corte.yaml` sin `PENDIENTE-DECISION`; la versión instalada coincide con la del paquete (`sgm --version`).
- **Pasos:** (1) reunión de corte: se revisa el índice requisito por requisito con el dueño de cada evidencia; (2) go/no-go por programa (un no-go se anota con su motivo y el programa sigue en SAS); (3) firma del acta de corte por ambos; (4) el corte se ejecuta según la guía de despliegue y el planificador de Talend pasa a ser el de producción **con SAS aún programado** (I-15); (5) primer ciclo de producción vigilado por operación con las alertas de I-9 activas; (6) arranca la estabilización (I-18).
- **Evidencia:** `docs/produccion/evidencia/corte/acta-corte-<fecha>.md` con el bloque de firmantes y `firma_ref` (PDF firmado fuera del repositorio con su `sha256`), el `indice.json` y los comandos del paso 4 con su salida.
- **Criterio de aceptación (GM8):** `acta.py verificar --tipo corte` devuelve `[]` con firmas de Negocio **y** Tecnología fechadas; `armar_paquete` con `completo: True`; el primer ciclo de producción sin alerta crítica sin atender.

---

### Task I-18: Estabilización de 2 a 4 semanas: defectos, parches con prueba y criterio de salida (MG-P14-11; serie `m`)

**Files:**
- Create: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tools\produccion\estabilizacion.py`
- Test: `C:\Users\USUARIO_BISOLUTION1\code\sgm-v2\tests\unit\test_estabilizacion.py`

**Interfaces:**
- Consumes: el CSV de hallazgos de I-10 (mismas columnas; `origen = "estabilizacion"`); `hallazgos.verificar_cierre(filas, raiz) -> list[str]`.
- Produces:
  ```python
  def estado_estabilizacion(filas: list[dict], inicio: date, hoy: date, raiz: Path,
                            minimo_dias: int = 14, maximo_dias: int = 28) -> dict:
      """{"dias_limpios": int, "criticos_abiertos": [id], "altos_abiertos": [id],
      "parches_sin_prueba": [id], "cumple": bool, "motivo": str}. `dias_limpios` cuenta desde
      el máximo entre `inicio` y la `fecha_apertura` del último crítico. `parches_sin_prueba`:
      `defecto_sgm` cerrado sin `caso_corpus` existente ni `commit`. `cumple` solo con
      `dias_limpios >= minimo_dias`, sin críticos abiertos y sin parches sin prueba; con más de
      `maximo_dias` desde `inicio` y sin cumplir, `motivo` dice que se extiende o se escala por
      decisión de Tecnología."""
  ```

- [ ] **Step 1: Write the failing tests** con `inicio = 2026-12-15`: sin hallazgos y `hoy = 2026-12-30` (15 días): `cumple=True`; con un crítico abierto: `cumple=False`, `criticos_abiertos=["H-3"]`; con un crítico abierto el `2026-12-24` y cerrado el `2026-12-26` y `hoy = 2027-01-05`: `dias_limpios == 12`, `cumple=False`; con un `defecto_sgm` cerrado sin `caso_corpus`: `parches_sin_prueba=["H-4"]` y `cumple=False`; con `hoy = 2027-01-20` (36 días), sin cumplir: `motivo` contiene `escala`.
- [ ] **Step 2: Run tests to verify they fail.** `uv run python -m pytest tests/unit/test_estabilizacion.py -q -p no:cacheprovider`.
- [ ] **Step 3: Implement** reutilizando `hallazgos.py`; CLI `python tools/produccion/estabilizacion.py <hallazgos.csv> --inicio AAAA-MM-DD` (sale 0 si `cumple`, 1 si no).
- [ ] **Step 4: Run tests to verify they pass.**
- [ ] **Step 5: Run** `uv run ruff check src tests tools`. **Commit** `hito N m: criterio de salida de la estabilizacion con parches probados`.

**Protocolo P14-11: soporte de estabilización (personas + agente)**

- **Quién:** operación detecta; Tecnología prioriza; Qlik Consulting (agente y Andres) corrige; Negocio valida las correcciones que cambian un resultado.
- **Entradas:** el acta de corte; `hallazgos.csv` de producción (`docs/produccion/evidencia/estabilizacion/hallazgos.csv`); las alertas de I-9; la compuerta de I-6.
- **Pasos por defecto:** (1) registrar el hallazgo con prioridad y causa; (2) triage dentro del plazo escrito en el runbook; (3) si la causa es `defecto_sgm`, reproducirlo como caso en `tests/corpus/` o en `tests/unit/` (la prueba falla); (4) corregir con la prueba en verde; (5) `uv run python tools/liberacion.py` en `LIBERABLE`; (6) `tools/publicar_version.py --nivel parche --ejecutar`, nuevo wheel y verificación de I-5; (7) desplegar según la guía y repetir la comparación de I-13 sobre los programas afectados; (8) cerrar el hallazgo con `commit`, `caso_corpus` y `evidencia`.
- **Evidencia:** `hallazgos.csv` actualizado; por cada parche, la entrada del `CHANGELOG.md` y la evidencia de la compuerta; el informe semanal de `estabilizacion.py`.
- **Criterio de aceptación:** `estabilizacion.py` devuelve `cumple=True` (2 a 4 semanas, cero defectos críticos abiertos, ningún parche sin prueba); Tecnología firma el cierre de la estabilización, que es lo que habilita apagar SAS (I-15).

---

### Task I-Gate: GM7 y GM8, y quién firma qué (serie `m`, la cierra Andres)

**Criterio de salida** (compuertas de la sección 10 del plan maestro: leer sus textos con `grep -n "GM7\|GM8" docs/plan-reescritura/plan-migrador-general.md` antes de empezar; GM7 = «Piloto y corrida paralela con diferencias explicadas» (P14-04 a P14-06) y GM8 = «Corte firmado» (P14-10)). La parte de código la cierra el agente; las compuertas **solo** las cierran las personas, con la evidencia que cada protocolo nombra.

1. **Código y herramientas (agente):** I-1 a I-18 integradas, suite y `ruff` en verde, `uv run python tools/liberacion.py` con veredicto `LIBERABLE` (con Studio) o `VERDE SIN STUDIO` (sin él, con su motivo: no se cuenta como liberable) y su JSON en `out/liberacion/`; `instalacion_limpia.py` con `coincide_con_arbol=True`; `verificar_docs.py` en verde sobre los cuatro YAML.
2. **GM7 (personas):** piloto de 3 programas reales con la lista de hallazgos cerrada (P14-04), UAT aceptado (P14-05) y corrida paralela de un ciclo completo con `declarar_ciclo` equivalente (P14-06). Con MG-D08 sin cubrir, GM7 queda «ensayo» y **no** se marca.
3. **GM8 (personas):** acta de corte firmada por Negocio y Tecnología y `armar_paquete` completo (P14-10); estabilización cumplida (P14-11) para cerrar MG-P14 y apagar SAS.

**Quién firma qué**

| Qué se firma | Firma | Evidencia que lo respalda | Herramienta que lo verifica |
|---|---|---|---|
| Instalación en máquina limpia | Tecnología | `evidencia/instalacion-<versión>.md` | `instalacion_limpia.py` (parte automática) |
| Guía de despliegue y runbook | Tecnología | Word firmado y acta de lectura | `verificar_docs.py` |
| Selección y revisión del piloto | Tecnología y equipo de Talend | `piloto/seleccion.json`, `acta-revision.md` | `hallazgos.py verificar` |
| Tolerancia numérica (MG-D07) | Negocio y Tecnología | manifiestos y acta | `leer_entrega` (exige tolerancia) |
| UAT por programa | Negocio (dueño del proceso) | `uat/<programa>.acta.md` | `acta.py verificar --tipo uat` |
| Equivalencia de la corrida paralela | Negocio | `paralela/<ciclo>/` y su acta | `diferencias.declarar_ciclo` |
| Pruebas de alerta | Tecnología | `alertas-<fecha>.md` | revisión de las seis pruebas |
| Plan de reversa y simulacro | Negocio y Tecnología | `reversa-simulacro-<fecha>.md` | `estado_corte.verificar_reversa` |
| Capacitación | Tecnología | `capacitacion-<fecha>.md` | revisión del 100 % de N1 |
| Corte a producción (GM8) | **Negocio y Tecnología** | `corte/acta-corte-<fecha>.md` e `indice.json` | `acta.py verificar --tipo corte`, `armar_paquete` |
| Cierre de la estabilización | Tecnología | `estabilizacion/hallazgos.csv` | `estabilizacion.py` |

Qlik Consulting (Andres y Byron) entrega, explica y corrige; **no** firma por el cliente.

- [ ] **Step 1: Run** `uv run python -m pytest -q` y `uv run ruff check src tests tools` (suite completa y lint de la serie).
- [ ] **Step 2: Subir la versión de liberación.** `uv run python tools/publicar_version.py --nivel menor` (vista previa) y, si el contenido de «Sin publicar» es el que se quiere publicar, `--ejecutar`; commit aparte `hito N m: version <x.y.z>`. Luego `uv run python tools/liberacion.py` y pegar la tabla de pasos en `PROGRESS.md`.
- [ ] **Step 3: Studio.** `uv run python -m sgm.cli studio salud`; con conexión, el paso `Studio` de la compuerta compila la salida completa y se pega `Jobs: N, compilan: M`. Sin conexión: «lote C pendiente» con el motivo y la sección 7 de `docs/guia-validacion-studio.md`; el veredicto es `VERDE SIN STUDIO` y la compuerta **no** se declara cerrada.
- [ ] **Step 4: Preparar a las personas.** Entregar a Tecnología `docs/produccion/` (plantillas, YAML, protocolos), las herramientas de `tools/produccion/` y el wheel con su `sha256`; abrir en `docs/produccion/evidencia/` la estructura de carpetas que los protocolos nombran (con `.gitkeep`); anotar en `PROGRESS.md` qué protocolos están «preparados por el agente» y cuáles «cerrados» (solo los que ya trajeron evidencia).
- [ ] **Step 5: Registrar** en `PROGRESS.md` el hito de cierre (fecha, tareas, pruebas, cifra de la compuerta, bloqueos y decisiones `DI-01` a `DI-04`) y actualizar en el mismo cambio el «Estado» de MG-P14 y la sección 11b de `plan-migrador-general.md` (el crédito de las 40 h de agente según el método: la compuerta ya tuvo verde técnico en el hito 126m y no se acredita hasta que el paso de Studio se haya corrido sobre toda la salida) y `docs/produccion.md` (bloqueos 3 a 5 con su estado real). GM7 y GM8 en la sección 10 se marcan solo con la evidencia de las personas. **Commit** `hito N m: cierre de MG-P14 por parte del agente; GM7 y GM8 a la espera de las personas`.

---

## Resumen de horas

| Tareas | Origen | Serie | Horas |
|---|---|---|---|
| I-2, I-3, I-4, I-5 | MG-P14-01 (empaquetado) | m | 9 |
| I-1, I-6, I-7 | MG-P14-02 (compuerta) | m | 8 |
| I-8 | MG-P14-03 (guía y runbook, contenido) | m | 3 |
| I-9 | MG-P14-07 (monitoreo y alertas) | m | 3 |
| I-10 | MG-P14-04 (herramientas del piloto) | m | 2 |
| I-11 | MG-P14-05 (herramienta de actas) | m | 1 |
| I-12, I-13, I-14 | MG-P14-06 (corrida paralela) | m | 7 |
| I-15 | MG-P14-08 (reversa) | m | 1 |
| I-16 | MG-P14-09 (capacitación, material) | m | 1 |
| I-17 | MG-P14-10 (paquete de corte) | m | 2 |
| I-18 | MG-P14-11 (estabilización) | m | 2 |
| I-Gate | cierre | m | 1 |
| **Total agente** | | | **40** |
| Personas (P14-01b, 03b, 04, 05, 06, 07b, 08, 09, 10, 11) | | | unos 40 días, no se acreditan al agente |

Las horas por tarea son estimaciones del plan; el crédito real se mide con el método de la sección 11b del plan maestro.

## Dependencias

**Necesita de otros planes**

| De | Tarea | Para qué |
|---|---|---|
| Plan A | compilación y salud de Studio (`sgm studio salud`, `compilar`, backend MCP o CLI); el candado de commit (`tools/validacion.py`, `.githooks/`) si ya está integrado | I-7 e I-Gate (paso `Studio`); sin Studio queda `VERDE SIN STUDIO` |
| Plan G | G-3 (`tools/determinismo.py`), G-17 (`sgm cobertura --verificar`), G-18 y G-19 (corrida nocturna y «estable 14 días») y el anillo B completo | I-6: sus pasos de la compuerta; si alguno no existe, el paso falla diciendo `no existe` y la compuerta no libera |
| Plan H | H-8 y H-9 (`sgm explicar`, `sgm comparar --paquete`), H-10 (guía de operación generada), H-11 (código de salida ante un secreto), H-12 y H-13 (columnas sensibles) y el SBOM (hito 136, `tools/seguridad/generar_sbom.py --check`) | I-6 (SBOM), I-8 (el runbook toma el texto de H-10 como fuente y no lo duplica), I-13 (la lista de columnas sensibles de H-12 es la que se refleja en `sensible` del manifiesto), I-16 |
| Plan F2 | emisor y joblets estables, y la exportación de Build Job | I-8 (sección `construccion`) y el piloto |
| Plan K | K-2 y K-3 (datos sintéticos) | ensayo del piloto y de la corrida paralela si MG-D08 no entrega datos reales |
| Decisiones | MG-D06, MG-D07, MG-D08, MG-D10 | ver la tabla de decisiones; sin MG-D07 y MG-D08, GM7 no se declara |

**Entrega a otros planes**

| A | Qué |
|---|---|
| Plan maestro | cierre de MG-P14 (parte agente) y las condiciones de GM7 y GM8; la fila C6 (Operable) pasa a «cumplido» cuando I-5 y la verificación de persona P14-01b estén hechas |
| Plan G | `out/liberacion/*.json` como fuente del criterio C6 del tablero (`tools/tablero.py`) |
| Operación | `docs/produccion/` completo (plantillas, guía, runbook, alertas, estado de corte) y `tools/produccion/` |

## Self-review

- **Cobertura de la spec:** MG-P14-01 en I-2 a I-5 (y P14-01b); P14-02 en I-1, I-6, I-7; P14-03 en I-8 (y P14-03b); P14-04 en I-10 (protocolo P14-04); P14-05 en I-11 (protocolo P14-05); P14-06 en I-12 a I-14 (protocolo P14-06); P14-07 en I-9 (y P14-07b); P14-08 en I-15; P14-09 en I-16; P14-10 en I-17; P14-11 en I-18; GM7 y GM8 en I-Gate con la tabla de firmas.
- **Hallazgos medidos al redactar (no supuestos):** `tools/liberacion.py` no tiene prueba propia (`grep -rln liberacion tests` solo lo hallaba en tools y docs); no corre anillos A y B explícitos, ni Studio, ni cobertura, ni SBOM, ni instalación; su anillo D y sus secretos usan **un** caso (`l2_01_inner_join_clientes_ventas`). 15 módulos de `src/sgm/` resuelven `rules/`, `schemas/` y `env/` con `parents[n]` y no funcionarían en un wheel. `sgm comparar` (`verify.py`) compara con igualdad exacta, sin tolerancia por columna ni clave. El comando de importación de lotes se llama `sgm intake`, no `sgm intake`.
- **Lo que queda `PENDIENTE-DECISION` o «verificar al ejecutar»:** la clave de datos de `uv_build` y su destino (I-2); el JDK exacto del Build Job (I-8); el formato real con que el Job publica conteos y su código de salida (I-9); las páginas y opciones de `PROC EXPORT` para la plantilla de SAS y la página de `lrcon` sobre espacios finales (I-12, I-13); la disposición de la carpeta de `sgm migrar` (I-7); los umbrales de conteo (DI-02), los plazos de escalamiento y el tiempo máximo de reversa (Negocio); MG-D07 firmada.
- **Decisiones con alternativa:** DI-01 (datos del wheel), DI-02 (umbrales relativos), DI-03 (códigos de salida de la compuerta), DI-04 (tolerancia de la suma = tolerancia por valor por las filas).
- **Lo que no se hace aquí:** generar el Word (lo hace `qlik-documentos`), ejecutar SAS, leer programas reales o archivos con contraseñas, tocar `tools/ci.py`, `tools/validacion.py`, `tools/instalar_ganchos.py`, `README.md` o `.githooks/`, y cerrar GM7 o GM8 sin evidencia de personas.
- **Archivos por encima de 300 líneas:** ninguna tarea los toca; `tools/liberacion.py` baja de 205 con I-6 y los módulos nuevos de `tools/produccion/` se mantienen cada uno por debajo de 300 líneas.
- **Proporción:** 18 tareas más la de cierre para 40 h de agente; diez protocolos de personas con evidencia, ruta y criterio medible; los cuerpos de funciones los decide quien implementa.
