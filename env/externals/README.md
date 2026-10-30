# Archivos externos

Esta carpeta guarda los archivos que un `%include` del código SAS trae de fuera del repositorio
(por ejemplo `/data/Programas_SAS/...`). Si un archivo está aquí con el mismo nombre, se lee como
cualquier fuente del proyecto y sus macros se expanden.

Si el archivo no está aquí, pero sí declarado en `../externals.json`, sus variables pasan a ser
contexto del Job y el `%include` no genera hueco. Si no está ni aquí ni declarado, sigue siendo hueco.

No declares el contenido interno de un archivo que no tienes. Solo declara lo que el código demuestra.
