import pytest
import numpy as np
from lunar_hazard_mapper.m6_planner.schemas import SiteResult, LanderProfile
from lunar_hazard_mapper.m6_planner.reachability.evaluator import filter_reachable_sites

def test_reachability_filtering():
    lander = LanderProfile(
        name="TestLander",
        mass=1000.0,
        maxSlope=10.0,
        maxVz=-2.0,
        maxVxy=1.0,
        footprint=2.0,
        clearance=1.0,
        deltaVBudget=100.0, # 100 m/s budget
        uncertaintyLimit=1.0, maxThrust=3000.0, isp=311.0, maxTiltAngle=45.0
    )
    
    current_state = np.array([0.0, 0.0, 100.0, 0.0, 0.0, -10.0])
    
    candidates = [
        # Close enough, should be reachable
        SiteResult(siteId="A", x=10.0, y=10.0, score=0.9, feasible=True, reasons=[], metrics={}),
        # Way too far, horizontal delta-v will blow the budget
        SiteResult(siteId="B", x=10000.0, y=10000.0, score=0.9, feasible=True, reasons=[], metrics={}),
        # Close, but already infeasible from M5
        SiteResult(siteId="C", x=5.0, y=5.0, score=0.2, feasible=False, reasons=["slope"], metrics={})
    ]
    
    reachable, unreachable = filter_reachable_sites(candidates, lander, current_state)
    
    assert len(reachable) == 1
    assert reachable[0].siteId == "A"
    
    assert len(unreachable) == 2
    assert "B" in [s.siteId for s in unreachable]
    assert "C" in [s.siteId for s in unreachable]
