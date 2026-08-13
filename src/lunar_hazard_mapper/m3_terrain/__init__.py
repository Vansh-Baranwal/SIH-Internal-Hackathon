"""
M3 terrain package public interface.

Downstream members (M4/M5/M6) should import from here rather than reaching
into individual M3 files directly -- this keeps M3's internals free to
change without breaking other members' code.
"""

import rasterio

from .dem import DEM, generate_dem, to_local_frame
from .synthetic import create_synthetic_terrain
from .export import export_dem
from .validation import validate_dem, qa_check_dem, qa_check_exported_file

__all__ = [
    "DEM",
    "generate_dem",
    "to_local_frame",
    "create_synthetic_terrain",
    "export_dem",
    "validate_dem",
    "qa_check_dem",
    "qa_check_exported_file",
    "get_terrain_product",
]


def get_terrain_product(path):
    """
    Stable M3 -> M4 interface.

    Loads an exported DEM GeoTIFF (written by export_dem) and returns a
    plain dict with exactly what downstream modules need, so M4/M5/M6 never
    have to deal with rasterio directly.

    Args:
        path: path to a GeoTIFF written by export_dem().

    Returns:
        dict with:
            "path": the file path (str)
            "elevation": 2D numpy array of elevation (meters)
            "confidence": 2D numpy array or None if not present
            "crs": CRS string or None (local-frame-only DEM)
            "is_georeferenced": True if crs is a real CRS, False if this
                is a local-frame-only prototype/synthetic DEM
            "pixel_size_m": float
            "transform": affine transform (pixel -> local meters)
            "nodata": nodata sentinel value
            "vertical_units": e.g. "meters"
            "source_type": "synthetic" | "sr_estimated" | "measured"
            "notes": provenance / limitation notes
    """
    with rasterio.open(path) as src:
        elevation = src.read(1)
        confidence = src.read(2) if src.count >= 2 else None
        tags = src.tags()

        return {
            "path": path,
            "elevation": elevation,
            "confidence": confidence,
            "crs": src.crs.to_string() if src.crs else None,
            "is_georeferenced": src.crs is not None,
            "pixel_size_m": float(tags.get("pixel_size_m", src.transform.a)),
            "transform": src.transform,
            "nodata": src.nodata,
            "vertical_units": tags.get("vertical_units", "unknown"),
            "source_type": tags.get("source_type", "unknown"),
            "notes": tags.get("notes", ""),
        }