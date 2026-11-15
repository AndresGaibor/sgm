"""Tabla de funciones SAS del traductor de Talend: nombre SAS → función constructora."""

from __future__ import annotations

from sgm.expressions.talend_funciones import (
    _routine,
)
from sgm.expressions.talend_funciones_fecha import (
    _datdif,
    _datepart,
    _intck,
    _intnx,
    _mdy,
    _part,
    _today,
    _yrdif,
)
from sgm.expressions.talend_funciones_formato import _input, _put
from sgm.expressions.talend_funciones_numerico import (
    _aggregate,
    _ceil_floor,
    _coalesce,
    _coalescec,
    _ifc,
    _ifn,
    _int,
    _missing,
    _mod,
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
from sgm.expressions.talend_funciones_texto_extra import (
    _count,
    _find,
    _index,
    _length,
    _lengthc,
    _lengthn,
    _translate,
    _tranwrd,
)

_FUNCTIONS = {
    "upcase": _routine("StringHandling", "UPCASE", 1), "lowcase": _routine("StringHandling", "DOWNCASE", 1),
    "strip": _routine("StringHandling", "TRIM", 1), "trim": _routine("StringHandling", "RTRIM", 1),
    "left": _routine("StringHandling", "LTRIM", 1), "tranwrd": _tranwrd,
    "count": _count,
    "length": _length, "lengthc": _lengthc,
    "lengthn": _lengthn,
    "compbl": _strfn('StringHandling.EREPLACE({0}, " +", " ")'), "reverse": _strfn("new StringBuilder({0}).reverse().toString()"),
    "cat": _cat(False), "cats": _cat(True), "catt": _cat(False, trailing_only=True), "catx": _cat(True, sep=True),
    "substr": _substr, "substrn": _substr, "scan": _scan, "compress": _compress,
    "propcase": _propcase,
    "repeat": _repeat,
    "right": _strfn('StringHandling.LPAD(StringHandling.TRIM({0}), StringHandling.LEN({0}), " ")'),
    "index": _index,
    "find": _find, "translate": _translate,
    "abs": _unary_math("Math.abs"), "ceil": _ceil_floor("Math.ceil"), "floor": _ceil_floor("Math.floor"),
    "sqrt": _unary_math("Math.sqrt"), "exp": _unary_math("Math.exp"),
    "log": _unary_math("Math.log"), "mod": _mod, "sign": _unary_math("Math.signum"),
    "round": _round, "int": _int,
    "coalesce": _coalesce, "coalescec": _coalescec, "ifn": _ifn, "ifc": _ifc,
    "missing": _missing,
    "max": _aggregate("max"), "min": _aggregate("min"), "sum": _aggregate("sum"), "mean": _aggregate("mean"),
    "n": _aggregate("n"), "nmiss": _aggregate("nmiss"), "cmiss": _aggregate("cmiss"),
    "input": _input, "inputn": _input, "inputc": _input, "put": _put, "putn": _put, "putc": _put,
    "today": _today("today"), "date": _today("date"),
    "datepart": _datepart, "mdy": _mdy, "intnx": _intnx, "intck": _intck,
    "datdif": _datdif, "yrdif": _yrdif,
    "year": _part("year"), "month": _part("month"), "day": _part("day"), "weekday": _part("weekday"),
    "qtr": _part("qtr"),
}  # fmt: skip
