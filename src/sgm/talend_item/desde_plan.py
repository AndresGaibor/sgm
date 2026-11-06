"""Emisor de Jobs de Talend a partir del plan de la IR: lectura, `tMap` y escritura.

El plan ya trae el grafo con sus operadores, los esquemas de las tablas de entrada (MG-P1-02) y el
componente candidato de cada operador (pasada 10). Aquí no se decide nada de eso otra vez: se arma
el Job, se conecta en el orden del flujo y se anota lo que no se pudo demostrar.

Dos reglas gobiernan el archivo, y son las del pedido del usuario:

* **Nada se pierde.** Un operador que no se traduce no desaparece: queda en `pendientes` con su
  código y su línea del SAS. Y un operador que lanza una excepción tampoco tumba la migración: se
  captura, se anota como `P-FALLO-INTERNO` y los demás se traducen igual.
* **Nada se inventa.** Sin esquema, sin separador o sin llave demostrable, hay pendiente.

Un `read` o un `write` que solo nombran un conjunto ya producido por otro operador del mismo Job no
son un paso: son el nombre que el SAS le da a ese flujo. Se pliegan sobre el operador que lo produce
en vez de generar un nodo vacío o un pendiente que no existe.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace

from sgm.ir.desplegar import plan_desplegado
from sgm.ir.models import Column, Operator, Plan
from sgm.migrar.esquemas import PendienteMigracion
from sgm.talend_item.conexiones import lookup
from sgm.talend_item.desde_plan_agregado import nodo_agregado
from sgm.talend_item.desde_plan_contextos import (
    contextos_de_plan,
    reemplazar_rutas,
    rutas_de_plan,
)
from sgm.talend_item.desde_plan_map import FALLO, Fuente, construir
from sgm.talend_item.desde_plan_nodos import nodo_escritura, nodo_lectura
from sgm.talend_item.desde_plan_orden import nodo_orden, nodo_unicos
from sgm.talend_item.desde_plan_union import nodo_union
from sgm.talend_item.modelo import Columna, Conexion, Fila, Job, Nodo, Tabla

CONFIG_RESUELTA = "P-CONFIGURACION-RESUELTA"
PASO = 192  # separación de la rejilla del lienzo, en píxeles
SIN_SOPORTE = "P-OPERADOR-SIN-SOPORTE"
# Operadores que el emisor sabe traducir a un componente del Job.
CON_NODO = frozenset(
    {"read_file", "write_file", "map", "filter", "derive", "select", "rename", "join"}
)


@dataclass
class ResultadoMigracion:
    """Lo que sale de migrar un plan: los Jobs, lo pendiente y la traza a las líneas del SAS."""

    jobs: list[Job] = field(default_factory=list)
    pendientes: list[PendienteMigracion] = field(default_factory=list)
    traza: dict[str, list[int]] = field(default_factory=dict)
    # Ids de los operadores del plan que se recorrieron. Todos tienen que estar: uno que no se
    # visitó no dejó nodo ni pendiente, y se perdió sin que nadie lo diga.
    visitados: set[str] = field(default_factory=set)
    # Ids de los `read`/`write` que solo nombran un flujo ya producido y se plegaron sobre él. No
    # son pasos y no tienen línea propia en la traza: su flujo lo representa el operador que los
    # produjo, y eso es lo que la aceptación del corpus comprueba.
    plegados: set[str] = field(default_factory=set)


def _linea(op: Operator) -> int | None:
    return op.evidence[0].line_start if op.evidence else None


def _tabla(dataset: str) -> str:
    """`WORK.ventas` a `ventas`: el `tMap` no conoce la librería."""
    return dataset.strip().lower().split(".")[-1]


def _produce(op: Operator) -> list[str]:
    producen = ("read_file", "map", "filter", "derive", "select", "rename", "join")
    if op.kind in (*producen, "sort", "dedup", "aggregate", "union"):
        return [str(d).lower() for d in op.params.get("outputs", [])]
    return []


def _como_paso(op: Operator) -> Operator:
    """Un `filter`, `derive` o `join` suelto, visto como el único paso de un `map`.

    El `tMap` los trata igual que los pasos de dentro de un `map`; así hay un solo camino de código
    para las dos formas y no dos traducciones que se pueden separar con el tiempo.
    """
    if op.kind == "map":
        return op
    paso = {"kind": op.kind, "params": op.params, "signature": op.signature}
    return replace(op, kind="map", params={"steps": [paso], **op.params})


def _renombrar(nodo: Nodo, unico: str) -> list[Fila | Tabla]:
    """Parámetros del nodo con su `UNIQUE_NAME` cambiado: una copia con el nombre viejo no sirve."""
    parametros: list[Fila | Tabla] = []
    for parametro in nodo.parametros:
        if isinstance(parametro, tuple) and parametro[1] == "UNIQUE_NAME":
            parametro = (parametro[0], parametro[1], unico, parametro[3])
        parametros.append(parametro)
    return parametros


class _Job:
    """Armado de un Job: un recorrido hacia adelante sobre los operadores de sus subjobs."""

    def __init__(
        self, plan: Plan, esquemas: dict[str, list[Column]], ruta_java: str | None
    ) -> None:
        self.plan = plan
        self.esquemas = esquemas
        self.ruta_java = ruta_java
        self.nodos: list[Nodo] = []
        self.conexiones: list[Conexion] = []
        self.pendientes: list[PendienteMigracion] = []
        self.traza: dict[str, list[int]] = {}
        self.visitados: set[str] = set()
        self.plegados: set[str] = set()
        self._usados: dict[str, int] = {}
        self._nodo: dict[str, Nodo] = {}  # id de operador -> nodo del Job
        self._instancias: dict[tuple[str, str | None], Nodo] = {}  # (operador, consumidor) -> nodo
        self._alias: dict[str, str] = {}  # id de operador plegado -> id que lo representa
        self._salida: dict[str, list[Columna]] = {}  # id de operador -> columnas que entrega
        self._tabla_de: dict[str, str] = {}  # UNIQUE_NAME del nodo -> tabla que entrega
        self._salidas_map: dict[str, str] = {}  # id de operador -> nombre de su salida
        self._entradas_map: dict[str, dict[str, str]] = {}  # id de operador -> origen -> fila
        self._uniones: dict[str, list[str]] = {}  # `union` -> sus entradas, en orden
        self._pasos: set[str] = set()  # operadores `sort` y `dedup` que sí dejaron nodo
        self._conector_de: dict[str, str] = {}  # UNIQUE_NAME -> conector de su salida principal
        self._productor = self._productores()
        self.rutas = rutas_de_plan(plan)

    # -- grafo -------------------------------------------------------------------------------
    def _productores(self) -> dict[str, str]:
        """Conjunto de datos -> operador que lo produce, dentro de este Job."""
        productores: dict[str, str] = {}
        for op in self.plan.graph.operators():
            for dataset in _produce(op):
                productores.setdefault(dataset, op.id)
        return productores

    def _resolver(self, op_id: str, visto: set[str] | None = None) -> str | None:
        """Operador que de verdad representa a este, siguiendo los plegados.

        Un `read` o un `write` que solo nombran un conjunto ya producido en el Job no son un paso:
        son el nombre que el SAS le da a ese flujo, y se pliegan sobre el operador que lo produce.
        """
        visto = set() if visto is None else visto
        if op_id in visto:
            return None
        visto.add(op_id)
        if op_id in self._nodo:
            return op_id
        if op_id in self._alias:
            return self._resolver(self._alias[op_id], visto)
        op = self.plan.graph.operator(op_id)
        if op.kind == "read":
            productor = self._productor.get(str(op.params.get("dataset", "")).lower())
            if productor and productor != op_id:
                self._alias[op_id] = productor
                return self._plegar(op_id, productor, visto)
        elif op.kind == "write":
            previos = self.plan.graph.predecessors(op_id)
            if previos:
                self._alias[op_id] = previos[0]
                return self._plegar(op_id, previos[0], visto)
        return None

    def _plegar(self, op_id: str, representante: str, visto: set[str]) -> str | None:
        """Resuelve el plegado y lo anota solo si llegó a un operador que tiene nodo."""
        resuelto = self._resolver(representante, visto)
        if resuelto is not None:
            self.plegados.add(op_id)
        return resuelto

    def _unico(self, componente: str) -> str:
        """UNIQUE_NAME con el ordinal del componente en el Job, como los escribe Studio."""
        self._usados[componente] = self._usados.get(componente, 0) + 1
        return f"{componente}_{self._usados[componente]}"

    def _consumidores(self, op_id: str) -> list[str]:
        """Operadores que consumen el flujo de este, atravesando los `read` que solo lo renombran.

        Una tabla que el SAS lee dos veces —dos `PROC SQL` sobre el mismo `WORK.x`— tiene un solo
        `read_file` en el plan, pero en Talend no puede salir dos veces del mismo componente: cada
        salida de un nodo tiene un nombre y un dueño. Se emite un nodo por consumidor, que es lo que
        hace una persona al copiar el componente.
        """
        destinos: list[str] = []
        por_ver = [op_id]
        vistos = {op_id}
        while por_ver:
            actual = por_ver.pop(0)
            for arista in self.plan.graph.edges():
                if arista.src != actual or arista.dst in vistos:
                    continue
                siguiente = self.plan.graph.operator(arista.dst)
                vistos.add(siguiente.id)
                dataset = str(siguiente.params.get("dataset", "")).lower()
                if siguiente.kind == "read" and self._productor.get(dataset) == op_id:
                    por_ver.append(siguiente.id)
                elif siguiente.kind != "read":
                    destinos.append(siguiente.id)
        return destinos

    def _instancia(self, op_id: str, consumidor: str | None) -> Nodo | None:
        """Nodo que representa al operador cuando lo consume `consumidor`."""
        return self._instancias.get((op_id, consumidor)) or self._nodo.get(op_id)


    # -- piezas ------------------------------------------------------------------------------
    def _sin_soporte(self, op: Operator) -> None:
        sentencia = str(op.params.get("statement") or "").strip()
        if op.params.get("reason") == "CONFIGURACION" and sentencia.lower().startswith("%let"):
            # La macro variable ya está sustituida en el resto del programa: no se pierde nada, pero
            # tampoco queda una variable de contexto que el Job pueda cambiar sin recompilar.
            motivo = f"{sentencia}: el valor se sustituyó al migrar; no hay variable de contexto"
            self.pendientes.append(PendienteMigracion(CONFIG_RESUELTA, motivo, _linea(op)))
            return
        motivo = op.notes[0] if op.notes else f"el operador '{op.kind}' no tiene componente"
        self.pendientes.append(PendienteMigracion(SIN_SOPORTE, motivo, _linea(op)))

    def _lectura(self, op: Operator, x: int) -> None:
        tabla = str((op.params.get("outputs") or ["WORK.sin_nombre"])[0]).lower()
        esquema = self.esquemas.get(tabla, [])
        if not esquema:
            self.pendientes.append(
                PendienteMigracion(
                    "P-ESQUEMA-VACIO",
                    f"{tabla}: el SAS no demuestra ninguna columna para esta lectura",
                    _linea(op),
                )
            )
        unico = self._unico(str((op.component or {}).get("name") or "tFileInputDelimited"))
        resultado = nodo_lectura(op, esquema, unico, x, 0, self.ruta_java)
        self.pendientes += resultado.pendientes
        if resultado.nodo is None:
            return
        for posicion, consumidor in enumerate(self._consumidores(op.id) or [None]):
            nodo = resultado.nodo
            if posicion:
                otro = self._unico(nodo.componente)
                nodo = replace(
                    nodo, unico=otro, y=96 * posicion, parametros=_renombrar(nodo, otro)
                )
            self._registrar(op, nodo, resultado.columnas, _tabla(tabla), consumidor)

    def _escritura(self, op: Operator, x: int) -> None:
        consumido = str((op.params.get("inputs") or [""])[0]).lower()
        columnas: list[Columna] = []
        productor = self._productor.get(consumido)
        if productor:
            # El productor puede ser un nodo, un operador plegado o uno que falló: su esquema de
            # salida se conoce igual, y es lo que la escritura necesita.
            representante = self._resolver(productor)
            columnas = self._salida.get(representante or productor, [])
        if not columnas:
            self.pendientes.append(
                PendienteMigracion(
                    "P-ESCRITURA-SIN-COLUMNAS",
                    f"{consumido}: no hay columnas demostradas para escribir",
                    _linea(op),
                )
            )
            return
        unico = self._unico(str((op.component or {}).get("name") or "tFileOutputDelimited"))
        resultado = nodo_escritura(op, columnas, unico, x, 0, self.ruta_java)
        self.pendientes += resultado.pendientes
        if resultado.nodo is None:
            return
        self._registrar(op, resultado.nodo, columnas, _tabla(consumido))

    def _fuentes(self, op: Operator) -> list[Fuente]:
        fuentes: list[Fuente] = []
        vistos: set[str] = set()
        previos = self.plan.graph.predecessors(op.id)
        # Un cruce intermedio ya consume sus tablas: la arista directa de una de ellas a este
        # operador es redundante y la haría pasar por un lookup sin llave.
        cruces = [p for p in previos if self.plan.graph.operator(p).kind == "join"]
        redundantes = {p for c in cruces for p in self.plan.graph.predecessors(c)}
        for previo in previos:
            if previo in redundantes:
                continue
            representante = self._resolver(previo)
            if representante is None or representante in vistos:
                continue
            vistos.add(representante)
            nodo = self._instancia(representante, op.id)
            fuentes.append(
                Fuente(
                    representante,
                    self._tabla_de.get(nodo.unico, "") if nodo else "",
                    self._salida[representante],
                    compuesta=previo in cruces,
                    bandera=self.plan.graph.operator(previo).params.get("in") or None,
                )
            )
        return fuentes

    def _mapa(self, op: Operator, x: int) -> None:
        fuentes = self._fuentes(op)
        unico = self._unico("tMap")
        armado = construir(_como_paso(op), fuentes, unico, x, 0, self.ruta_java)
        self.pendientes += armado.pendientes
        # El esquema de salida lo demuestra el SELECT, no el nodo: se guarda aunque el tMap falle,
        # para que la escritura de detrás sepa qué columnas tiene que escribir.
        self._salida[op.id] = list(armado.columnas)
        if armado.nodo is None:
            return
        tabla = _tabla(str((op.params.get("outputs") or ["WORK.sin_nombre"])[0]))
        self._registrar(op, armado.nodo, armado.columnas, tabla)
        self._entradas_map[op.id] = armado.entradas
        self._salidas_map[op.id] = (
            armado.nodo.metadatas[0].nombre if armado.nodo.metadatas else "out1"
        )

    def _orden(self, op: Operator, x: int) -> None:
        """`sort` a `tSortRow` y `dedup` a `tUniqRow`: pasan el esquema de su entrada tal cual."""
        fuentes = self._fuentes(op)
        if len(fuentes) != 1:
            motivo = f"el operador '{op.kind}' espera una sola entrada y tiene {len(fuentes)}"
            self.pendientes.append(PendienteMigracion(SIN_SOPORTE, motivo, _linea(op)))
            return
        fuente = fuentes[0]
        if op.kind == "sort":
            unico = self._unico("tSortRow")
            resultado = nodo_orden(
                op, fuente.columnas, unico, x, _linea(op), self.ruta_java
            )
        else:
            unico = self._unico("tUniqRow")
            resultado = nodo_unicos(
                op, fuente.columnas, unico, fuente.origen, x, _linea(op), self.ruta_java
            )
        self.pendientes += resultado.pendientes
        # Sin nodo no hay de dónde escribir (ver `_agregado`): la escritura queda pendiente.
        self._salida[op.id] = []
        if resultado.nodo is None:
            return
        tabla = _tabla(str((op.params.get("outputs") or ["WORK.sin_nombre"])[0]))
        self._registrar(op, resultado.nodo, fuente.columnas, tabla)
        self._pasos.add(op.id)
        if op.kind == "dedup":
            self._conector_de[resultado.nodo.unico] = "UNIQUE"

    def _agregado(self, op: Operator, x: int) -> None:
        """`aggregate` a `tAggregateRow`: sale con las columnas de grupo y los agregados."""
        fuentes = self._fuentes(op)
        if len(fuentes) != 1:
            motivo = f"el operador '{op.kind}' espera una sola entrada y tiene {len(fuentes)}"
            self.pendientes.append(PendienteMigracion(SIN_SOPORTE, motivo, _linea(op)))
            return
        unico = self._unico("tAggregateRow")
        resultado = nodo_agregado(op, fuentes[0].columnas, unico, x, _linea(op), self.ruta_java)
        self.pendientes += resultado.pendientes
        # Sin nodo no hay de dónde escribir: una escritura detrás quedaría sin entrada y el Job
        # sería inválido. Sin columnas, la escritura lo dice como pendiente y no se emite.
        self._salida[op.id] = []
        if resultado.nodo is None:
            return
        tabla = _tabla(str((op.params.get("outputs") or ["WORK.sin_nombre"])[0]))
        self._registrar(op, resultado.nodo, resultado.columnas, tabla)
        self._pasos.add(op.id)

    def _union(self, op: Operator, x: int) -> None:
        """`union` a `tUnite`: apila entradas con las mismas columnas."""
        fuentes = self._fuentes(op)
        unico = self._unico("tUnite")
        resultado = nodo_union(
            op, [f.columnas for f in fuentes], unico, x, _linea(op), self.ruta_java
        )
        self.pendientes += resultado.pendientes
        self._salida[op.id] = []
        if resultado.nodo is None:
            return
        tabla = _tabla(str((op.params.get("outputs") or ["WORK.sin_nombre"])[0]))
        self._registrar(op, resultado.nodo, fuentes[0].columnas, tabla)
        self._pasos.add(op.id)
        self._uniones[op.id] = [f.origen for f in fuentes]

    def _registrar(
        self,
        op: Operator,
        nodo: Nodo,
        salida: list[Columna],
        tabla: str,
        consumidor: str | None = None,
    ) -> None:
        self.nodos.append(nodo)
        self._nodo.setdefault(op.id, nodo)
        self._instancias[(op.id, consumidor)] = nodo
        self._salida[op.id] = list(salida)
        self._tabla_de[nodo.unico] = tabla
        evidencia = op.evidence[0] if op.evidence else None
        if evidencia is not None:
            self.traza[nodo.unico] = list(range(evidencia.line_start, evidencia.line_end + 1))

    # -- conexiones --------------------------------------------------------------------------
    def _conectar(self) -> None:
        vistas: set[tuple[str, str, str]] = set()
        for arista in self.plan.graph.edges():
            desde, hasta = self._resolver(arista.src), self._resolver(arista.dst)
            if desde is None or hasta is None or desde == hasta:
                continue
            nombre = self._nombre(desde, hasta)
            if nombre is None:
                continue
            nodo_origen = self._instancia(desde, hasta)
            nodo_destino = self._nodo.get(hasta)
            if nodo_origen is None or nodo_destino is None:
                continue
            origen, destino = nodo_origen.unico, nodo_destino.unico
            clave = (origen, destino, nombre)
            if clave in vistas:
                continue
            vistas.add(clave)
            if hasta in self._entradas_map and nombre != "row1":
                # Las entradas de búsqueda de un tMap van por LOOKUP (`lineStyle` 8), no por FLOW.
                self.conexiones.append(lookup(origen, destino, nombre))
            else:
                conector = self._conector_de.get(origen, "FLOW")
                self.conexiones.append(Conexion(origen, destino, nombre, conector=conector))

    def _nombre(self, desde: str, hasta: str) -> str | None:
        """Nombre de la conexión: la entrada que el `tMap` espera, o la salida que produce.

        `None` cuando el `tMap` de destino no tiene esa entrada: la arista existe en el plan pero no
        hay a qué fila del mapa corresponde, y una conexión con el nombre equivocado es peor que no
        tenerla.
        """
        if hasta in self._uniones:
            # `tUnite` recibe varias filas a la vez: cada entrada con su nombre.
            return f"{self._nodo[hasta].unico}_in{self._uniones[hasta].index(desde) + 1}"
        if hasta in self._pasos:
            # El nombre de una conexión es único en el Job, y `row1` ya es el de la fila principal
            # del `tMap` que viene detrás: la entrada de un orden o de un DISTINCT lleva el suyo.
            return f"{self._nodo[hasta].unico}_in"
        if hasta in self._entradas_map:
            return self._entradas_map[hasta].get(desde)
        if desde in self._pasos:
            return f"{self._nodo[desde].unico}_out"
        if desde in self._salidas_map:
            return self._salidas_map[desde]
        return "row1"

    # -- recorrido ---------------------------------------------------------------------------
    def armar(self, job) -> Job:
        orden = [
            op_id for subjob in job.subjobs for op_id in subjob
        ] or self.plan.graph.topological()
        # Un operador del plan que no quedó en ningún subjob —un `PROC REG`, una salida que el
        # análisis no agrupó— no se recorrería nunca y se perdería sin dejar rastro. Se añade al
        # final para que quede en `pendientes` con su línea: es la mitad de "nada se pierde".
        vistos = set(orden)
        orden += [op_id for op_id in self.plan.graph.topological() if op_id not in vistos]
        for posicion, op_id in enumerate(orden):
            if op_id in self._nodo:
                continue
            op = self.plan.graph.operator(op_id)
            x = PASO * posicion
            try:
                self._traducir(op, x)
            except Exception as error:  # noqa: BLE001 — un operador roto no tumba la migración
                self.pendientes.append(
                    PendienteMigracion(
                        FALLO,
                        f"{op.kind}: {type(error).__name__}: {error}",
                        _linea(op),
                    )
                )
            self.visitados.add(op_id)
        self._conectar()
        reemplazar_rutas(self.nodos, self.rutas)
        return Job(
            job.name,
            nodos=self.nodos,
            conexiones=self.conexiones,
            contextos=contextos_de_plan(self.plan),
        )

    def _traducir(self, op: Operator, x: int) -> None:
        if op.status == "hueco" or op.kind == "unsupported":
            self._sin_soporte(op)
            return
        if op.kind in ("read", "write"):
            # Si se pliega sobre otro nodo, el conjunto ya está en el flujo y no hay nada que hacer.
            if self._resolver(op.id) is None:
                self._sin_soporte(op)
            return
        componente = str((op.component or {}).get("name") or "none")
        if op.kind == "read_file":
            self._lectura(op, x)
        elif op.kind == "write_file":
            self._escritura(op, x)
        elif op.kind == "map":
            self._mapa(op, x)
        elif op.kind in ("sort", "dedup"):
            self._orden(op, x)
        elif op.kind == "aggregate":
            self._agregado(op, x)
        elif op.kind == "union":
            self._union(op, x)
        elif op.kind in CON_NODO:
            # Las transformaciones sueltas son un `tMap` de una sola entrada.
            self._mapa(op, x)
        elif componente == "none":
            self._sin_soporte(op)
        else:
            self.pendientes.append(
                PendienteMigracion(
                    SIN_SOPORTE,
                    f"el operador '{op.kind}' todavía no tiene emisor para {componente}",
                    _linea(op),
                )
            )


def plan_a_jobs(
    plan: Plan,
    esquemas: dict[str, list[Column]],
    ruta_java: str | None = None,
) -> ResultadoMigracion:
    """Un Job de Talend por cada Job del plan, con sus nodos, conexiones y pendientes."""
    resultado = ResultadoMigracion()
    # Cada instancia de una plantilla se escribe en línea hasta que haya Jobs hijos (`tRunJob`).
    plan, desplegados = plan_desplegado(plan)
    resultado.visitados |= desplegados
    for job in plan.jobs:
        armado = _Job(plan, esquemas, ruta_java)
        resultado.jobs.append(armado.armar(job))
        resultado.pendientes += armado.pendientes
        resultado.traza.update(armado.traza)
        resultado.visitados |= armado.visitados
        resultado.plegados |= armado.plegados
    return resultado


__all__ = ["ResultadoMigracion", "plan_a_jobs"]
