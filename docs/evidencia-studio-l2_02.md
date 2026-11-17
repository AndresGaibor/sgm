| Caso | Resultado | Diferencias | Archivos faltantes | Archivos de más | Error |
|---|---|---:|---|---|---|
| l2_02_left_join_con_faltantes | no coincide | 100 | - | - | - |

1 casos, 0 coinciden.

## l2_02_left_join_con_faltantes

### clientes_con_ventas.csv (diferente)
- filas: esperado 14, obtenido 100
- fila 1, columna 'id_venta': esperado '', obtenido '1.0'
- fila 1, columna 'monto': esperado '', obtenido '243.0'
- fila 3, columna 'id_cliente': esperado '103', obtenido '101.0'
- fila 3, columna 'nombre': esperado 'Bruno Demo', obtenido 'Gabriela Test'
- fila 3, columna 'id_venta': esperado '', obtenido '2.0'
- fila 13, columna 'id_cliente': esperado '109', obtenido '101.0'
- fila 13, columna 'nombre': esperado 'Jorge Caso', obtenido 'Gabriela Test'
- fila 13, columna 'id_venta': esperado '', obtenido '3.0'
- fila 13, columna 'monto': esperado '', obtenido '570.0'
- fila 14, columna 'id_cliente': esperado '110', obtenido '101.0'
- fila 14, columna 'nombre': esperado 'Ana Prueba', obtenido 'Gabriela Test'
- fila 14, columna 'id_venta': esperado '', obtenido '4.0'
- fila 14, columna 'monto': esperado '', obtenido '314.0'
- fila 5 de la salida no esperada: (101.0, Gabriela Test, 5.0, 740.0)
- fila 6 de la salida no esperada: (101.0, Gabriela Test, 6.0, )
- fila 7 de la salida no esperada: (101.0, Gabriela Test, 7.0, 448.0)
- fila 8 de la salida no esperada: (101.0, Gabriela Test, 8.0, 354.0)
- fila 9 de la salida no esperada: (101.0, Gabriela Test, 9.0, 900.0)
- fila 10 de la salida no esperada: (101.0, Gabriela Test, 10.0, 833.0)
- fila 11 de la salida no esperada: (102.0, Gabriela Test, 1.0, 243.0)
- fila 12 de la salida no esperada: (102.0, Gabriela Test, 2.0, )
- fila 14 de la salida no esperada: (102.0, Gabriela Test, 4.0, 314.0)
- fila 15 de la salida no esperada: (102.0, Gabriela Test, 5.0, 740.0)
- fila 16 de la salida no esperada: (102.0, Gabriela Test, 6.0, )
- fila 17 de la salida no esperada: (102.0, Gabriela Test, 7.0, 448.0)
- fila 18 de la salida no esperada: (102.0, Gabriela Test, 8.0, 354.0)
- fila 19 de la salida no esperada: (102.0, Gabriela Test, 9.0, 900.0)
- fila 20 de la salida no esperada: (102.0, Gabriela Test, 10.0, 833.0)
- fila 21 de la salida no esperada: (103.0, Bruno Demo, 1.0, 243.0)
- ... y 70 diferencias más

