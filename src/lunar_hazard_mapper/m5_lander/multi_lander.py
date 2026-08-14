"""Comparison of landing-site results across multiple lander profiles."""
from __future__ import annotations

from typing import Any, Mapping, Sequence

from .evaluator import evaluate_sites
from .profile import LanderProfile
from .site_generator import generate_candidate_sites


def compare_landers(
    m4_to_m5: Mapping[str, Any],
    profiles: Sequence[LanderProfile],
    *,
    sites: Sequence[Mapping[str, Any]] | None = None,
    request_id: str | None = None,
    target_xy_m: tuple[float, float] | None = None,
    delta_v_by_lander: Mapping[str, Mapping[str, float]] | None = None,
    max_unsafe_fraction: float = 0.0,
    scoring_weights: Mapping[str, float] | None = None,
) -> dict[str, Any]:
    """Evaluate identical candidates and identify shared/unique safe sites.

    Args:
        m4_to_m5: M4 hazard mapping output.
        profiles: Sequence of LanderProfile objects (names must be unique).
        sites: Candidate site list (auto-generated if None).
        request_id: Optional trace ID for M4->M5->M6 request chain.
        target_xy_m: Optional mission target (x_m, y_m) for scoring.
        delta_v_by_lander: Dict[lander_name -> Dict[site_id -> delta_v]].
        max_unsafe_fraction: Maximum acceptable hazard pixel fraction in zone.
        scoring_weights: Optional custom score weights.
    """
    if not profiles:
        raise ValueError("at least one lander profile is required")
    names = [profile.name for profile in profiles]
    if len(names) != len(set(names)):
        raise ValueError("lander profile names must be unique")
    candidate_list = list(sites) if sites is not None else generate_candidate_sites(
        m4_to_m5, landing_zone_size_m=max(profile.landing_zone_size_m for profile in profiles)
    )
    results = {
        profile.name: evaluate_sites(
            candidate_list, profile, m4_to_m5, request_id=request_id, target_xy_m=target_xy_m,
            delta_v_by_site=None if delta_v_by_lander is None else delta_v_by_lander.get(profile.name),
            max_unsafe_fraction=max_unsafe_fraction, scoring_weights=scoring_weights,
        )
        for profile in profiles
    }
    accepted_sets = {
        name: {str(site["site_id"]) for site in result["recommended_sites"]}
        for name, result in results.items()
    }
    shared = set.intersection(*accepted_sets.values())
    return {
        "lander_results": results,
        "shared_safe_sites": sorted(shared),
        "lander_specific_safe_sites": {
            name: sorted(site_ids - shared) for name, site_ids in accepted_sets.items()
        },
        "best_recommendation": {
            name: (result["recommended_sites"][0] if result["recommended_sites"] else None)
            for name, result in results.items()
        },
        "rejected_site_reasons": {
            name: {str(site["site_id"]): site["reason_codes"] for site in result["rejected_sites"]}
            for name, result in results.items()
        },
    }
