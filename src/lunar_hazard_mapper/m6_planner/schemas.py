from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

# ---------------------------------------------------------
# M5 Contracts (Inputs to M6)
# ---------------------------------------------------------

from enum import Enum

class LanderProfile(BaseModel):
    """
    Physical profile and constraints of the lander (provided by M5 configuration).
    """
    name: str
    mass: float = Field(..., description="Lander mass in kg")
    maxSlope: float = Field(..., description="Maximum tolerable slope in degrees")
    maxVz: float = Field(..., description="Maximum touchdown vertical velocity (m/s), usually negative")
    maxVxy: float = Field(..., description="Maximum touchdown horizontal velocity (m/s)")
    footprint: float = Field(..., description="Lander footprint radius/dimension in meters")
    clearance: float = Field(..., description="Ground clearance in meters")
    deltaVBudget: float = Field(..., description="Total available Δv budget for maneuvers (m/s)")
    maxThrust: float = Field(..., description="Maximum thrust of the main engine in Newtons")
    isp: float = Field(311.0, description="Specific impulse of the main engine in seconds")
    maxTiltAngle: float = Field(45.0, description="Maximum allowable thrust vector tilt from vertical in degrees")
    uncertaintyLimit: float = Field(0.9, description="Maximum acceptable uncertainty metric")

class ManeuverConfig(BaseModel):
    """
    Mission planning constraints for a maneuver.
    """
    maneuverTime: float = Field(30.0, description="Nominal time allocated for the maneuver in seconds")
    safetyMargin: float = Field(1.1, description="Safety margin multiplier for delta-v estimation")
    maxDuration: float = Field(60.0, description="Maximum allowable flight duration before timeout")

class UncertaintyConfig(BaseModel):
    """
    Configuration for sensor and state uncertainty.
    """
    position_std_m: float = 1.0
    velocity_std_mps: float = 0.1
    altitude_std_m: float = 1.0
    terrain_height_std_m: float = 0.5
    seed: int = 42

class SiteResult(BaseModel):
    """
    Safety evaluation result for a candidate site (provided by M5).
    """
    siteId: str
    x: float
    y: float
    score: float = Field(..., description="M5 safety score")
    feasible: bool = Field(..., description="True if M5 deems this site safe against hazards")
    reasons: List[str] = Field(default_factory=list, description="Reasons for infeasibility if false")
    metrics: Dict[str, Any] = Field(default_factory=dict, description="Additional site metrics (slope, crater, boulder)")

# ---------------------------------------------------------
# M6 Contracts (Outputs to Blender / Other components)
# ---------------------------------------------------------

class TrajectoryStatus(str, Enum):
    IN_PROGRESS = "IN_PROGRESS"
    SUCCESS = "SUCCESS"
    GROUND_COLLISION = "GROUND_COLLISION"
    TIMEOUT = "TIMEOUT"
    INVALID = "INVALID"

class TrajectoryPoint(BaseModel):
    """
    A single point in the generated trajectory.
    """
    t: float = Field(..., description="Simulation time in seconds")
    x: float = Field(..., description="Local X (East) coordinate in meters")
    y: float = Field(..., description="Local Y (North) coordinate in meters")
    z: float = Field(..., description="Local Z (Up) altitude in meters")
    vx: float = Field(..., description="X velocity in m/s")
    vy: float = Field(..., description="Y velocity in m/s")
    vz: float = Field(..., description="Z velocity in m/s")
    attitude: Optional[List[float]] = Field(None, description="Attitude representation (e.g. quaternions or euler angles)")

class Trajectory(BaseModel):
    """
    A full generated trajectory, exported to Blender.
    """
    targetSiteId: str
    status: TrajectoryStatus = Field(TrajectoryStatus.SUCCESS, description="End state of the trajectory")
    points: List[TrajectoryPoint]
    initialState: TrajectoryPoint
    finalState: TrajectoryPoint
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Simulation metadata (e.g. cost, planner version)")


class ReplanEvent(BaseModel):
    """
    An emergency re-planning event to be emitted to Blender.
    """
    timestamp: float
    trigger: str = Field(..., description="Event trigger (e.g. NEW_BOULDER, TRAJECTORY_DEVIATION)")
    oldSite: str
    newSite: Optional[str] = None
    candidates: List[SiteResult] = Field(..., description="Evaluated candidates during replan")
    reason: str = Field(..., description="Human-readable reason for replan")
    oldTrajectoryId: Optional[str] = None
    newTrajectoryId: Optional[str] = None
    rejectedCandidates: List[Dict[str, Any]] = Field(default_factory=list, description="Structured info on why alternatives were rejected")
    maneuverCost: float = Field(..., description="Required Δv cost for the new trajectory")
