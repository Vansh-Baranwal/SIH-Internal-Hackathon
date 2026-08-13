"""
M3 synthetic terrain orchestration.

Wraps the low-level generators in synthetic/terrain/*.py (flat, slope,
crater, boulder, combined) and turns their output into DEM objects via
dem.generate_dem(). Kept separate from synthetic/terrain/*.py so those stay
simple array generators, while this module owns the M3-specific step of
attaching DEM metadata.
"""

import os
import sys

# synthetic/terrain lives at the repo root, not under src/. Make sure the
# repo root is importable regardless of which directory a script is run
# from (VS Code, pytest, or a plain `python scripts/...`).
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                           "..", "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from synthetic.terrain.flat import generate_flat_terrain
from synthetic.terrain.slope import generate_slope
from synthetic.terrain.crater import generate_crater
from synthetic.terrain.boulder import generate_boulder
from synthetic.terrain.combined import generate_combined

from .dem import generate_dem

_GENERATORS = {
    "flat": generate_flat_terrain,
    "slope": generate_slope,
    "crater": generate_crater,
    "boulder": generate_boulder,
    "combined": generate_combined,
}


def create_synthetic_terrain(kind="combined", size=256, pixel_size_m=1.0,
                              **kwargs):
    """
    Generate a synthetic terrain type and wrap it as a DEM object.

    Args:
        kind: one of "flat", "slope", "crater", "boulder", "combined".
        size: grid size (pixels per side).
        pixel_size_m: ground sampling distance per pixel, in meters.
        **kwargs: forwarded to the underlying generator (e.g. slope_deg,
            depth_m, radius_px -- see synthetic/terrain/<kind>.py).

    Returns:
        DEM instance, tagged source_type="synthetic".
    """
    if kind not in _GENERATORS:
        raise ValueError(
            f"Unknown synthetic terrain kind '{kind}'. "
            f"Choose from: {sorted(_GENERATORS)}"
        )

    terrain = _GENERATORS[kind](size=size, pixel_size_m=pixel_size_m,
                                 **kwargs)
    return generate_dem(
        terrain,
        notes=f"Synthetic '{kind}' terrain generated for M3 pipeline testing.",
    )
