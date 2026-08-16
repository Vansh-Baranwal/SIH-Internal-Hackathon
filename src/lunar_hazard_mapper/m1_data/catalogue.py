"""Master source catalogue construction owned by Member 1 (M1)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from rasterio.crs import CRS
from rasterio.warp import transform_bounds

PRODUCTS = {
    "TMCORTHO5-1": "TMC_ORTHO",
    "ORTHONAC0.5-1": "HR_ORTHO",
    "NAC": "NAC",
    "TMCDTM": "DEM",
}


def _area(bounds: dict[str, float]) -> float:
    """Return the area of a bounding box."""
    return max(0.0, bounds["east"] - bounds["west"]) * max(0.0, bounds["north"] - bounds["south"])


def _comparable_bounds(record: dict[str, Any], target_crs: CRS) -> dict[str, float] | None:
    """Transform record bounds into target CRS when both CRS values are usable."""
    try:
        source_crs = CRS.from_wkt(record["crs"])
        bounds = record["bounds"]
        west, south, east, north = transform_bounds(
            source_crs, target_crs, bounds["west"], bounds["south"], bounds["east"], bounds["north"]
        )
        return {"west": west, "south": south, "east": east, "north": north}
    except (KeyError, TypeError, ValueError):
        return None


def find_overlapping_hr_tiles(
    tmc_record: dict[str, Any],
    hr_records: list[dict[str, Any]],
    min_overlap_fraction: float = 0.1,
) -> list[str]:
    """Find HR tiles covering at least a fraction of a TMC tile's area."""
    try:
        tmc_crs = CRS.from_wkt(tmc_record["crs"])
    except (KeyError, TypeError, ValueError):
        tmc_bounds = tmc_record["bounds"]
        tmc_area = _area(tmc_bounds)
        if tmc_area <= 0:
            return []
        overlaps = []
        for hr_record in hr_records:
            hr_bounds = hr_record.get("bounds")
            if not hr_bounds:
                continue
            width = min(tmc_bounds["east"], hr_bounds["east"]) - max(tmc_bounds["west"], hr_bounds["west"])
            height = min(tmc_bounds["north"], hr_bounds["north"]) - max(tmc_bounds["south"], hr_bounds["south"])
            if width > 0 and height > 0 and width * height / tmc_area >= min_overlap_fraction:
                overlaps.append(str(hr_record["file_path"]))
        return overlaps
    tmc_bounds = tmc_record["bounds"]
    tmc_area = _area(tmc_bounds)
    if tmc_area <= 0:
        return []
    overlaps: list[str] = []
    for hr_record in hr_records:
        hr_bounds = _comparable_bounds(hr_record, tmc_crs)
        if not hr_bounds:
            continue
        width = min(tmc_bounds["east"], hr_bounds["east"]) - max(tmc_bounds["west"], hr_bounds["west"])
        height = min(tmc_bounds["north"], hr_bounds["north"]) - max(tmc_bounds["south"], hr_bounds["south"])
        if width > 0 and height > 0 and (width * height) / tmc_area >= min_overlap_fraction:
            overlaps.append(str(hr_record["file_path"]))
    return overlaps


def _crs_match(left: dict[str, Any], right: dict[str, Any]) -> bool:
    try:
        return CRS.from_wkt(left["crs"]) == CRS.from_wkt(right["crs"])
    except (KeyError, TypeError, ValueError):
        return False


def _find_reference_tiles(tmc_record: dict[str, Any], hr_records: list[dict[str, Any]], min_overlap_fraction: float) -> list[str]:
    """Find overlaps after converting HR footprints, including lunar projection differences."""
    matches = find_overlapping_hr_tiles(tmc_record, hr_records, min_overlap_fraction)
    if matches:
        return matches
    # HR and TMC use different lunar coordinate frames; derive a common geographic frame.
    try:
        tmc_crs = CRS.from_wkt(tmc_record["crs"])
    except (KeyError, TypeError, ValueError):
        return []
    tmc_bounds = tmc_record["bounds"]
    tmc_area = _area(tmc_bounds)
    if tmc_area <= 0:
        return []
    for hr in hr_records:
        try:
            hr_crs = CRS.from_wkt(hr["crs"])
            h = hr["bounds"]
            west, south, east, north = transform_bounds(hr_crs, tmc_crs, h["west"], h["south"], h["east"], h["north"])
        except (KeyError, TypeError, ValueError):
            continue
        width = min(tmc_bounds["east"], east) - max(tmc_bounds["west"], west)
        height = min(tmc_bounds["north"], north) - max(tmc_bounds["south"], south)
        if width > 0 and height > 0 and width * height / tmc_area >= min_overlap_fraction:
            matches.append(str(hr["file_path"]))
    return matches



def _reference_tiles(tmc_record: dict[str, Any], hr_records: list[dict[str, Any]]) -> list[str]:
    return _find_reference_tiles(tmc_record, hr_records, 0.1)



# End of CRS-aware helpers.


def validate_crs_consistency(records: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Check whether each source product uses one CRS value."""
    grouped: dict[str, set[str]] = {}
    for record in records:
        grouped.setdefault(str(record["source_product"]), set()).add(str(record.get("crs")))
    return {
        product: {"crs_values": sorted(values), "is_consistent": len(values) <= 1}
        for product, values in sorted(grouped.items())
    }


def build_catalogue(inspection_dir: Path, config: dict[str, Any] | None = None) -> dict[str, Any]:
    """Build the authoritative catalogue from Phase 1 inspection manifests."""
    del config  # Reserved for future catalogue policy configuration.
    inspection_dir = Path(inspection_dir)
    source_records: list[dict[str, Any]] = []
    hr_records: list[dict[str, Any]] = []
    payloads: list[tuple[str, dict[str, Any]]] = []
    for path in sorted(inspection_dir.glob("inspection_*.json")):
        if path.name == "inspection_summary.json":
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        label = str(payload["dataset"])
        payloads.append((label, payload))
        if PRODUCTS.get(label) == "HR_ORTHO":
            hr_records.extend(payload.get("records", []))

    for label, payload in payloads:
        product = PRODUCTS.get(label)
        if product is None:
            continue
        for original in payload.get("records", []):
            record = dict(original)
            record["source_product"] = product
            record["processing_status"] = "pending"
            record["include"] = bool(record.get("has_valid_crs") and record.get("has_valid_transform"))
            record["exclusion_reason"] = None if record["include"] else "missing or invalid CRS/transform"
            references = _reference_tiles(record, hr_records) if product == "TMC_ORTHO" else []
            record["reference_available"] = bool(references)
            record["reference_hr_paths"] = references
            source_records.append(record)

    stats: dict[str, Any] = {product: {"total": 0, "reference_available": 0, "excluded": 0} for product in PRODUCTS.values()}
    for record in source_records:
        product_stats = stats[record["source_product"]]
        product_stats["total"] += 1
        product_stats["reference_available"] += int(record["reference_available"])
        product_stats["excluded"] += int(not record["include"])
    return {
        "version": "1.0",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "sources": source_records,
        "stats": stats,
        "crs_consistency": validate_crs_consistency(source_records),
    }


def save_catalogue(catalogue: dict[str, Any], output_path: Path) -> None:
    """Save a catalogue as formatted JSON."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(catalogue, indent=2) + "\n", encoding="utf-8")
