# Diseño: inventario de dependencias y licencias (MG-P13-04)

## Objetivo

Entregar un SBOM que enumere el paquete SGM y cada variante bloqueada por `uv.lock`, con versiones
exactas, alcance runtime/desarrollo y licencia declarada. El informe humano será `docs/sbom.md` y el
archivo SPDX 2.3 permitirá validación automática. Un manifest complementario mantendrá la relación
exacta entre cada archivo distribuible, su URL y su hash.

## Enfoques considerados

1. Mantener solo una tabla Markdown. Es sencilla de leer, pero no es una representación
   interoperable y se puede desincronizar del lock.
2. Mantener a mano Markdown y SPDX JSON. Es interoperable, pero duplica información y aumenta la
   posibilidad de divergencia.
3. Generar ambos artefactos desde `uv.lock` con la biblioteca estándar de Python. Conserva una sola
   fuente de versiones y hashes, permite comprobar la cobertura con pruebas y no instala ni agrega
   dependencias. **Elección:** enfoque 3.

## Alcance y límites

- El universo auditado es cada variante del lock del proyecto, incluidas dependencias transitivas y
  de desarrollo; la ruta distingue runtime y desarrollo y conserva los marcadores de resolución.
- Las referencias del grafo se resuelven por nombre y, cuando el lock lo declara, versión y origen.
  Una referencia ambigua falla explícitamente en vez de vincular varias variantes o inventar alcance.
- La versión y el checksum SPDX identifican un artefacto fuente concreto por variante. El manifest
  conserva nombre de archivo, URL y SHA-256 de todos los wheels y sdists por separado.
- Las licencias usan metadata de PyPI solo cuando el origen y la versión coinciden, o fuentes del
  proyecto publicador enlazadas desde el informe.
- Si el propio paquete `sgm` no declara licencia, el SBOM registra `NOASSERTION` y el informe deja
  pendiente la decisión legal; no se escoge una licencia por el equipo técnico.
- No se agregan dependencias, no se consulta una base de vulnerabilidades y no se afirma que el
  inventario sea una evaluación CVE.

## Verificación

Las pruebas cruzan cada variante del SPDX y cada artefacto del manifest con `uv.lock`: versión,
origen, marcadores, URL, nombre de archivo y hashes deben coincidir, sin variantes perdidas ni hashes
ambiguos. También se verifica que los IDs, relaciones y alcances apunten a la variante correcta, que
una referencia ambigua falle, que el namespace derive del contenido canónico y que el informe tenga
licencia y alcance para cada paquete.
