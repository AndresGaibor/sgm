# Tasks

## 1. Pruebas (TDD)

- [ ] 1.1 Crear `tests/unit/test_qlik_dataflow.py` para la consulta obligatoria, estados parciales/pendientes, operador sin mapeo con dos entradas, evidencia vacía e inmutabilidad; ejecutar `uv run python -m pytest -q tests/unit/test_qlik_dataflow.py` y confirmar fallo RED por falta del módulo.

## 2. Implementación

- [ ] 2.1 Crear `src/sgm/qlik_dataflow.py` con los modelos `DataFlowNode`, `DataFlowEdge`, `DataFlowGraph` y `map_graph(graph: Graph) -> DataFlowGraph`; mapear `read/filter/aggregate/write`, conservar parámetros, evidencia y enlaces, dejar fuente/destino pendientes sin ubicación Qlik, filtro parcial y agregados pendientes sin tipo requerido; ejecutar la prueba unitaria y confirmar verde.

## 3. Documentación

- [ ] 3.1 Registrar el cambio como Hito 295 en `PROGRESS.md` con alcance, límites NO-GO, pruebas, métricas y decisiones; comprobar que no se sobrescriban entradas anteriores.

## 4. Cierre

- [ ] 4.1 Ejecutar `uv run ruff check .` y `uv run python tools/ci.py` sobre el árbol final y guardar el resultado exigido por el gancho local.
- [ ] 4.2 Ejecutar `uv run python tools/validacion.py estado`, confirmar que el árbol validado no cambió y crear el commit local `hito 295: mapear SAS a Qlik DataFlow`; no hacer push ni alterar otras ramas.
