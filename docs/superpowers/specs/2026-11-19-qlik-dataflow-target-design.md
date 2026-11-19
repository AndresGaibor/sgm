# Diseño: destino Qlik Cloud Analytics DataFlow

## Intención

Agregar en una rama separada una primera salida lógica del migrador SAS hacia Qlik Cloud Analytics DataFlow. El objetivo inicial es comprobar qué operaciones SAS caben en el modelo visual y representar un `PROC SQL` sencillo como nodos y enlaces revisables.

## Alcance de la primera entrega

- Reutilizar el análisis SAS, el grafo de operadores y la evidencia que ya produce SGM.
- Mapear el caso `CREATE TABLE ... SELECT ... WHERE ... GROUP BY ...` a `Source → Filter → Aggregate → Target`.
- Clasificar cada operación como compatible, parcial o pendiente, conservando el motivo y la evidencia SAS.
- Probar la salida con SAS sintético y una prueba unitaria del grafo.
- Mantener el resultado en memoria o como JSON local; no conectarse a un tenant de Qlik.

## Fuera de alcance

- Crear o editar nodos DataFlow en Qlik Cloud, importar o generar `.dfw`, o ejecutar flujos.
- Usar formatos privados, endpoints no documentados o automatización de interfaz.
- Generar Qlik Script como sustituto de DataFlow. Solo se reconsidera con una instrucción posterior.
- Cambiar el destino Talend, agregar frontend/MCP, instalar dependencias o usar datos bancarios reales.

## Enfoques considerados

1. **Adaptador contra la IR existente (elegido):** consume `Operator` y `Graph` ya creados por `compile_project`; evita duplicar parser, linaje y semántica SAS. El adaptador no lee `Operator.component`, que pertenece a Talend.
2. **Parser y grafo Qlik nuevos:** duplicaría análisis y precedencia de `PROC SQL`, con riesgo de divergencia; se descarta.
3. **Emitir `.dfw` o una receta interna:** la documentación pública consultada no define un contrato de creación/modificación del lienzo; se descarta hasta que exista evidencia oficial.

## Diseño propuesto

- Añadir un paquete aislado `src/sgm/qlik_dataflow/` para el mapeo de operadores IR a tipos lógicos `Source`, `Filter`, `Aggregate` y `Target`.
- El mapper preserva parámetros, orden, aristas y referencias `Evidence`; cada nodo no mapeable se conserva como pendiente con motivo, sin inventar equivalencias.
- `compile_project` ya agrega un operador `write` para el destino SQL; se convierte a `Target` y conserva su enlace desde `Aggregate`.
- La compatibilidad DataFlow se calcula por separado de `Operator.status`, porque ese estado refleja el emisor Talend. Si el tipo necesario no está demostrado, el nodo se conserva como parcial/pendiente con el motivo.
- El adaptador acepta solo el subconjunto confirmado por el caso y catálogo de procesadores. No añade equivalencias de expresiones SAS por inferencia.
- La prueba usa datos sintéticos y verifica estructura, filtro y agregado. No declara equivalencia de ejecución en Qlik.

## Evidencia de producto y límite actual

- Qlik describe DataFlow Analytics como un lienzo con fuentes, procesadores y destinos: [crear un data flow](https://help.qlik.com/en-US/cloud-services/Subsystems/Hub/Content/Sense_Hub/DataFlow/Creating-data-flow.htm) y [lista de procesadores](https://help.qlik.com/en-US/cloud-services/Subsystems/Hub/Content/Sense_Hub/DataFlow/List-of-data-flow-processors.htm).
- La ayuda permite exportar un flujo como `.dfw` y cargarlo en otro tenant: [administrar data flows](https://help.qlik.com/en-US/cloud-services/Subsystems/Hub/Content/Sense_Hub/DataFlow/managing-data-flows.htm). No define aquí la estructura del archivo ni un endpoint de creación del grafo.
- La API de Apps enumera `DATAFLOW_PREP` como uso de app, pero la referencia revisada no documenta operaciones para crear o editar los procesadores del DataFlow: [Apps REST](https://qlik.dev/apis/rest/apps/).
- La API `di-projects` pertenece a Qlik Talend Data Integration, que es otro producto; no se toma como evidencia de un API para Analytics DataFlow: [Data integration projects REST](https://qlik.dev/apis/rest/di-projects/).
- Con la evidencia pública revisada, la generación/importación automatizada del lienzo queda **NO-GO** hasta localizar una API oficial que documente el grafo y sus procesadores. El mapeo lógico SAS→DataFlow permanece útil y separado de esa compuerta.

## Riesgos y decisiones

- La IR mezcla operadores portables con colocación y candidaturas Talend; el mapper debe basarse en `kind`, `params`, aristas y evidencia, no en el componente Talend.
- En el caso mínimo, `total` no tiene tipo en el SAS y el operador `Filter` actual queda `parcial`; `SUM(total)` también debe permanecer pendiente en compatibilidad hasta demostrar el tipo numérico con SAS o metadatos locales. Los datos sintéticos sirven para probar la estructura, no para inferir el tipo real.
- Una API para crear un app `DATAFLOW_PREP` no demostraría por sí sola soporte para definir el grafo visual; se exige documentación para ambas partes.
- La rama parte de `origin/main`, pero la suite de cierre y los artefactos OpenSpec todavía deben ejecutarse antes de implementar o cerrar un hito.
