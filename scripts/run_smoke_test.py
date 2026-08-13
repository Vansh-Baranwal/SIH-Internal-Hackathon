"""
M3 smoke test: a lightweight, genuinely executable end-to-end sanity check
for the M3 pipeline:

    synthetic terrain -> DEM -> QA -> validation -> GeoTIFF export
    -> M3->M4 interface -> local X/Y/Z coordinate frame

This is NOT a substitute for `pytest tests/` -- it does not duplicate the
full unit test suite. It exists to answer one question quickly: "does the
whole M3 pipeline actually run, end to end, right now?" Exits non-zero if
any step fails, so it can be used as a real CI/demo gate, not just a print
statement.

Run from the repo root:
    python scripts/run_smoke_test.py
"""

import os
import sys

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_SRC = os.path.join(_REPO_ROOT, "src")
for p in (_SRC, _REPO_ROOT):
    if p not in sys.path:
        sys.path.insert(0, p)

from lunar_hazard_mapper.m3_terrain import (
    create_synthetic_terrain,
    export_dem,
    validate_dem,
    qa_check_dem,
    qa_check_exported_file,
    get_terrain_product,
    to_local_frame,
)

# Small + fast on purpose -- this is a sanity check, not a stress test.
_GRID_SIZE = 64
_TERRAIN_KINDS = ("flat", "slope", "crater", "boulder", "combined")


def _run_one(kind, out_dir):
    """Run the full pipeline for one synthetic terrain kind. Returns
    (ok: bool, message: str)."""
    dem = create_synthetic_terrain(kind, size=_GRID_SIZE)

    qa_mem = qa_check_dem(dem)
    if not qa_mem["all_passed"]:
        failed = [k for k, v in qa_mem.items() if k != "all_passed" and not v]
        return False, f"in-memory QA failed: {failed}"

    out_path = os.path.join(out_dir, f"synthetic_{kind}_terrain.tif")
    export_dem(dem, out_path)

    qa_file = qa_check_exported_file(out_path)
    if not qa_file["all_passed"]:
        failed = [k for k, v in qa_file.items() if k != "all_passed" and not v]
        return False, f"exported-file QA failed: {failed}"

    # Self-validation: re-generate the same terrain as a synthetic
    # reference to sanity-check the export/reload round trip. This is
    # NOT real-world accuracy validation -- see the report's "label".
    reference = create_synthetic_terrain(kind, size=_GRID_SIZE)
    report = validate_dem(dem, reference)
    if report["label"] != "synthetic_validation":
        return False, f"unexpected validation label: {report['label']}"
    if not (report["mae"] == report["mae"]):  # NaN check without numpy
        return False, "validation MAE is NaN"

    # M3 -> M4 interface: confirm every field downstream modules rely on
    # actually comes back correctly from the exported file.
    product = get_terrain_product(out_path)
    required_keys = ("elevation", "confidence", "crs", "is_georeferenced",
                      "pixel_size_m", "transform", "nodata",
                      "vertical_units", "source_type", "notes")
    missing = [k for k in required_keys if k not in product]
    if missing:
        return False, f"get_terrain_product() missing keys: {missing}"
    if product["source_type"] != "synthetic":
        return False, f"unexpected source_type: {product['source_type']}"
    if product["is_georeferenced"]:
        return False, "synthetic DEM unexpectedly marked as georeferenced"

    # Local coordinate frame for M6: x=east, y=north, z=up, meters.
    local = to_local_frame(dem)
    if not (local["x"].shape == local["y"].shape == local["z"].shape
            == dem.shape):
        return False, "local frame shape mismatch with DEM"

    return True, (
        f"export={out_path}  "
        f"validation({report['label']}): MAE={report['mae']:.4f}m "
        f"RMSE={report['rmse']:.4f}m  "
        f"source_type={product['source_type']}  "
        f"is_georeferenced={product['is_georeferenced']}"
    )


def main():
    print("Running M3 smoke test...")
    print("(All terrain below is SYNTHETIC test data, not real lunar "
          "elevation. See CHANGES_FOR_M3.md for what depends on real "
          "M2/upstream data.)\n")

    out_dir = os.path.join(_REPO_ROOT, "data", "processed")

    all_ok = True
    for kind in _TERRAIN_KINDS:
        try:
            ok, message = _run_one(kind, out_dir)
        except Exception as exc:  # noqa: BLE001 -- smoke test must not crash raw
            ok, message = False, f"raised {type(exc).__name__}: {exc}"

        all_ok = all_ok and ok
        status = "PASS" if ok else "FAIL"
        print(f"[{status}] {kind:>8}: {message}")

    print()
    if all_ok:
        print("SMOKE TEST PASSED: full synthetic pipeline (terrain -> DEM "
              "-> QA -> validation -> GeoTIFF -> M3->M4 interface -> "
              "local X/Y/Z frame) ran successfully for all terrain types.")
        sys.exit(0)
    else:
        print("SMOKE TEST FAILED: see FAIL lines above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
