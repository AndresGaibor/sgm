"""Resuelve variantes y cierres del grafo de dependencias de `uv.lock`."""

from __future__ import annotations

import json
import re


def normalize_name(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def package_identity(package: dict) -> str:
    identity = {
        "name": normalize_name(package["name"]),
        "version": package["version"],
        "source": package.get("source", {}),
        "resolution_markers": package.get("resolution-markers", []),
    }
    return json.dumps(identity, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def resolve_dependency(reference: dict, packages_by_name: dict[str, list[dict]]) -> dict:
    name = normalize_name(reference["name"])
    candidates = list(packages_by_name.get(name, []))
    if "version" in reference:
        candidates = [
            package for package in candidates if package["version"] == reference["version"]
        ]
    if "source" in reference:
        candidates = [
            package for package in candidates if package.get("source", {}) == reference["source"]
        ]
    if len(candidates) != 1:
        reason = "ausente" if not candidates else "ambigua"
        raise ValueError(
            f"Referencia de dependencia {reason} en uv.lock: {reference.get('name')}"
        )
    return candidates[0]


def dependency_closure(roots: list[dict], packages_by_name: dict[str, list[dict]]) -> set[str]:
    visited: set[str] = set()
    pending = list(roots)
    while pending:
        package = pending.pop()
        identity = package_identity(package)
        if identity in visited:
            continue
        visited.add(identity)
        pending.extend(
            resolve_dependency(reference, packages_by_name)
            for reference in package.get("dependencies", [])
        )
    return visited
