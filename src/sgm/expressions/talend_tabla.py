"""Tabla de funciones SAS del traductor de Talend: nombre SAS → función constructora."""

from __future__ import annotations

from sgm.expressions.talend_base import (
    E,
    Unsupported,
)
from sgm.expressions.talend_funciones import (
    _datepart,
    _mdy,
    _part,
    _routine,
)
from sgm.expressions.talend_funciones_fecha import _intck, _intnx
from sgm.expressions.talend_funciones_formato import _input, _put
from sgm.expressions.talend_funciones_numerico import (
    _aggregate,
    _coalesce,
    _ifv,
    _int,
    _round,
    _unary_math,
)
from sgm.expressions.talend_funciones_texto import (
    _cat,
    _compress,
    _propcase,
    _repeat,
    _scan,
    _strfn,
    _substr,
)

_FUNCTIONS = {
    "upcase": _routine("StringHandling", "UPCASE", 1), "lowcase": _routine("StringHandling", "DOWNCASE", 1),
    "strip": _routine("StringHandling", "TRIM", 1), "trim": _routine("StringHandling", "RTRIM", 1),
    "left": _routine("StringHandling", "LTRIM", 1), "tranwrd": _routine("StringHandling", "CHANGE", 3),
    "count": _routine("StringHandling", "COUNT", 2),
    "length": _strfn("Math.max(StringHandling.LEN(StringHandling.RTRIM({0})), 1)"), "lengthc": _strfn("StringHandling.LEN({0})"),
    "lengthn": _strfn("StringHandling.LEN(StringHandling.RTRIM({0}))"),
    "compbl": _strfn('StringHandling.EREPLACE({0}, " +", " ")'), "reverse": _strfn("new StringBuilder({0}).reverse().toString()"),
    "cat": _cat(False), "cats": _cat(True), "catt": _cat(True), "catx": _cat(True, sep=True),
    "substr": _substr, "substrn": _substr, "scan": _scan, "compress": _compress,
    "propcase": _propcase,
    "repeat": _repeat,
    "right": _strfn('StringHandling.LPAD(StringHandling.TRIM({0}), StringHandling.LEN({0}), " ")'),
    "index": lambda p, a: E(f"({a[0].java}.indexOf({a[1].java}) + 1)") if len(a) == 2 else (_ for _ in ()).throw(Unsupported("index")),
    "abs": _unary_math("Math.abs"), "ceil": _unary_math("Math.ceil"), "floor": _unary_math("Math.floor"),
    "sqrt": _routine("Mathematical", "SQRT", 1), "exp": _routine("Mathematical", "EXP", 1),
    "log": _routine("Mathematical", "LN", 1), "mod": _routine("Mathematical", "MOD", 2),
    "round": _round, "int": _int,
    "coalesce": _coalesce, "coalescec": _coalesce, "ifn": _ifv, "ifc": _ifv,
    "missing": lambda p, a: E(f"Relational.ISNULL({a[0].java})", "bool"),
    "max": _aggregate("max"), "min": _aggregate("min"), "sum": _aggregate("sum"), "mean": _aggregate("mean"),
    "n": _aggregate("n"), "nmiss": _aggregate("nmiss"),
    "input": _input, "inputn": _input, "inputc": _input, "put": _put, "putn": _put, "putc": _put,
    "today": lambda p, a: E("TalendDate.getCurrentDate()", "date"), "date": lambda p, a: E("TalendDate.getCurrentDate()", "date"),
    "datetime": lambda p, a: E("TalendDate.getCurrentDate()", "date"),
    "datepart": _datepart, "mdy": _mdy, "intnx": _intnx, "intck": _intck,
    "year": _part("year"), "month": _part("month"), "day": _part("day"), "weekday": _part("weekday"),
}  # fmt: skip
