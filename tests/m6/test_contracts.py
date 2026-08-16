import pytest
from lunar_hazard_mapper.m6_planner.schemas import (
    LanderProfile, 
    SiteResult, 
    TrajectoryPoint, 
    Trajectory, 
    ReplanEvent
)

def test_lander_profile_schema():
    lander = LanderProfile(
        name="LanderA",
        mass=1500.0,
        maxSlope=15.0,
        maxVz=-3.0,
        maxVxy=1.0,
        footprint=4.0,
        clearance=1.0,
        deltaVBudget=50.0,
        uncertaintyLimit=0.9,
        maxThrust=3000.0, isp=311.0, maxTiltAngle=45.0
    )
    assert lander.name == "LanderA"
    assert lander.mass == 1500.0

def test_site_result_schema():
    site = SiteResult(
        siteId="SITE_001",
        x=100.0,
        y=200.0,
        score=0.95,
        feasible=True,
        metrics={"slope": 5.0}
    )
    assert site.siteId == "SITE_001"
    assert site.feasible is True

def test_trajectory_point_schema():
    pt = TrajectoryPoint(
        t=0.0, x=0.0, y=0.0, z=1000.0,
        vx=0.0, vy=0.0, vz=-10.0
    )
    assert pt.t == 0.0
    assert pt.z == 1000.0

def test_trajectory_schema():
    pt = TrajectoryPoint(t=0.0, x=0.0, y=0.0, z=100.0, vx=0.0, vy=0.0, vz=0.0)
    traj = Trajectory(
        targetSiteId="SITE_001",
        points=[pt],
        initialState=pt,
        finalState=pt,
        metadata={"cost": 15.0}
    )
    assert traj.targetSiteId == "SITE_001"
    assert len(traj.points) == 1

def test_replan_event_schema():
    site = SiteResult(siteId="SITE_002", x=0.0, y=0.0, score=0.9, feasible=True)
    event = ReplanEvent(
        timestamp=42.5,
        trigger="NEW_BOULDER",
        oldSite="SITE_001",
        newSite="SITE_002",
        candidates=[site],
        reason="Primary site invalidated due to boulder.",
        maneuverCost=12.5
    )
    assert event.trigger == "NEW_BOULDER"
    assert event.newSite == "SITE_002"
    assert event.maneuverCost == 12.5
