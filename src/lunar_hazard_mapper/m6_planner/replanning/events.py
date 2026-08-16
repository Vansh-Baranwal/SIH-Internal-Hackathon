from dataclasses import dataclass
from typing import Optional

@dataclass
class ReplanTrigger:
    HAZARD_INJECTED = "HAZARD_INJECTED"
    UNACCEPTABLE_UNCERTAINTY = "UNACCEPTABLE_UNCERTAINTY"
    TRAJECTORY_DEVIATION = "TRAJECTORY_DEVIATION"

@dataclass
class ReplanContext:
    timestamp: float
    trigger: str
    current_target_id: str
    reason: str
    current_state: tuple[float, float, float, float, float, float]
