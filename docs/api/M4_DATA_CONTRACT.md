# M4 Data Contract (proposed)

`docs/api/DATA_CONTRACTS.md` is shared across all six members and already
has content ("Interfaces between M1 through M6") — didn't want to overwrite
or guess how the team wants it structured. This file is M4's section,
written standalone; the team lead owns pasting/merging this into
DATA_CONTRACTS.md once the team agrees on a format.

## `dem` dict — input to every m4_hazards function that takes a DEM

```python
dem = {
    "z":  np.ndarray,  # 2D, float64, elevation in meters
    "dx": float,        # meters per pixel, x (column) direction
    "dy": float,        # meters per pixel, y (row) direction
}
```

Matches M3's real contract fields (`DEM path, CRS, pixel size, origin,
nodata, vertical units` — workflow §10) minus CRS/path, since M4 doesn't
own georeferencing. Whoever wires M3→M4 loads the raster via rasterio and
builds this dict from `pixel_size_x`/`pixel_size_y`.

## Function I/O reference

| Function | Input | Output |
|---|---|---|
| `compute_gradients(dem)` | `dem` | `{"zx": ndarray, "zy": ndarray}` |
| `compute_slope(gradients)` | output of `compute_gradients` | `{"slope_rad", "slope_deg"}` |
| `compute_hessian(dem)` | `dem` | `{"zxx", "zyy", "zxy"}` |
| `compute_eigenfeatures(hessian)` | output of `compute_hessian` | `{"l1", "l2", "principal_dir1", "principal_dir2"}` |
| `compute_curvature(dem)` | `dem` | `{"zxx","zyy","zxy","gaussian_curvature","mean_curvature"}` |
| `detect_craters(dem)` | `dem` | `list[{id, center_row, center_col, diameter_px, diameter_m, depth_m, rim_elevation_m, floor_elevation_m, rim_slope_deg, confidence}]` |
| `detect_boulders(dem)` | `dem` | `list[{id, center_row, center_col, height_m, radius_px, radius_m, hazard_radius_m, confidence}]` |
| `detect_shadows(image, sun_angle)` | `dem`-dict OR plain brightness ndarray | `ndarray[bool]` |
| `calculate_confidence(inputs)` | `{"shadow_mask"?, "sr_uncertainty"?, "detector_confidence_penalty"?}` | `ndarray[0,1]` |
| `fuse_hazards(hazard_layers)` | see `fusion.py` docstring | `{"binary_mask", "continuous_risk", "components"}` |
| `validate_hazards(fused_hazards)` | see `validation.py` docstring | `{"summary", "crater_detection", "boulder_detection"}` |

## What M4 hands to M5/M6

Not yet frozen as a single JSON schema — the workflow doc's target contract
(§10) is: `x, y, elevation, slope, curvature, l1, l2, craterRisk,
boulderRisk, shadow, confidence`. Building that exact flattened
per-cell JSON is straightforward from the outputs above (zip slope_deg,
mean_curvature, l1, l2, fused["components"]["crater_risk"]/["boulder_risk"],
shadow_mask, confidence into per-pixel rows) — not built yet since M5/M6
haven't confirmed they want per-cell JSON vs. raw rasters. Flagging this
as the next real decision point, not guessing it.
