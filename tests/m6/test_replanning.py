import pytest
import numpy as np
from lunar_hazard_mapper.m6_planner.mocks.scenarios import get_scenario_sites, PredefinedScenarios, LanderProfile
from lunar_hazard_mapper.m6_planner.replanning.manager import ReplanManager
from lunar_hazard_mapper.m6_planner.replanning.events import ReplanContext, ReplanTrigger

def test_replan_hazard_event_cascade():
    """
    Test the full re-planning cascade when a hazard is injected at the current target.
    """
    candidates = get_scenario_sites(PredefinedScenarios.SCENARIO_HAZARD_REPLAN)
    lander = LanderProfile(
        name="Test", mass=1000.0, maxSlope=12.0, maxVz=-3.0, maxVxy=1.5,
        footprint=2.0, clearance=1.0, deltaVBudget=500.0, uncertaintyLimit=1.0, maxThrust=3000.0, isp=311.0, maxTiltAngle=45.0
    )
    
    manager = ReplanManager(lander, candidates)
    
    # State: descending towards SITE_A
    current_state = (0.0, 0.0, 100.0, 10.0, 0.0, -10.0)
    
    # Inject Hazard at SITE_A
    context = ReplanContext(
        timestamp=35.0,
        trigger=ReplanTrigger.HAZARD_INJECTED,
        current_target_id="SITE_A",
        reason="Large boulder detected on descent",
        current_state=current_state
    )
    
    new_site, new_traj, event = manager.handle_replan_event(context, old_trajectory_id="TRAJ_OLD")
    
    # Assertions
    assert new_site is not None
    assert new_site.siteId == "SITE_B" # B is the next best reachable site
    assert new_traj is not None
    assert new_traj.targetSiteId == "SITE_B"
    
    assert event.oldSite == "SITE_A"
    assert event.newSite == "SITE_B"
    rejected_ids = [s["siteId"] for s in event.rejectedCandidates]
    assert "SITE_A" in rejected_ids # Because it was the invalidated target
    assert "SITE_D" in rejected_ids # Because it's infeasible
    assert "SITE_C" in rejected_ids # Because it's too far (delta-v limit)

def test_replan_no_reachable_site():
    """
    Test re-planning when no viable alternative exists.
    """
    candidates = get_scenario_sites(PredefinedScenarios.SCENARIO_NO_REACHABLE_SITE)
    lander = LanderProfile(
        name="Test", mass=1000.0, maxSlope=12.0, maxVz=-3.0, maxVxy=1.5,
        footprint=2.0, clearance=1.0, deltaVBudget=50.0, uncertaintyLimit=1.0, maxThrust=3000.0, isp=311.0, maxTiltAngle=45.0 # Low budget
    )
    
    manager = ReplanManager(lander, candidates)
    
    current_state = (0.0, 0.0, 100.0, 0.0, 0.0, -10.0)
    
    context = ReplanContext(
        timestamp=40.0,
        trigger=ReplanTrigger.HAZARD_INJECTED,
        current_target_id="SITE_X",
        reason="Hazard",
        current_state=current_state
    )
    
    new_site, new_traj, event = manager.handle_replan_event(context, old_trajectory_id="TRAJ_OLD")
    
    # Assertions
    assert new_site is None
    assert new_traj is None
    assert event.newSite is None
    rejected_ids = [s["siteId"] for s in event.rejectedCandidates]
    assert "SITE_A" in rejected_ids # unreachable
    assert "SITE_B" in rejected_ids # infeasible
