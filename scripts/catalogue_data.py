"""Build the M1 source catalogue from Phase 1 inspection manifests."""

from __future__ import annotations

import json
from pathlib import Path

from lunar_hazard_mapper.m1_data.catalogue import build_catalogue, save_catalogue


def main() -> int:
    project_root = Path(__file__).resolve().parents[1]
    manifest_dir = project_root / "data" / "manifests"
    output_path = manifest_dir / "source_catalogue.json"
    catalogue = build_catalogue(manifest_dir)
    save_catalogue(catalogue, output_path)

    for product, report in catalogue["crs_consistency"].items():
        if not report["is_consistent"]:
            print(f"WARNING: mixed CRS values for {product}: {report['crs_values']}")
    print(json.dumps(catalogue["stats"], indent=2))
    print(f"Saved catalogue to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
