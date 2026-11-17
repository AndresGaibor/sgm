"""Oráculo del `OUTPUT`: simula el PDV y los destinos sin usar el traductor (B-17).

Reglas, todas de SAS y no del repositorio:

* `OUTPUT` escribe el PDV de ese instante al dataset nombrado, o a todos los del encabezado si no
  nombra ninguno (`lestmtsref`, «OUTPUT Statement», p. 273-274).
* Si el paso tiene algún `OUTPUT` explícito, no hay escritura implícita al final de la iteración en
  ninguna vuelta: una observación que ninguna rama escribe, se descarta (`lrcon`, p. 498).
* Un faltante numérico es menor que cualquier número: `VALOR <= 2` es verdadero para un faltante y
  `VALOR >= 4` es falso (`lrcon`, «Comparison Operators», «Missing Values»).
* En una cadena `IF / ELSE IF / ELSE` gana la primera rama verdadera; el `ELSE` cubre el resto.
"""

from __future__ import annotations

from corpus_output.gramatica import DATASETS, Combinacion

_OPERADORES = {
    "<=": lambda a, b: a <= b,
    ">=": lambda a, b: a >= b,
}


def _numero(valor) -> float | None:
    """Valor numérico de una celda; `None` es faltante (vacío o no numérico)."""
    if valor is None or (isinstance(valor, str) and not valor.strip()):
        return None
    return float(valor)


def _verdadera(condicion: tuple, pdv: dict) -> bool:
    variable, operador, constante = condicion
    valor = pdv[variable]
    if valor is None:
        # El faltante es menor que cualquier número: solo cumple las comparaciones «menor que».
        return operador == "<="
    return _OPERADORES[operador](valor, constante)


def esperado(c: Combinacion, entradas: list[dict]) -> dict[str, list[dict]]:
    """Filas que debe escribir cada dataset del encabezado para las entradas dadas."""
    salida: dict[str, list[dict]] = {d: [] for d in DATASETS}
    for fila in entradas:
        pdv = {"ID": fila.get("ID") or None, "VALOR": _numero(fila.get("VALOR"))}
        for _, destinos in _ramas_que_se_ejecutan(c, pdv):
            for d in destinos or DATASETS:
                salida[d].append(dict(pdv))
    return salida


def _ramas_que_se_ejecutan(c: Combinacion, pdv: dict):
    """Los `OUTPUT` que se ejecutan para este PDV, como (condición, destinos)."""
    if c.rama == "incondicional":
        yield None, c.destinos[0]
        return
    for condicion, destinos in zip(c.condiciones, c.destinos, strict=True):
        if condicion is None or _verdadera(condicion, pdv):
            yield condicion, destinos
            return  # la cadena se detiene en la primera rama verdadera
