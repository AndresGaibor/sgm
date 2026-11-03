"""Catálogo de la documentación oficial que se descarga en `docs/referencia/`.

Solo datos y funciones puras: no hacen red. `descargar.py` usa estas listas para bajar los archivos.
Cada fuente lleva su versión, para que el README pueda decir qué se descargó y cuándo.
"""

from __future__ import annotations

from dataclasses import dataclass

SAS_BASE = (
    "https://documentation.sas.com/api/collections/pgmsascdc/9.4_3.5/"
    "docsets/{docset}/content/{docset}.pdf?locale=en"
)
TALEND_BASE = "https://help.qlik.com/talend/en-US/components/8.0/"
TALEND_STUDIO_BASE = "https://help.qlik.com/talend/en-US/studio-user-guide/8.0-R2026-09/"


@dataclass(frozen=True)
class SasDocset:
    docset: str  # nombre de la colección en documentation.sas.com
    titulo: str  # título de la guía oficial
    archivo: str  # nombre local sin extensión, en docs/referencia/sas/


SAS_DOCSETS: tuple[SasDocset, ...] = (
    SasDocset("sqlproc", "SAS 9.4 SQL Procedure User's Guide", "sqlproc"),
    SasDocset("mcrolref", "SAS 9.4 Macro Language Reference", "mcrolref"),
    SasDocset("lestmtsref", "SAS 9.4 Statements Reference", "lestmtsref"),
    SasDocset("ledsoptsref", "SAS 9.4 Data Set Options Reference", "ledsoptsref"),
    SasDocset("lefunctionsref", "SAS 9.4 Functions and CALL Routines Reference", "lefunctionsref"),
    SasDocset("proc", "SAS 9.4 Procedures Guide", "proc"),
)

# Componentes de Talend que usa el proyecto (ver rules/talend/official-component-inventory.json).
TALEND_COMPONENTES: tuple[str, ...] = (
    "tmap",
    "tsqltemplate",
    "tjdbcinput",
    "tjdbcoutput",
    "tjdbclookupinput",
    "tjdbcrow",
    "tjdbcconnection",
    "tjdbcclose",
    "tjdbccommit",
    "tjdbcrollback",
    "tjdbcscdelt",
    "tfileinputdelimited",
    "tfileinputexcel",
    "trunjob",
    "tprejob",
    "tpostjob",
    "tflowtoiterate",
    "titeratetoflow",
    "tlogrow",
    "tcacheout",
    "tcachein",
    "tdie",
    "twarn",
    "tfilelist",
    "tfilecopy",
    "tfileoutputdelimited",
    "tfileoutputexcel",
    "taggregaterow",
    "tsortrow",
    "tuniqrow",
    "tfilterrow",
    "treplicate",
    "tcontextload",
    "tjavarow",
    "tsetglobalvar",
    "tdbinput",
    "tdboutput",
    "tfixedflowinput",
    "trowgenerator",
    "tdbrow",
    "tdbconnection",
)

# Temas de la guía de Studio (versión R2026-09) que describen diseño de Jobs y contextos.
TALEND_STUDIO_RAICES: tuple[str, ...] = (
    "designing-a-job",
    "designing-a-joblet",
    "defining-variables",
    "applying-context-variable-to-joblet",
    "creating-connection",
)


def url_sas(docset: str) -> str:
    """URL del PDF oficial de una guía de SAS 9.4."""
    return SAS_BASE.format(docset=docset)


def url_componente(nombre: str) -> str:
    """URL base (sin `.md`) de la página de un componente de Talend 8.0."""
    return TALEND_BASE + nombre.lower()


def url_studio(tema: str) -> str:
    """URL base (sin `.md`) de un tema de la guía de Studio R2026-09."""
    return TALEND_STUDIO_BASE + tema
