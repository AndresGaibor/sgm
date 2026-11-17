# Diseño

## Decisiones

- **Generar, no escribir a mano.** El documento sale de `procs-usados.yaml` con una herramienta, y el
  modo `--verificar` detecta cuándo queda viejo. Así no hay dos fuentes que mantener.
- **Un solo módulo en `tools/`**, `tools/generar_cobertura.py`, con las funciones puras
  `filas(entradas)` y `markdown(filas)` y una `main` que lee y escribe. Las funciones puras son las que
  prueba la suite; la `main` solo une archivo y función.
- **Salida en `docs/cobertura.md`, versionada.** El documento se commitea para que se revise en
  cada cambio del catálogo.
- **El estado se muestra tal cual.** No hay tabla de traducción de estados a textos nuevos: se
  imprime `no_verificada`, igual que en el catálogo.

## Ingeniería

**Alternativas descartadas**
- Escribir el documento a mano: se desfasa en cuanto cambia el catálogo.
- Generarlo en `.cache/`: no se revisa en el repositorio.
- Añadirlo a `tools/tablero.py`: el tablero mide cifras, no documentos.
- Reclasificar `no_verificada` como «fuera de alcance»: sería inventar una decisión que el catálogo no
  tomó.

**Riesgos**
- El catálogo solo cubre `client_large.sas`. El documento lo dirá en su encabezado para que nadie
  lo lea como cobertura de todo el corpus.
- Una nota con `|` rompería la tabla Markdown. La celda escapa `|` como `\|`.
- Escritura en Windows: el archivo se escribe con `newline="\n"` y UTF-8 para que la verificación
  compare bytes iguales en cualquier máquina.

**Dependencias y frontera**
- Usa `yaml` (pyyaml, ya permitido). No toca `src/sgm/` ni `src/sgm/backend_talend/`, así que no
  entra en la frontera con Talend.
- No cambia el traductor ni `rules/`.

## Pruebas

Pruebas unitarias en `tests/unit/test_generar_cobertura.py`, sobre las funciones puras con datos
pequeños en memoria:
- Entradas mixtas: solo aparecen las no `reconocida`, en el orden del catálogo.
- Catálogo sin pendientes: el documento dice que no hay filas.
- Nota con `|`: la celda queda escapada.
- Entrada sin nota: celda vacía.
- Dos generaciones seguidas: salida idéntica.
- Verificación: sale 0 con documento al día y distinto de 0 con documento viejo, sin escribir.

Verificación con el catálogo real: `uv run python tools/generar_cobertura.py` debe producir siete
filas, y `--verificar` debe salir 0 justo después.

`uv run ruff check .` en cada cambio. `tools/ci.py` no se toca en este cambio; la suite completa se
corre al cerrar el hito.
