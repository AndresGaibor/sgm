"""Búsqueda con objeto hash (`FIND`) como `unir` izquierdo con la tabla de búsqueda (B-21).

Reglas de `lrcon`: al cargar un dataset, una llave repetida conserva la primera observación
(p. 632); `FIND` devuelve 0 si encuentra la llave y distinto de 0 si no (pp. 633-634).

Decisión 6 del dueño: `rc` solo se traduce en comparaciones con 0 y con la columna `rc`
eliminada. Si sobrevive a la salida, o aparece en otra sentencia, no se traduce. La columna
`_hit_` (1 si hubo coincidencia) sustituye a `rc` en las comparaciones.

Entran solo los pasos con un único `SET` sin `WHERE`, un `DECLARE HASH` con `DATASET:`,
`DEFINEKEY` de una llave, `DEFINEDATA`, `DEFINEDONE` y un `rc = h.FIND()`.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, replace

from sgm.frontend.datastep import DataStep, DsStatement, classify_statement
from sgm.ir import operadores
from sgm.ir.builder import Builder, qualify
from sgm.ir.models import Evidence, Operator
from sgm.ir.pasos import op_validado

HIT = "_hit_"
_DECLARA = re.compile(r"(?i)^declare\s+hash\s+(\w+)\s*\(\s*dataset\s*:\s*['\"]([\w.]+)['\"]\s*\)$")
_METODO = re.compile(r"(?i)^(?:(\w+)\s*=\s*)?(\w+)\s*\.\s*(\w+)\s*\((.*)\)$")
_CADENA = re.compile(r"""['"]([^'"]+)['"]""")
_RC = re.compile(r"(?i)\brc\b")
_IGUAL_0 = re.compile(r"(?i)\brc\s*=\s*0\b")
_DISTINTO_0 = re.compile(r"(?i)\brc\s*(?:ne|<>)\s*0\b")
_DROP_RC = re.compile(r"(?i)^drop\s+rc$")


@dataclass
class Busqueda:
    """Un `FIND` que se traduce: tabla de búsqueda, llave, datos y sentencias restantes."""

    tabla: str
    llave: str
    datos: list[str]
    fuente: str
    stmts: list[DsStatement]

    def paso(self, step: DataStep) -> DataStep:
        return replace(step, statements=self.stmts)

    def derecha(self) -> str:
        """Llave del lado derecho, calificada con el nombre de la tabla.

        El intérprete toma la tabla de la derecha del segundo elemento de la llave.
        """
        return f"{self.tabla.split('.')[-1]}.{self.llave}"

    def unir(self, izquierda: Operator, ev: Evidence, b: Builder) -> Operator:
        """Tabla de búsqueda sin llaves repetidas (primera) y `unir` izquierdo por la llave."""
        lectura = b.op("read", {"dataset": qualify(self.tabla), "in": None}, ev)
        marca = op_validado(
            b,
            # `modo: agrega`: el PDV conserva las variables de la tabla (lrcon, p. 498).
            lambda: operadores.calcular(
                "_", [{"target": HIT, "expression": "1"}], modo="agrega"
            ),
            "derive",
            {"assignments": [{"target": HIT, "expression": "1"}], "modo": "agrega"},
            ev,
        )
        b.link(lectura, marca)
        primera = op_validado(
            b,
            lambda: operadores.deduplicar(
                "_", by=[self.llave], keep="first", outputs=[qualify(self.tabla)]
            ),
            "dedup",
            {"by": [self.llave], "keep": "first"},
            ev,
        )
        b.link(marca, primera)
        union = op_validado(
            b,
            lambda: operadores.unir(
                "_",
                "left",
                [(self.llave, self.derecha())],
                [qualify(self.fuente), qualify(self.tabla)],
            ),
            "join",
            {"join_type": "left", "keys": [[self.llave, self.derecha()]]},
            ev,
        )
        b.link(izquierda, union)
        b.link(primera, union)
        return union


def detectar_busqueda(stmts: list[DsStatement]) -> Busqueda | None:
    """La búsqueda del paso si cumple las reglas; None si no (el paso queda con sus huecos)."""
    sets = [s for s in stmts if s.kind == "set"]
    if len(sets) != 1:
        return None
    refs = sets[0].fields.get("sources") or []
    if len(refs) != 1 or refs[0].get("where"):
        return None
    declaraciones = [(i, m) for i, s in enumerate(stmts) if (m := _DECLARA.match(s.text.strip()))]
    if len(declaraciones) != 1:
        return None
    i_decl, decl = declaraciones[0]
    objeto, tabla = decl.group(1).lower(), decl.group(2).lower()
    omitir = {i_decl}
    llave: str | None = None
    datos: list[str] | None = None
    hay_find = False
    reescritas: dict[int, DsStatement] = {}
    hay_drop = False
    for i, s in enumerate(stmts):
        if i == i_decl:
            continue
        texto = s.text.strip()
        metodo = _METODO.match(texto)
        if metodo and metodo.group(2).lower() == objeto:
            nombre, args = metodo.group(3).lower(), _CADENA.findall(metodo.group(4))
            if nombre == "definekey" and len(args) == 1 and llave is None:
                llave = args[0].lower()
            elif nombre == "definedata" and args and datos is None:
                datos = [a.lower() for a in args]
            elif nombre == "definedone" and not args:
                pass
            elif nombre == "find" and not args and not hay_find:
                hay_find = (metodo.group(1) or "").lower() == "rc"
                if not hay_find:
                    return None
            else:
                return None
            omitir.add(i)
            continue
        if not _RC.search(texto):
            continue
        if _DROP_RC.match(texto):
            reescritas[i] = classify_statement(f"DROP {HIT}", s.line)
            hay_drop = True
            continue
        nuevo = _IGUAL_0.sub(f"{HIT} = 1", texto)
        nuevo = _DISTINTO_0.sub(f"{HIT} ne 1", nuevo)
        if _RC.search(nuevo):
            return None  # `rc` en otra forma: no se traduce (decisión 6)
        reescritas[i] = classify_statement(nuevo, s.line)
    if llave is None or datos is None or not hay_find or not hay_drop:
        return None  # sin `DROP rc`, la columna `rc` saldría en la salida
    nuevas = [reescritas.get(i, s) for i, s in enumerate(stmts) if i not in omitir]
    return Busqueda(tabla, llave, datos, qualify(refs[0]["name"]), nuevas)
