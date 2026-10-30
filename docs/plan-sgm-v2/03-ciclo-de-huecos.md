# Ciclo de huecos: qué hacer cuando llega un archivo nuevo

Este es el proceso que hace que sgm mejore con cada archivo. Se aplica igual a un programa nuevo del cliente, a un archivo público o a un caso que alguien encontró a mano.

## Resumen

1. **Entra** el archivo con `sgm intake`.
2. **Se compila.** Nunca falla: lo que no entiende queda como hueco.
3. **Se reparte.** Cada hueco tiene dueño según su motivo.
4. **Se reproduce** en un caso mínimo de prueba.
5. **Se cierra** con un archivo de reglas, o con código si no hay otra forma.
6. **Se verifica** contra todo el corpus con el trinquete.
7. **Se registra** en `PROGRESS.md` y el archivo pasa a `corpus/accepted/`.

## Paso a paso

### 1. Entrada

```powershell
uv run python -m sgm.cli intake ruta\al\archivo.sas
```

`intake` hace, en orden:

1. Copia el archivo a `corpus/inbox/<fecha>-<hash>/`.
2. Detecta la codificación y la normaliza a UTF-8.
3. Redacta secretos (`pwencode`, `pass=`, `password=`, `pw=`) y avisa cuántos encontró.
4. Compila y escribe la guía, el plan y el reporte de huecos en la misma carpeta.
5. Registra cada hueco en la base de huecos con su firma.

Los archivos del cliente nunca se suben a un repositorio público. `corpus/` está en `.gitignore` salvo `corpus/README.md`.

### 2. Ver qué falló

```powershell
uv run python -m sgm.cli gaps list --file corpus\inbox\<carpeta> --top 50
uv run python -m sgm.cli gaps list --owner joseph
```

Cada hueco muestra:

| Campo | Ejemplo |
| --- | --- |
| Firma | `proc:transpose:id+var` |
| Motivo | `PROC_NO_SOPORTADO` |
| Dueño | Joseph |
| Archivos y ocurrencias | 4 archivos, 11 ocurrencias |
| Ejemplo | `programa.sas:120-131`, etiqueta "Pivotear saldos" |
| Se cierra con | `rules/sas/procs/transpose.yaml` |
| Comando sugerido | `sgm rules new proc --from-gap proc:transpose:id+var` |

Para entender una línea concreta:

```powershell
uv run python -m sgm.cli explain corpus\inbox\<carpeta>\programa.sas:120
```

### 3. Priorizar

Se trabaja en este orden:

1. Huecos que bloquean un programa que el cliente necesita pronto.
2. Huecos con más **archivos** afectados (no ocurrencias: un hueco en 40 archivos vale más que uno repetido 40 veces en un solo archivo).
3. Huecos que generan `tJava`.

Cada lunes, el dueño de cada motivo revisa su lista con `sgm gaps list --owner <persona>`.

### 4. Reproducir

```powershell
uv run python -m sgm.cli case new --from-gap proc:transpose:id+var
```

Crea `tests/cases/<firma-normalizada>/`:

```
input.sas        fragmento mínimo, anonimizado (tablas y columnas renombradas)
expected.yaml    lo que debe salir: estado, componentes, huecos esperados
README.md        de dónde salió el caso y qué demuestra
```

`expected.yaml` empieza con el estado actual (el hueco). El dueño lo edita con lo que **debería** salir. En ese momento la prueba falla, y eso es lo correcto.

### 5. Cerrar

Primero se intenta con un archivo de reglas:

```powershell
uv run python -m sgm.cli rules new proc --from-gap proc:transpose:id+var
```

Crea el YAML prellenado en la carpeta que corresponde (ver `04-puntos-de-extension.md`). Se completa, se valida y se prueba:

```powershell
uv run python -m sgm.cli rules validate
uv run pytest tests/cases/proc-transpose-id-var -q
```

Si el hueco no se puede cerrar con reglas (un error del parser, una pasada que no contempla el caso), se cambia el código. En ese caso, el cambio:

- lleva el caso de `tests/cases/` como prueba,
- explica en el commit por qué no bastaba una regla,
- y si abre un punto de extensión nuevo, lo agrega a `04-puntos-de-extension.md`.

Si el hueco no tiene traducción posible (por ejemplo `CALL EXECUTE` con código armado desde datos), se cierra como **decisión**: la regla lo marca `parcial` con alternativas claras y el texto que verá el usuario. Un hueco cerrado como decisión cuenta como cerrado.

### 6. Verificar contra todo el corpus

```powershell
uv run pytest -q
uv run python -m sgm.cli compile corpus\accepted tests\fixtures\sas --out out\
uv run python -m sgm.cli metrics --check
```

- Si una métrica empeora, el cambio no entra. Se corrige, o se justifica por escrito y Andres actualiza la línea base.
- Si cambia una salida golden, se revisa la diferencia y se acepta solo si es una mejora.

### 7. Registrar

- Commit con el mensaje `hueco <firma>: <cómo se cerró>`.
- `PROGRESS.md`: una línea con la firma, archivos afectados y métricas antes y después.
- Cuando un archivo de `corpus/inbox/` ya no tiene huecos abiertos sin decisión, pasa a `corpus/accepted/`.

## Errores del propio sgm

Si `sgm` lanza una excepción con cualquier archivo, eso es un error de prioridad máxima, no un hueco:

1. El archivo se guarda en `tests/fixtures/sas/hostile/` (anonimizado si es del cliente).
2. Se agrega una prueba que compila ese archivo sin excepción.
3. Lo corrige el dueño del módulo donde falló, ese mismo día si es posible.

La regla es que `compile` nunca lanza una excepción por contenido del archivo. A lo sumo, el archivo entero queda como hueco `PARSE_ERROR`.
