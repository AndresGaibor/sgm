# Resultados esperados

| Etapa | Resultado esperado |
|---|---|
| Clientes activos | 8 filas (10 de entrada; 1 inactivo y 1 bloqueado fuera) |
| Cuentas activas | 9 filas (10 de entrada; cuenta del cliente 1006 inactiva) |
| Transacciones únicas antes de los joins | 9 filas (la segunda `TX009` se elimina) |
| Transacciones enriquecidas | 6 filas y total de 3,560.50; incluye solo estado 1, monto >= 100 y clientes/cuentas válidos |
| Métricas por cliente tras `HAVING` | 5 filas y total de 3,440.00; el cliente 1001 queda fuera por volumen menor a 300 |
| Bandas actuales de riesgo | 1 HIGH (1005), 3 MEDIUM (1007, 1008, 1010), 1 LOW (1002) |
| Histórico tras APPEND | 8 filas: 3 del mes previo + 5 del mes actual |

## Métricas actuales por cliente

| Cliente | Región | Monto total | Transacciones | Puntuación | Banda |
|---:|---|---:|---:|---:|---|
| 1002 | Centro | 850.00 | 1 | 0 | LOW |
| 1005 | Norte | 1,250.00 | 1 | 65 | HIGH |
| 1007 | Sur | 600.00 | 1 | 25 | MEDIUM |
| 1008 | Occidente | 310.00 | 1 | 35 | MEDIUM |
| 1010 | Norte | 430.00 | 1 | 25 | MEDIUM |

La banda se calcula así: +40 si el monto total alcanza 1,000; +35 si la razón deuda/ingreso mensual alcanza 0.25; +25 si la utilización de cupo alcanza 0.80. `HIGH` empieza en 60 puntos, `MEDIUM` en 25; el resto es `LOW`.
