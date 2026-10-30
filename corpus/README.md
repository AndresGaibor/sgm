# corpus/

Lotes de programas que llegan para migrar. Esta carpeta **no va al repositorio**: `.gitignore` lo
excluye todo salvo este README, porque los programas pueden traer datos del cliente.

- `inbox/<fecha>-<hash>/`: un lote importado con `sgm intake <ruta>`. Dentro:
  - `fuente/`: copia en UTF-8 con credenciales redactadas (el original no se guarda).
  - `salida/`: guía y plan de cada programa.
  - `huecos.json`: huecos del lote, con dueño y comando sugerido.
- `accepted/`: lotes cuyos huecos ya están cerrados (se mueven a mano, al terminar el ciclo de
  huecos; ver `docs/plan-sgm-v2/03-ciclo-de-huecos.md`).

Para ver qué falló en un lote: `sgm gaps list --file <carpeta-del-lote>`.
