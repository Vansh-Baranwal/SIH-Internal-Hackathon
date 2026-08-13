"""
M3 DEM data structure and construction.

IMPORTANT SCIENTIFIC CONSTRAINT (see docs/members/m3_dem_terrain.md):
5 m optical imagery + super-resolution does NOT automatically give true 1 m
elevation. Optical super-resolution (sharper image) and elevation
reconstruction (actual terrain height) are different problems. This module
never silently treats a raw optical/super-resolved image as elevation --
callers must go through synthetic terrain, or explicitly acknowledge the
assumption via `assume_optical_as_elevation=True` when passing a raw image,
which is intentionally not the default.
"""

import warnings
from dataclasses import dataclass, field
from typing import Optional

import numpy as np
from affine import Affine


# Source-type labels used throughout M3. Only "measured" implies validated
# real-world elevation accuracy -- never set that from this module.
SOURCE_SYNTHETIC = "synthetic"
SOURCE_SR_ESTIMATED = "sr_estimated"
SOURCE_MEASURED = "measured"


@dataclass
class DEM:
    """
    M3's terrain/elevation product.

    This is the object every other M3 function (export, validate, QA) and
    the M3->M4 interface operate on. Coordinates follow the project's local
    convention (configs/coordinate_convention.yaml): x=east, y=north,
    z=up, all in meters.

    `crs` is None for local-frame-only DEMs (the current synthetic
    prototype output -- there is no geodetic reference, only local meters).
    It becomes a real CRS string only once M3 is fed genuinely georeferenced
    input (e.g. from M1/M2 once their output contract is defined). Use
    `is_georeferenced` rather than checking `crs` directly, so downstream
    code and QA have one clear way to ask "is this a real geospatial DEM or
    a local-only prototype terrain?".
    """
    elevation: np.ndarray          # 2D float32 array, elevation in meters
    pixel_size_m: float            # ground sampling distance per pixel
    transform: Affine              # affine pixel->local-meters transform
    crs: Optional[str]             # None for local-only (no geodetic CRS yet)
    nodata: float                  # sentinel value for invalid/missing cells
    vertical_units: str            # e.g. "meters"
    source_type: str               # "synthetic" | "sr_estimated" | "measured"
    confidence: Optional[np.ndarray] = None  # optional per-pixel confidence
    notes: str = ""                # free-text provenance / limitations
    extra: dict = field(default_factory=dict)  # feature params, etc.

    @property
    def shape(self):
        return self.elevation.shape

    @property
    def is_georeferenced(self):
        """True if this DEM carries a real geodetic CRS, False if it is a
        local-frame-only prototype/synthetic DEM (crs=None)."""
        return self.crs is not None


def generate_dem(source, pixel_size_m=None, origin_xy=(0.0, 0.0),
                  nodata=-9999.0, vertical_units="meters", crs=None,
                  assume_optical_as_elevation=False, notes=""):
    """
    Build a DEM object from a terrain source.

    Args:
        source: EITHER
            (a) a dict produced by a synthetic terrain generator
                (synthetic/terrain/*.py or m3_terrain/synthetic.py),
                containing "elevation", "pixel_size_m", "source_type", or
            (b) a raw 2D numpy array. Raw arrays are assumed to be optical /
                super-resolved image data, NOT elevation, unless
                `assume_optical_as_elevation=True` is explicitly passed.
        pixel_size_m: overrides source's pixel size if given.
        origin_xy: (x, y) local-meter coordinates of the top-left pixel.
        nodata: sentinel value for invalid cells.
        vertical_units: elevation units (meters by default).
        crs: optional real CRS string (e.g. an EPSG/WKT/PROJ string) if this
            DEM is genuinely georeferenced. Left as None by default -- the
            current synthetic prototype pipeline has no geodetic reference,
            only local meters, and this must never be set to a real CRS
            just to silence a warning or make output look more complete
            than it is.
        assume_optical_as_elevation: must be explicitly True to build a DEM
            from a raw image array. Left False by default so we never
            silently invent an elevation-reconstruction method.
        notes: extra provenance text, appended to any auto-generated notes.

    Returns:
        DEM instance.

    Raises:
        ValueError: if a raw image array is given without explicitly
            acknowledging the optical-vs-elevation assumption, or if
            required metadata is missing.
    """
    if isinstance(source, dict) and "elevation" in source:
        elevation = np.asarray(source["elevation"], dtype=np.float32)
        resolved_pixel_size = pixel_size_m or source.get("pixel_size_m")
        source_type = source.get("source_type", SOURCE_SYNTHETIC)
        confidence = source.get("confidence")
        extra = {k: v for k, v in source.items()
                 if k not in ("elevation", "pixel_size_m", "source_type",
                              "confidence")}
        auto_notes = ""
    elif isinstance(source, np.ndarray):
        if not assume_optical_as_elevation:
            raise ValueError(
                "Refusing to build a DEM directly from a raw image array. "
                "Optical (super-resolved) imagery is not the same as "
                "elevation data -- see the M3 scientific constraint in "
                "docs/members/m3_dem_terrain.md. If you have a specific, "
                "documented method for deriving elevation from this image "
                "(e.g. photoclinometry/shape-from-shading with a known "
                "light source), pass assume_optical_as_elevation=True and "
                "record the method in `notes`."
            )
        warnings.warn(
            "generate_dem(): building a DEM from a raw image with "
            "assume_optical_as_elevation=True. This elevation is an "
            "ESTIMATE derived from optical imagery, not independently "
            "validated, and must never be treated as measured elevation. "
            "It will be tagged source_type='sr_estimated'.",
            UserWarning,
            stacklevel=2,
        )
        elevation = np.asarray(source, dtype=np.float32)
        resolved_pixel_size = pixel_size_m
        source_type = SOURCE_SR_ESTIMATED
        confidence = None
        extra = {}
        auto_notes = ("Derived from a super-resolved optical image via an "
                       "explicitly acknowledged (not independently "
                       "validated) elevation assumption.")
    else:
        raise ValueError(
            "source must be a terrain dict (with 'elevation') or a numpy "
            "array."
        )

    if resolved_pixel_size is None:
        raise ValueError("pixel_size_m is required (not found on source "
                          "and not passed explicitly).")

    origin_x, origin_y = origin_xy
    transform = Affine.translation(origin_x, origin_y) * Affine.scale(
        resolved_pixel_size, -resolved_pixel_size
    )

    combined_notes = " ".join(n for n in (auto_notes, notes) if n).strip()

    return DEM(
        elevation=elevation,
        pixel_size_m=resolved_pixel_size,
        transform=transform,
        crs=crs,
        nodata=nodata,
        vertical_units=vertical_units,
        source_type=source_type,
        confidence=confidence,
        notes=combined_notes,
        extra=extra,
    )


def to_local_frame(dem):
    """
    Compute local simulation-frame (x=east, y=north in meters) coordinates
    for every pixel CENTER in a DEM, per configs/coordinate_convention.yaml.

    This is M3's contribution to the local coordinate frame M6 needs: pixel
    indices are converted to local meters using the DEM's affine transform,
    with z taken directly from the elevation array (already in meters, up).
    Original transform/origin is preserved on the DEM object for provenance.

    Uses pixel CENTERS (col+0.5, row+0.5), matching standard raster
    convention (e.g. rasterio.transform.xy()'s default) -- each x/y pair
    represents the coordinate of the middle of that elevation cell, not its
    corner.

    Returns:
        dict with "x" (2D array, meters east), "y" (2D array, meters north),
        "z" (2D array, meters up -- same as dem.elevation).
    """
    rows, cols = dem.shape
    col_idx, row_idx = np.meshgrid(np.arange(cols) + 0.5, np.arange(rows) + 0.5)
    x = dem.transform.a * col_idx + dem.transform.b * row_idx + dem.transform.c
    y = dem.transform.d * col_idx + dem.transform.e * row_idx + dem.transform.f
    return {"x": x.astype(np.float32), "y": y.astype(np.float32),
            "z": dem.elevation}
