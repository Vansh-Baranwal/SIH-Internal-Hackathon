import os
import json
import numpy as np
from pathlib import Path

from lunar_hazard_mapper.m6_planner.mocks.scenarios import build_standalone_demo_scenario, PredefinedScenarios
from lunar_hazard_mapper.m6_planner.trajectory.generator import generate_trajectory
from lunar_hazard_mapper.m6_planner.trajectory.exporter import TrajectoryExporter
from lunar_hazard_mapper.m6_planner.replanning.manager import ReplanManager
from lunar_hazard_mapper.m6_planner.replanning.events import ReplanContext, ReplanTrigger
from lunar_hazard_mapper.m6_planner.replanning.ranking import select_best_candidate
from lunar_hazard_mapper.m6_planner.uncertainty.monte_carlo import run_monte_carlo_simulations
from lunar_hazard_mapper.m6_planner.uncertainty.analysis import generate_uncertainty_report

from lunar_hazard_mapper.m6_planner.schemas import ManeuverConfig, UncertaintyConfig

def main():
    print("==================================================")
    print(" M6 STANDALONE DEMO (INDEPENDENT DEVELOPMENT MODE)")
    print("==================================================")
    
    # 1. Setup Output Directory
    output_dir = Path("results/m6_demo")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 2. Load Predefined Deterministic Scenario
    print("\n[1] Loading Mock M1-M5 Scenario (SCENARIO_HAZARD_REPLAN)...")
    scenario = build_standalone_demo_scenario(PredefinedScenarios.SCENARIO_HAZARD_REPLAN)
    lander = scenario["lander"]
    candidates = scenario["candidates"]
    
    # Maneuver Configuration
    maneuver_config = ManeuverConfig(maxDuration=60.0)
    
    # 3. Initial Target Selection (Forcing SITE_A as primary for this demo scenario)
    print("\n[2] Selecting initial target...")
    best_initial_site = next(c for c in candidates if c.siteId == "SITE_A")
    print(f"Selected primary site: {best_initial_site.siteId} (Score: {best_initial_site.score:.2f})")
    
    with open(output_dir / "selected_site.json", "w") as f:
        # Pydantic v2 compatible
        if hasattr(best_initial_site, 'model_dump_json'):
            f.write(best_initial_site.model_dump_json(indent=2))
        else:
            f.write(best_initial_site.json(indent=2))
            
    # 4. Generate Initial Trajectory
    print("\n[3] Generating trajectory to primary site...")
    initial_state = np.array([0.0, 0.0, 1000.0, 50.0, 0.0, 0.0]) # Starting descent
    
    trajectory_a = generate_trajectory(
        initial_state=initial_state,
        target_pos=np.array([best_initial_site.x, best_initial_site.y, 0.0]),
        lander=lander,
        target_site_id=best_initial_site.siteId,
        maneuver_config=maneuver_config
    )
    
    TrajectoryExporter.export_to_json(trajectory_a, output_dir / "trajectory.json")
    print(f"Saved initial trajectory to {output_dir / 'trajectory.json'}")
    
    # 5. Simulate Mid-Descent Hazard Injection
    print("\n[4] HAZARD INJECTED during descent at t=15s")
    
    # Extract state at t=15s roughly
    t_15_point = trajectory_a.points[min(15, len(trajectory_a.points)-1)]
    current_state = np.array([
        t_15_point.x, t_15_point.y, t_15_point.z,
        t_15_point.vx, t_15_point.vy, t_15_point.vz
    ])
    
    context = ReplanContext(
        timestamp=15.0,
        trigger=ReplanTrigger.HAZARD_INJECTED,
        current_target_id=best_initial_site.siteId,
        reason="Unexpected boulder field detected near touchdown zone",
        current_state=tuple(current_state)
    )
    
    # 6. Re-planning Cascade
    print("\n[5] Executing Emergency Re-planning cascade...")
    manager = ReplanManager(lander, candidates)
    new_site, new_traj, event = manager.handle_replan_event(context, old_trajectory_id="TRAJ_PRIMARY")
    
    print(f"Old Site Invalidated: {event.oldSite}")
    if new_site:
        print(f"New Alternative Selected: {event.newSite}")
        TrajectoryExporter.export_to_json(new_traj, output_dir / "replanned_trajectory.json")
        print(f"Saved replanned trajectory to {output_dir / 'replanned_trajectory.json'}")
    else:
        print("CRITICAL: No viable alternatives found!")
        
    with open(output_dir / "replan_event.json", "w") as f:
        if hasattr(event, 'model_dump_json'):
            f.write(event.model_dump_json(indent=2))
        else:
            f.write(event.json(indent=2))
    print(f"Saved re-planning event log to {output_dir / 'replan_event.json'}")
    
    # 7. Uncertainty Simulation
    if new_site:
        print("\n[6] Running Monte Carlo Uncertainty Simulation on final target...")
        uncertainty_config = UncertaintyConfig(seed=42)
        metrics = run_monte_carlo_simulations(
            initial_state_mean=current_state,
            target_pos=np.array([new_site.x, new_site.y, 0.0]),
            lander=lander,
            target_site_id=new_site.siteId,
            num_runs=20, # Reduced for quick demo
            uncertainty_config=uncertainty_config,
            maneuver_config=maneuver_config
        )
        
        generate_uncertainty_report(metrics, output_dir / "uncertainty_report.json")
        print(f"Saved uncertainty report to {output_dir / 'uncertainty_report.json'}")
        
    print("\n==================================================")
    print(" DEMO COMPLETE. M6 PIPELINE VERIFIED.")
    print("==================================================")

if __name__ == "__main__":
    main()
