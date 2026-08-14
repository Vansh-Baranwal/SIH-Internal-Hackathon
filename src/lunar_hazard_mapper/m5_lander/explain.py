"""Stable, M6-ready rejection records."""
from __future__ import annotations

from typing import Any, Mapping, Sequence


def generate_rejection_reason(
    site: Mapping[str, Any],
    violations: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Build a serialisable rejection record from constraint violations."""
    normalized = [
        {"code": str(item["code"]), "actual": item.get("actual"), "limit": item.get("limit"),
         "message": str(item["message"])}
        for item in violations
    ]
    if not normalized:
        raise ValueError("a rejection record requires at least one violation")
    return {
        "site_id": site.get("site_id"), "row": site.get("row"), "col": site.get("col"),
        "reason_codes": list(dict.fromkeys(item["code"] for item in normalized)),
        "violations": normalized,
    }
