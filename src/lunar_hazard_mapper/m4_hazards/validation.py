"""src/lunar_hazard_mapper/m4_hazards/validation.py"""
from __future__ import annotations
import numpy as np


def validate_hazards(fused_hazards: dict) -> dict:
    """M4-Q / handbook 5.9: IoU, Precision, Recall, F1 against ground truth
    where it exists, plus basic summary stats always. Craters/boulders are
    treated as circles (center, radius) for closed-form IoU.

    Args:
        fused_hazards: {
            "binary_mask": ndarray (from fusion.fuse_hazards, for summary stats),
            "continuous_risk": ndarray,
            "confidence": ndarray,
            "predicted_craters": list[dict] (optional, needs center_row/col + diameter_px or radius_px),
            "ground_truth_craters": list[dict] (optional, same shape),
            "predicted_boulders": list[dict] (optional, needs center_row/col + radius_px),
            "ground_truth_boulders": list[dict] (optional, same shape),
            "iou_threshold": float, default 0.15,
        }

    Returns:
        {"summary": {...}, "crater_detection": {...} or None, "boulder_detection": {...} or None}
    """
    summary = {
        "hazard_fraction_binary": float(np.mean(fused_hazards["binary_mask"])) if "binary_mask" in fused_hazards else None,
        "mean_continuous_risk": float(np.mean(fused_hazards["continuous_risk"])) if "continuous_risk" in fused_hazards else None,
        "mean_confidence": float(np.mean(fused_hazards["confidence"])) if "confidence" in fused_hazards else None,
    }

    iou_threshold = fused_hazards.get("iou_threshold", 0.15)
    crater_metrics = None
    if "ground_truth_craters" in fused_hazards:
        pred = [{"center_row": c["center_row"], "center_col": c["center_col"],
                 "radius_px": c.get("diameter_px", c.get("radius_px", 0) * 2) / 2.0}
                for c in fused_hazards.get("predicted_craters", [])]
        gt = [{"center_row": c["center_row"], "center_col": c["center_col"],
               "radius_px": c.get("diameter_px", c.get("radius_px", 0) * 2) / 2.0}
              for c in fused_hazards["ground_truth_craters"]]
        crater_metrics = _evaluate_circles(pred, gt, iou_threshold)

    boulder_metrics = None
    if "ground_truth_boulders" in fused_hazards:
        pred = fused_hazards.get("predicted_boulders", [])
        gt = fused_hazards["ground_truth_boulders"]
        boulder_metrics = _evaluate_circles(pred, gt, iou_threshold)

    return {"summary": summary, "crater_detection": crater_metrics, "boulder_detection": boulder_metrics}


def circle_iou(c1, r1: float, c2, r2: float) -> float:
    """IoU = Area(P n G) / Area(P u G) (handbook 5.9), closed-form for circles."""
    d = float(np.hypot(c1[0] - c2[0], c1[1] - c2[1]))
    r1, r2 = float(r1), float(r2)
    if r1 <= 0 or r2 <= 0:
        return 0.0
    area1, area2 = np.pi * r1 ** 2, np.pi * r2 ** 2
    if d >= r1 + r2:
        inter = 0.0
    elif d <= abs(r1 - r2):
        inter = np.pi * min(r1, r2) ** 2
    else:
        a1 = np.arccos(np.clip((d ** 2 + r1 ** 2 - r2 ** 2) / (2 * d * r1), -1.0, 1.0))
        a2 = np.arccos(np.clip((d ** 2 + r2 ** 2 - r1 ** 2) / (2 * d * r2), -1.0, 1.0))
        inter = r1 ** 2 * (a1 - np.sin(2 * a1) / 2.0) + r2 ** 2 * (a2 - np.sin(2 * a2) / 2.0)
    union = area1 + area2 - inter
    return float(inter / union) if union > 0 else 0.0


def _evaluate_circles(predictions: list[dict], ground_truth: list[dict], iou_threshold: float) -> dict:
    n_pred, n_gt = len(predictions), len(ground_truth)
    if n_gt == 0:
        return {"tp": 0, "fp": n_pred, "fn": 0, "precision": 0.0 if n_pred else 1.0, "recall": 1.0, "f1": 0.0 if n_pred else 1.0}
    if n_pred == 0:
        return {"tp": 0, "fp": 0, "fn": n_gt, "precision": 1.0, "recall": 0.0, "f1": 0.0}

    iou_matrix = np.zeros((n_pred, n_gt))
    for i, p in enumerate(predictions):
        for j, g in enumerate(ground_truth):
            iou_matrix[i, j] = circle_iou((p["center_row"], p["center_col"]), p["radius_px"],
                                            (g["center_row"], g["center_col"]), g["radius_px"])

    matched_gt, matched_pred, matches = set(), set(), []
    order = np.dstack(np.unravel_index(np.argsort(-iou_matrix, axis=None), iou_matrix.shape))[0]
    for i, j in order:
        i, j = int(i), int(j)
        if i in matched_pred or j in matched_gt or iou_matrix[i, j] < iou_threshold:
            continue
        matched_pred.add(i); matched_gt.add(j); matches.append(iou_matrix[i, j])

    tp = len(matches)
    fp, fn = n_pred - tp, n_gt - tp
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    return {"tp": tp, "fp": fp, "fn": fn, "precision": precision, "recall": recall, "f1": f1,
            "mean_iou_tp": float(np.mean(matches)) if matches else 0.0}
