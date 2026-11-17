"""Recorrido de las sentencias de un DATA step: cada sentencia se convierte en operadores del plan.

Se extrajo de `lower_data._lower_data_steps` sin cambio de comportamiento (B-5, límite de
300 líneas).
El estado que el bucle reasignaba (`current`, `pending_derive`, `loose`, `prev`, `omit`) vive en
`_Recorrido`; cada rama del bucle es un método que dice si la sentencia ya quedó resuelta.
"""

from __future__ import annotations

from dataclasses import replace

from sgm.frontend.datastep import DataStep, DsStatement
from sgm.ir import operadores
from sgm.ir.builder import Builder, qualify
from sgm.ir.lower_data_archivos import (
    escribir_file_put,
    file_put_lista_null,
    registrar_file_put_pendiente,
)
from sgm.ir.lower_data_arreglos import _ARRAY as _ARRAY_DECLARA
from sgm.ir.lower_data_arreglos import (
    arreglos_declarados,
    bucle_desenrollado,
    es_do_condicional,
    es_do_limite_no_constante,
    fin_de_bloque,
    indice_fuera_de_rango,
)
from sgm.ir.lower_data_asignaciones import _conditional_assignment, _statement_op
from sgm.ir.lower_data_automaticas import automaticas_en, motivo
from sgm.ir.lower_data_bloques import bloque_condicional
from sgm.ir.lower_data_hash import pendientes_hash
from sgm.ir.lower_data_lag import estado_de_lag
from sgm.ir.lower_data_salidas import _conditional_output_chain, _note, _output_sequence
from sgm.ir.lower_data_select import bloque_select, condicion_de_borrado, select_sin_otherwise
from sgm.ir.lower_data_substr import es_objetivo_substr_izquierda, reescribir_substr_izquierda
from sgm.ir.models import Evidence, Operator
from sgm.ir.pasos import op_validado

_HEAD_KINDS = frozenset(
    {"set", "merge", "update", "modify", "by", "infile", "input", "datalines"}
)


def _statement_evidence(stmt: DsStatement, ev: Evidence) -> Evidence:
    return replace(
        ev, file=stmt.file or ev.file, line_start=stmt.line, line_end=stmt.end_line or stmt.line
    )


class _Recorrido:
    """Estado del recorrido de las sentencias de un DATA step."""

    def __init__(
        self,
        step: DataStep,
        ev: Evidence,
        b: Builder,
        current: Operator | None,
        omit: set[int],
        pending_derive: Operator | None,
        loose: list[str],
        prev: DsStatement | None,
    ) -> None:
        self.step = step
        self.stmts = step.statements
        self.ev = ev
        self.b = b
        self.current = current
        self.omit = omit
        self.pending_derive = pending_derive
        self.loose = loose
        self.prev = prev
        self.file_put = file_put_lista_null(step)

    def ejecutar(self) -> None:
        # Objetos hash e iteradores: cada sentencia que los usa es un hueco con su código (B-21).
        hash_pendientes = {p.indice: p for p in pendientes_hash(self.stmts)}
        for index, s in enumerate(self.stmts):
            if index in self.omit:
                continue
            statement_ev = Evidence(self.ev.file, s.line, s.line, self.ev.label, self.ev.call)
            before, self.prev = self.prev, s
            if index in hash_pendientes:
                self._hueco_hash(index, statement_ev, hash_pendientes[index])
                continue
            if s.kind in _HEAD_KINDS:
                continue
            if self._automatica_sin_traduccion(index, statement_ev):
                continue
            if self._secuencia_output(index, statement_ev):
                continue
            if self._salida_condicional(index, statement_ev):
                continue
            if self._borrado_condicional(index, statement_ev):
                continue
            if self._arreglo_o_bucle(index, statement_ev):
                continue
            if self._asignacion_condicional(index, statement_ev):
                continue
            if s.kind == "assign":
                self._asignacion(s, statement_ev)
                continue
            self.pending_derive = None
            if self._sentencia_sin_operador(index, s, statement_ev):
                continue
            self._operador(s, before, statement_ev)

    def _enlazar(self, operador: Operator) -> None:
        if self.current is not None:
            self.b.link(self.current, operador)
        self.current = operador

    def _evidencia_de(self, posiciones: range) -> list[Evidence]:
        return [
            Evidence(
                self.ev.file,
                self.stmts[posicion].line,
                self.stmts[posicion].line,
                self.ev.label,
                self.ev.call,
            )
            for posicion in posiciones
        ]

    def _secuencia_output(self, index: int, statement_ev: Evidence) -> bool:
        secuencia = _output_sequence(self.stmts, index)
        if secuencia is None:
            return False
        destinos, ultimo = secuencia
        parametros = {"target": destinos[0], "condition": ""}
        if len(destinos) > 1:
            parametros["targets"] = destinos
        salida_multiple = self.b.op("split", parametros, statement_ev)
        salida_multiple.evidence.extend(self._evidencia_de(range(index + 1, ultimo + 1)))
        self._enlazar(salida_multiple)
        self.omit.update(range(index + 1, ultimo + 1))
        self.prev = self.stmts[ultimo]
        return True

    def _salida_condicional(self, index: int, statement_ev: Evidence) -> bool:
        destinos_validos = [d for d in self.step.outputs if d.lower() != "_null_"]
        salidas = _conditional_output_chain(self.stmts, index, destinos_validos)
        if salidas is None:
            return False
        ramas, destinos, siguiente, terminal = salidas
        if not terminal:
            ramas.append({"outputs": [], "continue": True})
        salida_condicional = self.b.op(
            "map",
            {"steps": [], "outputs": destinos, "branches": ramas},
            statement_ev,
        )
        salida_condicional.evidence.extend(self._evidencia_de(range(index + 1, siguiente + 1)))
        self._enlazar(salida_condicional)
        self.omit.update(range(index + 1, siguiente + 1))
        self.prev = self.stmts[siguiente]
        return True

    def _automatica_sin_traduccion(self, index: int, statement_ev: Evidence) -> bool:
        """Una sentencia que lee `_N_` o `_ERROR_` sale como operador `hueco` (B-20)."""
        s = self.stmts[index]
        variables = automaticas_en(s.text)
        if not variables:
            return False
        operador = self.b.op(
            "unsupported",
            {"statement": s.text, "reason": "VARIABLE_AUTOMATICA"},
            statement_ev,
            status="hueco",
            notes=[motivo(variables[0])],
        )
        self._enlazar(operador)
        self.pending_derive = None
        self.prev = s
        return True

    def _arreglo_o_bucle(self, index: int, statement_ev: Evidence) -> bool:
        """`ARRAY` con lista explícita (sin operador) y `DO` con límites constantes (B-16)."""
        s = self.stmts[index]
        arreglos = arreglos_declarados(self.stmts)
        if s.kind == "array":
            declara = _ARRAY_DECLARA.fullmatch(s.text.strip())
            return declara is not None and declara.group(1).lower() in arreglos
        if s.kind != "do":
            return False
        if es_do_condicional(s.text):
            fin = fin_de_bloque(self.stmts, index)
            if fin is None:
                return False
            self._hueco_de_bucle(
                index,
                statement_ev,
                "P-DO-WHILE-UNTIL: DO WHILE/UNTIL no se desenrolla y aún no tiene su bucle en "
                "tJavaRow (lrcon, p. 675)",
                "DO_WHILE_UNTIL",
                "P-DO-WHILE-UNTIL",
                fin,
            )
            return True
        desenrollado = bucle_desenrollado(self.stmts, index, arreglos)
        if desenrollado is None:
            fuera = indice_fuera_de_rango(self.stmts, index, arreglos)
            if fuera is None:
                if es_do_limite_no_constante(s.text):
                    fin = fin_de_bloque(self.stmts, index)
                    if fin is None:
                        return False
                    self._hueco_de_bucle(
                        index,
                        statement_ev,
                        "P-DO-LIMITE-NO-CONSTANTE: el DO iterativo tiene un límite que no es "
                        "constante; el bucle necesita tJavaRow, pendiente (lrcon, p. 671)",
                        "DO_LIMITE_NO_CONSTANTE",
                        "P-DO-LIMITE-NO-CONSTANTE",
                        fin,
                    )
                    return True
                return False
            elemento, fin = fuera
            self._hueco_de_bucle(
                index,
                statement_ev,
                f"P-ARRAY-FUERA-DE-RANGO: {elemento} está fuera del arreglo; SAS detiene el paso "
                "(lrcon, p. 192)",
                "ARRAY_FUERA_DE_RANGO",
                "P-ARRAY-FUERA-DE-RANGO",
                fin,
            )
            return True
        asignaciones, fin = desenrollado
        for destino, expresion in asignaciones:
            texto = f"{destino} = {expresion}"
            campos = {"target": destino, "expression": expresion}
            self._asignacion(DsStatement("assign", texto, s.line, campos), statement_ev)
        self.omit.update(range(index + 1, fin + 1))
        self.prev = self.stmts[fin]
        return True

    def _hueco_hash(self, index: int, statement_ev: Evidence, pendiente) -> None:
        """Hueco con el código del objeto hash o iterador (`lrcon`, pp. 628 a 642)."""
        operador = self.b.op(
            "unsupported",
            {
                "statement": self.stmts[index].text,
                "reason": "HASH_SIN_EQUIVALENCIA",
                "codigo": pendiente.codigo,
            },
            statement_ev,
            status="hueco",
            notes=[pendiente.motivo],
        )
        self._enlazar(operador)
        self.pending_derive = None

    def _hueco_de_bucle(
        self, index: int, statement_ev: Evidence, motivo: str, reason: str, codigo: str, fin: int
    ) -> None:
        """Hueco con su pendiente para un `DO` que no se traduce. El Job no se emite, y el cuerpo
        del bucle (hasta su `END`, en `fin`) no genera operadores aparte."""
        operador = self.b.op(
            "unsupported",
            {"statement": self.stmts[index].text, "reason": reason, "codigo": codigo},
            statement_ev,
            status="hueco",
            notes=[motivo],
        )
        self._enlazar(operador)
        self.pending_derive = None
        self.omit.update(range(index + 1, fin + 1))
        self.prev = self.stmts[fin]

    def _borrado_condicional(self, index: int, statement_ev: Evidence) -> bool:
        """`IF cond THEN DELETE;` como `filter` con la condición negada (B-15). Con `OUTPUT` antes
        no se traduce: queda como sentencia sin traducción."""
        condicion = condicion_de_borrado(self.stmts, index)
        if condicion is None:
            return False
        if any(s.kind == "output" for s in self.stmts[:index]):
            _note(
                self.current,
                "P-DELETE-CON-OUTPUT: DELETE condicional tras un OUTPUT; una fila puede "
                "salir varias veces y el filtro no lo representa",
                status="parcial",
            )
            return False
        expresion = f"not ({condicion})"
        filtro = op_validado(
            self.b,
            lambda: operadores.filtrar("_", expresion),
            "filter",
            {"expression": expresion},
            statement_ev,
        )
        self._enlazar(filtro)
        self.pending_derive = None
        self.prev = self.stmts[index]
        return True

    def _estado_lag(self, index: int, statement_ev: Evidence) -> bool:
        """`LAG`/`DIF` como estado entre filas: hueco con su cola (lefunctionsref, p. 1164)."""
        s = self.stmts[index]
        params = estado_de_lag(s.text)
        if params is None:
            return False
        # Un `ELSE` detrás asignaría la variable sin pasar por la cola: se deja como antes.
        if index + 1 < len(self.stmts) and self.stmts[index + 1].text.strip().lower().startswith(
            "else"
        ):
            return False
        salidas = [qualify(n) for n in self.step.outputs if n.lower() != "_null_"]
        operador = self.b.op(
            "stateful_row",
            {**params, "outputs": salidas},
            statement_ev,
            status="hueco",
            notes=["LAG/DIF sin emisor en Talend todavía (lefunctionsref, p. 1164; B-13)"],
        )
        self._enlazar(operador)
        self.pending_derive = None
        self.prev = s
        return True

    def _asignacion_condicional(self, index: int, statement_ev: Evidence) -> bool:
        if self._estado_lag(index, statement_ev):
            return True
        conditional = _conditional_assignment(self.stmts, index)
        if conditional is not None:
            conditional = ([conditional[0]], conditional[1])
        else:
            conditional = bloque_condicional(self.stmts, index) or bloque_select(
                self.stmts, index
            )
        if conditional is None:
            if select_sin_otherwise(self.stmts, index):
                _note(
                    self.current,
                    "P-SELECT-SIN-OTHERWISE: SELECT sin OTHERWISE; si ningún WHEN coincide SAS "
                    "detiene el paso (lestmtsref, p. 340)",
                    status="parcial",
                )
            return False
        asignaciones, siguiente = conditional
        if self.pending_derive is None:
            self.pending_derive = self.b.op(
                "derive", {"assignments": [], "modo": "agrega"}, statement_ev
            )
            self._enlazar(self.pending_derive)
        self.pending_derive.params["assignments"].extend(asignaciones)
        self.b.refresh(self.pending_derive)
        self.omit.update(range(index + 1, siguiente))
        self.prev = self.stmts[siguiente - 1]
        return True

    def _asignacion(self, s: DsStatement, statement_ev: Evidence) -> None:
        target = s.fields["target"]
        expression = s.fields["expression"]
        rewritten = reescribir_substr_izquierda(target, expression)
        if rewritten is not None:
            target, expression = rewritten
        elif es_objetivo_substr_izquierda(target):
            note = "Pendiente: P-DATASTEP-SUBSTR-IZQ; la pseudovariable no se puede reescribir"
            if self.pending_derive is None:
                self.pending_derive = self.b.op(
                    "derive",
                    {"assignments": [], "modo": "agrega"},
                    statement_ev,
                    status="hueco",
                    notes=[note],
                )
                self._enlazar(self.pending_derive)
            else:
                self.pending_derive.status = "hueco"
                if note not in self.pending_derive.notes:
                    self.pending_derive.notes.append(note)
                self.b.refresh(self.pending_derive)
            return
        assignment = {"target": target, "expression": expression}
        if self.pending_derive is None:
            # `modo`: una asignación de DATA step conserva las columnas que ya venían; el
            # `derive` de un `SELECT` las reemplaza. Sin la marca, el emisor escribiría un
            # `tMap` con una sola columna y el Job perdería el resto de la fila.
            self.pending_derive = self.b.op(
                "derive", {"assignments": [], "modo": "agrega"}, statement_ev
            )
            self._enlazar(self.pending_derive)
        self.pending_derive.params["assignments"].append(assignment)
        origin = _statement_evidence(s, self.ev)
        path = ("assignments", len(self.pending_derive.params["assignments"]) - 1, "expression")
        self.pending_derive.expression_evidence[path] = [origin]
        self.b.refresh(self.pending_derive)

    def _sentencia_sin_operador(self, index: int, s: DsStatement, statement_ev: Evidence) -> bool:
        """DECLARE, ARRAY/DO/END, FILE/PUT y OUTPUT de continuación: True si ya quedó resuelta."""
        kind = s.kind
        if kind == "declare":
            _note(self.current, f"declaración sin efecto en la lógica: {s.text}")
            return True
        if kind in ("array", "do", "end"):
            mensaje = f"{kind} no traducido: revisar el bucle o el arreglo"
            _note(self.current, mensaje, status="parcial")
            return True
        if kind == "file" and self.file_put is not None:
            return True
        if kind == "put" and self.file_put is not None:
            self._enlazar(escribir_file_put(self.file_put, statement_ev, self.b))
            return True
        if kind in ("file", "put"):
            self.current = registrar_file_put_pendiente(s, statement_ev, self.b, self.current)
            return True
        if kind == "output" and not s.fields.get("targets") and index < len(self.stmts) - 1:
            destinos = [qualify(n) for n in self.step.outputs if n.lower() != "_null_"]
            if destinos:
                ramas = [{"outputs": [destino]} for destino in destinos]
                ramas.append({"outputs": [], "continue": True})
                continuacion = self.b.op(
                    "map",
                    {"steps": [], "outputs": destinos, "branches": ramas},
                    statement_ev,
                )
                if self.current is not None:
                    self.b.link(self.current, continuacion)
                self.current = continuacion
                return True
        return False

    def _operador(self, s: DsStatement, before: DsStatement | None, statement_ev: Evidence) -> None:
        outputs = [qualify(n) for n in self.step.outputs if n.lower() != "_null_"]
        new = _statement_op(s, s.kind, before, statement_ev, self.b, outputs)
        if new is None:
            _note(self.current, f"sentencia sin traducción: {s.text}", status="parcial")
            if self.current is not None:
                self.current.params.setdefault("untranslated", []).append(s.text)
                self.b.refresh(self.current)
            else:
                self.loose.append(s.text)  # sin operador aún: se adjunta al operador final
            return
        if new.kind == "filter":
            origin = _statement_evidence(s, self.ev)
            new.expression_evidence[("expression",)] = [origin]
        self._enlazar(new)
