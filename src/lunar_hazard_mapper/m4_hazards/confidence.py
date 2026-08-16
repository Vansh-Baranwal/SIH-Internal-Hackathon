"""src/lunar_hazard_mapper/m4_hazards/confidence.py"""
from __future__ import annotations
import numpy as np


def calculate_confidence(inputs: dict) -> np.ndarray:
    """C = 1 - U_norm (handbook 5.10). Combines whichever normalized
    uncertainty indicators are present -- shadow/occlusion, SR
    reconstruction-error proxy, detector-confidence deficit -- per M4-N.
    Missing keys are simply skipped, so this works before every upstream
    uncertainty source exists yet (M2's SR error, M4's own detector
    confidence), matching the "start by combining what's available" rule.

    Args:
        inputs: dict, any subset of:
            "shadow_mask": bool ndarray (True = shadowed)
            "sr_uncertainty": ndarray, arbitrary scale (will be normalized)
            "detector_confidence_penalty": ndarray in [0,1]
            "shadow_penalty_weight": float, default 0.35 -- how much a
                shadowed pixel counts toward uncertainty (shadow lowers
                confidence, it is NEVER treated as hazard -- critical
                warning #4 / M4-O)

    Returns:
        ndarray in [0,1], same shape as the inputs
    """
    components = []

    if "shadow_mask" in inputs:
        weight = inputs.get("shadow_penalty_weight", 0.35)
        components.append(inputs["shadow_mask"].astype(np.float64) * weight)

    if "sr_uncertainty" in inputs:
        x = inputs["sr_uncertainty"]
        components.append(_normalize(x))

    if "detector_confidence_penalty" in inputs:
        components.append(np.clip(inputs["detector_confidence_penalty"], 0.0, 1.0))

    if not components:
        raise ValueError(
            "calculate_confidence(inputs) needs at least one of "
            "'shadow_mask', 'sr_uncertainty', 'detector_confidence_penalty'"
        )

    u_norm = np.clip(sum(components) / len(components), 0.0, 1.0)
    return np.clip(1.0 - u_norm, 0.0, 1.0)


def _normalize(x: np.ndarray) -> np.ndarray:
    x_min, x_max = float(np.min(x)), float(np.max(x))
    if x_max - x_min < 1e-9:
        return np.zeros_like(x, dtype=np.float64)
    return np.clip((x - x_min) / (x_max - x_min), 0.0, 1.0)
