"""SHA256 checksum manifests for Member 1 outputs."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def compute_checksum(path: Path) -> str:
    """Compute a streaming SHA256 digest."""
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def build_checksum_manifest(paths: list[Path]) -> dict[str, str]:
    """Build deterministic path-to-digest records."""
    return {Path(path).as_posix(): compute_checksum(path) for path in sorted(paths, key=lambda item: item.as_posix())}


def save_checksum_manifest(checksums: dict[str, str], output_path: Path) -> None:
    """Write checksum records as formatted JSON."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(checksums, indent=2) + "\n", encoding="utf-8")
