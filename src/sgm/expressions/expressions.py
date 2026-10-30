"""Traducción conservadora de condiciones y expresiones SAS a Java (sintaxis de Talend).

Solo cubre un subconjunto seguro (comparaciones, AND/OR/NOT, aritmética, literales, funciones
de texto simples). Todo lo demás devuelve `talend=None`: no se inventa una traducción.
Cada resultado debe validarse semánticamente (missing, mayúsculas, tipos).
"""

import os
import re
from dataclasses import dataclass, field

from sgm.expressions.talend_translator import (
    Unsupported,
    translate_to_talend,
)


@dataclass
class Translation:
    sas: str
    talend: str | None = None
    columns: list[str] = field(default_factory=list)
    simple: list[dict] | None = None  # condiciones tFilterRow (modo simple)
    logical: str | None = None  # "&&" | "||" para el modo simple
    warnings: list[str] = field(default_factory=list)
    engine: str = "inline"  # "inline" (traductor original) | "talend" (rutinas de sistema de Talend)
    kind: str = "any"  # num | str | bool | date | any: tipo que el Java emitido produce


class _Unsupported(Exception):
    pass


_TOKEN = re.compile(
    r"""\s*(?:
    (?P<str>'(?:[^']|'')*'|"(?:[^"]|"")*")
    |(?P<num>\d+(?:\.\d+)?)
    |(?P<mvar>&[A-Za-z_]\w*\.?)
    |(?P<op>\^=|~=|<>|>=|<=|\|\||=|>|<|\+|-|\*|/|\(|\)|,|&|\|)
    |(?P<fmt>(?:best|comma|dollar|yymmdd|ddmmyy|mmddyy|date|datetime)\d*\.\d*)
    |(?P<id>[A-Za-z_][\w]*(?:\.[A-Za-z_]\w*)?)
    )""",
    re.VERBOSE,
)
_ARITHMETIC_TOKEN = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\.[A-Za-z_][A-Za-z0-9_]*|\d+(?:\.\d+)?|[()+*/-]")
_CMP = {"=": "==", "eq": "==", "^=": "!=", "~=": "!=", "<>": "!=", "ne": "!=", ">": ">", "gt": ">",
        "<": "<", "lt": "<", ">=": ">=", "ge": ">=", "<=": "<=", "le": "<="}  # fmt: skip
_FUNCS = {
    "upcase": "{0}.toUpperCase()",
    "lowcase": "{0}.toLowerCase()",
    "strip": "{0}.trim()",
    "trim": "{0}.trim()",
}


_NUMBER = re.compile(r"-?\d+(?:\.\d+)?")


def _guard(value: str, expr: str) -> str:
    """Función con guarda de nulo: un argumento missing da null (como en SAS, el resultado es missing)."""
    return f"({value} == null ? null : {expr})"


def _f_substr(args: list[str]) -> str:
    if len(args) != 3:
        raise _Unsupported("substr() sin los tres argumentos (cadena, inicio, longitud)")
    text, start, length = args
    first = str(int(start) - 1) if re.fullmatch(r"\d+", start) else f"({start} - 1)"
    return _guard(text, f"{text}.substring({first}, {first} + {length})")


def _f_round(args: list[str]) -> str:
    if len(args) not in (1, 2):
        raise _Unsupported("round() con más de dos argumentos")
    value = args[0]
    unit = args[1] if len(args) == 2 else "1"
    if unit == "1":
        return _guard(value, f"Math.round({value})")
    return _guard(value, f"(Math.round({value} / {unit}) * {unit})")


def _f_length(args: list[str]) -> str:
    if len(args) != 1:
        raise _Unsupported("length() con más de un argumento")
    return f"({args[0]} == null ? 0 : {args[0]}.length())"


def _f_abs(args: list[str]) -> str:
    if len(args) != 1:
        raise _Unsupported("abs() con más de un argumento")
    return _guard(args[0], f"Math.abs({args[0]})")


def _f_int(args: list[str]) -> str:
    if len(args) != 1:
        raise _Unsupported("int() con más de un argumento")
    return _guard(args[0], f"((long) ({args[0]}))")


def _f_cats(args: list[str]) -> str:
    if not args:
        raise _Unsupported("cats() sin argumentos")
    parts = [f'({arg} == null ? "" : String.valueOf({arg}))' for arg in args]
    return "(" + " + ".join(parts) + ")"


def _f_if(args: list[str]) -> str:
    """ifn/ifc(condición, si verdadera, si falsa): operador condicional de Java."""
    if len(args) != 3:
        raise _Unsupported("ifn()/ifc() sin los tres argumentos (condición, verdadero, falso)")
    condition, when_true, when_false = args
    return f"({condition} ? {when_true} : {when_false})"


def _f_min(args: list[str]) -> str:
    if len(args) < 2:
        raise _Unsupported("min() con menos de dos argumentos")
    result = args[0]
    for arg in args[1:]:
        result = f"Math.min({result}, {arg})"
    return result


def _f_max(args: list[str]) -> str:
    if len(args) < 2:
        raise _Unsupported("max() con menos de dos argumentos")
    result = args[0]
    for arg in args[1:]:
        result = f"Math.max({result}, {arg})"
    return result


def _f_coalesce(args: list[str]) -> str:
    """Primer argumento no missing (como coalesce de SAS)."""
    if not args:
        raise _Unsupported("coalesce() sin argumentos")
    result = args[-1]
    for arg in reversed(args[:-1]):
        result = f"({arg} != null ? {arg} : {result})"
    return result


def _f_compress(args: list[str]) -> str:
    """compress(texto) quita los blancos; con lista de caracteres no hay equivalente simple."""
    if len(args) != 1:
        raise _Unsupported("compress() con lista de caracteres: sin equivalente simple")
    return _guard(args[0], args[0] + '.replaceAll("\\\\s", "")')


def _f_index(args: list[str]) -> str:
    """index(texto, subcadena): posición de 1 base, 0 si no está (como en SAS)."""
    if len(args) != 2:
        raise _Unsupported("index() con más de dos argumentos")
    text, sub = args
    return _guard(text, f"({text}.indexOf({sub}) + 1)")


_NUMERIC_FORMAT = re.compile(r'"(?:best|comma)\d*\.\d*"', re.IGNORECASE)


#: Formatos de fecha de SAS y su patrón Java (SimpleDateFormat) para TalendDate.
_DATE_FORMATS = {
    "yymmdd8.": "yyyyMMdd",
    "yymmdd10.": "yyyy-MM-dd",
    "ddmmyy10.": "dd/MM/yyyy",
    "mmddyy10.": "MM/dd/yyyy",
    "date9.": "ddMMMyyyy",
    "datetime20.": "ddMMMyyyy:HH:mm:ss",
}
#: Intervalos de intnx/intck y su unidad de TalendDate.
_INTERVALS = {"day": "dd", "week": "dd", "month": "mm", "year": "yy"}


def _date_format(literal: str) -> str | None:
    return _DATE_FORMATS.get(literal.strip('"').lower())


def _f_mdy(args: list[str]) -> str:
    if len(args) != 3:
        raise _Unsupported("mdy() sin los tres argumentos (mes, día, año)")
    month, day, year = args
    guard = f"({month} == null || {day} == null || {year} == null)"
    text = f'String.format("%04d-%02d-%02d", {year}, {month}, {day})'
    return f'({guard} ? null : TalendDate.parseDate("yyyy-MM-dd", {text}))'


def _f_datepart(args: list[str]) -> str:
    if len(args) != 1:
        raise _Unsupported("datepart() con más de un argumento (solo la parte de fecha)")
    value = args[0]
    return _guard(value, f'TalendDate.parseDate("yyyy-MM-dd", TalendDate.formatDate("yyyy-MM-dd", {value}))')


def _f_intnx(args: list[str]) -> str:
    if len(args) not in (3, 4):
        raise _Unsupported("intnx() con intervalo, fecha y desplazamiento (alineación opcional)")
    interval, value, step = args[0], args[1], args[2]
    alignment = args[3].strip('"').lower() if len(args) == 4 else "same"
    name = interval.strip('"').lower()
    unit = _INTERVALS.get(name)
    if unit is None:
        raise _Unsupported(f"intnx() con intervalo {name} sin equivalente")
    if alignment not in ("same", "begin"):
        raise _Unsupported(f"intnx() con alineación {alignment}: solo same y begin")
    amount = f"({step}) * 7" if name == "week" else step
    moved = f'TalendDate.addDate({value}, (int) ({amount}), "{unit}")'
    if alignment == "begin" and unit == "mm":
        moved = f'TalendDate.parseDate("yyyy-MM-dd", TalendDate.formatDate("yyyy-MM-01", {moved}))'
    elif alignment == "begin" and unit == "yy":
        moved = f'TalendDate.parseDate("yyyy-MM-dd", TalendDate.formatDate("yyyy-01-01", {moved}))'
    return _guard(value, moved)


def _f_intck(args: list[str]) -> str:
    if len(args) != 3:
        raise _Unsupported("intck() sin los tres argumentos (intervalo, inicio, fin)")
    interval, start, end = args
    name = interval.strip('"').lower()
    unit = _INTERVALS.get(name)
    if unit is None:
        raise _Unsupported(f"intck() con intervalo {name} sin equivalente")
    divisor = " / 7" if name == "week" else ""
    return _guard(start, f'(TalendDate.diffDate({end}, {start}, "{unit}"){divisor})')


def _f_today(args: list[str]) -> str:
    if args:
        raise _Unsupported("today() sin argumentos")
    return "TalendDate.getCurrentDate()"


def _f_date_part(part: str):
    def build(args: list[str]) -> str:
        if len(args) != 1:
            raise _Unsupported(f"{part.lower()}() con más de un argumento")
        return _guard(args[0], f'TalendDate.getPartOfDate("{part}", {args[0]})')

    return build


def _f_input(args: list[str]) -> str:
    """input(texto, formato numérico): conversión a número; las fechas de SAS quedan fuera (sin equivalente simple)."""
    if len(args) == 2 and _date_format(args[1]):
        text = args[0]
        return _guard(text, f'TalendDate.parseDate("{_date_format(args[1])}", {text})')
    if len(args) != 2 or not _NUMERIC_FORMAT.fullmatch(args[1]):
        raise _Unsupported("input() solo con formato numérico (best./comma.)")
    return _guard(args[0], f"Double.parseDouble({args[0]})")


def _f_put(args: list[str]) -> str:
    """put(número, formato numérico): conversión a texto."""
    if len(args) == 2 and _date_format(args[1]):
        return _guard(args[0], f'TalendDate.formatDate("{_date_format(args[1])}", {args[0]})')
    if len(args) != 2 or not _NUMERIC_FORMAT.fullmatch(args[1]):
        raise _Unsupported("put() solo con formato numérico (best./comma.)")
    return _guard(args[0], f"String.valueOf({args[0]})")


_FUNCTIONS = {
    "mdy": _f_mdy,
    "datepart": _f_datepart,
    "intnx": _f_intnx,
    "intck": _f_intck,
    "today": _f_today,
    "year": _f_date_part("YEAR"),
    "month": _f_date_part("MONTH"),
    "day": _f_date_part("DAY_OF_MONTH"),
    "input": _f_input,
    "put": _f_put,
    "min": _f_min,
    "max": _f_max,
    "coalesce": _f_coalesce,
    "compress": _f_compress,
    "index": _f_index,
    "ifn": _f_if,
    "ifc": _f_if,
    "substr": _f_substr,
    "round": _f_round,
    "length": _f_length,
    "abs": _f_abs,
    "int": _f_int,
    "cats": _f_cats,
    "cat": _f_cats,
}
_FUNCTION_WARNINGS = {
    "today": ["today(): en SAS es días desde 1960; en Talend es un Date: validar al comparar con fechas SAS"],
    "year": ["year/month/day(): sobre un Date de Talend; con fecha SAS numérica validar la conversión de época"],
    "month": ["year/month/day(): sobre un Date de Talend; con fecha SAS numérica validar la conversión de época"],
    "day": ["year/month/day(): sobre un Date de Talend; con fecha SAS numérica validar la conversión de época"],
    "mdy": ["mdy(): devuelve un Date de Talend; con missing en mes, día o año devuelve null"],
    "datepart": ["datepart(): quita la hora; validar con datetimes SAS (época 1960 frente a Date de Talend)"],
    "intnx": ["intnx(): alineación same/begin; end no se traduce. Validar la unidad con datos reales"],
    "intck": ["intck(): cuenta fronteras de unidad como SAS; diffDate devuelve la diferencia de la unidad, validar el signo"],
    "input": ["input(): convierte texto con el formato indicado; un texto no válido lanza excepción"],
    "put": ["put(): convierte un valor con el formato indicado a texto"],
    "min": ["min()/max(): con missing en Java el resultado es null; SAS ignora el missing"],
    "max": ["min()/max(): con missing en Java el resultado es null; SAS ignora el missing"],
    "coalesce": ["coalesce(): el orden de los argumentos se conserva"],
    "compress": ["compress(): quita solo blancos (espacios, tabuladores, saltos)"],
    "index": ["index(): 0 si la subcadena no aparece, como en SAS"],
    "ifn": ["ifn()/ifc(): con missing en la condición Java la evalúa como falsa; validar con datos"],
    "ifc": ["ifn()/ifc(): con missing en la condición Java la evalúa como falsa; validar con datos"],
    "substr": ["substr(): posición de 1 base convertida a 0; con cadena más corta puede fallar"],
    "round": ["round(): redondeo al múltiplo indicado (la mitad sube, como en SAS)"],
    "length": ["length(): en SAS los blancos finales cuentan; revisar con datos reales"],
    "int": ["int(): trunca hacia cero, como en SAS"],
    "cats": ["cats()/cat(): no quita blancos finales; los numéricos se convierten con String.valueOf"],
    "cat": ["cats()/cat(): no quita blancos finales; los numéricos se convierten con String.valueOf"],
}


TEXT_TYPE_WARNING = "tipo no confirmado: se asumió texto; confirmar con el esquema real"


def _text_is(column: str, literal: str) -> str:
    """Igualdad null-safe de una columna con un literal de texto (SAS: ausente equivale a blanco)."""
    if literal == '""':
        return f'({column} == null || {column}.trim().isEmpty())'
    return f"{literal}.equals({column})"


def _tokens(s: str) -> list[tuple[str, str]]:
    out, pos = [], 0
    s = s.strip()
    while pos < len(s):
        m = _TOKEN.match(s, pos)
        if not m or m.end() == pos:
            raise _Unsupported(f"token no soportado: {s[pos : pos + 12]!r}")
        kind = m.lastgroup or ""
        out.append((kind, m.group(kind)))
        pos = m.end()
    return out


class _Parser:
    def __init__(self, toks: list[tuple[str, str]]):
        self.t, self.i = toks, 0
        self.cols: list[str] = []
        self.warnings: list[str] = []
        self.simple: list[dict] = []
        self.ops: set[str] = set()
        self.unsafe_comparison = False

    def peek(self) -> tuple[str, str]:
        return self.t[self.i] if self.i < len(self.t) else ("end", "")

    def take(self) -> tuple[str, str]:
        tok = self.peek()
        self.i += 1
        return tok

    def is_word(self, w: str) -> bool:
        k, v = self.peek()
        return k == "id" and v.lower() == w

    # lógica
    def expr(self) -> str:
        left = self.and_()
        while self.is_word("or") or self.peek()[1] == "|":
            self.take()
            self.ops.add("||")
            left = f"({left} || {self.and_()})"
        return left

    def and_(self) -> str:
        left = self.not_()
        while self.is_word("and") or self.peek()[1] == "&":
            self.take()
            self.ops.add("&&")
            left = f"({left} && {self.not_()})"
        return left

    def not_(self) -> str:
        if self.is_word("not") or self.peek()[1] in ("^", "~"):
            self.take()
            self.ops.add("!")
            return f"!({self.not_()})"
        return self.cmp()

    def cmp(self) -> str:
        left_start = self.i
        left = self.arith()
        k, v = self.peek()
        op = _CMP.get(v.lower()) if k in ("op", "id") else None
        if self.is_word("in"):
            self.take()
            if self.take()[1] != "(":
                raise _Unsupported("IN sin paréntesis")
            vals = [self.arith()]
            while self.peek()[1] in (",",) or self.peek()[0] in ("str", "num"):
                if self.peek()[1] == ",":
                    self.take()
                vals.append(self.arith())
            if self.take()[1] != ")":
                raise _Unsupported("IN sin cierre")
            self.ops.add("in")
            if re.fullmatch(r"input_row\.\w+", left) and all(
                x.startswith('"') and not _NUMBER.fullmatch(x.strip('"')) for x in vals
            ):
                self.warnings.append(TEXT_TYPE_WARNING)
                return "(" + " || ".join(_text_is(left, x) for x in vals) + ")"
            if re.fullmatch(r"input_row\.\w+", left):
                self.unsafe_comparison = True
                self.warnings.append(
                    "IN sobre columna sin tipo conocido: validar conversión y semántica de missing/nulos"
                )
            return (
                "("
                + " || ".join(
                    f"{left}.equals({x})" if x.startswith('"') else f"{left} == {x}" for x in vals
                )
                + ")"
            )
        if op is None:
            return left
        self.take()
        right = self.arith()
        text_expr: str | None = None
        left_column = re.fullmatch(r"input_row\.\w+", left)
        right_column = re.fullmatch(r"input_row\.\w+", right)
        if left_column or right_column:
            other = right if left_column else left
            column = left if left_column else right
            if op in ("==", "!=") and other.startswith('"') and not _NUMBER.fullmatch(other.strip('"')):
                # Igualdad con texto: la columna se asume texto; el paso se valida con el esquema real.
                self.warnings.append(TEXT_TYPE_WARNING)
                text_expr = _text_is(column, other)
                if op == "!=":
                    text_expr = f"!({text_expr})"
            elif _NUMBER.fullmatch(other) and op in ("<", ">", "<=", ">="):
                # Orden frente a un literal numérico: el tipo sale del literal (validar en Studio).
                # La igualdad no se infiere: sin tipo, una columna puede ser texto.
                self.warnings.append(
                    "tipo no confirmado: el tipo numérico se infiere del literal de la comparación; validar que la columna es numérica"
                )
            else:
                self.unsafe_comparison = True
                self.warnings.append(
                    "Comparación con columna sin tipo conocido: validar conversión, orden y semántica de missing/nulos"
                )
        if (
            len(self.t)
            and self.i - left_start == 3
            and self.t[left_start][0] == "id"
            and self.t[left_start + 2][0] in ("str", "num", "mvar")
        ):
            self.simple.append(
                {
                    "column": self.t[left_start][1],
                    "operator": op,
                    "value": self.t[left_start + 2][1],
                }
            )
        else:
            self.simple.append({})  # no representable en modo simple
        if text_expr is not None:
            return text_expr
        if op in ("<", "<=", "!="):
            self.warnings.append(
                "Missing numérico: en SAS es menor que cualquier número; en Java un null no compara igual"
            )
        if op in ("==", "!=") and (right.startswith('"') or left.startswith('"')):
            s, o = (right, left) if right.startswith('"') else (left, right)
            return f"{'!' if op == '!=' else ''}{o}.equals({s})"
        return f"({left} {op} {right})"

    def function(self, name: str, args: list[str]) -> str:
        """Llamada a función SAS con argumentos ya traducidos. Sin equivalente claro: `_Unsupported`."""
        if name in _FUNCS and len(args) == 1:
            self.warnings.append(f"{name}(): comprobar nulos antes de invocar el método")
            return _FUNCS[name].format(args[0])
        handler = _FUNCTIONS.get(name)
        if handler is None:
            raise _Unsupported(f"función {name}")
        result = handler(args)
        self.warnings.extend(_FUNCTION_WARNINGS.get(name, []))
        return result

    # aritmética
    def arith(self) -> str:
        left = self.term()
        while self.peek()[1] in ("+", "-", "||"):
            op = self.take()[1]
            right = self.term()
            left = f"({left} {'+' if op == '||' else op} {right})"
        return left

    def term(self) -> str:
        left = self.atom()
        while self.peek()[1] in ("*", "/"):
            op = self.take()[1]
            left = f"({left} {op} {self.atom()})"
        return left

    def atom(self) -> str:
        k, v = self.take()
        if k == "str":
            body = v[1:-1].replace(v[0] * 2, v[0]).replace("\\", "\\\\").replace('"', '\\"')
            return f'"{body}"'
        if k == "num":
            return v
        if k == "fmt":
            return f'"{v}"'
        if k == "mvar":
            name = v.lstrip("&").rstrip(".")
            self.warnings.append(
                f"Macrovariable &{name} → context.{name} (crear variable de contexto)"
            )
            return f"context.{name}"
        if k == "op" and v == "(":
            e = self.expr()
            if self.take()[1] != ")":
                raise _Unsupported("paréntesis sin cerrar")
            return f"({e})"
        if k == "op" and v == "-":
            return f"-{self.atom()}"
        if k == "id":
            if self.peek()[1] == "(":
                name = v.lower()
                if name == "missing":
                    self.take()
                    arg = self.expr()
                    if self.take()[1] != ")":
                        raise _Unsupported("missing(")
                    self.warnings.append("missing(): null (y cadena vacía si es texto) en Java")
                    return f"({arg} == null)"
                self.take()  # "("
                args: list[str] = []
                if self.peek()[1] != ")":
                    args.append(self.expr())
                    while self.peek()[1] == ",":
                        self.take()
                        args.append(self.expr())
                if self.take()[1] != ")":
                    raise _Unsupported(f"{v}(")
                return self.function(name, args)
            if v == "." or v.lower() in ("and", "or", "not", "in"):
                raise _Unsupported(f"palabra {v}")
            col = v.split(".")[-1]
            self.cols.append(col)
            return f"input_row.{col}"
        raise _Unsupported(f"inesperado: {v!r}")


def talend_expressions_enabled() -> bool:
    """Interruptor del traductor con rutinas de Talend: `SGM_TALEND_EXPRESSIONS=1`.

    Apagado por defecto hasta comprobar en Studio que el Java que emite compila (`talend_job_verify`); no necesita nada
    instalado: solo usa rutinas de sistema de Talend y Java nativo.
    """
    return os.environ.get("SGM_TALEND_EXPRESSIONS", "").strip().lower() in {"1", "true", "yes", "on"}


def translate(sas: str) -> Translation:
    """Traduce una condición o expresión SAS; `talend=None` si no es seguro.

    Primero el traductor en línea (lo que ya traducía no cambia); si se rinde y `SGM_TALEND_EXPRESSIONS` está activo, el de rutinas de Talend, que cubre la
    gramática completa con `StringHandling`, `TalendDate`, `Mathematical` y Java nativo, y conserva la semántica del perdido.
    """
    t = _translate_inline(sas)
    if t.talend is not None:
        # El tipo del resultado no depende del motor que escribe el Java: el traductor completo lo sabe.
        t.kind = _talend_kind(sas)
        return t
    if not talend_expressions_enabled():
        return t
    try:
        result = translate_to_talend(sas)
    except Unsupported as error:
        t.warnings.append(f"Sin traducción con rutinas de Talend: {error}")
        return t
    t.talend, t.columns, t.warnings, t.engine = result.java, result.columns, result.warnings, "talend"
    t.kind = result.kind
    return t


def _talend_kind(sas: str) -> str:
    """Tipo del valor que produce la expresión, según el traductor completo (`any` si no lo sabe)."""
    try:
        return translate_to_talend(sas).kind
    except Unsupported:
        return "any"


def _translate_inline(sas: str) -> Translation:
    t = Translation(sas=sas)
    s = re.sub(r"\s+", " ", sas).strip()
    if re.search(r"\bis\s+(not\s+)?missing\b|\bcalculated\b", s, re.IGNORECASE):
        t.warnings.append("Construcción SAS sin traducción automática")
        return t
    try:
        p = _Parser(_tokens(s))
        java = p.expr()
        if p.i != len(p.t):
            raise _Unsupported("texto sobrante")
    except _Unsupported as e:
        t.warnings.append(f"Sin traducción automática: {e}")
        return t
    t.talend = None if p.unsafe_comparison else java
    t.columns = sorted(set(p.cols))
    t.warnings = sorted(set(p.warnings))
    if p.simple and all(p.simple) and len(p.ops) <= 1 and p.ops <= {"&&", "||"}:
        t.simple = p.simple
        t.logical = next(iter(p.ops), "&&")
    return t


def is_simple_arithmetic_translation(expression: str | None) -> bool:
    """Indica si la traducción solo contiene columnas, números y aritmética básica."""
    if not expression:
        return False
    tokens = _ARITHMETIC_TOKEN.findall(expression)
    if not tokens or "".join(tokens) != re.sub(r"\s+", "", expression):
        return False

    expecting_value = True
    depth = 0
    for token in tokens:
        if token == "(":
            if not expecting_value:
                return False
            depth += 1
            continue
        if token == ")":
            if expecting_value or depth == 0:
                return False
            depth -= 1
            expecting_value = False
            continue
        if token in {"+", "-", "*", "/"}:
            if token in {"+", "-"} and expecting_value:
                continue
            if expecting_value:
                return False
            expecting_value = True
            continue
        if not expecting_value:
            return False
        expecting_value = False
    return not expecting_value and depth == 0
