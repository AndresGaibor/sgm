# Secretos en los artefactos de sgm

Estado: el escáner y la compuerta de publicación están implementados. La decisión de entrega del
secreto (DC-06 en `docs/plan-reescritura/ruta-a-produccion.md`, sección 3) sigue **abierta**.
Las opciones de entrega quedan para que las decida el dueño del proyecto.

## 1. Qué no entra nunca al repositorio ni a los artefactos

- Ninguna contraseña en claro en el repositorio: ni en código, ni en `decisiones/`, ni en fixtures.
- Ninguna contraseña en claro en los artefactos que emite `sgm talend`: los `.item`, los `.properties` y los grupos de contexto.
- Ninguna contraseña en los logs que escribe sgm.
- Un `proc pwencode in='...'` con clave real no se copia: en el repositorio se sustituye por `in='***'`.

## 2. Qué lleva el `.item`

El `.item` lleva el parámetro de contexto **vacío**. El emisor lo fija así en `src/sgm/talend_item/base.py` (`PASS` y `PASS_IMPLICIT_CONTEXT` con valor `""`) y en los grupos de contexto de tipo `id_Password`, que se escriben sin valor (`needs_value` es verdadero para cualquier nombre sensible en `src/sgm/emit/conventions/context_rules.py`).

Un `.item` puede llevar `***` como marcador. Un valor real no puede estar en él.

## 3. Cómo llega el valor a cada entorno (propuesta)

Cada entorno (DEV, QA, PROD) recibe el valor por una de estas dos vías, ambas fuera del repositorio:

1. **Grupo de contexto cargado fuera del repositorio.** Talend lee el valor de un grupo de contexto (por ejemplo `PROD`) que se carga en el entorno de ejecución, no en el `.item`.
2. **Variable de entorno del lanzador.** El programa que lanza el Job exporta el valor de la contraseña como variable de entorno, y el contexto la toma de ahí.

Opciones de almacén (vault corporativo, cifrado del contexto de Talend u otro gestor) quedan sin elegir. Elegir una es parte de DC-06 y no le corresponde a este documento.

## 4. Lista blanca y cómo se audita

El escáner tiene **una** excepción: el marcador `"sgm_ref"` en el parámetro `PASSWORD` de `tFileInputExcel`. Motivo: Studio no compila `tFileInputExcel` con `PASSWORD` vacío ni con `***`, y el Excel de insumo no tiene clave. Lo emiten `flujos_ubicacion`, `periodo` y `totalizadores`.

La lista está en `src/sgm/seguridad/lista_blanca.py`, en la tupla `LISTA_BLANCA`. Cada entrada tiene campo, componente, valor literal y motivo. Para auditarla:

- `grep -n Excepcion src/sgm/seguridad/lista_blanca.py` lista las entradas.
- `tests/unit/test_secretos_limpios.py` comprueba que el emisor sí la usa y que, sin ella, el escáner da hallazgos. Si alguien quita la entrada, esa prueba lo nota.
- Añadir una entrada exige revisión de Seguridad, y debe quedar aquí con su motivo.

## 5. La compuerta: `sgm secretos` y `sgm migrar`

`sgm secretos <carpeta o archivo> [--formato texto|json]` revisa archivos de texto y sale así:

- código **1** si hay algún hallazgo;
- código **0** si no hay ninguno.

Cada hallazgo muestra archivo, línea, tipo y el valor enmascarado (los 2 primeros caracteres y `***`). El valor completo nunca sale. La salida es determinista: los hallazgos van ordenados por archivo, línea y tipo.

Uso propuesto antes de un despliegue:

```
uv run sgm secretos <carpeta de artefactos>
uv run sgm secretos decisiones
```

`sgm migrar` integra la revisión antes de publicar cada paquete. Primero genera en staging, incluye
los archivos del paquete previo y luego escanea el conjunto. Si encuentra un secreto, no puede leer
algún archivo o detecta enlaces simbólicos o junctions de Windows, descarta el staging y sale con
código 1. No reemplaza ni
borra el paquete previo. En una migración por carpeta, publica los paquetes limpios y termina con
código 1 si alguno se bloqueó. El mensaje identifica archivo, línea y tipo, pero no muestra el valor.

El workflow `.github/workflows/seguridad-nocturna.yml` queda configurado para correr a diario o
manualmente. El cron se activa al integrar el workflow en la rama predeterminada. Migra un caso
controlado a una carpeta temporal, vuelve a ejecutar `sgm secretos` sobre el paquete y escanea
`decisiones/`. El workflow no usa secretos de CI, Studio ni una base de datos.

Si cualquiera de los comandos de escaneo sale con 1, se detiene la entrega y se corrige el origen del
secreto. El escaneo no sustituye la revisión de Seguridad (R9-09).

Alcance: la compuerta está pensada para los artefactos y para `decisiones/`. Escanear todo el repositorio incluye manuales SAS copiados en `docs/referencia/` con ejemplos de `pass=` y `pwencode`; esos hallazgos no son secretos y no forman parte de la compuerta.

## 6. Límites del escáner

- Detecta por forma y por nombre de clave (`password`, `pwd`, `passwd`, `secret`, `token`, `api_key`, `PASSWORD` en `field`, `type="id_Password"`). Una clave sin nombre reconocible puede pasar.
- Las reglas son expresiones regulares. Un valor partido por saltos de línea dentro de comillas no se ve.
- Los archivos binarios no se revisan.
- Una cadena de conexión con un nombre de clave nuevo necesita una regla nueva y su prueba.

## 7. Pendiente

- DC-06: elegir el almacén de secretos y el mecanismo de carga por entorno. Abierta.
- MG-P13-02: la revisión del `{SAS002}` en el fixture real y del adjunto con `pwencode` requiere que
  una persona confirme que son públicos o que fueron rotados. El migrador no puede confirmar esto.
- R9-09: revisión de Seguridad de estos artefactos y de los logs.
