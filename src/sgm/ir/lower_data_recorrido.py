"""Recorrido de las sentencias de un DATA step: cada sentencia se convierte en operadores del plan.

Se extrajo de `lower_data._lower_data_steps` sin cambio de comportamiento (B-5, límite de
300 líneas).
El estado que el bucle reasignaba (`current`, `pending_derive`, `loose`, `prev`, `omit`) vive en
`_Recorrido`; cada rama del bucle es un método que dice si la sentencia ya quedó resuelta.
"""

from __future__ import annotations

from dataclasses import replace

from sgm.frontend.datastep import DataStep, DsStatement
from sgm.ir.builder import Builder, qualify
from sgm.ir.lower_data_asignaciones import _conditional_assignment, _statement_op
from sgm.ir.lower_data_bloques import bloque_condicional
from sgm.ir.lower_data_salidas import _conditional_output_chain, _note, _output_sequence
from sgm.ir.models import Evidence, Operator

_HEAD_KINDS = frozenset({"set", "merge", "by", "infile", "input", "datalines"})


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

    def ejecutar(self) -> None:
        for index, s in enumerate(self.stmts):
            if index in self.omit:
                continue
            statement_ev = Evidence(self.ev.file, s.line, s.line, self.ev.label, self.ev.call)
            before, self.prev = self.prev, s
            if s.kind in _HEAD_KINDS:
                continue
            if self._secuencia_output(index, statement_ev):
                continue
            if self._salida_condicional(index, statement_ev):
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

    def _asignacion_condicional(self, index: int, statement_ev: Evidence) -> bool:
        conditional = _conditional_assignment(self.stmts, index)
        if conditional is not None:
            conditional = ([conditional[0]], conditional[1])
        else:
            conditional = bloque_condicional(self.stmts, index)
        if conditional is None:
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
        assignment = {"target": s.fields["target"], "expression": s.fields["expression"]}
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
        if kind in ("file", "put"):
            self._file_put(s, statement_ev)
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

    def _file_put(self, s: DsStatement, statement_ev: Evidence) -> None:
        if self.current is not None and self.current.kind != "unsupported":
            note = f"FILE_PUT_SIN_PLANTILLA: {s.text}"
            if note not in self.current.notes:
                self.current.notes.append(note)
            unsupported = self.b.op(
                "unsupported",
                {
                    "reason": "SENTENCIA_NO_SOPORTADA",
                    "reason_detail": "FILE_PUT_SIN_PLANTILLA",
                    "unsupported_statements": [s.text],
                    "statement": s.text,
                },
                statement_ev,
                status="hueco",
            )
            self.b.link(self.current, unsupported)
            self.current = unsupported
        elif self.current is None:
            self.current = self.b.op(
                "unsupported",
                {
                    "reason": "SENTENCIA_NO_SOPORTADA",
                    "reason_detail": "FILE_PUT_SIN_PLANTILLA",
                    "unsupported_statements": [s.text],
                    "statement": s.text,
                },
                statement_ev,
                status="hueco",
            )
        else:
            note = f"FILE_PUT_SIN_PLANTILLA: {s.text}"
            if note not in self.current.notes:
                self.current.notes.append(note)
            unsupported = self.current.params.setdefault("unsupported_statements", [])
            if s.text not in unsupported:
                unsupported.append(s.text)
                self.current.params["statement"] = " | ".join(unsupported)
                self.b.refresh(self.current)

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
