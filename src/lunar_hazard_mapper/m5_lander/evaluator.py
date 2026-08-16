"""End-to-end, per-lander landing-site evaluation."""
from __future__ import annotations

from typing import Any, Mapping, Sequence

from .constraints import check_hard_constraints
from .explain import generate_rejection_reason
from .footprint import evaluate_footprint
from .landing_zone import analyze_landing_zone
from .profile import LanderProfile
from .scorer import score_site
from .site_generator import generate_candidate_sites


def evaluate_sites(
    sites: Sequence[Mapping[str, Any]] | None,
    profile: LanderProfile,
    m4_to_m5: Mapping[str, Any],
    *,
    request_id: str | None = None,
    target_xy_m: tuple[float, float] | None = None,
    delta_v_by_site: Mapping[str, float] | None = None,
    max_unsafe_fraction: float = 0.0,
    scoring_weights: Mapping[str, float] | None = None,
) -> dict[str, Any]:
    """Evaluate, explain, score, and rank sites for one lander profile.

    Args:
        sites: Candidate site list (auto-generated if None).
        profile: Lander profile with constraints.
        m4_to_m5: M4 hazard mapping output.
        request_id: Optional trace ID for M4->M5->M6 request chain.
        target_xy_m: Optional mission target (x_m, y_m) for scoring.
        delta_v_by_site: Optional site_id -> delta-v cost mapping from M6.
        max_unsafe_fraction: Maximum acceptable hazard pixel fraction in zone.
        scoring_weights: Optional custom score weights.
    """
    if profile.footprint_radius_m is None:
        raise ValueError(f"{profile.name} needs footprint_radius_m before site evaluation")
    candidates = list(sites) if sites is not None else generate_candidate_sites(
        m4_to_m5, landing_zone_size_m=profile.landing_zone_size_m
    )
    accepted, rejected = [], []
    for site in candidates:
        zone = analyze_landing_zone(site, m4_to_m5, radius_m=profile.landing_zone_size_m / 2)
        footprint = evaluate_footprint(site, profile, m4_to_m5)
        constraints = check_hard_constraints(
            site, profile, zone, footprint, max_unsafe_fraction=max_unsafe_fraction
        )
        if not constraints["feasible"]:
            rejected.append(generate_rejection_reason(site, constraints["violations"]))
            continue
        delta_v = None if delta_v_by_site is None else delta_v_by_site.get(str(site.get("site_id")))
        ranking = score_site(
            site, profile, zone, footprint, target_xy_m=target_xy_m,
            delta_v_mps=delta_v, weights=scoring_weights,
        )
        accepted.append({
            **dict(site), **ranking,
            "zone_summary": zone,
            "footprint_summary": footprint,
            "constraints_passed": ["ALL_HARD_CONSTRAINTS"],
            "notes": [],
        })

    accepted.sort(key=lambda item: (-item["score"], str(item.get("site_id", ""))))
    for rank, site in enumerate(accepted, start=1):
        site["rank"] = rank
    result = {
        "lander": _profile_summary(profile),
        "recommended_sites": accepted,
        "rejected_sites": rejected,
        "candidate_count": len(candidates),
    }
    if request_id is not None:
        result["request_id"] = request_id
    return result


def handle_m6_feedback(
    evaluation_result: dict[str, Any],
    m6_feedback: Mapping[str, Any],
    profile: LanderProfile,
    m4_to_m5: Mapping[str, Any],
    *,
    target_xy_m: tuple[float, float] | None = None,
    scoring_weights: Mapping[str, float] | None = None,
) -> dict[str, Any]:
    """Process M6 replanning feedback and return next-best alternative.

    When M6 determines the top-ranked site is trajectory-infeasible, it sends
    feedback. M5 excludes that site and returns the next-best alternative,
    optionally re-scored with updated delta-v cost from M6.

    Args:
        evaluation_result: Original evaluation output from evaluate_sites().
        m6_feedback: Dict with keys:
            - site_id (str): Site ID rejected by M6
            - trajectory_feasible (bool): False if rejected
            - delta_v_mps (float | None): Updated delta-v estimate from trajectory eval
            - reason (str | None): Human-readable rejection reason
        profile: Lander profile (for re-scoring if needed).
        m4_to_m5: M4 payload (for re-scoring if needed).
        target_xy_m: Optional mission target for re-scoring.
        scoring_weights: Optional custom weights for re-scoring.

    Returns:
        Dict with keys:
            - next_recommended_site (dict): Next-best site with updated score (if delta_v_mps provided).
            - rejected_site_id (str): Site ID rejected by M6.
            - reason (str | None): M6 rejection reason.
            - alternatives_count (int): Total remaining feasible alternatives.
            - no_alternatives (bool): True if no other sites are feasible.
    """
    rejected_site_id = str(m6_feedback.get("site_id", ""))
    delta_v_mps = m6_feedback.get("delta_v_mps")
    reason = m6_feedback.get("reason")

    # Find and remove the rejected site
    remaining_sites = [
        site for site in evaluation_result["recommended_sites"]
        if str(site.get("site_id", "")) != rejected_site_id
    ]

    if not remaining_sites:
        return {
            "next_recommended_site": None,
            "rejected_site_id": rejected_site_id,
            "reason": reason,
            "alternatives_count": 0,
            "no_alternatives": True,
        }

    # If M6 provides updated delta-v, re-score all remaining sites
    if delta_v_mps is not None:
        for site in remaining_sites:
            zone_summary = site.get("zone_summary", {})
            footprint_summary = site.get("footprint_summary", {})
            if zone_summary and footprint_summary:
                new_score = score_site(
                    site, profile, zone_summary, footprint_summary,
                    target_xy_m=target_xy_m, delta_v_mps=delta_v_mps,
                    weights=scoring_weights,
                )
                site["score"] = new_score["score"]
                site["score_components"] = new_score["score_components"]
                site["weights"] = new_score["weights"]

        # Re-sort by new scores
        remaining_sites.sort(key=lambda item: (-item["score"], str(item.get("site_id", ""))))
        for rank, site in enumerate(remaining_sites, start=1):
            site["rank"] = rank

    return {
        "next_recommended_site": remaining_sites[0],
        "rejected_site_id": rejected_site_id,
        "reason": reason,
        "alternatives_count": len(remaining_sites),
        "no_alternatives": False,
    }


def _profile_summary(profile: LanderProfile) -> dict[str, float | str | None]:
    return {
        "name": profile.name, "mass_kg": profile.mass_kg,
        "max_slope_deg": profile.max_slope_deg, "footprint_radius_m": profile.footprint_radius_m,
        "landing_zone_size_m": profile.landing_zone_size_m,
    }
