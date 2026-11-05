# Revision del segundo agente: casos L0

Revisor: segundo_agente. Cada caso se calculo a mano a partir de `programa.sas` y `entradas/`
antes de abrir `esperado/` y `razonamiento`. No se cambio ningun archivo de `esperado/`.

| Caso | Resultado | Detalle |
|---|---|---|
| l0_01_where_sentencia | COINCIDE | Filas 102, 104, 105; columnas originales. |
| l0_02_where_opcion | COINCIDE | Filas 101, 102, 103, 107 con WHERE= en SET. |
| l0_03_keep | COINCIDE | KEEP conserva el orden de entrada: id_cliente, nombre, saldo. |
| l0_04_drop | COINCIDE | Quedan codigo, descripcion, precio. |
| l0_05_rename | COINCIDE | sede y saldo_actual en la posicion original. |
| l0_06_asignacion | COINCIDE | total_valor 8432, 277, 2340, 6300, 316, 5562, 1170. |
| l0_07_if_then_else | COINCIDE | LENGTH $ 5 evita el corte de MEDIO; niveles correctos. |
| l0_08_concatenar | COINCIDE | TRIM antes de || y etiquetas sin comas, sin comillas. |
| l0_09_set_dos_tablas | AMBIGUO | Filas, orden y columnas coinciden. La columna fecha se da como texto ISO; PROC IMPORT con DBMS=CSV puede inferir una fecha de SAS y entonces PROC EXPORT escribiria otro formato. No hay fuente que confirme el tipo para yyyy-mm-dd. |
| l0_10_if_subsetting | COINCIDE | Filas 1, 3, 4 con IF de subconjunto. |
| l0_11_rename_keep | COINCIDE | codigo, precio_lista, stock en orden original. |
| l0_12_bandera_numerica | COINCIDE | valor 4872, 5434, 9594, 255, 2800, 800; grande 1,1,1,0,1,0. |
| l0_13_do_end | COINCIDE | Saldos -184 y -198 pasan a 0 con revision SI; el resto NO. |
| l0_14_where_drop | AMBIGUO | Filas, recargo y columnas coinciden. La columna fecha tiene el mismo problema de tipo que en l0_09. |
| l0_15_importar_exportar | COINCIDE | valor_stock 700, 1248, 5856, 10740, 4464, 6206. |

Ningun caso DIFIERE. Los 13 casos COINCIDE deberian pasar a `estado: revisado` con
`revisor: segundo_agente`, y los casos 09 y 14 llevar `observacion_revision`. Eso no se aplico en
`caso.yaml`: el cargador `tools/corpus_lib/caso.py` solo acepta los campos `nivel`, `construcciones`,
`capa`, `tolerancia`, `orden_relevante`, `estado`, `motivo`, `salidas` y `razonamiento`, y los estados
`traducible`, `parcial`, `pendiente` y `pendiente_revision`. Con esos campos el oraculo `--verificar`
falla. Los `caso.yaml` quedan como estaban; el veredicto se registra solo aqui. Para aplicarlo hace
falta que el cargador acepte `revisado`, `revisor` y `observacion_revision` (cambio en `tools/`, fuera
de esta revision).

Patrones del primer autor. Las celdas calculadas son correctas en los 15 casos, y las reglas de SAS que
usa (LENGTH antes del primer IF, orden de columnas de KEEP y RENAME, TRIM antes de ||, WHERE antes de
DROP) estan bien aplicadas. El patron a vigilar es otro: el autor supone que PROC IMPORT lee las fechas
ISO como texto, sin declararlo ni fijarlo (casos 09 y 14). Ese supuesto se apoya en un detalle del
importador que no se puede comprobar sin SAS. En los siguientes casos conviene evitar fechas ISO en
entradas CSV, o fijar el tipo con un INFORMAT y dejarlo escrito en el razonamiento. Tambien conviene no
afirmar reglas de formato de PROC EXPORT (comillas, separadores) sin citar fuente, porque el razonamiento
de los casos lo da por sentado.
