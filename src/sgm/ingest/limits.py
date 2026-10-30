"""Límites de una importación. Protegen contra lotes enormes o archivos anómalos."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ImportLimits:
    max_file_bytes: int = 5 * 1024 * 1024
    max_files: int = 5000
    max_zip_members: int = 10_000
    max_total_bytes: int = 256 * 1024 * 1024
