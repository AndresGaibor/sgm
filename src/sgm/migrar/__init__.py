"""Migrador general: de un programa SAS a Jobs de Talend sin ningún YAML.

`esquemas` deduce las tablas de entrada; `informes` escribe lo que una persona tiene que completar;
`interprete` ejecuta el plan en Python con la semántica de SAS para comparar contra el esperado.
"""

from __future__ import annotations

from sgm.migrar.esquemas import PendienteMigracion, esquemas_de_entrada

__all__ = ["PendienteMigracion", "esquemas_de_entrada"]
