"""
M3 DEM export -- writes a DEM object to a GeoTIFF, preserving all metadata
needed by downstream modules (M4/M5/M6).
"""

import os

import rasterio


def export_dem(dem, path):
    """
    Export a DEM object to a GeoTIFF file, preserving pixel size, transform,
    NoData, vertical units, source_type, and (if present) confidence as a
    second band.

    Args:
        dem: a DEM instance (see dem.py).
        path: output file path, e.g. "data/processed/terrain_flat.tif".

    Returns:
        The path written to.
    """
    out_dir = os.path.dirname(path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    count = 2 if dem.confidence is not None else 1

    profile = {
        "driver": "GTiff",
        "height": dem.elevation.shape[0],
        "width": dem.elevation.shape[1],
        "count": count,
        "dtype": "float32",
        "crs": dem.crs,          # None is valid: local-frame-only DEM
        "transform": dem.transform,
        "nodata": dem.nodata,
    }

    with rasterio.open(path, "w", **profile) as dst:
        dst.write(dem.elevation.astype("float32"), 1)
        dst.set_band_description(1, "elevation_m")
        if dem.confidence is not None:
            dst.write(dem.confidence.astype("float32"), 2)
            dst.set_band_description(2, "confidence")

        dst.update_tags(
            pixel_size_m=str(dem.pixel_size_m),
            vertical_units=dem.vertical_units,
            source_type=dem.source_type,
            notes=dem.notes,
        )

    return path
