"""El `tMap` que sale de un operador `map`: entradas, llaves de unión, asignaciones y filtro.

Un `map` del plan es una cadena de pasos (`join`, `filter`, `derive`, `aggregate`) sobre una o
varias fuentes. El `tMap` hace de una sola vez lo que en SQL son tres cláusulas: las llaves de unión
van en los lookups, las asignaciones del `SELECT` en las expresiones de la salida y el `WHERE` en el
`expressionFilter` de esa misma salida.

Lo que no se puede demostrar no se escribe: un paso sin traducción deja su pendiente y el resto del
mapa se arma igual, para que el Job siga siendo útil y el hueco quede a la vista.

Los nombres de las conexiones los decide este módulo, no el llamador: la fuente principal es `row1`
y los lookups `row2` en adelante, en el orden en que llegaron. `Armado.entradas` devuelve ese
reparto para que el Job conecte cada nodo con el nombre que el `tMap` espera.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from sgm.ir.models import Operator
from sgm.migrar.esquemas import PendienteMigracion, tipo_de_expresion
from sgm.talend_item.desde_plan_expresiones import expresion
from sgm.talend_item.desde_plan_nodos import TIPOS
from sgm.talend_item.modelo import Columna, Nodo
from sgm.talend_item.tmap import EntradaMap, SalidaMap, tmap

PRINCIPAL = "row1"
NO_SOPORTADO = "P-OPERADOR-SIN-SOPORTE"
SIN_TRADUCIR = "P-ASIGNACION-SIN-TRADUCIR"
FILTRO_SIN_TRADUCIR = "P-FILTRO-SIN-TRADUCIR"
FALLO = "P-FALLO-INTERNO"


@dataclass(frozen=True)
class Fuente:
    """Una entrada del `tMap`: el nodo que la produce y las columnas que trae."""

    origen: str  # UNIQUE_NAME del nodo que la alimenta
    tabla: str  # nombre sin librería, en minúsculas: `ventas`, `clientes`
    columnas: list[Columna] = field(default_factory=list)
    # Resultado de un cruce anterior (`a JOIN b JOIN c`): ya trae las columnas de las dos tablas y
    # es el lado izquierdo del cruce siguiente.
    compuesta: bool = False
    # Nombre de la bandera `IN=` que el `MERGE` le puso a esta tabla, si se la puso.
    bandera: str | None = None


@dataclass
class Armado:
    """Resultado de armar el `tMap`: el nodo (si se pudo), el reparto de filas y los pendientes.

    `columnas` es el esquema de la salida y se calcula antes de montar el nodo: aunque el `tMap` no
    se pueda montar, la escritura que viene detrás sigue sabiendo qué columnas tiene que escribir, y
    el fallo queda como pendiente en vez de arrastrar al resto del Job.
    """

    nodo: Nodo | None = None
    entradas: dict[str, str] = field(default_factory=dict)  # origen -> row1, row2, ...
    columnas: list[Columna] = field(default_factory=list)
    pendientes: list[PendienteMigracion] = field(default_factory=list)


@dataclass(frozen=True)
class _Meseta:
    """Las fuentes ya ordenadas: la principal primero, con su nombre de fila y su tipo."""

    fuentes: list[Fuente]

    def fila(self, indice: int) -> str:
        return PRINCIPAL if indice == 0 else f"row{indice + 1}"

    @property
    def filas(self) -> dict[str, set[str]]:
        return {self.fila(i): {c.nombre for c in f.columnas} for i, f in enumerate(self.fuentes)}

    @property
    def tipos(self) -> dict[str, str]:
        return {
            f"{self.fila(i)}.{c.nombre}": c.tipo
            for i, fuente in enumerate(self.fuentes)
            for c in fuente.columnas
        }

    def tipo_de(self, fila: str, columna: str) -> str:
        for indice, fuente in enumerate(self.fuentes):
            if self.fila(indice) != fila:
                continue
            for propia in fuente.columnas:
                if propia.nombre == columna:
                    return propia.tipo
        return "id_String"

    def nombre_real(self, indice: int, columna: str) -> str:
        """Nombre de `columna` tal como lo trae la fuente: SAS no distingue mayúsculas."""
        for propia in self.fuentes[indice].columnas:
            if propia.nombre.lower() == columna.lower():
                return propia.nombre
        return columna


def _linea(op: Operator) -> int | None:
    return op.evidence[0].line_start if op.evidence else None


def _tabla(calificada: str) -> tuple[str, str]:
    """`work.ventas` o `ventas` a `(tabla, columna)`; `ventas.k` a `(ventas, k)`."""
    partes = [p for p in calificada.strip().lower().split(".") if p]
    if len(partes) >= 2:
        return partes[-2], partes[-1]
    return "", (partes[0] if partes else "")


def _pasos(op: Operator, tipo: str) -> list[dict]:
    return [
        paso.get("params", {}) for paso in op.params.get("steps", []) if paso.get("kind") == tipo
    ]


def _longitudes_declaradas(op: Operator) -> dict[str, int]:
    """Largo de las columnas String que el DATA step fija con `LENGTH` (pasada 9 y `declared`).

    Solo cuenta el tipo String con largo; el resto de tipos no lleva `length` en Talend.
    """
    largos: dict[str, int] = {}
    for paso in _pasos(op, "derive"):
        for nombre, (tipo, longitud) in (paso.get("declared") or {}).items():
            if tipo == "String" and longitud:
                largos[str(nombre).lower()] = int(longitud)
    return largos


def _principal(fuentes: list[Fuente], join: dict | None) -> int:
    """Índice de la fuente principal: la que el paso `join` declara como origen del `FROM`.

    En el SAS el `FROM` va primero y los `JOIN` después; `sources` guarda ese primer conjunto. Si no
    hay paso de unión, la principal es la primera entrada, que es el orden en que llegaron las
    aristas.
    """
    for indice, fuente in enumerate(fuentes):
        if fuente.compuesta:
            return indice
    if join:
        declaradas = [str(s).lower().split(".")[-1] for s in join.get("sources", [])]
        for tabla in declaradas:
            for indice, fuente in enumerate(fuentes):
                if fuente.tabla == tabla:
                    return indice
    return 0


def _consulta(meseta: _Meseta, tabla: str) -> int | None:
    """Índice del lookup que trae esa tabla, si es una entrada de consulta del mapa."""
    for indice, fuente in enumerate(meseta.fuentes):
        if indice and tabla and fuente.tabla == tabla:
            return indice
    return None


def _llaves(
    meseta: _Meseta, uniones: list[dict], armado: Armado, op: Operator
) -> tuple[dict[int, dict[str, str]], dict[int, bool]]:
    """Por cada lookup, sus columnas de unión con la expresión que las iguala, y si es interno.

    Un mapa puede traer varios cruces (`a JOIN b JOIN c`, o dos pasos del SAS fundidos en uno):
    cada lookup toma las llaves y el tipo del cruce que lo nombra. La llave de un lookup puede ser
    una columna de la principal o de un lookup anterior (`row2.ciudad`), que es como se encadenan
    las consultas en un `tMap`.
    """
    union: dict[int, dict[str, str]] = {i: {} for i in range(1, len(meseta.fuentes))}
    internas: dict[int, bool] = {}
    for join in uniones:
        interna = str(join.get("join_type", "")).lower() == "inner"
        if not join.get("keys") and join.get("by"):
            # `MERGE ... BY k`: la llave es la misma columna en todas las tablas.
            for indice in union:
                internas[indice] = interna
                for columna in join["by"]:
                    propia = meseta.nombre_real(indice, str(columna))
                    union[indice][propia] = f"{PRINCIPAL}.{meseta.nombre_real(0, str(columna))}"
            continue
        for par in join.get("keys") or []:
            if len(par) != 2:
                armado.pendientes.append(
                    PendienteMigracion(
                        "P-LLAVE-INCOMPLETA",
                        f"llave de unión {par!r} sin las dos columnas",
                        _linea(op),
                    )
                )
                continue
            tabla_izq, columna_izq = _tabla(par[0])
            tabla_der, columna_der = _tabla(par[1])
            der, izq = _consulta(meseta, tabla_der), _consulta(meseta, tabla_izq)
            if der is not None and izq is not None and der != izq:
                # Las dos tablas son lookups: la llave es del que llegó después.
                if der > izq:
                    indice, propia, otro, ajena = der, columna_der, izq, columna_izq
                else:
                    indice, propia, otro, ajena = izq, columna_izq, der, columna_der
            elif der is not None:
                indice, propia, otro, ajena = der, columna_der, 0, columna_izq
            elif izq is not None:
                # El `ON` escrito al revés: la principal quedó a la derecha.
                indice, propia, otro, ajena = izq, columna_izq, 0, columna_der
            else:
                continue
            real = meseta.nombre_real(indice, propia)
            union[indice][real] = f"{meseta.fila(otro)}.{meseta.nombre_real(otro, ajena)}"
            internas[indice] = interna
    return union, internas


def _tipos_soportados(uniones: list[dict], armado: Armado, op: Operator) -> bool:
    """Todos los cruces del mapa tienen un tipo que el `tMap` hace."""
    return all([_tipo_soportado(join, armado, op) for join in uniones])


def _tipo_soportado(join: dict | None, armado: Armado, op: Operator) -> bool:
    """El `tMap` hace cruces internos y externos por la izquierda; el resto no se supone.

    Un `MERGE` nunca se emite como `tMap`: el `tMap` cruza por llave y no reproduce el
    emparejamiento fila con fila de SAS cuando la llave se repite. Queda pendiente.
    """
    if not join:
        return True
    # Un MERGE tiene `by` y no `keys`; un JOIN de SQL, al revés.
    if "keys" not in join and "by" in join:
        armado.pendientes.append(PendienteMigracion(
            "P-UNION-TIPO-SIN-SOPORTE",
            "MERGE: el tMap cruza por llave y no reproduce el emparejamiento fila con fila "
            "de SAS cuando la llave se repite; hace falta tJavaRow o una secuencia por grupo",
            _linea(op),
        ))
        return False
    tipo = str(join.get("join_type") or "").strip().lower()
    if tipo in ("inner", "left", "left outer"):
        return True
    motivo = (
        f"unión '{tipo}'" if tipo else "tipo de unión no deducible"
    ) + ": un tMap solo hace INNER y LEFT OUTER; se necesita un tMap por lado y un tUnite"
    armado.pendientes.append(PendienteMigracion("P-UNION-TIPO-SIN-SOPORTE", motivo, _linea(op)))
    return False


def _entradas(
    meseta: _Meseta, uniones: list[dict], armado: Armado, op: Operator
) -> list[EntradaMap]:
    """Entradas del `tMap`: la principal sin unión y cada lookup con sus llaves."""
    if not uniones:
        return [
            EntradaMap(meseta.fila(i), list(fuente.columnas))
            for i, fuente in enumerate(meseta.fuentes)
        ]
    llaves, internas = _llaves(meseta, uniones, armado, op)
    entradas: list[EntradaMap] = []
    for indice, fuente in enumerate(meseta.fuentes):
        if indice == 0:
            entradas.append(EntradaMap(PRINCIPAL, list(fuente.columnas)))
            continue
        propias = llaves.get(indice, {})
        if not propias:
            armado.pendientes.append(
                PendienteMigracion(
                    "P-UNION-SIN-LLAVES",
                    f"{fuente.tabla}: el SAS no da una llave de unión demostrable "
                    "para esta entrada",
                    _linea(op),
                )
            )
        entradas.append(
            EntradaMap(
                meseta.fila(indice),
                list(fuente.columnas),
                expresiones_union=propias,
                # Un `ON` de SQL produce una fila por cada pareja: un cliente con cuatro ventas
                # sale cuatro veces. `UNIQUE_MATCH` —el modo de omisión de Studio— devuelve solo
                # la primera pareja y se come las demás en silencio: `l2_02` daba 10 filas donde
                # el SAS da 14. `ALL_ROWS` recorre todas y, si la llave es única, se comporta
                # igual que `UNIQUE_MATCH`.
                union="ALL_ROWS" if propias else "UNIQUE_MATCH",
                union_interna=internas.get(indice, False) and bool(propias),
            )
        )
    return entradas


def _filtro(meseta: _Meseta, op: Operator, armado: Armado) -> str:
    """El `WHERE` del SAS como `expressionFilter`, o vacío si no se pudo demostrar."""
    textos = [str(paso.get("expression", "")).strip() for paso in _pasos(op, "filter")]
    textos = [texto for texto in textos if texto]
    if not textos:
        return ""
    texto = " AND ".join(f"({t})" for t in textos)
    # Las banderas `IN=` de un MERGE no son columnas de ninguna entrada: se resuelven como la
    # pregunta «¿aportó esta tabla una fila?», que en Java es un booleano.
    booleanas = _banderas_booleanas(meseta, op)
    filas = {**meseta.filas, "bandera": set(booleanas)}
    tipos = {**meseta.tipos, **{f"bandera.{n}": "id_Boolean" for n in booleanas}}
    traducido, motivo = expresion(texto, filas, tipos)
    if traducido is not None and booleanas:
        if "(Number) bandera." in traducido:
            traducido, motivo = None, "una bandera IN= se usa como número en la condición"
        else:
            for nombre, java in booleanas.items():
                traducido = traducido.replace(f"bandera.{nombre}", f"({java})")
    if traducido is None:
        armado.pendientes.append(
            PendienteMigracion("P-FILTRO-SIN-TRADUCIR", f"filtro '{texto}': {motivo}", _linea(op))
        )
        return ""
    return traducido


def _valor(
    meseta: _Meseta,
    asignacion: dict,
    armado: Armado,
    op: Operator,
    previas: dict[str, tuple[str, str]] | None = None,
) -> tuple[str | None, str]:
    """Java de una asignación: la columna tal cual, o la expresión traducida."""
    destino = str(asignacion.get("target", "")).strip()
    valor = str(asignacion.get("expression", "")).strip()

    def traducir(texto: str) -> tuple[str | None, str | None]:
        filas = {fila: set(columnas) for fila, columnas in meseta.filas.items()}
        tipos = dict(meseta.tipos)
        for nombre, (_, tipo) in (previas or {}).items():
            filas[PRINCIPAL].add(nombre)
            tipos[f"{PRINCIPAL}.{nombre}"] = tipo
        java, motivo = expresion(texto, filas, tipos)
        if java is None:
            return None, motivo
        for nombre, (java_previa, _) in (previas or {}).items():
            if java_previa == f"{PRINCIPAL}.{nombre}":
                continue
            java = re.sub(
                rf"\b{re.escape(PRINCIPAL)}\.{re.escape(nombre)}\b",
                f"({java_previa})",
                java,
            )
        return java, None

    condicional = asignacion.get("conditional")
    if isinstance(condicional, dict):
        condiciones = (
            [str(rama.get("condition") or "") for rama in condicional["branches"]]
            if condicional.get("branches")
            else [str(condicional.get("condition") or "")]
        )
        for nombre, (java_previa, tipo_previo) in (previas or {}).items():
            if (
                java_previa != f"{PRINCIPAL}.{nombre}"
                and tipo_previo in {"id_Double", "id_Float", "id_BigDecimal"}
                and any(
                    re.search(rf"\b{re.escape(nombre)}\b", condicion)
                    for condicion in condiciones
                )
            ):
                motivo = (
                    f"la condición usa la columna derivada numérica '{nombre}'; el `tMap` la emite "
                    "como primitivo y no se puede preservar el faltante SAS en Java"
                )
                armado.pendientes.append(
                    PendienteMigracion(
                        FILTRO_SIN_TRADUCIR,
                        f"columna '{destino}', condición: {motivo}",
                        _linea(op),
                    )
                )
                return None, motivo
        if condicional.get("branches"):
            ramas = []
            for rama in condicional["branches"]:
                condicion = traducir(str(rama.get("condition") or ""))
                resultado = traducir(str(rama.get("expression") or ""))
                ramas.append((condicion, resultado))
            falsa = traducir(str(condicional.get("otherwise") or ""))
            traducidas = [java for pareja in ramas for java, _ in pareja] + [falsa[0]]
            motivos = [motivo for pareja in ramas for java, motivo in pareja if java is None]
            if falsa[0] is None:
                motivos.append(falsa[1])
            if any(java is None for java in traducidas):
                armado.pendientes.append(
                    PendienteMigracion(
                        SIN_TRADUCIR,
                        f"columna '{destino}', rama: "
                        f"{motivos[0] or 'expresión condicional sin traducir'}",
                        _linea(op),
                    )
                )
                return None, motivos[0] if motivos else "expresión condicional sin traducir"
            java = falsa[0]
            for condicion, resultado in reversed(ramas):
                if condicion[0] is None:
                    armado.pendientes.append(
                        PendienteMigracion(
                            FILTRO_SIN_TRADUCIR,
                            f"columna '{destino}', condición: {condicion[1]}",
                            _linea(op),
                        )
                    )
                    return None, condicion[1]
                java = f"({condicion[0]} ? {resultado[0]} : {java})"
            return java, ""
        condicion = traducir(str(condicional.get("condition") or ""))
        verdadera = traducir(valor)
        falsa = traducir(str(condicional.get("otherwise") or ""))
        for indice, (java, motivo) in enumerate((condicion, verdadera, falsa)):
            if java is None:
                codigo = FILTRO_SIN_TRADUCIR if indice == 0 else SIN_TRADUCIR
                concepto = "condición" if indice == 0 else "rama"
                armado.pendientes.append(
                    PendienteMigracion(
                        codigo,
                        f"columna '{destino}', {concepto}: "
                        f"{motivo or 'expresión condicional sin traducir'}",
                        _linea(op),
                    )
                )
                return None, motivo or f"{concepto} condicional sin traducir"
        return f"({condicion[0]} ? {verdadera[0]} : {falsa[0]})", ""
    if asignacion.get("origin") == "columna":
        fila, motivo = _fila_de_columna(meseta, valor)
        if fila is None:
            armado.pendientes.append(
                PendienteMigracion(SIN_TRADUCIR, f"columna '{destino}': {motivo}", _linea(op))
            )
        return fila, ""
    java, motivo = traducir(valor)
    if java is None:
        armado.pendientes.append(
            PendienteMigracion(SIN_TRADUCIR, f"columna '{destino}': {motivo}", _linea(op))
        )
    return java, motivo or ""


def _fila_de_columna(meseta: _Meseta, valor: str) -> tuple[str | None, str]:
    """`ventas.id_venta` o `id_venta` a `row1.id_venta`, según la entrada que tenga la columna."""
    tabla, columna = _tabla(valor)
    if tabla:
        for indice, fuente in enumerate(meseta.fuentes):
            if fuente.tabla == tabla:
                return f"{meseta.fila(indice)}.{meseta.nombre_real(indice, columna)}", ""
        # Una tabla ya cruzada no es una entrada propia: su columna viene en el resultado del cruce.
        for indice, fuente in enumerate(meseta.fuentes):
            if fuente.compuesta and any(
                propia.nombre.lower() == columna.lower() for propia in fuente.columnas
            ):
                return f"{meseta.fila(indice)}.{meseta.nombre_real(indice, columna)}", ""
        return None, f"la tabla '{tabla}' no es una entrada del mapa"
    candidatas = [
        indice
        for indice, fuente in enumerate(meseta.fuentes)
        if any(propia.nombre.lower() == columna.lower() for propia in fuente.columnas)
    ]
    if len(candidatas) == 1:
        real = meseta.nombre_real(candidatas[0], columna)
        return f"{meseta.fila(candidatas[0])}.{real}", ""
    if not candidatas:
        return None, f"la columna '{columna}' no está en ninguna entrada del mapa"
    return None, f"la columna '{columna}' está en varias entradas y el SAS no dice de cuál"


_ENTEROS = frozenset({"id_Integer", "id_Long", "id_Short", "id_Byte"})
_NUMERICOS = _ENTEROS | {"id_Double", "id_Float", "id_BigDecimal"}


def _solo_enteros(meseta: _Meseta, java: str) -> bool:
    """La expresión usa columnas, todas enteras, y no divide ni lleva decimales."""
    columnas = re.findall(r"\b(row\d+)\.(\w+)", java)
    if not columnas or "/" in java or re.search(r"\d\.\d", java):
        return False
    return all(meseta.tipo_de(fila, nombre) in _ENTEROS for fila, nombre in columnas)


def _tipo_de_texto(meseta: _Meseta, texto: str) -> str | None:
    """Tipo de una rama de un condicional: el de su columna o el que su literal demuestra."""
    limpio = texto.strip()
    if re.fullmatch(r"-?\d+", limpio):
        return "id_Long"
    if re.fullmatch(r"-?\d+\.\d+", limpio):
        return "id_Double"
    if re.fullmatch(r"\w+", limpio):
        for indice in range(len(meseta.fuentes)):
            tipo = meseta.tipo_de(meseta.fila(indice), meseta.nombre_real(indice, limpio))
            if any(c.nombre.lower() == limpio.lower() for c in meseta.fuentes[indice].columnas):
                return tipo
    return None


def _tipo_condicional(meseta: _Meseta, asignacion: dict) -> str | None:
    """Tipo de un `IF ... THEN a ELSE b`: si las ramas son todas números, el más ancho.

    `IF saldo < 0 THEN saldo = 0` mezcla un literal entero con una columna `Double`; el `?:` de
    Java da `double` y la columna de salida tiene que ser `Double`, no `Long`.
    """
    condicional = asignacion.get("conditional")
    if not isinstance(condicional, dict):
        return None
    textos = [str(asignacion.get("expression") or ""), str(condicional.get("otherwise") or "")]
    textos += [str(r.get("expression") or "") for r in condicional.get("branches") or []]
    tipos = [_tipo_de_texto(meseta, t) for t in textos if t.strip()]
    if not tipos or any(t not in _NUMERICOS for t in tipos):
        return None
    for ancho in ("id_BigDecimal", "id_Double", "id_Float"):
        if ancho in tipos:
            return ancho
    return "id_Long"


def _tipo_de_salida(meseta: _Meseta, java: str, asignacion: dict) -> str:
    """Tipo de la columna que produce una asignación.

    Una columna copiada conserva el tipo que trae. Una expresión que opera con números produce un
    número aunque el esquema no lo demuestre —`precio * stock` es doble en SAS—, y si no, texto.
    Sin esto la salida quedaba `id_String` y Studio no compilaba: `double cannot be converted to
    String`.
    """
    condicional = _tipo_condicional(meseta, asignacion)
    if condicional is not None:
        return condicional
    demostrado = tipo_de_expresion(str(asignacion.get("expression") or ""))
    if demostrado is not None:
        if demostrado == "Boolean":
            # Las comparaciones del DATA step devuelven 1/0 en SAS, no un booleano de Java.
            return "id_Long"
        if demostrado == "Double" and _solo_enteros(meseta, java):
            # `agg_1 - agg_2` entre dos `Long` da `long`: guardarlo en un `Double` no compila.
            return "id_Long"
        return TIPOS.get(demostrado, "id_String")
    fila, _, nombre = java.partition(".")
    if fila.startswith("row"):
        return meseta.tipo_de(fila, nombre)
    return "id_String"


def _expandir_estrellas(meseta: _Meseta, asignaciones: list[dict]) -> list[dict]:
    """`t.*` del SELECT como una asignación por cada columna de la entrada `t`.

    Si `t` no es una entrada del mapa la asignación se deja tal cual y falla con su motivo.
    """
    expandidas: list[dict] = []
    for asignacion in asignaciones:
        expresion = str(asignacion.get("expression", "")).strip()
        tabla = expresion[:-2].lower().split(".")[-1] if expresion.endswith(".*") else None
        fuente = next((f for f in meseta.fuentes if tabla and f.tabla == tabla), None)
        if fuente is None:
            expandidas.append(asignacion)
            continue
        expandidas += [
            {"target": c.nombre, "expression": f"{tabla}.{c.nombre}", "origin": "columna"}
            for c in fuente.columnas
        ]
    return expandidas


def _salidas(meseta: _Meseta, op: Operator, armado: Armado) -> list[SalidaMap]:
    """Salidas del `tMap`: las asignaciones del `SELECT` y, si hay, el `WHERE` como filtro.

    Un `derive` con `modo: agrega` viene de un DATA step: la fila conserva sus columnas y las
    asignaciones se suman o se reemplazan por nombre. Uno sin la marca viene de un `SELECT` y su
    lista de asignaciones es toda la salida.
    """
    filtro = _filtro(meseta, op, armado)
    derivaciones = _pasos(op, "derive")
    selecciones = _pasos(op, "select")
    asignaciones = derivaciones[-1].get("assignments", []) if derivaciones else []
    asignaciones = _expandir_estrellas(meseta, asignaciones)
    agrega = bool(derivaciones) and derivaciones[-1].get("modo") == "agrega"
    columnas: list[Columna] = []
    expresiones: dict[str, str] = {}
    if agrega:
        principal = meseta.fuentes[0]
        columnas = list(principal.columnas)
        expresiones = {c.nombre: f"{PRINCIPAL}.{c.nombre}" for c in principal.columnas}
    elif not asignaciones:
        principal = meseta.fuentes[0]
        columnas = list(principal.columnas)
        expresiones = {c.nombre: f"{PRINCIPAL}.{c.nombre}" for c in principal.columnas}
        if _pasos(op, "join"):
            _banderas(meseta, op, columnas, expresiones)
            # `SELECT *` sobre un cruce trae las columnas de todas las tablas; si un nombre se
            # repite, queda el de la primera.
            for indice, fuente in enumerate(meseta.fuentes[1:], start=1):
                for columna in fuente.columnas:
                    if columna.nombre.lower() not in {c.nombre.lower() for c in columnas}:
                        columnas.append(columna)
                        expresiones[columna.nombre] = f"{meseta.fila(indice)}.{columna.nombre}"
    tipos_previos = {c.nombre: c.tipo for c in columnas}
    largos = _longitudes_declaradas(op)
    for asignacion in asignaciones:
        destino = str(asignacion.get("target", "")).strip()
        if not destino or not str(asignacion.get("expression", "")).strip():
            continue
        previas = {
            nombre: (java_previa, tipos_previos[nombre])
            for nombre, java_previa in expresiones.items()
        }
        java, _ = _valor(meseta, asignacion, armado, op, previas)
        if java is None:
            continue
        demostrado = tipo_de_expresion(str(asignacion.get("expression") or ""))
        if demostrado == "Boolean":
            java = f"Long.valueOf(({java}) ? 1L : 0L)"
        tipo = _tipo_de_salida(meseta, java, asignacion)
        tipos_previos[destino] = tipo
        longitud = largos.get(destino.lower(), -1)
        if destino in expresiones:
            columnas = [
                Columna(destino, tipo, longitud=longitud) if c.nombre == destino else c
                for c in columnas
            ]
        else:
            columnas.append(Columna(destino, tipo, longitud=longitud))
        expresiones[destino] = java
    for seleccion in selecciones:
        nombres = {str(nombre).lower() for nombre in seleccion.get("names") or []}
        modo = str(seleccion.get("mode") or "").lower()
        if modo == "keep":
            columnas = [columna for columna in columnas if columna.nombre.lower() in nombres]
        elif modo == "drop":
            columnas = [columna for columna in columnas if columna.nombre.lower() not in nombres]
        else:
            armado.pendientes.append(
                PendienteMigracion(
                    NO_SOPORTADO, f"modo de selección '{modo}' sin traducir", _linea(op)
                )
            )
            return []
        expresiones = {columna.nombre: expresiones[columna.nombre] for columna in columnas}
    renombrados = _pasos(op, "rename")
    if renombrados:
        cambios = {
            str(origen).lower(): str(destino).lower()
            for origen, destino in renombrados[-1].get("pairs") or []
        }
        columnas = [
            Columna(
                cambios.get(columna.nombre.lower(), columna.nombre),
                columna.tipo,
                longitud=columna.longitud,
            )
            for columna in columnas
        ]
        expresiones = {
            cambios.get(nombre.lower(), nombre): expresion
            for nombre, expresion in expresiones.items()
        }
    if not columnas:
        return []
    return [SalidaMap("out1", columnas, expresiones, filtro=filtro)]


def _banderas_booleanas(meseta: _Meseta, op: Operator) -> dict[str, str]:
    """Nombre de cada bandera `IN=` -> expresión Java booleana de «la tabla aportó fila»."""
    unir = _pasos(op, "join")
    llaves = [str(k) for k in (unir[-1].get("by") or [])] if unir else []
    resultado: dict[str, str] = {}
    for indice, fuente in enumerate(meseta.fuentes):
        if not fuente.bandera:
            continue
        if indice == 0 or not llaves:
            resultado[fuente.bandera.lower()] = "true"
        else:
            llave = f"{meseta.fila(indice)}.{meseta.nombre_real(indice, llaves[0])}"
            resultado[fuente.bandera.lower()] = f"{llave} != null"
    return resultado


def _banderas(meseta: _Meseta, op: Operator, columnas: list[Columna], expresiones: dict) -> None:
    """Las banderas `IN=` de un `MERGE`: 1 si la tabla aportó una fila, 0 si no.

    La principal siempre aporta (el cruce parte de ella); una tabla de consulta aportó si su llave
    no es nula tras el cruce izquierdo.
    """
    unir = _pasos(op, "join")
    llaves = [str(k) for k in (unir[-1].get("by") or [])] if unir else []
    for indice, fuente in enumerate(meseta.fuentes):
        if not fuente.bandera or fuente.bandera.lower() in {c.nombre.lower() for c in columnas}:
            continue
        columnas.append(Columna(fuente.bandera, "id_Long"))
        if indice == 0 or not llaves:
            expresiones[fuente.bandera] = "1L"
        else:
            llave = f"{meseta.fila(indice)}.{meseta.nombre_real(indice, llaves[0])}"
            expresiones[fuente.bandera] = f"({llave} != null ? 1L : 0L)"


def construir(
    op: Operator,
    fuentes: list[Fuente],
    unico: str,
    x: int,
    y: int,
    ruta_java: str | None = None,
) -> Armado:
    """`tMap` del operador `map` con sus entradas, llaves, expresiones y filtro."""
    armado = Armado()
    if not fuentes:
        armado.pendientes.append(
            PendienteMigracion(
                NO_SOPORTADO, "el mapa no tiene ninguna entrada demostrable", _linea(op)
            )
        )
        return armado
    uniones = _pasos(op, "join")
    if not _tipos_soportados(uniones, armado, op):
        return armado
    # De qué tabla parte el mapa lo dice el primer cruce que nombra su `FROM`.
    con_origen = [u for u in uniones if u.get("sources")]
    principal = _principal(fuentes, (con_origen or uniones or [None])[0])
    ordenadas = [fuentes[principal], *(f for i, f in enumerate(fuentes) if i != principal)]
    meseta = _Meseta(ordenadas)
    armado.entradas = {fuente.origen: meseta.fila(i) for i, fuente in enumerate(ordenadas)}
    for paso in ("aggregate",):
        if _pasos(op, paso):
            armado.pendientes.append(
                PendienteMigracion(
                    NO_SOPORTADO, f"el paso '{paso}' no tiene equivalente en el tMap", _linea(op)
                )
            )
    entradas = _entradas(meseta, uniones, armado, op)
    salidas = _salidas(meseta, op, armado)
    if not salidas:
        armado.pendientes.append(
            PendienteMigracion(
                NO_SOPORTADO, "el mapa no produce ninguna columna demostrable", _linea(op)
            )
        )
        return armado
    armado.columnas = list(salidas[0].columnas)
    try:
        armado.nodo = tmap(unico, entradas, salidas, x, y, ruta_java)
    except Exception as error:  # noqa: BLE001 — un mapa roto no se lleva el resto del Job
        armado.pendientes.append(
            PendienteMigracion(
                FALLO, f"tMap: {type(error).__name__}: {error}", _linea(op)
            )
        )
    return armado


__all__ = ["FALLO", "NO_SOPORTADO", "PRINCIPAL", "Armado", "Fuente", "construir"]
