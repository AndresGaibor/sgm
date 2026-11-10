"""Genera el SBOM SPDX y el inventario humano desde `pyproject.toml` y `uv.lock`."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tomllib
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.seguridad.sbom_grafo import normalize_name, package_identity, resolve_dependency  # noqa: E402
from tools.seguridad.sbom_modelo import create_packages  # noqa: E402


def generate(root: Path, created: str | None = None) -> tuple[str, str, str]:
    """Devuelve el informe Markdown, el SPDX JSON y el manifest de artefactos."""
    lock_path = root / "uv.lock"
    lock_bytes = lock_path.read_bytes()
    lock = tomllib.loads(lock_bytes.decode("utf-8"))
    pyproject = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
    project = pyproject["project"]
    name = project["name"]
    version = project["version"]
    created = created or datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )
    lock_digest = hashlib.sha256(lock_bytes).hexdigest()
    packages, rows, distribution_packages = create_packages(lock, pyproject)
    sorted_locked_packages = sorted(lock["package"], key=package_identity)
    package_ids = {
        package_identity(locked_package): spdx_package["SPDXID"]
        for locked_package, spdx_package in zip(
            sorted_locked_packages, packages, strict=True
        )
    }
    packages_by_name: dict[str, list[dict]] = {}
    for locked_package in lock["package"]:
        packages_by_name.setdefault(normalize_name(locked_package["name"]), []).append(
            locked_package
        )

    relationships = []
    for locked_package in lock["package"]:
        source_id = package_ids[package_identity(locked_package)]
        for dependency in locked_package.get("dependencies", []):
            target_package = resolve_dependency(dependency, packages_by_name)
            target_id = package_ids[package_identity(target_package)]
            comment_parts = []
            if dependency.get("marker"):
                comment_parts.append(f"marcador de dependencia uv: {dependency['marker']}")
            if locked_package.get("resolution-markers"):
                markers = "; ".join(locked_package["resolution-markers"])
                comment_parts.append(f"marcadores de resolución del origen: {markers}")
            if target_package.get("resolution-markers"):
                markers = "; ".join(target_package["resolution-markers"])
                comment_parts.append(f"marcadores de resolución del destino: {markers}")
            relationship = {
                "spdxElementId": source_id,
                "relationshipType": "DEPENDS_ON",
                "relatedSpdxElement": target_id,
            }
            if comment_parts:
                relationship["comment"] = "; ".join(comment_parts)
            relationships.append(relationship)
        for dependency in locked_package.get("dev-dependencies", {}).get("dev", []):
            target_package = resolve_dependency(dependency, packages_by_name)
            markers = target_package.get("resolution-markers", [])
            comment = "Dependencia del grupo de desarrollo fijada en uv.lock."
            if dependency.get("marker"):
                comment += f" Marcador de dependencia uv: {dependency['marker']}."
            if markers:
                comment += " Marcadores de resolución de la variante: " + "; ".join(markers)
            relationships.append(
                {
                    "spdxElementId": source_id,
                    "relationshipType": "DEPENDS_ON",
                    "relatedSpdxElement": package_ids[package_identity(target_package)],
                    "comment": comment,
                }
            )
    relationships = sorted(
        relationships,
        key=lambda relationship: (
            relationship["spdxElementId"],
            relationship["relatedSpdxElement"],
            relationship.get("comment", ""),
        ),
    )
    described = sorted(
        package_ids[package_identity(locked_package)]
        for locked_package in lock["package"]
        if normalize_name(locked_package["name"]) == normalize_name(name)
        and any(key in locked_package.get("source", {}) for key in ("editable", "virtual"))
    )
    document = {
        "spdxVersion": "SPDX-2.3",
        "dataLicense": "CC0-1.0",
        "SPDXID": "SPDXRef-DOCUMENT",
        "name": f"{name}-{version}",
        "documentDescribes": described,
        "creationInfo": {"created": created, "creators": ["Tool: sgm-sbom-audit 0.1"]},
        "packages": packages,
        "relationships": relationships,
    }
    canonical_document = json.dumps(
        document, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    document_digest = hashlib.sha256(canonical_document).hexdigest()
    safe_name = quote(name, safe="")
    safe_version = quote(version, safe="")
    document["documentNamespace"] = (
        f"https://spdx.org/spdxdocs/{safe_name}-{safe_version}-{document_digest}"
    )
    distribution_manifest = {
        "format": "sgm-distribution-artifacts-1",
        "name": name,
        "version": version,
        "lockSha256": lock_digest,
        "packages": distribution_packages,
    }

    package_count = len(packages)
    artifact_count = sum(len(package["artifacts"]) for package in distribution_packages)
    runtime_direct = len(project.get("dependencies", []))
    dev_direct = len(pyproject.get("dependency-groups", {}).get("dev", []))
    lines = [
        f"# SBOM de {name}",
        "",
        f"- Versión del paquete: `{version}`.",
        f"- Variantes fijadas: {package_count} (incluye variantes por plataforma y paquete local).",
        f"- Artefactos de distribución con hash: {artifact_count}.",
        (
            f"- Dependencias directas declaradas: {runtime_direct} runtime "
            f"y {dev_direct} de desarrollo."
        ),
        f"- SHA-256 de `uv.lock`: `{lock_digest}`.",
        f"- Fecha del inventario: `{created}`.",
        "- Formato interoperable: [SPDX 2.3](sbom.spdx.json).",
        (
            "- Mapeo exacto de archivo, URL y hash: [manifest de distribuciones]"
            "(sbom.distribuciones.json)."
        ),
        "",
        "## Inventario",
        "",
        (
            "El checksum SPDX identifica el archivo de origen (sdist) cuando está disponible. "
            "El manifest complementario conserva la relación individual entre cada wheel/sdist, "
            "su URL y su SHA-256."
        ),
        "",
        (
            "Las licencias usan identificadores SPDX cuando la metadata o una fuente del "
            "publicador las demuestra. `NOASSERTION` significa que no se asignó una licencia "
            "sin evidencia suficiente."
        ),
        "",
        (
            "| Paquete | Marcadores de resolución uv | Alcance | Relación | "
            "Licencia declarada | Artefactos con hash | Archivo representativo |"
        ),
        "|---|---|---|---|---:|---|",
    ]
    lines.extend("| " + " | ".join(row) + " |" for row in rows)
    lines += [
        "",
        "## Hallazgos y límites",
        "",
        (
            "- El paquete `sgm` no declara licencia en `pyproject.toml`; queda `NOASSERTION` y "
            "requiere decisión legal antes de distribuirlo fuera de la organización."
        ),
        "- Excepciones de metadata verificadas en fuentes de los publicadores: `colorama 0.4.6`",
        "  usa BSD de 3 cláusulas ([README del proyecto](https://github.com/tartley/colorama));",
        "  `markdown-it-py 4.2.0` y `mdurl 0.1.2` declaran MIT en sus publicaciones de PyPI.",
        "- Este inventario no es un escaneo de vulnerabilidades ni una aprobación de",
        "  compatibilidad legal.",
        "- Regenerar los tres artefactos con `uv run python tools/seguridad/generar_sbom.py`;",
        "  verificar sin escribir con `uv run python tools/seguridad/generar_sbom.py --check`.",
        "",
    ]
    markdown = "\n".join(lines)
    spdx_json = json.dumps(document, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    distributions_json = (
        json.dumps(distribution_manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    )
    return markdown, spdx_json, distributions_json


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--check", action="store_true", help="falla si el snapshot no está al día")
    args = parser.parse_args()
    markdown_path = args.root / "docs/sbom.md"
    spdx_path = args.root / "docs/sbom.spdx.json"
    distributions_path = args.root / "docs/sbom.distribuciones.json"
    created = None
    if args.check and spdx_path.is_file():
        created = json.loads(spdx_path.read_text(encoding="utf-8"))["creationInfo"]["created"]
    markdown, spdx_json, distributions_json = generate(args.root, created)
    if args.check:
        correct = all(
            path.is_file() and path.read_text(encoding="utf-8") == expected
            for path, expected in (
                (markdown_path, markdown),
                (spdx_path, spdx_json),
                (distributions_path, distributions_json),
            )
        )
        if not correct:
            print(
                "SBOM ausente o desactualizado; ejecuta tools/seguridad/generar_sbom.py",
                file=sys.stderr,
            )
            return 1
        print("SBOM y manifest de distribuciones coinciden con pyproject.toml y uv.lock.")
        return 0
    markdown_path.write_text(markdown, encoding="utf-8", newline="\n")
    spdx_path.write_text(spdx_json, encoding="utf-8", newline="\n")
    distributions_path.write_text(distributions_json, encoding="utf-8", newline="\n")
    print(f"Generados {markdown_path}, {spdx_path} y {distributions_path}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
