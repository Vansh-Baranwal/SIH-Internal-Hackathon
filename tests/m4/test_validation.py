import numpy as np
from lunar_hazard_mapper.m4_hazards.validation import circle_iou, validate_hazards


def test_circle_iou_identical():
    assert np.isclose(circle_iou((10, 10), 5.0, (10, 10), 5.0), 1.0)


def test_circle_iou_disjoint():
    assert circle_iou((0, 0), 2.0, (100, 100), 2.0) == 0.0


def test_circle_iou_nested():
    iou = circle_iou((0, 0), 10.0, (0, 0), 2.0)
    assert np.isclose(iou, (np.pi * 4) / (np.pi * 100))


def test_validate_hazards_perfect_crater_match():
    fused = {
        "binary_mask": np.zeros((10, 10), dtype=bool),
        "continuous_risk": np.zeros((10, 10)),
        "confidence": np.ones((10, 10)),
        "predicted_craters": [{"center_row": 5, "center_col": 5, "diameter_px": 8}],
        "ground_truth_craters": [{"center_row": 5, "center_col": 5, "diameter_px": 8}],
    }
    result = validate_hazards(fused)
    assert result["crater_detection"]["tp"] == 1
    assert np.isclose(result["crater_detection"]["f1"], 1.0)
    assert result["boulder_detection"] is None  # no boulder ground truth supplied


def test_validate_hazards_missed_boulder():
    fused = {
        "predicted_boulders": [{"center_row": 1, "center_col": 1, "radius_px": 2}],
        "ground_truth_boulders": [{"center_row": 1, "center_col": 1, "radius_px": 2},
                                   {"center_row": 50, "center_col": 50, "radius_px": 2}],
    }
    result = validate_hazards(fused)
    m = result["boulder_detection"]
    assert m["tp"] == 1 and m["fn"] == 1 and m["fp"] == 0
