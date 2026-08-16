import numpy as np
import sys
import os

# Ensure src is in pythonpath
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(script_dir, "..", "src"))

from lunar_hazard_mapper.m6_planner.physics.integrator import simulate
from lunar_hazard_mapper.m6_planner.physics.constants import GRAVITY_MOON
from lunar_hazard_mapper.m6_planner.physics.thrust import get_zero_thrust_profile, get_constant_thrust_profile
from lunar_hazard_mapper.m6_planner.schemas import LanderProfile, SiteResult, ManeuverConfig, UncertaintyConfig
from lunar_hazard_mapper.m6_planner.trajectory.generator import generate_trajectory
from lunar_hazard_mapper.m6_planner.replanning.manager import ReplanManager
from lunar_hazard_mapper.m6_planner.replanning.events import ReplanContext
from lunar_hazard_mapper.m6_planner.uncertainty.monte_carlo import run_monte_carlo_simulations

def print_result_table(title: str, results: list):
    print(f"\n### {title}")
    print("| Test | Analytical | Numerical | Absolute Error | Relative Error |")
    print("| :--- | ---: | ---: | ---: | ---: |")
    for r in results:
        test_name = r["name"]
        ana = r["analytical"]
        num = r["numerical"]
        abs_err = abs(ana - num)
        rel_err = abs_err / abs(ana) if ana != 0 else 0.0
        
        # Check tolerances
        status = "PASS" if abs_err < r.get("tol", 0.01) else "FAIL"
        
        print(f"| {test_name} ({status}) | {ana:.4f} | {num:.4f} | {abs_err:.4f} | {rel_err:.4f} |")

def test_1_free_fall():
    # z(t) = z0 + v0*t - 0.5 * g * t^2
    z0 = 1000.0
    v0 = 0.0
    t = 10.0
    
    # Analytical
    z_ana = z0 + v0 * t - 0.5 * GRAVITY_MOON * t**2
    v_ana = v0 - GRAVITY_MOON * t
    
    # Numerical
    initial_state = np.array([0.0, 0.0, z0, 0.0, 0.0, v0])
    sol = simulate(initial_state, 1000.0, get_zero_thrust_profile(), t, max_step=0.1)
    
    z_num = sol.y[2, -1]
    v_num = sol.y[5, -1]
    
    results = [
        {"name": "Free fall position (m)", "analytical": z_ana, "numerical": z_num, "tol": 0.05},
        {"name": "Free fall velocity (m/s)", "analytical": v_ana, "numerical": v_num, "tol": 0.05}
    ]
    print_result_table("Test 1: Lunar Free Fall", results)

def test_2_hover():
    # Thrust = mass * gravity
    mass = 1000.0
    z0 = 500.0
    t = 10.0
    
    thrust = np.array([0.0, 0.0, mass * GRAVITY_MOON])
    initial_state = np.array([0.0, 0.0, z0, 0.0, 0.0, 0.0])
    
    sol = simulate(initial_state, mass, get_constant_thrust_profile(thrust), t, max_step=0.1)
    
    z_num = sol.y[2, -1]
    v_num = sol.y[5, -1]
    
    results = [
        {"name": "Hover position (m)", "analytical": z0, "numerical": z_num, "tol": 0.01},
        {"name": "Hover velocity (m/s)", "analytical": 0.0, "numerical": v_num, "tol": 0.01}
    ]
    print_result_table("Test 2: Hover", results)

def test_3_constant_thrust():
    mass = 1000.0
    z0 = 0.0
    t = 10.0
    Tz = 3000.0
    
    thrust = np.array([0.0, 0.0, Tz])
    initial_state = np.array([0.0, 0.0, z0, 0.0, 0.0, 0.0])
    
    a_net = (Tz / mass) - GRAVITY_MOON
    z_ana = 0.5 * a_net * t**2
    
    sol = simulate(initial_state, mass, get_constant_thrust_profile(thrust), t, max_step=0.1)
    z_num = sol.y[2, -1]
    
    results = [
        {"name": "Constant thrust pos (m)", "analytical": z_ana, "numerical": z_num, "tol": 0.05}
    ]
    print_result_table("Test 3: Constant Thrust", results)

def test_4_controlled_descent():
    lander = LanderProfile(
        name="TestLander", mass=1500.0, maxSlope=10.0, maxVz=-2.0, maxVxy=1.0,
        footprint=3.5, clearance=0.8, deltaVBudget=500.0,
        maxThrust=5000.0, isp=311.0, maxTiltAngle=45.0
    )
    maneuver_config = ManeuverConfig(maxDuration=60.0)
    
    initial_state = np.array([0.0, 0.0, 500.0, 10.0, 5.0, -20.0])
    target_pos = np.array([100.0, 100.0, 0.0])
    
    traj = generate_trajectory(initial_state, target_pos, lander, "SITE_A", maneuver_config)
    
    fx = traj.finalState.x
    fy = traj.finalState.y
    fz = traj.finalState.z
    fvz = traj.finalState.vz
    
    landing_error = np.sqrt((fx - 100.0)**2 + (fy - 100.0)**2)
    flight_time = traj.finalState.t
    
    print(f"\n### Test 4: Controlled Descent")
    print(f"- **Landing Error (m):** {landing_error:.2f}")
    print(f"- **Touchdown Velocity (m/s):** {fvz:.2f}")
    print(f"- **Flight Time (s):** {flight_time:.1f}")
    print(f"- **Trajectory Status:** {traj.status.value}")

def test_5_replanning():
    lander = LanderProfile(
        name="TestLander", mass=1500.0, maxSlope=10.0, maxVz=-2.0, maxVxy=1.0,
        footprint=3.5, clearance=0.8, deltaVBudget=500.0,
        maxThrust=5000.0, isp=311.0, maxTiltAngle=45.0
    )
    
    site_b = SiteResult(siteId="SITE_B", x=200.0, y=0.0, score=0.9, feasible=True)
    manager = ReplanManager(lander, [site_b])
    
    context = ReplanContext(
        timestamp=20.0, trigger="HAZARD", current_target_id="SITE_A",
        current_state=[50.0, 0.0, 300.0, 0.0, 0.0, -10.0], reason="Boulder"
    )
    
    best_site, traj, event = manager.handle_replan_event(context, "TRAJ_1")
    
    print(f"\n### Test 5: Re-planning Cascade")
    print(f"- **Event Trigger:** {event.trigger}")
    print(f"- **Old Site:** {event.oldSite}")
    print(f"- **New Selected Site:** {event.newSite}")
    print(f"- **Diversion Trajectory Generated:** {traj is not None}")
    if traj:
        print(f"- **Diversion Status:** {traj.status.value}")

def test_6_uncertainty():
    lander = LanderProfile(
        name="TestLander", mass=1500.0, maxSlope=10.0, maxVz=-2.0, maxVxy=1.0,
        footprint=3.5, clearance=0.8, deltaVBudget=500.0,
        maxThrust=5000.0, isp=311.0, maxTiltAngle=45.0
    )
    
    initial_state_mean = np.array([0.0, 0.0, 500.0, 10.0, 5.0, -20.0])
    target_pos = np.array([100.0, 100.0, 0.0])
    
    print(f"\n### Test 6: Uncertainty (Monte Carlo)")
    for n in [10, 50]: # Keep it short for CI/testing, normally 100-1000
        metrics = run_monte_carlo_simulations(
            initial_state_mean, target_pos, lander, "SITE_A", num_runs=n
        )
        print(f"- **Runs:** {n} | **Success:** {metrics['success_rate']*100:.1f}% | **Mean Error:** {metrics['landing_error_mean']:.2f} m")

if __name__ == "__main__":
    print("==================================================")
    print("M6 SCIENTIFIC VALIDATION MATRIX")
    print("==================================================")
    test_1_free_fall()
    test_2_hover()
    test_3_constant_thrust()
    test_4_controlled_descent()
    test_5_replanning()
    test_6_uncertainty()
