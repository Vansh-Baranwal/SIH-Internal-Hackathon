# M4 - Hazard Detection

**"I mathematically analyze the terrain and produce hazard + confidence layers."**

Responsibilities: Slope, curvature, Hessian, boulders, craters, confidence.

## Modules (`src/lunar_hazard_mapper/m4_hazards/`)

| File | Function | Status |
|---|---|---|
| `gradients.py` | `compute_gradients(dem)` | Done, tested |
| `slope.py` | `compute_slope(gradients)` + `compute_aspect`, `compute_surface_normal`, `compute_roughness` | Done, tested |
| `hessian.py` | `compute_hessian(dem)` | Done, tested |
| `eigenfeatures.py` | `compute_eigenfeatures(hessian)` | Done, tested |
| `curvature.py` | `compute_curvature(dem)` | Done, tested |
| `crater.py` | `detect_craters(dem)` | Done, tested (morphology baseline, not YOLO) |
| `boulder.py` | `detect_boulders(dem)` | Done, tested (elevation-anomaly baseline) |
| `shadow.py` | `detect_shadows(image, sun_angle)` | Done, tested (DEM-raycast + brightness-threshold modes) |
| `confidence.py` | `calculate_confidence(inputs)` | Done, tested |
| `fusion.py` | `fuse_hazards(hazard_layers)` | Done, tested |
| `validation.py` | `validate_hazards(fused_hazards)` | Done, tested |

## Data contract (see `docs/api/DATA_CONTRACTS.md` for the full spec)

`dem = {"z": ndarray, "dx": float, "dy": float}` — this is M4's own convention,
defined here because the scaffold's stubs didn't fix one. M3 hands off a
DEM path + CRS + pixel size; whoever wires M3→M4 needs to load the raster
into this dict shape before calling any m4_hazards function.

## Known scope gap vs. the architecture diagram

`crater.py`/`boulder.py` implement the morphology/elevation-anomaly
**baseline** (handbook §7.8/§7.11, Method Ladder §12: baseline before
deep learning). The system architecture diagram shows YOLOv8/Faster-RCNN
(craters) and YOLOv8+SAM (boulders) — that's the upgrade tier, blocked on
M1 delivering real imagery and labeled data (Robbins crater DB, Watkins
boulder DB). Baseline is correct-and-complete for now; upgrade is separate
future work, not a bug.

## Tests

`tests/m4/` — 22 tests covering: flat→0°, 5°/10° plane recovery, ridge/bowl
Hessian sign checks, crater depth/diameter recovery, confidence/hazard
channel independence, boulder detection, shadow dual-mode, IoU/P/R/F1.
Standard workflow uses editable install first: `pip install -e .`, then run
`pytest tests/`. `tests/conftest.py` is kept as a fallback bootstrap for
environments that are not yet packaged consistently.

## Demo

`python scripts/run_m4_demo.py` — runs the full stack on a synthetic
landing-corridor DEM, writes `outputs/hazards/{hazard_layers.npz,
craters.json, boulders.json}` and `results/metrics/m4_evaluation.json`.
