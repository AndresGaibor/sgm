"""Verifica que el SBOM represente cada paquete fijado y cada artefacto de distribución."""

from __future__ import annotations

import copy
import hashlib
import json
import re
import subprocess
import sys
import tomllib
from collections import Counter
from pathlib import Path

import pytest

from tools.seguridad.generar_sbom import generate
from tools.seguridad.sbom_modelo import create_packages, normalize_name

ROOT = Path(__file__).resolve().parents[2]
LOCK = tomllib.loads((ROOT / "uv.lock").read_text(encoding="utf-8"))
CREATED = json.loads((ROOT / "docs/sbom.spdx.json").read_text(encoding="utf-8"))[
    "creationInfo"
]["created"]


def _read_json(path: Path) -> dict:
    assert path.is_file(), f"Falta el artefacto generado: {path.name}"
    return json.loads(path.read_text(encoding="utf-8"))


def _locked_artifacts(package: dict) -> list[dict]:
    artifacts = []
    candidates = []
    if "sdist" in package:
        candidates.append(package["sdist"])
    candidates.extend(sorted(package.get("wheels", []), key=lambda wheel: wheel["url"]))
    for item in candidates:
        filename = item.get("filename") or item["url"].rsplit("/", 1)[-1]
        artifact = {
            "filename": filename,
            "url": item["url"],
            "sha256": item["hash"].removeprefix("sha256:"),
        }
        if "size" in item:
            artifact["size"] = item["size"]
        if "upload-time" in item:
            artifact["uploadTime"] = item["upload-time"]
        artifacts.append(artifact)
    return artifacts


def _package_variant(package: dict) -> tuple[str, str, tuple[str, ...], str]:
    source_fingerprint = package.get("sourceFingerprint")
    if source_fingerprint is None:
        source = json.dumps(package.get("source", {}), sort_keys=True, separators=(",", ":"))
        source_fingerprint = hashlib.sha256(source.encode("utf-8")).hexdigest()
    return (
        normalize_name(package["name"]),
        package["version"],
        tuple(package.get("resolution-markers", package.get("resolutionMarkers", []))),
        source_fingerprint,
    )


def test_spdx_contains_every_locked_version_and_valid_sdist_checksum():
    sbom = _read_json(ROOT / "docs/sbom.spdx.json")
    actual = sbom["packages"]
    assert sbom["spdxVersion"] == "SPDX-2.3"
    assert len(actual) == len(LOCK["package"])
    assert Counter((normalize_name(p["name"]), p["versionInfo"]) for p in actual) == Counter(
        (normalize_name(p["name"]), p["version"]) for p in LOCK["package"]
    )

    for package_lock in LOCK["package"]:
        matches = [
            package
            for package in actual
            if normalize_name(package["name"]) == normalize_name(package_lock["name"])
            and package["versionInfo"] == package_lock["version"]
        ]
        assert len(matches) == 1
        package_spdx = matches[0]
        artifacts = _locked_artifacts(package_lock)
        if not artifacts:
            assert package_spdx["checksums"] == []
            continue

        sdist = next(
            (artifact for artifact in artifacts if artifact["filename"].endswith((".tar.gz", ".zip"))),
            artifacts[0],
        )
        assert package_spdx["packageFileName"] == sdist["filename"]
        assert package_spdx["downloadLocation"] == sdist["url"]
        assert package_spdx["checksums"] == [
            {"algorithm": "SHA256", "checksumValue": sdist["sha256"]}
        ]
        assert re.fullmatch(r"[0-9a-f]{64}", package_spdx["checksums"][0]["checksumValue"])


def test_distribution_manifest_preserves_each_filename_url_and_hash():
    manifest = _read_json(ROOT / "docs/sbom.distribuciones.json")
    actual = manifest["packages"]
    assert manifest["lockSha256"] == hashlib.sha256((ROOT / "uv.lock").read_bytes()).hexdigest()
    assert Counter(_package_variant(package) for package in actual) == Counter(
        _package_variant(package) for package in LOCK["package"]
    )

    for package_lock in LOCK["package"]:
        package_manifest = next(
            package
            for package in actual
            if _package_variant(package) == _package_variant(package_lock)
        )
        assert package_manifest["artifacts"] == _locked_artifacts(package_lock)


def test_report_identifies_lock_scope_and_all_package_versions():
    report = (ROOT / "docs/sbom.md").read_text(encoding="utf-8")
    digest = hashlib.sha256((ROOT / "uv.lock").read_bytes()).hexdigest()
    assert digest in report
    assert "runtime" in report.lower()
    assert "desarrollo" in report.lower()
    assert "Marcadores de resolución uv" in report
    assert "[manifest de distribuciones](sbom.distribuciones.json)" in report
    assert "sbom.distribuciones.json" in report
    for package in LOCK["package"]:
        assert f"{package['name']}@{package['version']}" in report


def test_project_license_is_not_inferred():
    sbom = _read_json(ROOT / "docs/sbom.spdx.json")
    own_packages = [package for package in sbom["packages"] if normalize_name(package["name"]) == "sgm"]
    assert own_packages
    assert all(package["licenseDeclared"] == "NOASSERTION" for package in own_packages)
    assert all("licencia" in package.get("comment", "").lower() for package in own_packages)


def test_generation_is_stable_for_the_same_inputs_and_changes_namespace_with_content():
    report, spdx_text, distributions_text = generate(ROOT, CREATED)
    assert report == (ROOT / "docs/sbom.md").read_text(encoding="utf-8")
    assert spdx_text == (ROOT / "docs/sbom.spdx.json").read_text(encoding="utf-8")
    assert distributions_text == (ROOT / "docs/sbom.distribuciones.json").read_text(
        encoding="utf-8"
    )

    _, changed_text, _ = generate(ROOT, "2026-11-11T00:00:00Z")
    assert json.loads(changed_text)["documentNamespace"] != json.loads(spdx_text)["documentNamespace"]


def test_distinct_locked_variants_keep_unique_spdx_ids_and_relationship_targets(tmp_path: Path):
    (tmp_path / "pyproject.toml").write_text(
        """
[project]
name = "sgm"
version = "0.2.0"
requires-python = ">=3.12"
dependencies = ["referencing>=0.1"]

[dependency-groups]
dev = []
""",
        encoding="utf-8",
    )
    (tmp_path / "uv.lock").write_text(
        """
version = 1
revision = 3
requires-python = ">=3.12"

[[package]]
name = "sgm"
version = "0.2.0"
source = { editable = "." }
dependencies = [{ name = "referencing" }]

[[package]]
name = "referencing"
version = "0.1.0"
source = { registry = "https://pypi.org/simple" }
dependencies = [{ name = "attrs", version = "26.1.0", source = { registry = "https://pypi.org/simple" }, marker = "python_full_version >= '3.12'" }]

[[package]]
name = "attrs"
version = "24.1.0"
source = { registry = "https://pypi.org/simple" }
resolution-markers = ["python_full_version < '3.12'"]
sdist = { url = "https://files.pythonhosted.org/attrs-24.1.0.tar.gz", hash = "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa" }

[[package]]
name = "attrs"
version = "26.1.0"
source = { registry = "https://pypi.org/simple" }
resolution-markers = ["python_full_version >= '3.12'"]
sdist = { url = "https://files.pythonhosted.org/attrs-26.1.0.tar.gz", hash = "sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb" }

[[package]]
name = "attrs"
version = "26.1.0"
source = { registry = "https://mirror.example/simple" }
resolution-markers = ["python_full_version >= '3.12' and sys_platform == 'linux'"]
sdist = { url = "https://mirror.example/attrs-26.1.0.tar.gz", hash = "sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc" }
""",
        encoding="utf-8",
    )

    project = tomllib.loads((tmp_path / "pyproject.toml").read_text(encoding="utf-8"))
    ambiguous_lock = tomllib.loads((tmp_path / "uv.lock").read_text(encoding="utf-8"))
    ambiguous_lock["package"][1]["dependencies"] = [{"name": "attrs"}]
    with pytest.raises(ValueError, match="ambigua"):
        create_packages(ambiguous_lock, project)

    _, spdx_text, _ = generate(tmp_path, "2026-11-10T19:36:52Z")
    sbom = json.loads(spdx_text)
    attrs_packages = [
        package for package in sbom["packages"] if normalize_name(package["name"]) == "attrs"
    ]
    assert len(attrs_packages) == 3
    assert len({package["SPDXID"] for package in attrs_packages}) == 3
    sgm_id = next(package["SPDXID"] for package in sbom["packages"] if package["name"] == "sgm")
    referencing_package = next(
        package for package in sbom["packages"] if package["name"] == "referencing"
    )
    dependency_targets = {
        relationship["relatedSpdxElement"]
        for relationship in sbom["relationships"]
        if relationship["spdxElementId"] == referencing_package["SPDXID"]
    }
    attrs_26 = next(
        package
        for package in attrs_packages
        if package["versionInfo"] == "26.1.0" and package.get("externalRefs")
    )
    attrs_26_id = attrs_26["SPDXID"]
    assert dependency_targets == {attrs_26_id}
    relationship = next(
        relation
        for relation in sbom["relationships"]
        if relation["spdxElementId"] == referencing_package["SPDXID"]
    )
    assert "marcador de dependencia" in relationship["comment"]
    assert "marcadores de resolución del destino" in relationship["comment"]
    attrs_24 = next(package for package in attrs_packages if package["versionInfo"] == "24.1.0")
    attrs_mirror = next(
        package
        for package in attrs_packages
        if package["versionInfo"] == "26.1.0" and not package.get("externalRefs")
    )
    assert "Alcance: sin clasificar" in attrs_24["comment"]
    assert "Alcance: sin clasificar" in attrs_mirror["comment"]
    assert "Alcance: runtime" in attrs_26["comment"]
    sgm_targets = {
        relation["relatedSpdxElement"]
        for relation in sbom["relationships"]
        if relation["spdxElementId"] == sgm_id
    }
    assert sgm_targets == {referencing_package["SPDXID"]}


def test_invalid_lock_digest_is_rejected():
    lock = copy.deepcopy(LOCK)
    package = next(item for item in lock["package"] if item.get("sdist"))
    package["sdist"]["hash"] = "sha256:not-a-digest"
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))

    with pytest.raises(ValueError, match="SHA-256"):
        create_packages(lock, project)


def test_generator_script_check_mode_is_runnable():
    result = subprocess.run(
        [sys.executable, str(ROOT / "tools/seguridad/generar_sbom.py"), "--check"],
        cwd=ROOT,
        capture_output=True,
        check=False,
        text=True,
    )

    assert result.returncode == 0, result.stderr
