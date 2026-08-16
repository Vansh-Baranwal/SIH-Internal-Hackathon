"""
M3 elevation validation and DEM quality-assurance (QA) checks.

IMPORTANT: any validation report produced here is only as trustworthy as
its reference. If the reference is itself synthetic (no real measured
lunar elevation available), the report is labeled "synthetic" and must
never be presented as real-world accuracy.
"""

import numpy as np
import pyproj
import rasterio

from .dem import SOURCE_MEASURED


def validate_dem(dem, reference):
    """
    Compare a DEM's elevation against a reference and compute MAE/RMSE.

    Args:
        dem: DEM instance to validate.
        reference: EITHER a DEM instance OR a raw numpy array of elevation,
            same shape as dem.elevation.

    Returns:
        dict with:
            "mae": mean absolute error (meters)
            "rmse": root-mean-square error (meters)
            "n_pixels": number of valid pixels compared
            "label": "synthetic_validation" if the reference is not
                labeled source_type="measured", else "measured_validation"
            "reference_source_type": the reference's source_type, or
                "unknown" if a bare array was given

    NOTE: a low/zero MAE against a SYNTHETIC reference only confirms the
    M3 pipeline (DEM construction / export / reload) is internally
    consistent. It does NOT establish accuracy against real lunar terrain.
    Only a "measured_validation" report (reference source_type="measured",
    i.e. a genuine independent reference DEM) speaks to real-world
    accuracy. See docs/members/m3_dem_terrain.md for what a real reference
    DEM would require.
    """
    if hasattr(reference, "elevation"):
        ref_elevation = reference.elevation
        ref_source_type = reference.source_type
    else:
        ref_elevation = np.asarray(reference)
        ref_source_type = "unknown"

    if ref_elevation.shape != dem.elevation.shape:
        raise ValueError(
            f"Shape mismatch: dem is {dem.elevation.shape}, "
            f"reference is {ref_elevation.shape}."
        )

    valid_mask = (dem.elevation != dem.nodata) & np.isfinite(dem.elevation)
    valid_mask &= np.isfinite(ref_elevation)

    diff = dem.elevation[valid_mask] - ref_elevation[valid_mask]
    mae = float(np.mean(np.abs(diff))) if diff.size else float("nan")
    rmse = float(np.sqrt(np.mean(diff ** 2))) if diff.size else float("nan")

    label = ("measured_validation" if ref_source_type == SOURCE_MEASURED
              else "synthetic_validation")

    return {
        "mae": mae,
        "rmse": rmse,
        "n_pixels": int(diff.size),
        "label": label,
        "reference_source_type": ref_source_type,
    }


def qa_check_dem(dem):
    """
    Run DEM quality-assurance checks directly on an in-memory DEM object
    (before export).

    Returns:
        dict mapping check name -> bool, plus "all_passed": bool.
    """
    checks = {}

    checks["has_transform"] = dem.transform is not None
    checks["pixel_size_positive"] = dem.pixel_size_m is not None and dem.pixel_size_m > 0
    checks["dimensions_valid"] = (dem.elevation.ndim == 2
                                   and dem.elevation.shape[0] > 0
                                   and dem.elevation.shape[1] > 0)
    checks["vertical_units_set"] = bool(dem.vertical_units)
    checks["nodata_defined"] = dem.nodata is not None

    finite_mask = np.isfinite(dem.elevation)
    non_nodata_mask = dem.elevation != dem.nodata
    checks["elevation_values_finite"] = bool(
        np.all(finite_mask[non_nodata_mask])
    ) if non_nodata_mask.any() else True

    checks["source_type_valid"] = dem.source_type in (
        "synthetic", "sr_estimated", "measured"
    )

    # Transform scale should match the declared pixel size (both axes),
    # otherwise pixel_size_m and the geometry it implies would disagree.
    checks["transform_consistent_with_pixel_size"] = bool(
        np.isclose(abs(dem.transform.a), dem.pixel_size_m, rtol=1e-6)
        and np.isclose(abs(dem.transform.e), dem.pixel_size_m, rtol=1e-6)
    )

    # CRS: None is a valid state (local-frame-only prototype DEM). If a CRS
    # string IS provided, it must actually be parseable -- catches a typo'd
    # or garbage CRS string rather than silently accepting it.
    if dem.crs is None:
        checks["crs_valid"] = True
    else:
        try:
            pyproj.CRS(dem.crs)
            checks["crs_valid"] = True
        except Exception:
            checks["crs_valid"] = False

    # Confidence is optional; if present it must match the elevation grid
    # shape and contain only finite values wherever elevation is valid.
    if dem.confidence is None:
        checks["confidence_shape_valid"] = True
        checks["confidence_values_valid"] = True
    else:
        shape_ok = dem.confidence.shape == dem.elevation.shape
        checks["confidence_shape_valid"] = shape_ok
        if not shape_ok:
            # Can't safely compare mismatched shapes element-wise.
            checks["confidence_values_valid"] = False
        else:
            checks["confidence_values_valid"] = bool(
                np.all(np.isfinite(dem.confidence[non_nodata_mask]))
            ) if non_nodata_mask.any() else True

    checks["all_passed"] = all(checks.values())
    return checks


def qa_check_exported_file(path):
    """
    Run DEM QA checks by re-opening an exported GeoTIFF, confirming the
    round trip preserved metadata correctly.

    Returns:
        dict mapping check name -> bool, plus "all_passed": bool.
    """
    checks = {}
    try:
        with rasterio.open(path) as src:
            checks["file_opens"] = True
            checks["has_transform"] = src.transform is not None and not src.transform.is_identity
            checks["dimensions_valid"] = src.width > 0 and src.height > 0
            checks["nodata_defined"] = src.nodata is not None

            tags = src.tags()
            checks["vertical_units_preserved"] = "vertical_units" in tags
            checks["source_type_preserved"] = "source_type" in tags
            checks["pixel_size_preserved"] = "pixel_size_m" in tags

            checks["band_count_valid"] = src.count in (1, 2)

            band1 = src.read(1)
            checks["elevation_readable"] = band1.size > 0

            # If a second band exists it should be the confidence band we
            # write in export_dem(): same shape as elevation, readable.
            if src.count >= 2:
                band2 = src.read(2)
                checks["confidence_band_preserved"] = (
                    band2.shape == band1.shape and band2.size > 0
                )
            else:
                checks["confidence_band_preserved"] = True
    except Exception:
        checks["file_opens"] = False

    checks["all_passed"] = all(checks.values())
    return checks
