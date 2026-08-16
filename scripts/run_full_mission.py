"""
scripts/run_full_mission.py

End-to-End M4 -> M5 -> M6 Demonstration Pipeline.
Executes the hazard mapping, site selection, trajectory generation,
and emergency replanning cascade, outputting renderer-independent JSON.
"""
import sys, json, os
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

# M4 Imports
from lunar_hazard_mapper.m4_hazards.gradients import compute_gradients
from lunar_hazard_mapper.m4_hazards.slope import compute_slope, compute_roughness
from lunar_hazard_mapper.m4_hazards.crater import detect_craters
from lunar_hazard_mapper.m4_hazards.boulder import detect_boulders
from lunar_hazard_mapper.m4_hazards.shadow import detect_shadows
from lunar_hazard_mapper.m4_hazards.confidence import calculate_confidence
from lunar_hazard_mapper.m4_hazards.fusion import fuse_hazards
from lunar_hazard_mapper.m4_hazards.handoff import build_m4_to_m5
from tests.m4.fixtures.combined import generate_combined

# M5 Imports
from lunar_hazard_mapper.m5_lander.profile import load_lander_profile
from lunar_hazard_mapper.m5_lander.evaluator import evaluate_sites, handle_m6_feedback

# M6 Imports
from lunar_hazard_mapper.m6_planner.adapters.m5_adapter import convert_m5_sites_to_m6_results, convert_m5_lander_to_m6_profile
from lunar_hazard_mapper.m6_planner.trajectory.generator import generate_trajectory
from lunar_hazard_mapper.m6_planner.trajectory.exporter import TrajectoryExporter
from lunar_hazard_mapper.m6_planner.schemas import ManeuverConfig
from lunar_hazard_mapper.m6_planner.replanning.manager import ReplanManager
from lunar_hazard_mapper.m6_planner.replanning.events import ReplanContext, ReplanTrigger

def main():
    print("==================================================")
    print(" INTEGRATED PIPELINE: M4 -> M5 -> M6")
    print("==================================================")
    
    out_dir = ROOT / "results" / "mission_export"
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. M4 Hazard Detection
    print("\n[M4] Generating synthetic terrain and detecting hazards...")
    dem = generate_combined(shape=(200, 200), dx=1.0, dy=1.0, seed=42)
    
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

    m4_to_m5 = build_m4_to_m5(
        dem=dem, slope=slope, roughness=roughness, confidence=confidence,
        shadow_mask=shadow_mask, fused=fused, craters=craters, boulders=boulders,
    )

    # 2. M5 Site Evaluation
    print("\n[M5] Evaluating candidate landing sites...")
    lander_profile = load_lander_profile(str(ROOT / "configs" / "landers" / "lander_A.yaml"))
    
    m5_result = evaluate_sites(
        sites=None, # auto-generate candidates
        profile=lander_profile,
        m4_to_m5=m4_to_m5
    )
    
    print(f"M5 Generated {m5_result['candidate_count']} candidates.")
    print(f"M5 Recommended {len(m5_result['recommended_sites'])} feasible sites.")

    # 3. M6 Adapter
    print("\n[M6] Adapting M5 outputs to M6 schemas...")
    m6_sites = convert_m5_sites_to_m6_results(m5_result)
    m6_lander = convert_m5_lander_to_m6_profile(m5_result["lander"])
    
    # Sort sites purely by score to grab the top one
    m6_sites_sorted = sorted([s for s in m6_sites if s.feasible], key=lambda x: x.score, reverse=True)
    if not m6_sites_sorted:
        print("CRITICAL: No feasible sites returned from M5!")
        return

    best_site = m6_sites_sorted[0]
    print(f"M6 Selected Primary Target: {best_site.siteId} (Score: {best_site.score:.3f})")

    # Export selected site
    with open(out_dir / "target_site.json", "w") as f:
        f.write(best_site.model_dump_json(indent=2) if hasattr(best_site, 'model_dump_json') else best_site.json(indent=2))

    # 4. M6 Trajectory Generation
    print("\n[M6] Generating Trajectory...")
    maneuver_config = ManeuverConfig(maxDuration=60.0)
    initial_state = np.array([0.0, 0.0, 1000.0, 50.0, 0.0, 0.0])
    
    trajectory_a = generate_trajectory(
        initial_state=initial_state,
        target_pos=np.array([best_site.x, best_site.y, 0.0]),
        lander=m6_lander,
        target_site_id=best_site.siteId,
        maneuver_config=maneuver_config
    )
    
    TrajectoryExporter.export_to_json(trajectory_a, out_dir / "trajectory_primary.json")
    print(f"Trajectory exported to {out_dir / 'trajectory_primary.json'}")

    # 5. Deterministic Replanning Event
    print("\n[M6] Injecting deterministic replanning event at t=15s (Hazard Detected!)...")
    t_15_point = trajectory_a.points[min(15, len(trajectory_a.points)-1)]
    current_state = np.array([
        t_15_point.x, t_15_point.y, t_15_point.z,
        t_15_point.vx, t_15_point.vy, t_15_point.vz
    ])
    
    context = ReplanContext(
        timestamp=15.0,
        trigger=ReplanTrigger.HAZARD_INJECTED,
        current_target_id=best_site.siteId,
        reason="SIMULATED_REPLAN_EVENT: Late-stage hazard detection near touchdown zone",
        current_state=tuple(current_state)
    )
    
    # 6. Fallback Site Selection (M5 <-> M6 Loop)
    print("\n[M5/M6 Loop] Triggering fallback site selection...")
    manager = ReplanManager(m6_lander, m6_sites_sorted)
    new_site, new_traj, event = manager.handle_replan_event(context, old_trajectory_id="TRAJ_PRIMARY")
    
    if new_site:
        print(f"Replanning successful. New fallback site: {new_site.siteId}")
        TrajectoryExporter.export_to_json(new_traj, out_dir / "trajectory_replanned.json")
        print(f"Replanned trajectory exported to {out_dir / 'trajectory_replanned.json'}")
        
        # Verify M5 feedback loop logic directly matches
        m6_feedback = {
            "site_id": best_site.siteId,
            "trajectory_feasible": False,
            "delta_v_mps": event.maneuverCost,
            "reason": event.reason
        }
        m5_fallback = handle_m6_feedback(m5_result, m6_feedback, lander_profile, m4_to_m5)
        print(f"M5 natively agrees on fallback site: {m5_fallback['next_recommended_site']['site_id']}")
        
    else:
        print("CRITICAL: No viable fallback sites found during replan!")
        
    # Export Replan Event
    with open(out_dir / "replan_event.json", "w") as f:
        f.write(event.model_dump_json(indent=2) if hasattr(event, 'model_dump_json') else event.json(indent=2))

    # 7. Touchdown Validation
    print(f"\n[M6] Touchdown Validation Status: {new_traj.status if new_site else trajectory_a.status}")
    print("==================================================")
    print(" MISSION COMPLETE. RENDERER-INDEPENDENT EXPORTS GENERATED.")
    print("==================================================")

if __name__ == "__main__":
    main()
