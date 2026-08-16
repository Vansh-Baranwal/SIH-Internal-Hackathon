"""
scripts/run_m4_demo.py

Standalone M4 demo -- deliberately NOT a rewrite of scripts/run_pipeline.py,
which is the whole-team orchestrator (M1->M2->...->M6) that shouldn't be
overwritten by one member alone. Run directly:

    python scripts/run_m4_demo.py

Writes GeoTIFF-free JSON/NPZ artifacts to outputs/hazards/ (gitignored,
regenerable) and metrics to results/metrics/ (small, trackable).
"""
import sys, json, os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

import numpy as np

from lunar_hazard_mapper.m4_hazards.gradients import compute_gradients
from lunar_hazard_mapper.m4_hazards.slope import compute_slope, compute_roughness
from lunar_hazard_mapper.m4_hazards.crater import detect_craters
from lunar_hazard_mapper.m4_hazards.boulder import detect_boulders
from lunar_hazard_mapper.m4_hazards.shadow import detect_shadows
from lunar_hazard_mapper.m4_hazards.confidence import calculate_confidence
from lunar_hazard_mapper.m4_hazards.fusion import fuse_hazards
from lunar_hazard_mapper.m4_hazards.validation import validate_hazards
from lunar_hazard_mapper.m4_hazards.handoff import build_m4_to_m5

from tests.m4.fixtures.combined import generate_combined


def main():
    out_hazards = ROOT / "outputs" / "hazards"
    out_metrics = ROOT / "results" / "metrics"
    out_hazards.mkdir(parents=True, exist_ok=True)
    out_metrics.mkdir(parents=True, exist_ok=True)

    print("Generating synthetic landing-corridor DEM...")
    dem = generate_combined(shape=(200, 200), dx=1.0, dy=1.0, seed=7)
    gt = dem["ground_truth"]

    gradients = compute_gradients(dem)
    slope = compute_slope(gradients)
    roughness = compute_roughness(dem, window=5)

    craters = detect_craters(dem, depression_min_depth=1.0)
    boulders = detect_boulders(dem, min_height=0.3)
    shadow_mask = detect_shadows(dem, sun_angle=22.0, sun_azimuth_deg=140.0)
    confidence = calculate_confidence({"shadow_mask": shadow_mask})

    fused = fuse_hazards({
        "slope_deg": slope["slope_deg"], "roughness": roughness,
        "confidence": confidence, "shadow_mask": shadow_mask,
        "dx": dem["dx"], "dy": dem["dy"],
        "craters": craters, "boulders": boulders,
        "slope_limit_deg": 10.0,
    })

    metrics = validate_hazards({
        "binary_mask": fused["binary_mask"], "continuous_risk": fused["continuous_risk"],
        "confidence": confidence,
        "predicted_craters": craters, "ground_truth_craters": gt["craters"],
        "predicted_boulders": [{"center_row": b["center_row"], "center_col": b["center_col"],
                                 "radius_px": b["radius_px"]} for b in boulders],
        "ground_truth_boulders": gt["boulders"],
    })

    np.savez_compressed(out_hazards / "hazard_layers.npz",
                         slope_deg=slope["slope_deg"], roughness=roughness,
                         confidence=confidence, shadow_mask=shadow_mask,
                         binary_mask=fused["binary_mask"], continuous_risk=fused["continuous_risk"])
    with open(out_hazards / "craters.json", "w") as f:
        json.dump(craters, f, indent=2)
    with open(out_hazards / "boulders.json", "w") as f:
        json.dump(boulders, f, indent=2)
    with open(out_metrics / "m4_evaluation.json", "w") as f:
        json.dump(metrics, f, indent=2)

    # M4 -> M5 handoff, per docs/api/M4_DATA_CONTRACT.md / the Member 5
    # Integration Contract. This is pure assembly of the arrays/lists
    # already computed above -- see handoff.py for the field-by-field
    # source mapping.
    m4_to_m5 = build_m4_to_m5(
        dem=dem, slope=slope, roughness=roughness, confidence=confidence,
        shadow_mask=shadow_mask, fused=fused, craters=craters, boulders=boulders,
    )
    np.savez_compressed(
        out_hazards / "m4_to_m5.npz",
        z=m4_to_m5["terrain"]["z"], dx=m4_to_m5["terrain"]["dx"], dy=m4_to_m5["terrain"]["dy"],
        slope_deg=m4_to_m5["hazards"]["slope_deg"], binary_mask=m4_to_m5["hazards"]["binary_mask"],
        continuous_risk=m4_to_m5["hazards"]["continuous_risk"], confidence=m4_to_m5["hazards"]["confidence"],
        roughness=m4_to_m5["hazards"]["roughness"], crater_risk=m4_to_m5["hazards"]["crater_risk"],
        boulder_risk=m4_to_m5["hazards"]["boulder_risk"], shadow_mask=m4_to_m5["hazards"]["shadow_mask"],
    )
    with open(out_hazards / "m4_to_m5_craters.json", "w") as f:
        json.dump(m4_to_m5["craters"], f, indent=2)
    with open(out_hazards / "m4_to_m5_boulders.json", "w") as f:
        json.dump(m4_to_m5["boulders"], f, indent=2)

    print(f"\nGround truth: {len(gt['craters'])} craters, {len(gt['boulders'])} boulders")
    print(f"Detected:     {len(craters)} craters, {len(boulders)} boulders")
    print(f"Crater detection:  {metrics['crater_detection']}")
    print(f"Boulder detection: {metrics['boulder_detection']}")
    print(f"\nWrote: {out_hazards}/hazard_layers.npz, craters.json, boulders.json")
    print(f"Wrote: {out_metrics}/m4_evaluation.json")
    print(f"Wrote: {out_hazards}/m4_to_m5.npz, m4_to_m5_craters.json, m4_to_m5_boulders.json "
          f"(M5 handoff, per M4_DATA_CONTRACT.md)")


if __name__ == "__main__":
    main()
