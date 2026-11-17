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

import re
from dataclasses import dataclass, field, replace

from sgm.formatos.informat_archivo import informat_numerico_soportado
from sgm.formatos.informat_fecha import informat_fecha_soportado
from sgm.ir.desplegar import plan_desplegado
from sgm.ir.models import Column, Operator, Plan
from sgm.ir.types_code import informat_type
from sgm.migrar.esquemas import PendienteMigracion
from sgm.optimizar import Decision, optimizar
from sgm.talend_item.componentes import log_row
from sgm.talend_item.conexiones import lookup
from sgm.talend_item.desde_plan_agregado import nodo_agregado
from sgm.talend_item.desde_plan_conexion import parametros_conexion
from sgm.talend_item.desde_plan_conexiones import conexiones_de_plan
from sgm.talend_item.desde_plan_contextos import (
    contextos_de_plan,
    reemplazar_rutas,
    rutas_de_plan,
)
from sgm.talend_item.desde_plan_lag import nodo_lag
from sgm.talend_item.desde_plan_map import FALLO, Fuente, construir
from sgm.talend_item.desde_plan_nodos import nodo_escritura, nodo_lectura
from sgm.talend_item.desde_plan_orden import nodo_orden, nodo_unicos
from sgm.talend_item.desde_plan_paso_directo import (
    esquema_paso_directo,
    nodo_paso_directo,
)
from sgm.talend_item.desde_plan_union import nodo_union
from sgm.talend_item.jobs_diseno import java
from sgm.talend_item.jobs_parciales import CODIGO_DETALLE, tiene_hueco
from sgm.talend_item.modelo import Columna, Conexion, Fila, Job, Nodo, Tabla
from sgm.talend_item.plantillas import nodo_desde_plantilla

CONFIG_RESUELTA = "P-CONFIGURACION-RESUELTA"
PASO = 192  # separación de la rejilla del lienzo, en píxeles
SIN_SOPORTE = "P-OPERADOR-SIN-SOPORTE"
PIVOTAR = "P-OPERADOR-PIVOTAR"  # PROC TRANSPOSE: el pivote sin componente (B-8)
RECONVERGE = "P-REPARTO-RECONVERGE"
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
    # Cambios de diseño que hizo el optimizador, para `decisiones-tomadas.md`.
    decisiones: list[Decision] = field(default_factory=list)


def _linea(op: Operator) -> int | None:
    return op.evidence[0].line_start if op.evidence else None


def _tabla(dataset: str) -> str:
    """`WORK.ventas` a `ventas`: el `tMap` no conoce la librería."""
    return dataset.strip().lower().split(".")[-1]


def _produce(op: Operator) -> list[str]:
    producen = ("read_file", "map", "filter", "derive", "select", "rename", "join", "stateful_row")
    if op.kind in (*producen, "sort", "dedup", "aggregate", "union"):
        return [str(d).lower() for d in op.params.get("outputs", [])]
    if op.kind == "read" and (op.placement or "").startswith("db:"):
        return [str(d).lower() for d in op.params.get("outputs", [])]
    if op.kind == "split":
        destinos = op.params.get("targets") or [op.params.get("target")]
        return [str(destino).lower() for destino in destinos if destino]
    return []


def _libname_registrado(statement: str) -> bool:
    """Distingue la config estática de motor/CLEAR de una biblioteca de ruta."""
    limpio = statement.strip().rstrip(";").strip()
    if re.match(r"(?is)^libname\s+(?:_all_\s+)?(?:[A-Za-z_]\w*\s+)?clear$", limpio):
        return True
    declaracion = re.match(r"(?is)^libname\s+[A-Za-z_]\w*\s+(.+)$", limpio)
    if not declaracion:
        return False
    valor = declaracion.group(1).lstrip()
    return valor.startswith(("'", '"')) or bool(re.match(r"[A-Za-z_]\w*(?:\s|$)", valor))


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
        self,
        plan: Plan,
        esquemas: dict[str, list[Column]],
        ruta_java: str | None,
        conexion_en_contexto: bool,
    ) -> None:
        self.plan = plan
        self.esquemas = esquemas
        self.ruta_java = ruta_java
        self._conexion_en_contexto = conexion_en_contexto
        self.nodos: list[Nodo] = []
        self.conexiones: list[Conexion] = []
        self.pendientes: list[PendienteMigracion] = []
        for conexion_sql in conexiones_de_plan(plan):
            if conexion_sql.opciones:
                self.pendientes.append(
                    PendienteMigracion(
                        "P-CONEXION-OPCIONES",
                        f"{conexion_sql.alias}: opciones SAS de conexión requieren revisión y no "
                        f"se aplican al componente: {conexion_sql.opciones}",
                        conexion_sql.linea,
                    )
                )
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
        self._alineados: dict[str, dict[int, str]] = {}  # `union` -> tMap por entrada desalineada
        self.emitidos: set[str] = set()  # operadores de estado con componente (LAG como tJavaRow)
        self.escritura_sin_columnas = False
        self._pasos: set[str] = set()  # operadores `sort` y `dedup` que sí dejaron nodo
        self._conector_de: dict[str, str] = {}  # UNIQUE_NAME -> conector de su salida principal
        self._ramas: dict[str, dict[str, str]] = {}  # `map` con ramas -> consumidor -> salida
        self._principal_de: dict[str, str] = {}  # `map` -> nombre de su fila principal
        self._filas = 0  # filas de entrada que ya usan los `tMap` del Job
        self._salidas_n = 0  # salidas que ya usan los `tMap` del Job
        self._reparto: dict[str, Nodo] = {}  # id de operador -> `tReplicate` de su flujo
        self._turnos: dict[str, list[str]] = {}  # id de operador -> consumidores, en orden
        self.bloquea_emision = False
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
            # La arista dice quién produjo lo que este `read` lee. El nombre solo sirve si no hay
            # arista: un nombre reutilizado (`WORK.temporal`) tiene varios productores.
            previos = self.plan.graph.predecessors(op_id)
            productor = (
                previos[0]
                if previos
                else self._productor.get(str(op.params.get("dataset", "")).lower())
            )
            if productor and productor != op_id:
                self._alias[op_id] = productor
                return self._plegar(op_id, productor, visto)
        elif op.kind == "write":
            previos = self.plan.graph.predecessors(op_id)
            if previos:
                self._alias[op_id] = previos[0]
                resultado = self._plegar(op_id, previos[0], visto)
                productor = self.plan.graph.operator(previos[0])
                if (
                    resultado is None
                    and op.placement == "flow"
                    and productor.kind == "read_file"
                    and productor.params.get("file_format") == "positional"
                ):
                    # La salida WORK de esta lectura solo da nombre al flujo: el pendiente de la
                    # plantilla ya explica por qué no se materializó y no se duplica como genérico.
                    self.plegados.add(op_id)
                return resultado
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
        `read_file` en el plan. Si sus consumidores no se vuelven a juntar, se lee una vez y un
        `tReplicate` reparte las filas (`_repartos`). Si se juntan más abajo —un cruce de la tabla
        consigo misma—, Talend no admite que un flujo repartido vuelva al mismo componente: se
        emite una lectura por consumidor, que es lo que hace una persona al copiar el componente.
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

    def _reconvergen(self, consumidores: list[str]) -> bool:
        """Dos de los consumidores, o lo que sale de ellos, llegan a un mismo operador."""
        alcances = [{c} | self.plan.graph.descendants(c) for c in consumidores]
        return any(
            alcances[i] & alcances[j]
            for i in range(len(alcances))
            for j in range(i + 1, len(alcances))
        )

    def _instancia(self, op_id: str, consumidor: str | None) -> Nodo | None:
        """Nodo que representa al operador cuando lo consume `consumidor`."""
        return self._instancias.get((op_id, consumidor)) or self._nodo.get(op_id)


    # -- piezas ------------------------------------------------------------------------------
    def _sin_soporte(self, op: Operator) -> None:
        sentencia = str(op.params.get("statement") or "").strip()
        if (
            op.params.get("reason") == "CONFIGURACION"
            and sentencia.lower().startswith("libname")
            and _libname_registrado(sentencia)
        ):
            # El libref ya se registró durante el lowering; su lectura o su efecto de ruta
            # generan el pendiente específico cuando un paso los consume. La declaración queda
            # cubierta como configuración aplicada al registro estático, aunque no sea un nodo Job.
            self.plegados.add(op.id)
            return
        if op.params.get("reason") == "CONFIGURACION" and sentencia.lower().startswith("filename"):
            # La asociación se resuelve en preparar_plan; el operador conserva la declaración para
            # trazabilidad, pero no se convierte en un nodo Talend por sí solo.
            self.plegados.add(op.id)
            return
        if op.params.get("reason") == "CONFIGURACION" and sentencia.lower().startswith("%let"):
            # La macro variable ya está sustituida en el resto del programa: no se pierde nada, pero
            # tampoco queda una variable de contexto que el Job pueda cambiar sin recompilar.
            motivo = f"{sentencia}: el valor se sustituyó al migrar; no hay variable de contexto"
            self.pendientes.append(PendienteMigracion(CONFIG_RESUELTA, motivo, _linea(op)))
            return
        motivo = op.notes[0] if op.notes else f"el operador '{op.kind}' no tiene componente"
        # `codigo`: un hueco que ya sabe su pendiente (p. ej. P-ARRAY-FUERA-DE-RANGO) lo declara.
        codigo = (
            op.params.get("pending_code")
            or op.params.get("codigo")
            or CODIGO_DETALLE.get(op.params.get("reason_detail"))
        )
        codigo = codigo or (PIVOTAR if op.kind == "pivot" else SIN_SOPORTE)
        self.pendientes.append(PendienteMigracion(codigo, motivo, _linea(op)))

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
        informats = {
            str(nombre).casefold(): str(informat)
            for nombre, informat in (op.params.get("input_informats") or {}).items()
        }
        numericos = {
            nombre: informat
            for nombre, informat in informats.items()
            if informat_numerico_soportado(informat)
        }
        fechas = {
            nombre: informat
            for nombre, informat in informats.items()
            if informat_fecha_soportado(informat)
        }
        no_soportados = [
            (nombre, informat)
            for nombre, informat in informats.items()
            if not (tipo := informat_type(informat))
            or (tipo.type not in {"String", "Double", "BigDecimal", "Date"})
            or (tipo.type in {"Double", "BigDecimal"} and not informat_numerico_soportado(informat))
            or (tipo.type == "Date" and not informat_fecha_soportado(informat))
        ]
        if no_soportados:
            self.pendientes.append(
                PendienteMigracion(
                    "P-INFORMAT-SIN-SOPORTE",
                    f"{tabla}: INPUT contiene informats sin conversión verificada: "
                    + ", ".join(f"{nombre}={informat}" for nombre, informat in no_soportados),
                    _linea(op),
                )
            )
            self.bloquea_emision = True
            return

        esquema_lector = [
            replace(columna, type="String")
            if columna.name.casefold() in numericos or columna.name.casefold() in fechas
            else columna
            for columna in esquema
        ]
        unico = self._unico(str((op.component or {}).get("name") or "tFileInputDelimited"))
        resultado = nodo_lectura(op, esquema_lector, unico, x, 0, self.ruta_java)
        self.pendientes += resultado.pendientes
        if resultado.nodo is None:
            if "infile_statement" in op.params or "input_statement" in op.params or any(
                pendiente.codigo
                in {
                    "P-GUESSINGROWS",
                    "P-DATAROW-DINAMICO",
                    "P-DATAROW-INVALIDO",
                    "P-DATAROW-EXCEL-SIN-SOPORTE",
                    "P-INFILE-FLOWOVER",
                    "P-INFILE-TRUNCOVER-LISTA",
                }
                for pendiente in resultado.pendientes
            ):
                # Sin tipos demostrados o fila de inicio válida, los nodos posteriores serían un
                # fragmento ejecutable sin la entrada que declara PROC IMPORT.
                self.bloquea_emision = True
            return
        consumidores = self._consumidores(op.id)
        copias = consumidores if self._reconvergen(consumidores) else [None]
        conversiones = numericos | fechas
        if conversiones:
            if len(copias or [None]) > 1:
                self.pendientes.append(
                    PendienteMigracion(
                        "P-INFORMAT-REPARTO-SIN-SOPORTE",
                        f"{tabla}: la lectura con conversiones de informats tiene ramas que "
                        "reconvergen; se requiere materializar la salida antes de continuar.",
                        _linea(op),
                    )
                )
                self.bloquea_emision = True
                return
            self._registrar(op, resultado.nodo, resultado.columnas, _tabla(tabla))
            asignaciones = [
                {
                    "target": columna.name,
                    "expression": f"input({columna.name}, {conversiones[columna.name.casefold()]})",
                }
                for columna in esquema
                    if columna.name.casefold() in conversiones
            ]
            op_conversion = replace(
                op,
                kind="map",
                params={
                    "outputs": [tabla],
                    "steps": [
                        {
                            "kind": "derive",
                            "params": {"modo": "agrega", "assignments": asignaciones},
                        }
                    ],
                },
            )
            unico_conversion = self._unico("tMap")
            armado = construir(
                op_conversion,
                [Fuente(op.id, _tabla(tabla), resultado.columnas)],
                unico_conversion,
                x + PASO // 2,
                0,
                self.ruta_java,
                self._filas,
                self._salidas_n,
            )
            self.pendientes += armado.pendientes
            if armado.nodo is None:
                self.bloquea_emision = True
                return
            self.nodos.append(armado.nodo)
            self._nodo[op.id] = armado.nodo
            self._instancias[(op.id, None)] = armado.nodo
            self._salida[op.id] = list(armado.columnas)
            self._tabla_de[armado.nodo.unico] = _tabla(tabla)
            lineas = {n for ev in op.evidence for n in range(ev.line_start, ev.line_end + 1)}
            if lineas:
                self.traza[armado.nodo.unico] = sorted(lineas)
            self._entradas_map[op.id] = armado.entradas
            self._salidas_map[op.id] = armado.salidas[0]
            self._principal_de[op.id] = next(iter(armado.entradas.values()))
            self._filas += 1
            self._salidas_n += max(1, len(armado.salidas))
            self.conexiones.append(
                Conexion(resultado.nodo.unico, armado.nodo.unico, self._principal_de[op.id])
            )
            return
        for posicion, consumidor in enumerate(copias or [None]):
            nodo = resultado.nodo
            if posicion:
                otro = self._unico(nodo.componente)
                nodo = replace(
                    nodo, unico=otro, y=96 * posicion, parametros=_renombrar(nodo, otro)
                )
            self._registrar(op, nodo, resultado.columnas, _tabla(tabla), consumidor)

    def _paso_directo(self, op: Operator, x: int) -> None:
        esquema = esquema_paso_directo(op, self.esquemas)
        unico = self._unico(str((op.component or {}).get("name") or "tImpalaInput"))
        resultado = nodo_paso_directo(
            op,
            esquema,
            unico,
            x,
            0,
            self.ruta_java,
            self._conexion_en_contexto,
        )
        self.pendientes += resultado.pendientes
        if resultado.nodo is None:
            return
        destino = str((op.params.get("outputs") or [""])[0])
        self._registrar(op, resultado.nodo, resultado.columnas, _tabla(destino))

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
            # Decisión 5: sin columnas no hay archivo; un pendiente de escritura impide el Job.
            self.escritura_sin_columnas = True
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
            # No publicar el fragmento anterior a una escritura ausente: sería un Job ejecutable
            # que omite el archivo declarado por el programa SAS.
            self.bloquea_emision = True
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
        para_armar = _como_paso(op)
        if op.kind == "split":
            destinos = op.params.get("targets") or [op.params.get("target")]
            if not destinos or any(not destino for destino in destinos):
                self._sin_soporte(op)
                return
            if any(
                self.plan.graph.operator(previo).kind == "split"
                for previo in self.plan.graph.predecessors(op.id)
            ):
                self._sin_soporte(op)
                return
            condicion = str(op.params.get("condition") or "").strip()
            rama = op.params.get("branch")
            if rama and (rama != "then" or not condicion):
                self._sin_soporte(op)
                return
            salidas = [str(destino) for destino in destinos]
            ramas = [
                {"outputs": [destino], **({"expression": condicion} if condicion else {})}
                for destino in salidas
            ]
            para_armar = replace(
                op,
                kind="map",
                params={
                    "steps": [],
                    "outputs": salidas,
                    "branches": ramas,
                },
            )
        armado = construir(
            para_armar, fuentes, unico, x, 0, self.ruta_java, self._filas, self._salidas_n
        )
        self._filas += len(fuentes)
        self._salidas_n += max(1, len(armado.salidas))
        self.pendientes += armado.pendientes
        # El esquema de salida lo demuestra el SELECT, no el nodo: se guarda aunque el tMap falle,
        # para que la escritura de detrás sepa qué columnas tiene que escribir.
        self._salida[op.id] = list(armado.columnas)
        if armado.nodo is None:
            return
        tabla = _tabla(str((para_armar.params.get("outputs") or ["WORK.sin_nombre"])[0]))
        self._registrar(op, armado.nodo, armado.columnas, tabla)
        self._entradas_map[op.id] = armado.entradas
        self._salidas_map[op.id] = armado.salidas[0]
        self._principal_de[op.id] = next(iter(armado.entradas.values()))
        if len(armado.salidas) > 1:
            self._ramas[op.id] = self._consumidor_de_rama(para_armar, armado.salidas)

    def _consumidor_de_rama(self, op: Operator, salidas: list[str]) -> dict[str, str]:
        """Qué operador consume cada salida de un `map` con ramas.

        Una rama que nombra su tabla la consume quien lee esa tabla; las que no la nombran van, en
        orden, con los consumidores que quedan.
        """
        ramas = op.params.get("branches") or []
        libres = [i for i, rama in enumerate(ramas) if not rama.get("outputs")]
        reparto: dict[str, str] = {}
        for siguiente in self.plan.graph.successors(op.id):
            destino = self.plan.graph.operator(siguiente)
            leido = _tabla(
                str(destino.params.get("dataset") or (destino.params.get("inputs") or [""])[0])
            )
            indice = next(
                (
                    i
                    for i, rama in enumerate(ramas)
                    if leido and leido in {_tabla(str(o)) for o in rama.get("outputs") or []}
                ),
                None,
            )
            if indice is None and libres and destino.kind not in ("read", "write"):
                indice = libres.pop(0)
            if indice is not None and indice < len(salidas):
                reparto[siguiente] = salidas[indice]
        return reparto

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
            op, [f.columnas for f in fuentes], unico, x, _linea(op), self.ruta_java,
            lambda: self._unico("tMap"),
        )
        self.pendientes += resultado.pendientes
        self._salida[op.id] = []
        if resultado.nodo is None:
            return
        tabla = _tabla(str((op.params.get("outputs") or ["WORK.sin_nombre"])[0]))
        self._registrar(op, resultado.nodo, resultado.columnas, tabla)
        self._pasos.add(op.id)
        self._uniones[op.id] = [f.origen for f in fuentes]
        # Entrada desalineada: sale de su `tMap`, cuya salida se llama como su entrada del tUnite.
        for i, alineado in resultado.alineados.items():
            self.nodos.append(alineado)
            self._alineados.setdefault(op.id, {})[i] = alineado.unico
            nombre_salida = f"{unico}_in{i + 1}"
            self.conexiones.append(Conexion(alineado.unico, unico, nombre_salida, "MERGE", 10))

    def _sql_impala(self, op: Operator, x: int) -> None:
        """`exec_sql` como `tImpalaRow`; la conexión solo sale del contexto DEV explícito."""
        sql = str(op.params.get("sql") or "").strip()
        if not sql:
            self.pendientes.append(
                PendienteMigracion(SIN_SOPORTE, "exec_sql sin SQL para tImpalaRow", _linea(op))
            )
            return
        unico = self._unico("tImpalaRow")
        nodo = nodo_desde_plantilla(
            "tImpalaRow",
            unico,
            x,
            0,
            {
                "QUERY": java(sql),
                # La plantilla extraída refiere a una conexión inexistente en este Job. Desactivar
                # esa referencia permite abrir/compilar el componente; los parámetros concretos
                # del servidor siguen a cargo del usuario en Studio.
                "USE_EXISTING_CONNECTION": "false",
                **parametros_conexion(self._conexion_en_contexto),
                # PASS vacío hace que el Javajet genere una condición inválida.
                # Null tipado mantiene Java válido sin guardar credenciales.
                # Se conserva HIVE2, el driver predeterminado de la plantilla extraída de Studio.
                "PASS": "((String)null)",
            },
            ruta_java=self.ruta_java,
        )
        self._registrar(op, nodo, [], "")
        self.pendientes.append(
            PendienteMigracion(
                "P-CONEXION-BASE",
                (
                    f"{unico}: host, puerto y base salen de context.impala_*; configure esos "
                    "valores para cada entorno"
                    if self._conexion_en_contexto
                    else f"{unico}: configure en Studio el host, puerto, base y autenticación de "
                    "Impala; no se infieren del SAS"
                ),
                _linea(op),
            )
        )

    def _plegar_lectura_en_sql(self, op: Operator) -> bool:
        """Una lectura de base ya está representada por el FROM del `exec_sql` siguiente."""
        dataset = str(op.params.get("dataset") or "").casefold()
        if not dataset or op.placement != "db:impala":
            return False
        for siguiente in self.plan.graph.successors(op.id):
            consumidor = self.plan.graph.operator(siguiente)
            sql = str(consumidor.params.get("sql") or "").casefold()
            if (
                consumidor.kind == "exec_sql"
                and consumidor.placement == op.placement
                and (consumidor.component or {}).get("name") == "tImpalaRow"
                and dataset in sql
            ):
                # Alias, no conexión Talend: el SQL ejecuta la lectura directamente en Impala.
                self._alias[op.id] = consumidor.id
                self.plegados.add(op.id)
                return True
        return False

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
        # Un operador fundido trae la evidencia de cada paso del SAS que absorbió.
        lineas = {n for ev in op.evidence for n in range(ev.line_start, ev.line_end + 1)}
        if lineas:
            self.traza[nodo.unico] = sorted(lineas)

    # -- conexiones --------------------------------------------------------------------------
    def _alinear_tmaps(self) -> None:
        """Alinea la salida de un `tMap` con la única entrada del `tMap` siguiente."""
        for arista in self.plan.graph.edges():
            desde, hasta = self._resolver(arista.src), self._resolver(arista.dst)
            if (
                desde is None
                or hasta is None
                or desde not in self._salidas_map
                or hasta not in self._entradas_map
            ):
                continue
            entrada = self._entradas_map[hasta].get(desde)
            nodo = self._nodo.get(desde)
            rama = self._ramas.get(desde, {}).get(hasta)
            if not rama and len(self.plan.graph.successors(desde)) != 1:
                continue
            actual = rama or self._salidas_map[desde]
            if not entrada or not nodo or entrada == actual:
                continue
            patron = rf'(<outputTables\b[^>]*\bname="){re.escape(actual)}(")'
            nodo.datos, cambios = re.subn(
                patron, rf"\g<1>{entrada}\g<2>", nodo.datos, count=1
            )
            if cambios:
                # El esquema de la salida se llama como la salida: si no, Studio carga el Job
                # pero avisa de un error en esa conexión («Some errors appear after the migration»).
                nodo.metadatas = [
                    replace(bloque, nombre=entrada) if bloque.nombre == actual else bloque
                    for bloque in nodo.metadatas or []
                ]
                if rama:
                    self._ramas[desde][hasta] = entrada
                else:
                    self._salidas_map[desde] = entrada

    def _repartos(self) -> None:
        """Un nodo con varios consumidores reparte su flujo con un `tReplicate`.

        En Talend la salida de un componente tiene un solo destino. Leer o calcular una vez y
        repartir es lo que evita repetir el trabajo por cada paso del SAS que usa el resultado.
        """
        destinos: dict[str, list[str]] = {}
        for arista in self.plan.graph.edges():
            desde, hasta = self._resolver(arista.src), self._resolver(arista.dst)
            if desde is None or hasta is None or desde == hasta or hasta not in self._nodo:
                continue
            if hasta not in destinos.setdefault(desde, []):
                destinos[desde].append(hasta)
        for desde, consumidores in destinos.items():
            if len(consumidores) < 2 or not self._salida.get(desde) or desde in self._ramas:
                continue
            if any((desde, consumidor) in self._instancias for consumidor in consumidores):
                continue  # lectura con una copia por consumidor
            nodo = self._nodo[desde]
            if self._reconvergen(consumidores):
                self.pendientes.append(
                    PendienteMigracion(
                        RECONVERGE,
                        f"{nodo.unico}: su resultado lo usan dos ramas que se vuelven a juntar; "
                        "Talend no admite repartirlo con tReplicate y hace falta guardarlo con "
                        "tHashOutput y releerlo con tHashInput",
                        _linea(self.plan.graph.operator(desde)),
                    )
                )
                continue
            unico = self._unico("tReplicate")
            reparto = nodo_desde_plantilla(
                "tReplicate",
                unico,
                nodo.x + PASO // 2,
                nodo.y + 96,
                columnas=list(self._salida[desde]),
                ruta_java=self.ruta_java,
            )
            self.nodos.append(reparto)
            self._reparto[desde] = reparto
            self._turnos[desde] = consumidores
            nombre = self._salidas_map.get(desde) or f"{nodo.unico}_out"
            conector = self._conector_de.get(nodo.unico, "FLOW")
            self.conexiones.append(Conexion(nodo.unico, unico, nombre, conector=conector))

    def _nombre_repartido(self, desde: str, hasta: str) -> str | None:
        """Nombre de la conexión que sale del `tReplicate` de `desde` hacia `hasta`."""
        if hasta in self._uniones:
            return f"{self._nodo[hasta].unico}_in{self._uniones[hasta].index(desde) + 1}"
        if hasta in self._pasos:
            return f"{self._nodo[hasta].unico}_in"
        if hasta in self._entradas_map:
            return self._entradas_map[hasta].get(desde)
        turno = self._turnos[desde].index(hasta) + 1
        return f"{self._reparto[desde].unico}_out{turno}"

    def _conectar(self) -> None:
        vistas: set[tuple[str, str, str]] = set()
        for arista in self.plan.graph.edges():
            desde, hasta = self._resolver(arista.src), self._resolver(arista.dst)
            if desde is None or hasta is None or desde == hasta:
                continue
            repartido = desde in self._reparto and hasta in self._turnos[desde]
            nombre = (
                self._nombre_repartido(desde, hasta) if repartido else self._nombre(desde, hasta)
            )
            if nombre is None:
                continue
            nodo_origen = self._reparto[desde] if repartido else self._instancia(desde, hasta)
            nodo_destino = self._nodo.get(hasta)
            if nodo_origen is None or nodo_destino is None:
                continue
            origen, destino = nodo_origen.unico, nodo_destino.unico
            entradas_union = self._uniones.get(hasta, [])
            indice = entradas_union.index(desde) if desde in entradas_union else -1
            if not repartido and indice in self._alineados.get(hasta, {}):
                # Entrada desalineada: entra por la `row1` de su `tMap`, no directo al tUnite.
                destino = self._alineados[hasta][indice]
                if (origen, destino, "row1") not in vistas:
                    vistas.add((origen, destino, "row1"))
                    conector = self._conector_de.get(origen, "FLOW")
                    self.conexiones.append(Conexion(origen, destino, "row1", conector=conector))
                continue
            clave = (origen, destino, nombre)
            if clave in vistas:
                continue
            vistas.add(clave)
            if hasta in self._entradas_map and nombre != self._principal_de.get(hasta):
                # Las entradas de búsqueda de un tMap van por LOOKUP (`lineStyle` 8), no por FLOW.
                self.conexiones.append(lookup(origen, destino, nombre))
            elif hasta in self._uniones:
                # Las entradas de un `tUnite` son conexiones MERGE (`lineStyle` 10, el id de
                # FLOW_MERGE en `EConnectionType`); con FLOW, Studio no genera la unión.
                self.conexiones.append(Conexion(origen, destino, nombre, "MERGE", 10))
            else:
                operador_origen = self.plan.graph.operator(desde)
                salidas_duplicadas = {
                    str(tabla).lower()
                    for tabla in operador_origen.params.get("duplicate_outputs") or []
                }
                conector = (
                    "DUPLICATE"
                    if arista.dataset and arista.dataset.lower() in salidas_duplicadas
                    else self._conector_de.get(origen, "FLOW")
                )
                self.conexiones.append(Conexion(origen, destino, nombre, conector=conector))

    def _cierres(self) -> None:
        """Un orden, un `DISTINCT`, un agregado o una unión sin nadie detrás no compila en Studio.

        `tSortRow` y los demás generan su código contra la conexión de salida: sin ella aparece
        `defaultRow` sin declarar. Es la tabla final de un `PROC SQL` que no se exporta; se le pone
        un `tLogRow`, que además deja ver las filas al ejecutar.
        """
        con_salida = {c.origen for c in self.conexiones}
        for op_id in sorted(self._pasos):
            nodo = self._nodo[op_id]
            if nodo.unico in con_salida or not self._salida.get(op_id):
                continue
            columnas = self._salida[op_id]
            unico = self._unico("tLogRow")
            # Debajo de la fila de nodos, para no pisar a ninguno.
            y = 96 * (2 + sum(1 for n in self.nodos if n.componente == "tLogRow"))
            cierre = log_row(unico, columnas, nodo.x, y, self.ruta_java or "")
            self.nodos.append(cierre)
            conector = self._conector_de.get(nodo.unico, "FLOW")
            self.conexiones.append(
                Conexion(nodo.unico, cierre.unico, f"{nodo.unico}_out", conector=conector)
            )

    def _nombre(self, desde: str, hasta: str) -> str | None:
        """Nombre de la conexión: la entrada que el `tMap` espera, o la salida que produce.

        `None` cuando el `tMap` de destino no tiene esa entrada: la arista existe en el plan pero no
        hay a qué fila del mapa corresponde, y una conexión con el nombre equivocado es peor que no
        tenerla.
        """
        if desde in self._ramas:
            # Cada rama del `tMap` es una salida con su condición, y la conexión lleva su nombre.
            return self._ramas[desde].get(hasta)
        if (
            desde in self._salidas_map
            and hasta not in self._entradas_map
            and len(self.plan.graph.successors(desde)) == 1
        ):
            # Studio exige que la conexión que sale de un `tMap` lleve el nombre de su salida
            # (`outputTables`); si no, el Job no carga («Error al cargar el trabajo»). Con un solo
            # consumidor, la salida y la conexión coinciden. Con varios, sigue el nombre de abajo.
            return self._salidas_map[desde]
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
            # Salida de un `tMap` hacia un destino que no es paso ni entrada de otro `tMap`.
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
        self._alinear_tmaps()
        self._repartos()
        self._conectar()
        self._cierres()
        reemplazar_rutas(self.nodos, self.rutas)
        return Job(
            job.name,
            nodos=self.nodos,
            conexiones=self.conexiones,
            contextos=contextos_de_plan(self.plan, dev={} if self._conexion_en_contexto else None),
        )

    def _lag(self, op: Operator, x: int) -> bool:
        """`LAG`/`DIF` como `tJavaRow` si la forma es la que se sabe emitir (desde_plan_lag)."""
        fuentes = self._fuentes(op)
        if len(fuentes) != 1:
            return False
        unico = self._unico("tJavaRow")
        resultado = nodo_lag(op, fuentes[0].columnas, unico, x, _linea(op), self.ruta_java)
        if resultado is None or resultado.nodo is None:
            return False
        self._registrar(op, resultado.nodo, resultado.columnas, "")
        self._pasos.add(op.id)
        self.emitidos.add(op.id)
        return True

    def _traducir(self, op: Operator, x: int) -> None:
        if op.kind == "stateful_row" and self._lag(op, x):
            return
        if op.status == "hueco" or op.kind == "unsupported":
            self._sin_soporte(op)
            return
        if op.kind in ("read", "write"):
            # Si se pliega sobre otro nodo, el conjunto ya está en el flujo y no hay nada que hacer.
            if op.kind == "read" and self._plegar_lectura_en_sql(op):
                return
            if op.kind == "read" and (op.placement or "").startswith("db:"):
                self._paso_directo(op, x)
                return
            if self._resolver(op.id) is None and op.id not in self.plegados:
                self._sin_soporte(op)
            return
        componente = str((op.component or {}).get("name") or "none")
        if op.kind == "read_file":
            self._lectura(op, x)
        elif op.kind == "write_file":
            self._escritura(op, x)
        elif op.kind == "map":
            self._mapa(op, x)
        elif op.kind == "split":
            self._mapa(op, x)
        elif op.kind in ("sort", "dedup"):
            self._orden(op, x)
        elif op.kind == "aggregate":
            self._agregado(op, x)
        elif op.kind == "union":
            self._union(op, x)
        elif op.kind == "exec_sql" and componente == "tImpalaRow":
            self._sql_impala(op, x)
        elif op.kind in CON_NODO:
            # Las transformaciones sueltas son un `tMap` de una sola entrada.
            self._mapa(op, x)
        elif componente == "none":
            self._sin_soporte(op)
        else:
            # `codigo`: el operador sin emisor declara su pendiente (P-POR-GRUPO-SIN-EMISOR, ...).
            self.pendientes.append(
                PendienteMigracion(
                    str(op.params.get("codigo") or SIN_SOPORTE),
                    f"el operador '{op.kind}' todavía no tiene emisor para {componente}",
                    _linea(op),
                )
            )


def plan_a_jobs(
    plan: Plan,
    esquemas: dict[str, list[Column]],
    ruta_java: str | None = None,
    conexion_en_contexto: bool = False,
) -> ResultadoMigracion:
    """Un Job de Talend por cada Job del plan, con sus nodos, conexiones y pendientes."""
    resultado = ResultadoMigracion()
    marcado = next(
        (
            op
            for op in plan.graph.operators()
            if op.params.get("subconsulta_from") or op.params.get("create_like")
        ),
        None,
    )
    if marcado is not None:
        # Una subconsulta en FROM no está verificada en Studio: el programa no se emite (C-8).
        resultado.visitados = {op.id for op in plan.graph.operators()}
        resultado.pendientes.append(
            PendienteMigracion(
                "P-OPERADOR-SIN-SOPORTE",
                "subconsulta en FROM o CREATE LIKE sin verificar en Studio; el Job no se emite",
                _linea(marcado),
            )
        )
        return resultado
    # Cada instancia de una plantilla se escribe en línea hasta que haya Jobs hijos (`tRunJob`).
    plan, desplegados = plan_desplegado(plan)
    resultado.visitados |= desplegados
    # El diseño de Talend, no el del SAS: las intermedias que nadie más usa se funden. Los
    # operadores absorbidos cuentan como plegados sobre el que los representa.
    plan, informe = optimizar(plan)
    resultado.decisiones = informe.decisiones
    resultado.visitados |= set(informe.absorbidos)
    resultado.plegados |= set(informe.absorbidos)
    for job in plan.jobs:
        armado = _Job(plan, esquemas, ruta_java, conexion_en_contexto)
        construido = armado.armar(job)
        # Un Job con un hueco es parcial: sus pendientes se informan, pero el Job no se escribe.
        if (
            not armado.bloquea_emision
            and not tiene_hueco(plan, job, armado.emitidos)
            and not armado.escritura_sin_columnas
        ):
            resultado.jobs.append(construido)
        resultado.pendientes += armado.pendientes
        resultado.traza.update(armado.traza)
        resultado.visitados |= armado.visitados
        resultado.plegados |= armado.plegados
    return resultado


__all__ = ["ResultadoMigracion", "plan_a_jobs"]
