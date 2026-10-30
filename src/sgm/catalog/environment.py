"""Catálogo de entorno: lo que el SAS no trae y hay que declarar una vez por proyecto.

Un `environment.json` declara cada `libname` (motor y conexión, sin credenciales: solo el nombre del
grupo de contexto) y cada dataset (tabla física o archivo, formato y columnas con sus tipos).
No inventa nada: lo que el catálogo no declara sigue siendo un pendiente con su motivo.

Porte de la versión anterior: la validación de pydantic se sustituyó por comprobaciones explícitas
para no añadir dependencias fuera de la lista permitida.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

#: Tipos de Talend admitidos en una columna del catálogo.
TALEND_TYPES = frozenset(
    {"id_String", "id_Integer", "id_Long", "id_Double", "id_Float", "id_BigDecimal", "id_Date", "id_Boolean"}
)
#: Cómo se lee cada tipo de dataset.
DATASET_KINDS = frozenset({"table", "delimited", "positional", "excel", "sas7bdat"})


class CatalogError(ValueError):
    """El catálogo no sirve: se dice por qué en vez de seguir con datos dudosos."""


@dataclass
class EnvironmentColumn:
    name: str
    talend_type: str
    nullable: bool = True
    length: int | None = None
    precision: int | None = None


@dataclass
class EnvironmentLibrary:
    name: str  # el libname de SAS, tal cual aparece en el programa
    engine: str  # motor, p. ej. "oracle" o "base"
    connection: str | None = None  # grupo de contexto de Talend; nunca usuario ni contraseña
    path: str | None = None
    note: str | None = None

    @property
    def is_file_library(self) -> bool:
        return self.engine in {"base", "file"}


@dataclass
class EnvironmentDataset:
    library: str
    name: str
    kind: str = "table"
    target: str | None = None  # tabla física o ruta; por defecto, el nombre del dataset
    delimiter: str | None = None
    header: bool | None = None
    encoding: str | None = None
    columns: list[EnvironmentColumn] = field(default_factory=list)

    @property
    def physical(self) -> str:
        return self.target or self.name


@dataclass
class EnvironmentCatalog:
    schema_version: int = 1
    project: str | None = None
    libraries: list[EnvironmentLibrary] = field(default_factory=list)
    datasets: list[EnvironmentDataset] = field(default_factory=list)

    def library(self, name: str) -> EnvironmentLibrary | None:
        target = name.casefold()
        return next((lib for lib in self.libraries if lib.name.casefold() == target), None)

    def dataset(self, libname: str, name: str) -> EnvironmentDataset | None:
        """Dataset por librería y nombre; `work` no se busca (es temporal, no está en el catálogo)."""
        if libname.casefold() == "work":
            return None
        library, dataset = libname.casefold(), name.casefold()
        return next(
            (
                item
                for item in self.datasets
                if item.library.casefold() == library and item.name.casefold() == dataset
            ),
            None,
        )

    def dataset_by_path(self, path: str) -> EnvironmentDataset | None:
        """Dataset por la ruta física (para `PROC IMPORT` y `INFILE` de un archivo del catálogo)."""
        target = path.replace("\\", "/").casefold()
        return next(
            (item for item in self.datasets if item.physical.replace("\\", "/").casefold() == target),
            None,
        )


def _text(item: dict[str, Any], key: str) -> str | None:
    value = item.get(key)
    if value is not None and not isinstance(value, str):
        raise CatalogError(f"el campo {key!r} debe ser texto")
    return value


def _column(raw: dict[str, Any]) -> EnvironmentColumn:
    if "name" not in raw or "talend_type" not in raw:
        raise CatalogError("cada columna necesita 'name' y 'talend_type'")
    return EnvironmentColumn(
        name=str(raw["name"]),
        talend_type=str(raw["talend_type"]),
        nullable=bool(raw.get("nullable", True)),
        length=raw.get("length"),
        precision=raw.get("precision"),
    )


def _library(raw: dict[str, Any]) -> EnvironmentLibrary:
    if "name" not in raw or "engine" not in raw:
        raise CatalogError("cada librería necesita 'name' y 'engine'")
    return EnvironmentLibrary(
        name=str(raw["name"]),
        engine=str(raw["engine"]),
        connection=_text(raw, "connection"),
        path=_text(raw, "path"),
        note=_text(raw, "note"),
    )


def _dataset(raw: dict[str, Any]) -> EnvironmentDataset:
    if "library" not in raw or "name" not in raw:
        raise CatalogError("cada dataset necesita 'library' y 'name'")
    return EnvironmentDataset(
        library=str(raw["library"]),
        name=str(raw["name"]),
        kind=str(raw.get("kind", "table")),
        target=_text(raw, "target"),
        delimiter=_text(raw, "delimiter"),
        header=raw.get("header"),
        encoding=_text(raw, "encoding"),
        columns=[_column(c) for c in raw.get("columns", [])],
    )


def parse(raw: Any) -> EnvironmentCatalog:
    """Construye el catálogo desde un dato ya leído del JSON (sin validar motores; eso es `validate`)."""
    if not isinstance(raw, dict):
        raise CatalogError("el catálogo debe ser un objeto JSON")
    return EnvironmentCatalog(
        schema_version=int(raw.get("schema_version", 1)),
        project=_text(raw, "project"),
        libraries=[_library(x) for x in raw.get("libraries", [])],
        datasets=[_dataset(x) for x in raw.get("datasets", [])],
    )


def validate(catalog: EnvironmentCatalog, engines: set[str]) -> EnvironmentCatalog:
    """Comprueba lo que haría fallar el Job: motores desconocidos, datasets huérfanos, tipos raros."""
    seen: set[str] = set()
    for lib in catalog.libraries:
        key = lib.name.casefold()
        if key in seen:
            raise CatalogError(f"librería duplicada en el catálogo: {lib.name}")
        seen.add(key)
        if not lib.is_file_library and lib.engine.casefold() not in engines:
            raise CatalogError(
                f"librería {lib.name}: motor {lib.engine!r} sin componentes en el catálogo de Talend "
                f"(admitidos: {', '.join(sorted(engines))})"
            )
    keys: set[tuple[str, str]] = set()
    for dataset in catalog.datasets:
        key = (dataset.library.casefold(), dataset.name.casefold())
        if key in keys:
            raise CatalogError(f"dataset duplicado en el catálogo: {dataset.library}.{dataset.name}")
        keys.add(key)
        if catalog.library(dataset.library) is None:
            raise CatalogError(f"dataset {dataset.library}.{dataset.name}: la librería no está declarada")
        if dataset.kind not in DATASET_KINDS:
            raise CatalogError(f"dataset {dataset.library}.{dataset.name}: tipo {dataset.kind!r} no admitido")
        if dataset.kind == "delimited" and not dataset.delimiter:
            raise CatalogError(f"dataset {dataset.library}.{dataset.name}: falta el delimitador")
        for column in dataset.columns:
            if column.talend_type not in TALEND_TYPES:
                raise CatalogError(
                    f"dataset {dataset.library}.{dataset.name}: tipo {column.talend_type!r} de {column.name} "
                    f"no es un tipo de Talend (admitidos: {', '.join(sorted(TALEND_TYPES))})"
                )
    return catalog


def load(path: Path, engines: set[str]) -> EnvironmentCatalog:
    """Lee y valida un `environment.json`; falla con el motivo exacto, nunca con un catálogo a medias."""
    if not path.exists():
        raise CatalogError(f"no existe el catálogo de entorno: {path}")
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise CatalogError(f"{path.name} no es JSON válido: {error}") from error
    catalog = parse(raw)
    if catalog.schema_version != 1:
        raise CatalogError(
            f"{path.name}: versión de esquema {catalog.schema_version} no soportada (se espera 1)"
        )
    return validate(catalog, engines)


def load_if_present(path: Path, engines: set[str]) -> EnvironmentCatalog | None:
    """El catálogo es opcional: sin él, el plan sigue pidiendo los datos que faltan."""
    return load(path, engines) if path.exists() else None
