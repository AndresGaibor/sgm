# Referencia Talend Studio 8.0: componentes usados por sgm-v2

Descargado el 2026-11-03 desde la documentación oficial de Qlik/Talend (`https://help.qlik.com/talend/en-US/components/8.0/`). Cada archivo reúne la página del componente y sus subpáginas en Markdown. Lista de componentes tomada de `rules/talend/official-component-inventory.json`.

Además, la guía de usuario de Studio (no de componentes) está en
[`studio-guia-jobs-contextos.md`](studio-guia-jobs-contextos.md): diseño de Jobs, joblets y
variables de contexto (versión R2026-09).

| Componente | Páginas | Errores | Caracteres |
|---|---|---|---|
| [tmap](tmap.md) | 20 | 0 | 71691 |
| [tsqltemplate](tsqltemplate.md) | 1 | 0 | 6196 |
| [tjdbcinput](tjdbcinput.md) | 3 | 0 | 25897 |
| [tjdbcoutput](tjdbcoutput.md) | 4 | 0 | 45447 |
| [tjdbclookupinput](tjdbclookupinput.md) | 1 | 0 | 11948 |
| [tjdbcrow](tjdbcrow.md) | 1 | 0 | 11842 |
| [tjdbcconnection](tjdbcconnection.md) | 1 | 0 | 5922 |
| [tjdbcclose](tjdbcclose.md) | 1 | 0 | 2991 |
| [tjdbccommit](tjdbccommit.md) | 1 | 0 | 3652 |
| [tjdbcrollback](tjdbcrollback.md) | 1 | 0 | 3309 |
| [tjdbcscdelt](tjdbcscdelt.md) | 1 | 0 | 10954 |
| [tfileinputdelimited](tfileinputdelimited.md) | 25 | 0 | 55592 |
| [tfileinputexcel](tfileinputexcel.md) | 1 | 0 | 13639 |
| [trunjob](trunjob.md) | 11 | 0 | 36521 |
| [tprejob](tprejob.md) | 7 | 0 | 8272 |
| [tpostjob](tpostjob.md) | 1 | 0 | 2185 |
| [tflowtoiterate](tflowtoiterate.md) | 5 | 0 | 8875 |
| [titeratetoflow](titeratetoflow.md) | 2 | 0 | 7091 |
| [tlogrow](tlogrow.md) | 9 | 0 | 30909 |
| [tcacheout](tcacheout.md) | 14 | 0 | 38257 |
| [tcachein](tcachein.md) | 3 | 0 | 11826 |
| [tdie](tdie.md) | 1 | 0 | 3030 |
| [twarn](twarn.md) | 1 | 0 | 2654 |
| [tfilelist](tfilelist.md) | 6 | 0 | 17169 |
| [tfilecopy](tfilecopy.md) | 5 | 0 | 8773 |
| [tfileoutputdelimited](tfileoutputdelimited.md) | 8 | 0 | 37294 |
| [tfileoutputexcel](tfileoutputexcel.md) | 1 | 0 | 13418 |
| [taggregaterow](taggregaterow.md) | 5 | 0 | 28687 |
| [tsortrow](tsortrow.md) | 4 | 0 | 6895 |
| [tuniqrow](tuniqrow.md) | 4 | 0 | 16505 |
| [tfilterrow](tfilterrow.md) | 9 | 0 | 27869 |
| [treplicate](treplicate.md) | 5 | 0 | 17395 |
| [tcontextload](tcontextload.md) | 1 | 0 | 5495 |
| [tjavarow](tjavarow.md) | 13 | 0 | 32538 |
| [tsetglobalvar](tsetglobalvar.md) | 5 | 0 | 4511 |
| [tdbinput](tdbinput.md) | 1 | 0 | 1184 |
| [tdboutput](tdboutput.md) | 1 | 0 | 1225 |
| [tfixedflowinput](tfixedflowinput.md) | 6 | 0 | 17422 |
| [trowgenerator](trowgenerator.md) | 8 | 0 | 19517 |
| [tdbrow](tdbrow.md) | 1 | 0 | 1176 |
| [tdbconnection](tdbconnection.md) | 1 | 0 | 1256 |

## Qué hay además de los 41 componentes

- [`catalogo/`](catalogo/): página raíz de los 539 componentes de `rules/talend/components.json`, en
  Markdown oficial. Se baja con `uv run python tools/referencia/descargar.py talend --catalogo`.
- [`catalogo/VERIFICACION.md`](catalogo/VERIFICACION.md): comparación del catálogo con las páginas
  (título y familia). Se regenera con `uv run python tools/referencia/verificar.py`. Hoy hay 8
  discrepancias de familia (6 LDAP, `tReplace`, `tREST`), para revisar a mano; el catálogo no se
  cambia solo.
- [`studio-guia-jobs-contextos.md`](studio-guia-jobs-contextos.md): guía de Studio R2026-09 (diseño de
  Jobs, joblets, contextos y conexiones), 16 temas. Se baja con `descargar.py talend --guia`.
- [`tjdbcconnection-opciones.yaml`](tjdbcconnection-opciones.yaml): 14 propiedades de la conexión
  JDBC, extraídas de sus tablas (`tools/referencia/opciones.py`).
- [`inventario.sha256`](inventario.sha256): huella del inventario oficial. Si el inventario cambia, la
  prueba `test_talend_referencia` falla hasta que se revise y se actualice la huella.
- [`cruce-con-el-codigo.md`](cruce-con-el-codigo.md): qué dice la documentación y qué hace el código
  sobre contextos, `tPrejob`/`tPostjob`, `tRunJob` y manejo de errores, con las brechas y lo pendiente.
