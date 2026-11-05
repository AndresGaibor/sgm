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
# Segunda forma de URL, para las guías que no están en la colección `pgmsascdc` (por ejemplo
# `lrcon`, que responde 404 en la colección y 200 por aquí).
SAS_DOCSET_BASE = "https://documentation.sas.com/api/docsets/{docset}/9.4/content/{docset}.pdf"
TALEND_BASE = "https://help.qlik.com/talend/en-US/components/8.0/"
TALEND_STUDIO_BASE = "https://help.qlik.com/talend/en-US/studio-user-guide/8.0-R2026-09/"


@dataclass(frozen=True)
class SasDocset:
    docset: str  # nombre de la colección en documentation.sas.com
    titulo: str  # título de la guía oficial
    archivo: str  # nombre local sin extensión, en docs/referencia/sas/
    base: str = SAS_BASE  # plantilla de la URL; casi todas viven en `pgmsascdc`


SAS_DOCSETS: tuple[SasDocset, ...] = (
    SasDocset("sqlproc", "SAS 9.4 SQL Procedure User's Guide", "sqlproc"),
    SasDocset("mcrolref", "SAS 9.4 Macro Language Reference", "mcrolref"),
    SasDocset("lestmtsref", "SAS 9.4 Statements Reference", "lestmtsref"),
    SasDocset("ledsoptsref", "SAS 9.4 Data Set Options Reference", "ledsoptsref"),
    SasDocset("lefunctionsref", "SAS 9.4 Functions and CALL Routines Reference", "lefunctionsref"),
    SasDocset("proc", "SAS 9.4 Procedures Guide", "proc"),
    SasDocset("lepg", "SAS 9.4 Programmer's Guide: Essentials", "lepg"),
    SasDocset("lrcon", "SAS 9.4 Language Reference: Concepts", "lrcon", base=SAS_DOCSET_BASE),
    SasDocset("leforinforref", "SAS 9.4 Formats and Informats: Reference", "leforinforref"),
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


def url_sas(docset: str, base: str = SAS_BASE) -> str:
    """URL del PDF oficial de una guía de SAS 9.4. `base` cambia la colección de origen."""
    return base.format(docset=docset)


def url_guia(guia: SasDocset) -> str:
    """URL del PDF de una guía del catálogo, con la colección que le corresponde."""
    return url_sas(guia.docset, guia.base)


def url_componente(nombre: str) -> str:
    """URL base (sin `.md`) de la página de un componente de Talend 8.0."""
    return TALEND_BASE + nombre.lower()


def url_studio(tema: str) -> str:
    """URL base (sin `.md`) de un tema de la guía de Studio R2026-09."""
    return TALEND_STUDIO_BASE + tema
