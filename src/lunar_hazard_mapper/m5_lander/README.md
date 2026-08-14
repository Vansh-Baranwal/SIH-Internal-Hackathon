# Member 5: Lander Landing-Site Evaluation

Member 5 owns the **lander-intelligence layer** between M4 (hazard mapping) and M6 (trajectory planning). It evaluates candidate landing sites against lander-specific constraints, produces ranked safe-site recommendations, and explains rejections in a format M6 can use for replanning.

## Overview

The M5 pipeline:
1. **Accept M4 output** — Terrain grid (z, dx, dy) and per-cell hazard layers (slope, binary_mask, continuous_risk, confidence, roughness, crater/boulder risk).
2. **Generate candidate sites** — Sample grid positions respecting border margins and landing-zone size constraints.
3. **Analyze each candidate** — Measure landing-zone statistics and evaluate circular footprint.
4. **Apply hard constraints** — Reject sites that violate slope, hazard, confidence, or clearance limits.
5. **Score and rank** — Transparent multi-factor scoring (risk, terrain quality, target distance, delta-v).
6. **Output for M6** — Ranked accepted sites and explained rejections; M6 can request replanning without re-running M4.

---

## Module Descriptions

### 1. **profile.py** — Lander Configuration

Defines lander-specific physical limits and loads them from YAML.

#### Key Components:

**`LanderProfile` dataclass**
```python
@dataclass(frozen=True, slots=True)
class LanderProfile:
    name: str                          # Lander identifier
    mass_kg: float                     # Vehicle mass
    max_slope_deg: float               # Maximum safe slope (hard limit)
    footprint_radius_m: float | None   # Circular footprint radius (None if not evaluated)
    landing_zone_size_m: float         # Zone size for analysis (default 24.0 m)
    min_clearance_m: float | None      # Minimum safe distance from boulders
    max_roughness_m: float | None      # Maximum terrain roughness
    min_confidence: float | None       # Minimum hazard-detection confidence [0, 1]
```

**Validation:**
- Rejects invalid name, non-positive mass, slope outside [0, 90).
- Enforces min_confidence ∈ [0, 1].
- Checks all optional fields are non-negative (or zero for clearance).

**Functions:**
- `load_lander_profile(path: str | Path) -> LanderProfile` — Load from YAML file (with fallback parser if PyYAML unavailable).
- `LanderProfile.from_mapping(values: Mapping[str, Any]) -> LanderProfile` — Build from dict, with strict field validation and numeric coercion.

#### Example Usage:
```python
# Load lander from YAML
profile_a = load_lander_profile("configs/landers/lander_A.yaml")
# Lander A: max_slope_deg=10°, footprint_radius_m=None (not yet agreed)

# Create programmatically
profile_b = LanderProfile(
    name="Lander B", mass_kg=2000, max_slope_deg=5,
    footprint_radius_m=2.5, min_confidence=0.8
)
```

---

### 2. **site_generator.py** — Candidate Site Generation

Generates deterministic grid positions for landing-site evaluation.

#### Key Function:

**`generate_candidate_sites(terrain: Mapping[str, Any], *, landing_zone_size_m: float = 24.0, spacing_m: float | None = None) -> list[dict[str, int | float | str]]`**

**Input:**
- `terrain` — Either M4's `m4_to_m5["terrain"]` dict or complete M4-to-M5 payload.
- `landing_zone_size_m` — Size of analysis zone (default 24 m).
- `spacing_m` — Sample spacing in metres (default: same as landing_zone_size_m).

**Logic:**
- Extracts 2D terrain grid (z) and resolution (dx, dy).
- Computes border margins: `landing_zone_size_m / 2` on each side (to fit a complete zone).
- Samples grid positions on regular spacing.
- **Critical:** Excludes image edges to ensure a full 24×24 m zone fits around every candidate.

**Output:** List of candidate dicts:
```python
{
    "site_id": "r{row}_c{col}",  # Unique identifier
    "row": int,                  # Grid row index
    "col": int,                  # Grid column index
    "x_m": float,                # Absolute metre coordinate (includes origin offset)
    "y_m": float,                # Absolute metre coordinate
    "elevation_m": float,        # Terrain elevation at centre
}
```

**Features:**
- Respects origin offset from M4 payload (if provided).
- Returns empty list if zone cannot fit (small grids).
- Deterministic: identical input → identical candidates.

#### Example Usage:
```python
terrain = m4_to_m5["terrain"]
candidates = generate_candidate_sites(terrain, landing_zone_size_m=24.0, spacing_m=12.0)
# Each candidate represents a potential landing site centre
```

---

### 3. **landing_zone.py** — Landing-Zone Analysis

Analyzes the rectangular 24×24 m region around each candidate.

#### Key Function:

**`analyze_landing_zone(site: Mapping[str, Any], m4_to_m5: Mapping[str, Any], *, radius_m: float = 12.0) -> dict[str, Any]`**

**Input:**
- `site` — Candidate dict with `row`, `col` fields.
- `m4_to_m5` — Complete M4-to-M5 payload (or extracted `m4_to_m5["terrain"]` and `m4_to_m5["hazards"]`).
- `radius_m` — Half-width of rectangular zone (default 12 m → 24×24 m).

**Output:** Zone analysis dict:
```python
{
    "site_id": str,
    "in_bounds": bool,              # True if complete zone fits inside grid
    "reason": str | None,           # "OUT_OF_BOUNDS" if not in_bounds
    "row_bounds": (int, int),       # [row_start, row_end)
    "col_bounds": (int, int),       # [col_start, col_end)
    "size_m": {"x": float, "y": float},
    "pixel_count": int,
    "max_slope_deg": float,         # Max slope in zone
    "mean_slope_deg": float,
    "max_risk": float,              # Max continuous_risk
    "mean_risk": float,
    "unsafe_fraction": float,       # Fraction of binary_mask==True pixels
    "min_confidence": float,        # Min detection confidence
    "max_roughness_m": float,
    "mean_roughness_m": float,
    "max_crater_risk": float,       # Max crater_risk layer
    "max_boulder_risk": float,      # Max boulder_risk layer
    "crater_count": int,            # Crater candidates inside zone
    "boulder_count": int,           # Boulder candidates inside zone
}
```

**Features:**
- **Strict boundary check:** Returns OUT_OF_BOUNDS if zone doesn't fully fit (no clipping).
- Counts crater and boulder candidates from M4 lists.
- All statistics computed on M4 grid cells, preserving precision.

#### Example Usage:
```python
zone = analyze_landing_zone(candidate, m4_to_m5)
if zone["in_bounds"]:
    print(f"Max slope: {zone['max_slope_deg']}°, craters: {zone['crater_count']}")
else:
    print(f"Site too close to edge: {zone['reason']}")
```

---

### 4. **footprint.py** — Footprint Evaluation

Evaluates every pixel inside the lander's circular footprint.

#### Key Function:

**`evaluate_footprint(site: Mapping[str, Any], profile: LanderProfile, m4_to_m5: Mapping[str, Any]) -> dict[str, Any]`**

**Input:**
- `site` — Candidate with row, col.
- `profile` — LanderProfile (must include `footprint_radius_m`).
- `m4_to_m5` — M4-to-M5 payload.

**Output:** Footprint evaluation dict:
```python
{
    "site_id": str,
    "in_bounds": bool,
    "safe": bool,                              # All checks passed
    "passes": {
        "slope": bool,                         # max_slope_deg ≤ profile.max_slope_deg
        "hazards": bool,                       # No binary_mask pixels or crater intersections
        "confidence": bool,                    # min_confidence ≥ profile.min_confidence (if set)
        "roughness": bool,                     # max_roughness ≤ profile.max_roughness_m (if set)
        "boulder_clearance": bool,             # min_clearance ≥ profile.min_clearance_m (if set)
    },
    "checked_pixel_count": int,                # Pixels inside footprint circle
    "max_slope_deg": float,
    "max_risk": float,
    "mean_risk": float,
    "min_confidence": float,
    "max_roughness_m": float,
    "unsafe_pixel_count": int,                 # binary_mask==True inside footprint
    "minimum_boulder_clearance_m": float,      # Min distance to boulder edge
    "crater_intersects_footprint": bool,       # True if any crater overlaps footprint
}
```

**Features:**
- Uses circular mask to select only footprint pixels.
- Checks **every covered pixel**, not just the centre.
- Measures boulder clearance as distance from footprint edge to boulder edge.
- Detects crater intersections (crater centre + crater radius).
- Requires `footprint_radius_m` in profile (raises ValueError otherwise).

#### Example Usage:
```python
profile = LanderProfile("A", 1500, 10, footprint_radius_m=2.5)
footprint = evaluate_footprint(candidate, profile, m4_to_m5)
if not footprint["passes"]["slope"]:
    print(f"Footprint slope {footprint['max_slope_deg']}° exceeds limit {profile.max_slope_deg}°")
```

---

### 5. **constraints.py** — Hard Feasibility Checks

Applies profile-specific hard constraints to reject unfeasible sites.

#### Key Function:

**`check_hard_constraints(site: Mapping[str, Any], profile: LanderProfile, zone: Mapping[str, Any], footprint: Mapping[str, Any], *, max_unsafe_fraction: float = 0.0) -> dict[str, Any]`**

**Input:**
- `site`, `profile`, `zone`, `footprint` — From prior analysis steps.
- `max_unsafe_fraction` — Acceptable fraction of unsafe pixels in zone (default 0).

**Output:**
```python
{
    "site_id": str,
    "feasible": bool,                 # True if no violations
    "violations": [                   # ALL failed constraints (not just first)
        {
            "code": str,              # e.g., "SLOPE_EXCEEDED", "LOW_CONFIDENCE"
            "actual": float | int,    # Measured value
            "limit": float | int,     # Profile or default limit
            "message": str,           # Human-readable description
        },
        ...
    ],
}
```

**Violation Codes:**
- `OUT_OF_BOUNDS` — Zone or footprint doesn't fit in grid.
- `SLOPE_EXCEEDED` — Zone or footprint max slope exceeds profile limit.
- `UNSAFE_ZONE_FRACTION_EXCEEDED` — Too many hazardous pixels in zone.
- `CRATER_IN_ZONE` — Crater candidate intersects landing zone.
- `FOOTPRINT_HAZARD` — Unsafe pixel or crater inside footprint.
- `LOW_CONFIDENCE` — Zone or footprint confidence below minimum.
- `ROUGHNESS_EXCEEDED` — Zone or footprint roughness exceeds maximum.
- `BOULDER_CLEARANCE` — Boulder clearance below minimum.

**Features:**
- Returns **all** violations so rejection is fully explainable.
- Optional constraints (confidence, roughness, clearance) only checked if profile specifies limits.
- Both zone and footprint measurements checked independently.

#### Example Usage:
```python
result = check_hard_constraints(candidate, profile_b, zone, footprint)
if not result["feasible"]:
    for violation in result["violations"]:
        print(f"{violation['code']}: {violation['actual']} vs {violation['limit']}")
```

---

### 6. **explain.py** — Structured Rejection Records

Converts constraint violations into M6-ready rejection explanations.

#### Key Function:

**`generate_rejection_reason(site: Mapping[str, Any], violations: Sequence[Mapping[str, Any]]) -> dict[str, Any]`**

**Input:**
- `site` — Candidate dict.
- `violations` — List of violation dicts from `check_hard_constraints()`.

**Output:**
```python
{
    "site_id": str,
    "row": int,
    "col": int,
    "reason_codes": [str],                # Deduplicated codes (e.g., ["SLOPE_EXCEEDED"])
    "violations": [                       # Complete violation records
        {"code": str, "actual": float, "limit": float, "message": str},
        ...
    ],
}
```

**Features:**
- Deduplicates reason codes (preserve first occurrence) while keeping all violation details.
- Fully serializable (no enums, no custom objects).
- M6 can use reason_codes for quick categorization and violations for detailed analysis.

#### Example Usage:
```python
rejection = generate_rejection_reason(candidate, constraints["violations"])
print(f"Site rejected: {', '.join(rejection['reason_codes'])}")
for v in rejection["violations"]:
    print(f"  {v['message']}: {v['actual']} (limit: {v['limit']})")
```

---

### 7. **scorer.py** — Transparent Site Ranking

Ranks feasible sites using multi-factor scoring with visible trade-offs.

#### Key Function:

**`score_site(site: Mapping[str, Any], profile: LanderProfile, zone: Mapping[str, Any], footprint: Mapping[str, Any], *, target_xy_m: tuple[float, float] | None = None, delta_v_mps: float | None = None, distance_scale_m: float = 1_000.0, delta_v_scale_mps: float = 1_000.0, weights: Mapping[str, float] | None = None) -> dict[str, Any]`**

**Input:**
- `site`, `profile`, `zone`, `footprint` — From prior analysis.
- `target_xy_m` — (x, y) coordinates of mission target (optional).
- `delta_v_mps` — Estimated delta-v cost from M6 (optional).
- `distance_scale_m` — Normalisation scale for distance (default 1000 m).
- `delta_v_scale_mps` — Normalisation scale for delta-v (default 1000 m/s).
- `weights` — Custom score weights (default: risk=0.45, target_distance=0.25, delta_v=0.15, terrain_quality=0.15).

**Output:**
```python
{
    "site_id": str,
    "score": float,                    # 0 to 1, higher is better
    "score_components": {
        "risk": float,                 # 1 - (0.6 × zone_mean_risk + 0.4 × footprint_max_risk)
        "terrain_quality": float,      # 0.5 × slope_quality + 0.5 × confidence
        "target_distance": float | None,  # 1 - (distance / scale), None if no target
        "delta_v": float | None,       # 1 - (delta_v / scale), None if no estimate
    },
    "weights": {
        "risk": float,                 # Normalised weights (sum = 1)
        "terrain_quality": float,
        "target_distance": float | None,
        "delta_v": float | None,
    },
}
```

**Features:**
- **Transparent:** All score components exposed; no hidden calculations.
- **Dynamic normalization:** If target or delta-v not provided, their weights are removed and remaining weights normalised.
- **Risk formula:** Weighted blend of zone mean risk (60%) and footprint max risk (40%).
- **Terrain quality:** Blend of slope quality (distance to max_slope_deg limit) and confidence.
- **Scoring scale:** [0, 1], where 1.0 is ideal.

#### Example Usage:
```python
score_a = score_site(
    candidate_a, profile, zone, footprint,
    target_xy_m=(1000, 2000), delta_v_mps=50
)
score_b = score_site(
    candidate_b, profile, zone, footprint,
    target_xy_m=(1000, 2000), delta_v_mps=75
)
# candidate_a scores higher if closer to target or lower delta-v
print(f"Score A: {score_a['score']:.3f}, Score B: {score_b['score']:.3f}")
```

---

### 8. **evaluator.py** — End-to-End Pipeline

Orchestrates the complete per-lander landing-site evaluation.

#### Key Function:

**`evaluate_sites(sites: Sequence[Mapping[str, Any]] | None, profile: LanderProfile, m4_to_m5: Mapping[str, Any], *, target_xy_m: tuple[float, float] | None = None, delta_v_by_site: Mapping[str, float] | None = None, max_unsafe_fraction: float = 0.0, scoring_weights: Mapping[str, float] | None = None) -> dict[str, Any]`**

**Input:**
- `sites` — List of candidate dicts (auto-generated if None).
- `profile` — LanderProfile (must include footprint_radius_m).
- `m4_to_m5` — M4-to-M5 payload.
- `target_xy_m` — Mission target location (optional).
- `delta_v_by_site` — Dict mapping site_id → delta-v cost from M6.
- `max_unsafe_fraction` — Acceptable hazard fraction (default 0).
- `scoring_weights` — Custom score weights.

**Pipeline:**
1. Generate candidates if not provided.
2. For each candidate:
   - Analyze landing zone.
   - Evaluate footprint.
   - Check hard constraints.
   - If feasible: score and rank.
   - If infeasible: explain rejection.
3. Sort accepted sites by score (descending).
4. Assign rank (1, 2, 3, ...).

**Output:**
```python
{
    "lander": {
        "name": str,
        "mass_kg": float,
        "max_slope_deg": float,
        "footprint_radius_m": float | None,
        "landing_zone_size_m": float,
    },
    "recommended_sites": [
        {
            # All site fields + scoring + measurements + notes
            "site_id": str,
            "row": int, "col": int, "x_m": float, "y_m": float,
            "score": float,
            "rank": int,
            "score_components": {...},
            "weights": {...},
            "zone_summary": {...},
            "footprint_summary": {...},
            "constraints_passed": ["ALL_HARD_CONSTRAINTS"],
            "notes": [],
        },
        ...
    ],
    "rejected_sites": [
        {
            "site_id": str,
            "row": int, "col": int,
            "reason_codes": [str],
            "violations": [...],
        },
        ...
    ],
    "candidate_count": int,
}
```

**Features:**
- Single entry point for complete per-lander evaluation.
- Deterministic ranking (ties broken by site_id).
- Accepted sites include all data needed by M6 (coordinates, scores, constraints).
- Rejected sites are explained, not hidden.

#### Example Usage:
```python
result = evaluate_sites(
    sites=None,  # Auto-generate
    profile=profile_a,
    m4_to_m5=m4_to_m5,
    target_xy_m=(1000, 2000),
    delta_v_by_site={"r20_c20": 50, "r20_c24": 60}
)
print(f"Lander {result['lander']['name']}: {len(result['recommended_sites'])} safe sites")
for site in result["recommended_sites"][:3]:
    print(f"  Rank {site['rank']}: {site['site_id']} (score {site['score']:.3f})")
```

---

### 9. **multi_lander.py** — Cross-Lander Comparison

Evaluates identical candidates across multiple lander profiles to identify shared and unique safe sites.

#### Key Function:

**`compare_landers(m4_to_m5: Mapping[str, Any], profiles: Sequence[LanderProfile], *, sites: Sequence[Mapping[str, Any]] | None = None, target_xy_m: tuple[float, float] | None = None, delta_v_by_lander: Mapping[str, Mapping[str, float]] | None = None, max_unsafe_fraction: float = 0.0, scoring_weights: Mapping[str, float] | None = None) -> dict[str, Any]`**

**Input:**
- `m4_to_m5` — M4-to-M5 payload.
- `profiles` — List of LanderProfile objects (names must be unique).
- `sites` — Candidate list (auto-generated from max landing_zone_size_m if None).
- `target_xy_m` — Mission target.
- `delta_v_by_lander` — Dict[lander_name → Dict[site_id → delta_v]].
- Other parameters as in `evaluate_sites()`.

**Output:**
```python
{
    "lander_results": {
        "Lander A": {...},    # Result from evaluate_sites()
        "Lander B": {...},
    },
    "shared_safe_sites": ["r20_c20", "r20_c24"],  # Accepted by all landers
    "lander_specific_safe_sites": {
        "Lander A": ["r24_c28"],                    # Accepted only by A
        "Lander B": [],                             # None unique to B
    },
    "best_recommendation": {
        "Lander A": {...},    # Top-ranked site or None
        "Lander B": {...},
    },
    "rejected_site_reasons": {
        "Lander A": {
            "r30_c30": ["SLOPE_EXCEEDED"],          # Why this site was rejected
            "r32_c32": ["LOW_CONFIDENCE"],
        },
        "Lander B": {
            "r30_c30": ["SLOPE_EXCEEDED", "ROUGHNESS_EXCEEDED"],
        },
    },
}
```

**Features:**
- Evaluates **identical candidate list** across profiles (ensures fair comparison).
- Identifies sites where lander A has 10° slope limit but lander B has 5° (key differentiator).
- Returns per-lander results for detailed analysis.
- Highlights shared vs. unique safe sites (valuable for mission planning).

#### Example Usage:
```python
comparison = compare_landers(
    m4_to_m5,
    [profile_a, profile_b],
    target_xy_m=(1000, 2000)
)
print(f"Shared safe sites: {comparison['shared_safe_sites']}")
print(f"Lander A only: {comparison['lander_specific_safe_sites']['Lander A']}")
print(f"Lander B best: {comparison['best_recommendation']['Lander B']['site_id']}")
```

---

## M4 ↔ M5 Data Contract

### M4 Output (Input to M5)

M4 produces the `m4_to_m5` dict:

```python
{
    "terrain": {
        "z": np.ndarray,              # 2D elevation grid [m]
        "dx": float,                  # Pixel width [m]
        "dy": float,                  # Pixel height [m]
        "origin": {                   # Optional: absolute coordinates
            "x_m": float,
            "y_m": float,
        },
    },
    "hazards": {
        "slope_deg": np.ndarray,      # 2D slope grid [°]
        "binary_mask": np.ndarray,    # 2D bool array: True = unsafe (M4's default slope limit 10°)
        "continuous_risk": np.ndarray,  # 2D risk [0, 1]
        "confidence": np.ndarray,     # 2D confidence [0, 1] (detection quality)
        "roughness": np.ndarray,      # 2D roughness [m]
        "crater_risk": np.ndarray,    # 2D crater hazard [0, 1]
        "boulder_risk": np.ndarray,   # 2D boulder hazard [0, 1]
    },
    "craters": [                      # Candidate crater detections
        {
            "center_row": float,
            "center_col": float,
            "diameter_m": float,
            ...
        },
        ...
    ],
    "boulders": [                     # Candidate boulder detections
        {
            "center_row": float,
            "center_col": float,
            "hazard_radius_m": float,  # or "radius_m"
            ...
        },
        ...
    ],
}
```

**Critical Notes:**
- M4's `binary_mask` uses M4's slope threshold (default 10°). **M5 applies each lander's own limit** (e.g., Lander B's 5°).
- All rasters must have identical shape.
- dx, dy must be positive (grid resolution).
- Crater/boulder lists can be empty.

---

## M5 Output (Input to M6)

M5 produces per-lander evaluation results for M6's trajectory planning:

### For Accepted Sites:
```python
{
    "site_id": "r20_c20",
    "row": 20, "col": 20,             # Grid indices
    "x_m": 1234.5, "y_m": 5678.9,     # Absolute coordinates (for path planning)
    "elevation_m": 1000.0,            # Terrain height
    "score": 0.87,                    # Ranking score [0, 1]
    "rank": 1,                        # Ordinal rank among accepted sites
    "score_components": {
        "risk": 0.9,
        "terrain_quality": 0.85,
        "target_distance": 0.95,
        "delta_v": None,              # Not provided by M6 during initial planning
    },
    "weights": {...},                 # Score weight breakdown
    "zone_summary": {...},            # Landing-zone statistics
    "footprint_summary": {...},       # Footprint evaluation details
    "constraints_passed": ["ALL_HARD_CONSTRAINTS"],
    "notes": [],
}
```

### For Rejected Sites:
```python
{
    "site_id": "r30_c30",
    "row": 30, "col": 30,
    "reason_codes": ["SLOPE_EXCEEDED"],
    "violations": [
        {
            "code": "SLOPE_EXCEEDED",
            "actual": 12.0,
            "limit": 10.0,
            "message": "landing-zone maximum slope exceeds limit",
        },
    ],
}
```

**M6 Integration:**
- **Initial planning:** M6 receives ranked accepted sites + rejection explanations; selects top alternative if first choice becomes unreachable.
- **Replanning:** M6 can request M5 to re-score sites using updated delta-v costs **without re-running M4 hazard detection** (faster feedback loop).

---

## Test Coverage

Run all tests:
```bash
pytest tests/m5/ -v
```

### Test Files

#### `test_profile_and_site_generator.py`
- ✅ Load Lander B profile (max_slope_deg=5).
- ✅ Profile validation (reject invalid confidence).
- ✅ Candidate generation respects 24 m zone borders.
- ✅ Candidates use origin offset from M4 payload.
- ✅ Empty candidates when zone cannot fit.

#### `test_landing_zone_and_footprint.py`
- ✅ Zone analysis returns statistics and crater/boulder counts.
- ✅ Zone rejects incomplete border window (OUT_OF_BOUNDS).
- ✅ Footprint checks all covered pixels (not just centre).
- ✅ Profile limits enforced: 6° slope fails 5° max.
- ✅ Footprint requires agreed radius.

#### `test_constraints_explain_scorer.py`
- ✅ Constraints return **all** violations.
- ✅ Explanations deduplicate reason codes.
- ✅ Optional constraints only applied if set in profile.
- ✅ Scoring is transparent (all components visible).
- ✅ Score prefers near, low-risk sites.
- ✅ Delta-v removed from weights if not provided.

#### `test_evaluator_and_multi_lander.py`
- ✅ Evaluator returns ranked accepted + explained rejected sites.
- ✅ Multi-lander: Lander A accepts 7° site (max 10°).
- ✅ Multi-lander: Lander B rejects same 7° site (max 5°).
- ✅ Shared safe sites identified correctly.
- ✅ Rejected site reasons keyed by site_id.

---

## Key Design Decisions

1. **Raster-based:** All calculations use NumPy grids. Preserves M4's native format and supports efficient neighbourhood operations.

2. **Per-lander profiles:** Each lander enforces its own slope limit independently. M5 never relies solely on M4's binary_mask.

3. **Complete zone enforcement:** Sites must have a full 24×24 m zone inside the grid. Partial zones are OUT_OF_BOUNDS (not clipped).

4. **All violations enumerated:** Hard-constraint checks return **every** failure, enabling complete explanations for M6.

5. **Transparent scoring:** All score components and weights exposed; no black-box ranking.

6. **Deterministic output:** Identical input always produces identical rankings (no randomness, no floating-point seed variability).

7. **Optional footprint evaluation:** Footprint checks only run if `profile.footprint_radius_m` is set. This allows staged evaluation (zone-only → footprint once agreed).

8. **M6 re-ranking:** Accepted sites can be re-scored with updated delta-v costs without re-running M4 hazard detection (supports replanning workflows).

---

## Dependencies

- **numpy** ≥ 1.21.0 — Raster operations (required).
- **PyYAML** ≥ 5.4 — Profile loading (optional; fallback parser available).

Install:
```bash
pip install -r src/lunar_hazard_mapper/m5_lander/requirements.txt
```

---

## Example Workflow

```python
from lunar_hazard_mapper.m5_lander.profile import load_lander_profile
from lunar_hazard_mapper.m5_lander.multi_lander import compare_landers
from some_m4_module import produce_m4_to_m5

# 1. Load M4 output
m4_to_m5 = produce_m4_to_m5(dem_path, hazard_model)

# 2. Load lander profiles
lander_a = load_lander_profile("configs/landers/lander_A.yaml")
lander_b = load_lander_profile("configs/landers/lander_B.yaml")

# 3. Evaluate both landers on identical candidates
result = compare_landers(
    m4_to_m5,
    [lander_a, lander_b],
    target_xy_m=(1234.5, 5678.9),  # Mission target
    delta_v_by_lander={
        "Lander A": {"r20_c20": 50, "r20_c24": 60},
        "Lander B": {"r20_c20": 55, "r20_c24": 65},
    }
)

# 4. Inspect results
print(f"Shared safe sites: {result['shared_safe_sites']}")
print(f"Lander A best: {result['best_recommendation']['Lander A']['site_id']}")

# 5. Pass to M6
for name, lander_result in result["lander_results"].items():
    send_to_m6(name, lander_result["recommended_sites"], lander_result["rejected_sites"])
```

---

## Integration with M6

M6 receives:

1. **Ranked accepted sites** — With score, coordinates, terrain/hazard summary, footprint/zone measurements.
2. **Rejected sites with reasons** — Codes (SLOPE_EXCEEDED, CRATER_IN_ZONE, etc.) + detailed violations.
3. **Best recommendation per lander** — Top site in rank order.

M6 can:
- Select top-ranked site and plan trajectory.
- Request alternatives if top site is unreachable (M6 provides delta-v cost update).
- Re-run M5's scorer with updated delta-v without re-triggering M4 hazard detection.

---

## Status

✅ All 9 modules implemented and tested.  
✅ Lander profiles (A: 10° slope, B: 5° slope) configured.  
✅ Hard constraints and explanations working.  
✅ Transparent scoring with visible trade-offs.  
✅ Multi-lander comparison identifying shared/unique safe sites.  
✅ Ready for M6 integration.

---

## References

- **Member 5 Work Plan:** `docs/members/m5_next_steps.md`
- **M4→M5 Data Contract:** `docs/api/M5_INTEGRATION_CONTRACT.md`
- **System Architecture:** `docs/architecture/SYSTEM_ARCHITECTURE.md`
