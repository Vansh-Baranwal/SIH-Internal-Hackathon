"""Source raster catalogue."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

from .checksums import calculate_sha256
from .metadata import inspect_raster
from .utils import write_json


def raster_paths(inputs: Iterable[str | Path]) -> list[Path]:
    paths: list[Path] = []
    for value in inputs:
        path = Path(value)
        if path.is_dir():
            paths.extend(sorted(p for p in path.iterdir() if p.suffix.lower() in {".tif", ".tiff"}))
        elif path.is_file():
            paths.append(path)
        else:
            raise FileNotFoundError(path)
    return sorted(set(paths))


def build_source_catalog(inputs: Iterable[str | Path], output: str | Path, *, allow_unreferenced: bool = False) -> dict:
    records = []
    for path in raster_paths(inputs):
        record = inspect_raster(path, allow_unreferenced=allow_unreferenced)
        record.update({
            "path": record.pop("file_path"),
            "checksum": calculate_sha256(path),
            "processing_status": "raw",
            "reference_data_available": False,
            "acquisition_metadata": record.get("metadata", {}),
        })
        records.append(record)
    manifest = {"schema_version": "1.0", "sources": records}
    write_json(output, manifest)
    return manifest
