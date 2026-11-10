"""Construye registros de paquetes SPDX y detalles de distribución desde un lock de uv."""

from __future__ import annotations

import hashlib
import importlib.metadata as metadata
import json
import re
from urllib.parse import quote, urlsplit

from tools.seguridad.sbom_grafo import (
    dependency_closure,
    normalize_name,
    package_identity,
    resolve_dependency,
)

_LICENSE_OVERRIDES = {
    ("colorama", "0.4.6"): (
        "BSD-3-Clause",
        "https://github.com/tartley/colorama",
        "README del proyecto: licencia BSD de 3 cláusulas.",
    ),
    ("markdown-it-py", "4.2.0"): (
        "MIT",
        "https://pypi.org/project/markdown-it-py/4.2.0/",
        "Metadata de la publicación exacta en PyPI.",
    ),
    ("mdurl", "0.1.2"): (
        "MIT",
        "https://pypi.org/project/mdurl/0.1.2/",
        "Metadata de la publicación exacta en PyPI.",
    ),
}
_KNOWN_LICENSES = {
    "mit": "MIT",
    "mit license": "MIT",
    "apache-2.0": "Apache-2.0",
    "bsd-2-clause": "BSD-2-Clause",
    "bsd-3-clause": "BSD-3-Clause",
    "isc license": "ISC",
    "bsd 2-clause license": "BSD-2-Clause",
    "bsd 3-clause license": "BSD-3-Clause",
    "psf-2.0": "PSF-2.0",
    "python software foundation license": "PSF-2.0",
}


def spdx_package_id(package: dict) -> str:
    safe_name = re.sub(r"[^A-Za-z0-9.-]", "-", normalize_name(package["name"]))
    identity_hash = hashlib.sha256(package_identity(package).encode("utf-8")).hexdigest()
    return f"SPDXRef-Package-{safe_name}-{identity_hash}"


def _is_official_pypi(package: dict) -> bool:
    registry = package.get("source", {}).get("registry", "").rstrip("/")
    return registry == "https://pypi.org/simple"


def _license_declaration(package: dict) -> tuple[str, str]:
    name = normalize_name(package["name"])
    version = package["version"]
    if any(key in package.get("source", {}) for key in ("editable", "virtual")):
        return "NOASSERTION", "El proyecto no declara una licencia; requiere decisión legal."
    if _is_official_pypi(package) and (name, version) in _LICENSE_OVERRIDES:
        expression, source, reason = _LICENSE_OVERRIDES[(name, version)]
        return expression, f"{reason} Fuente: {source}"
    if not _is_official_pypi(package):
        return "NOASSERTION", "El origen bloqueado no es el índice oficial de PyPI."
    try:
        distribution = metadata.distribution(package["name"])
    except metadata.PackageNotFoundError:
        return "NOASSERTION", "No se encontró metadata local de la distribución."
    if distribution.version != version:
        return "NOASSERTION", "La metadata instalada no coincide con la versión de uv.lock."
    distribution_metadata = distribution.metadata
    expression = distribution_metadata.get("License-Expression")
    if expression:
        return expression.strip(), "License-Expression de la metadata de la distribución fijada."
    label = (distribution_metadata.get("License") or "").strip()
    known_license = _KNOWN_LICENSES.get(label.casefold())
    if known_license:
        return known_license, "Campo License de la metadata de la distribución fijada."
    return "NOASSERTION", "La metadata de la distribución no declara una licencia identificable."


def _safe_url(value: str) -> str:
    parsed = urlsplit(value)
    if parsed.scheme not in {"http", "https"} or parsed.username or parsed.password:
        return "NOASSERTION"
    if parsed.query or parsed.fragment:
        return "NOASSERTION"
    return value


def _distribution_artifacts(package: dict) -> list[dict]:
    candidates = []
    if "sdist" in package:
        candidates.append(package["sdist"])
    candidates.extend(sorted(package.get("wheels", []), key=lambda wheel: wheel["url"]))
    artifacts = []
    for item in candidates:
        filename = item.get("filename") or urlsplit(item["url"]).path.rsplit("/", 1)[-1]
        digest = item["hash"]
        algorithm, separator, value = digest.partition(":")
        if (
            not separator
            or algorithm.casefold() != "sha256"
            or not re.fullmatch(r"[0-9a-fA-F]{64}", value)
        ):
            raise ValueError("uv.lock contiene un digest que no es SHA-256 hexadecimal válido")
        artifact = {
            "filename": filename,
            "url": _safe_url(item["url"]),
            "sha256": value.lower(),
        }
        if "size" in item:
            artifact["size"] = item["size"]
        if "upload-time" in item:
            artifact["uploadTime"] = item["upload-time"]
        artifacts.append(artifact)
    return artifacts


def create_packages(lock: dict, pyproject: dict) -> tuple[list[dict], list[list[str]], list[dict]]:
    locked_packages = lock["package"]
    packages_by_name: dict[str, list[dict]] = {}
    identities = set()
    for package in locked_packages:
        identity = package_identity(package)
        if identity in identities:
            raise ValueError("uv.lock contiene una variante duplicada de paquete")
        identities.add(identity)
        packages_by_name.setdefault(normalize_name(package["name"]), []).append(package)
    project = pyproject["project"]
    project_packages = [
        package
        for package in packages_by_name.get(normalize_name(project["name"]), [])
        if any(key in package.get("source", {}) for key in ("editable", "virtual"))
    ]
    if not project_packages:
        raise ValueError("uv.lock no contiene el paquete local del proyecto")
    for package in locked_packages:
        for dependency in package.get("dependencies", []):
            resolve_dependency(dependency, packages_by_name)
        for dependency in package.get("dev-dependencies", {}).get("dev", []):
            resolve_dependency(dependency, packages_by_name)

    runtime_direct = [
        resolve_dependency(dependency, packages_by_name)
        for package in project_packages
        for dependency in package.get("dependencies", [])
    ]
    dev_direct = [
        resolve_dependency(dependency, packages_by_name)
        for package in project_packages
        for dependency in package.get("dev-dependencies", {}).get("dev", [])
    ]
    runtime_reachable = dependency_closure(runtime_direct, packages_by_name)
    dev_reachable = dependency_closure(dev_direct, packages_by_name)
    direct_identities = {
        package_identity(package) for package in runtime_direct + dev_direct
    }

    spdx_packages = []
    markdown_rows = []
    distribution_packages = []
    for package in sorted(locked_packages, key=package_identity):
        name = normalize_name(package["name"])
        identity = package_identity(package)
        local = any(key in package.get("source", {}) for key in ("editable", "virtual"))
        scope = "aplicación" if local else ", ".join(
            label
            for active, label in (
                (runtime_reachable, "runtime"),
                (dev_reachable, "desarrollo"),
            )
            if identity in active
        ) or "sin clasificar"
        relation = (
            "propio"
            if local
            else "directa"
            if identity in direct_identities
            else "transitiva"
            if identity in runtime_reachable | dev_reachable
            else "sin ruta detectada"
        )
        license_expression, license_evidence = _license_declaration(package)
        artifacts = _distribution_artifacts(package)
        canonical_artifact = next(
            (
                artifact
                for artifact in artifacts
                if artifact["filename"].endswith((".tar.gz", ".zip"))
            ),
            artifacts[0] if artifacts else None,
        )
        package_id = spdx_package_id(package)
        package_comment = f"Alcance: {scope}; relación: {relation}. {license_evidence}"
        markers = package.get("resolution-markers", [])
        if markers:
            package_comment += " Marcadores de resolución uv: " + "; ".join(markers)
        spdx_package = {
            "name": package["name"],
            "SPDXID": package_id,
            "versionInfo": package["version"],
            "downloadLocation": canonical_artifact["url"] if canonical_artifact else "NOASSERTION",
            "filesAnalyzed": False,
            "licenseConcluded": "NOASSERTION",
            "licenseDeclared": license_expression,
            "copyrightText": "NOASSERTION",
            "comment": package_comment,
            "sourceInfo": (
                "Versión fijada en uv.lock; todos los artefactos se detallan en "
                "docs/sbom.distribuciones.json."
            ),
            "checksums": (
                [
                    {
                        "algorithm": "SHA256",
                        "checksumValue": canonical_artifact["sha256"],
                    }
                ]
                if canonical_artifact and canonical_artifact["url"] != "NOASSERTION"
                else []
            ),
            "primaryPackagePurpose": "APPLICATION" if local else "LIBRARY",
        }
        if canonical_artifact and canonical_artifact["filename"]:
            spdx_package["packageFileName"] = canonical_artifact["filename"]
        if _is_official_pypi(package) and not local:
            spdx_package["externalRefs"] = [
                {
                    "referenceCategory": "PACKAGE-MANAGER",
                    "referenceType": "purl",
                    "referenceLocator": f"pkg:pypi/{name}@{package['version']}",
                }
            ]
        spdx_packages.append(spdx_package)
        distribution_packages.append(
            {
                "name": package["name"],
                "version": package["version"],
                "spdxId": package_id,
                "sourceFingerprint": hashlib.sha256(
                    json.dumps(
                        package.get("source", {}), sort_keys=True, separators=(",", ":")
                    ).encode("utf-8")
                ).hexdigest(),
                "resolutionMarkers": markers,
                "artifacts": artifacts,
            }
        )
        source_link = "NOASSERTION"
        if canonical_artifact and canonical_artifact["url"] != "NOASSERTION":
            filename = canonical_artifact["filename"].replace("[", "\\[").replace("]", "\\]")
            artifact_url = quote(canonical_artifact["url"], safe=":/-._~")
            source_link = f"[{filename}]({artifact_url})"
        escaped_markers = [
            marker.replace("|", "\\|").replace("`", "&#96;").replace("\n", " ")
            for marker in markers
        ]
        marker_text = "<br>".join(f"`{marker}`" for marker in escaped_markers) or "sin marcadores"
        markdown_rows.append(
            [
                f"{package['name']}@{package['version']}",
                marker_text,
                scope,
                relation,
                license_expression,
                str(len(artifacts)),
                source_link,
            ]
        )
    return spdx_packages, markdown_rows, distribution_packages
