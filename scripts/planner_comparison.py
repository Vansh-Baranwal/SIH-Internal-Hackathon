import numpy as np
import sys
import os

script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(script_dir, "..", "src"))

from lunar_hazard_mapper.m6_planner.schemas import LanderProfile, SiteResult, ManeuverConfig, UncertaintyConfig
from lunar_hazard_mapper.m6_planner.reachability.evaluator import filter_reachable_sites
from lunar_hazard_mapper.m6_planner.replanning.ranking import select_best_candidate
from lunar_hazard_mapper.m6_planner.trajectory.generator import generate_trajectory
from lunar_hazard_mapper.m6_planner.uncertainty.monte_carlo import run_monte_carlo_simulations

def run_planner_comparison():
    print("==================================================")
    print(" M6 PLANNER COMPARISON MATRIX")
    print("==================================================")

    lander = LanderProfile(
        name="Apollo_Analog", mass=2000.0, maxSlope=12.0, maxVz=-3.0, maxVxy=1.5,
        footprint=4.0, clearance=1.0, deltaVBudget=800.0,
        maxThrust=8000.0, isp=311.0, maxTiltAngle=45.0
    )
    
    maneuver_config = ManeuverConfig(maneuverTime=30.0, safetyMargin=1.1, maxDuration=60.0)
    uncertainty_config = UncertaintyConfig(seed=123)
    
    current_state = np.array([0.0, 0.0, 1000.0, 20.0, 0.0, -10.0])
    
    # 1. Identical Candidate Set
    candidates = [
        SiteResult(siteId="Site A (Closest)", x=200.0, y=0.0, score=0.60, feasible=True),
        SiteResult(siteId="Site B (M6 Opt)", x=400.0, y=100.0, score=0.85, feasible=True),
        SiteResult(siteId="Site C (Safest)", x=1200.0, y=500.0, score=0.99, feasible=True)
    ]
    
    print("Evaluating Identical Candidate Set...")
    reachable_sites, _ = filter_reachable_sites(candidates, lander, current_state, maneuver_config)
    
    # Baseline 1: Closest Safe Site
    baseline1 = min(reachable_sites, key=lambda s: np.linalg.norm([s.x, s.y]))
    
    # Baseline 2: Lowest Terrain Risk (Highest Safety Score)
    baseline2 = max(reachable_sites, key=lambda s: s.score)
    
    # M6: Multi-objective ranking
    m6_site = select_best_candidate(reachable_sites)
    
    selected_sites = {
        "Closest Safe": baseline1,
        "Lowest Risk": baseline2,
        "M6 Planner": m6_site
    }
    
    metrics_table = {}
    
    for planner, site in selected_sites.items():
        dist = np.linalg.norm([site.x, site.y])
        dv = site.metrics.get("maneuverCost", 0.0)
        
        # Run trajectory to get landing metrics
        traj = generate_trajectory(
            current_state, np.array([site.x, site.y, 0.0]), lander, site.siteId, maneuver_config
        )
        
        fx, fy = traj.finalState.x, traj.finalState.y
        err = np.linalg.norm([fx - site.x, fy - site.y])
        
        # Run small MC for uncertainty/success rate
        mc = run_monte_carlo_simulations(
            current_state, np.array([site.x, site.y, 0.0]), lander, site.siteId,
            num_runs=20, uncertainty_config=uncertainty_config, maneuver_config=maneuver_config
        )
        
        metrics_table[planner] = {
            "Site": site.siteId,
            "Risk": f"{(1.0 - site.score):.2f}",
            "Distance (m)": f"{dist:.0f}",
            "Req. Delta-v (m/s)": f"{dv:.0f}",
            "Reachable": "YES",
            "Landing Err (m)": f"{err:.1f}",
            "Success Prob": f"{mc['success_rate']*100:.0f}%"
        }
        
    # Print Markdown Table
    columns = ["Metric", "Closest Safe", "Lowest Risk", "M6 Planner"]
    
    print("\n| " + " | ".join(columns) + " |")
    print("| " + " | ".join(["---"] * len(columns)) + " |")
    
    keys = ["Site", "Risk", "Distance (m)", "Req. Delta-v (m/s)", "Reachable", "Landing Err (m)", "Success Prob"]
    
    for key in keys:
        row = [key]
        for planner in ["Closest Safe", "Lowest Risk", "M6 Planner"]:
            row.append(metrics_table[planner][key])
        print("| " + " | ".join(row) + " |")

if __name__ == "__main__":
    run_planner_comparison()
