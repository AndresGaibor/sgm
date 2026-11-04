# Fase 0: referencia legible por máquina del diseño manual

Meta de aceptación de la reescritura: `docs/diseno-talend-exogena-depositos.md`. Esta fase lo
convierte en datos y deja una prueba de conformidad que empieza en rojo.

## Archivos

- `tests/fixtures/referencia/diseno_manual.yaml`: 118 filas con id estable, clave natural,
  `clasificacion`, `motivo` y las columnas del documento (sin el formato de comillas invertidas).
- `tests/conformidad/cargador.py`: carga el YAML y cuenta filas del Markdown de origen.
- `tests/conformidad/interfaz.py`: `obtener_diseno(programa_sas) -> dict`, hoy lanza
  `NotImplementedError`. Contrato: `{seccion: {clave_de_fila: {columna: texto}}}`.
- `tests/conformidad/test_referencia.py`: 28 pruebas que pasan hoy (YAML válido, ids y claves
  únicos, conteos por sección, 6 decisiones, 12 pendientes y riesgos, coincidencia con el Markdown).
- `tests/conformidad/test_conformidad.py`: 140 pruebas `xfail(strict=True, raises=NotImplementedError)`,
  una por sección (22) y una por fila (118). Al llegar el emisor, cada una que pase se marca como
  error hasta quitarle el `xfail`; no se borra ni se debilita ninguna.

## Filas por sección

| Sección | Filas | Derivable | Declarada | Humana |
|---|---|---|---|---|
| 1.1 Fuentes | 8 | 4 | 4 | 0 |
| 1.2 Cachés | 10 | 10 | 0 | 0 |
| 1.3 Variables globales | 3 | 3 | 0 | 0 |
| 1.4 Salidas | 5 | 4 | 1 | 0 |
| 2.1 Contexto Default | 9 | 7 | 1 | 1 |
| 2.2 Entornos | 6 | 2 | 3 | 1 |
| 2.3 Parámetros por Job | 3 | 2 | 1 | 0 |
| 2.4 Reglas de contexto | 4 | 4 | 0 | 0 |
| 3.1 a 3.5 Jobs (con 3 notas: 3.1b, 3.2b, 3.3b) | 32 | 31 | 1 | 0 |
| 4 Joblets (con rutina DV, 4b) | 7 | 6 | 1 | 0 |
| 5 Decisiones D1-D6 | 6 | 4 | 0 | 2 |
| 6 Equivalencias | 8 | 8 | 0 | 0 |
| 7 Pendientes P1-P8 y riesgos R1-R4 | 12 | 0 | 3 | 9 |
| 8 Orden de construcción | 7 | 7 | 0 | 0 |
| **Total** | **118** | **90** | **15** | **13** |

## Criterio de clasificación

- `derivable`: el emisor lo produce solo, desde la estructura del SAS o por una convención fija
  del emisor (joblets, cachés de totales, reglas de contexto).
- `declarada`: falta un valor que el SAS no demuestra (archivo DANE, tablas de origen, host,
  puerto y usuario de Impala, archivo de rechazos de D2, rutina de DV); va en el YAML de decisiones.
- `humana`: la confirma una persona (tolerancia, contraseña, D2, D3, P4 a P8, R1 a R4).

## Conformidad máxima sin decisiones humanas

- Solo con lo derivable: 90 de 118, es decir **76,3 %**.
- Derivable más lo declarado en el YAML: 105 de 118, es decir **89,0 %**. Es el techo sin que una
  persona tome o confirme una decisión.
- El 11,0 % restante (13 filas) queda como pendiente con su motivo, según la regla de no inventar datos.

Nota: en la sección 7 la clase indica quién cierra el pendiente. El migrador debe listarlo en
cualquier caso; la conformidad de esas filas se mide contra su presencia y texto, no contra su cierre.
