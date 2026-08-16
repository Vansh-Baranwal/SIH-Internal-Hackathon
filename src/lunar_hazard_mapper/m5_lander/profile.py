"""Lander-specific configuration used by the Member 5 site evaluator."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

try:
    import yaml
except ImportError:  # Keep the current minimal environment runnable.
    yaml = None


@dataclass(frozen=True, slots=True)
class LanderProfile:
    """Physical limits and evaluation settings for one lander.

    Only name, mass, and maximum slope are currently configured for the two
    project landers. The other limits are deliberately optional until the team
    agrees their mission values; ``None`` means that constraint is not applied.
    """

    name: str
    mass_kg: float
    max_slope_deg: float
    footprint_radius_m: float | None = None
    landing_zone_size_m: float = 24.0
    min_clearance_m: float | None = None
    max_roughness_m: float | None = None
    min_confidence: float | None = None

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise ValueError("name must be a non-empty string")
        if self.mass_kg <= 0:
            raise ValueError("mass_kg must be positive")
        if not 0 <= self.max_slope_deg < 90:
            raise ValueError("max_slope_deg must be in [0, 90)")
        if self.landing_zone_size_m <= 0:
            raise ValueError("landing_zone_size_m must be positive")
        _validate_optional_positive("footprint_radius_m", self.footprint_radius_m)
        _validate_optional_positive("min_clearance_m", self.min_clearance_m, allow_zero=True)
        _validate_optional_positive("max_roughness_m", self.max_roughness_m, allow_zero=True)
        if self.min_confidence is not None and not 0 <= self.min_confidence <= 1:
            raise ValueError("min_confidence must be in [0, 1]")

    @classmethod
    def from_mapping(cls, values: Mapping[str, Any]) -> "LanderProfile":
        """Build and validate a profile from a YAML-decoded mapping."""
        allowed = {field.name for field in cls.__dataclass_fields__.values()}
        unknown = set(values) - allowed
        if unknown:
            raise ValueError(f"unknown lander profile fields: {sorted(unknown)}")
        converted = dict(values)
        for name in (
            "mass_kg", "max_slope_deg", "footprint_radius_m",
            "landing_zone_size_m", "min_clearance_m", "max_roughness_m",
            "min_confidence",
        ):
            if converted.get(name) is not None:
                try:
                    converted[name] = float(converted[name])
                except (TypeError, ValueError) as exc:
                    raise ValueError(f"{name} must be numeric") from exc
        try:
            return cls(**converted)
        except TypeError as exc:
            raise ValueError(f"invalid lander profile fields: {exc}") from exc


def load_lander_profile(path: str | Path) -> LanderProfile:
    """Load a single lander profile from a YAML file."""
    profile_path = Path(path)
    text = profile_path.read_text(encoding="utf-8")
    values = yaml.safe_load(text) if yaml is not None else _parse_flat_yaml(text)
    if not isinstance(values, Mapping):
        raise ValueError(f"{profile_path} must contain one YAML mapping")
    return LanderProfile.from_mapping(values)


def _validate_optional_positive(name: str, value: float | None, *, allow_zero: bool = False) -> None:
    if value is None:
        return
    if value < 0 or (value == 0 and not allow_zero):
        qualifier = "non-negative" if allow_zero else "positive"
        raise ValueError(f"{name} must be {qualifier} when provided")


def _parse_flat_yaml(text: str) -> dict[str, str]:
    """Parse the project's flat ``key: value`` profile files without PyYAML.

    Nested YAML is intentionally unsupported in this fallback; install PyYAML
    for richer profile configuration.
    """
    result: dict[str, str] = {}
    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.split("#", maxsplit=1)[0].strip()
        if not line:
            continue
        if ":" not in line:
            raise ValueError(f"invalid YAML at line {line_number}: expected 'key: value'")
        key, value = (part.strip() for part in line.split(":", maxsplit=1))
        if not key or not value:
            raise ValueError(f"invalid YAML at line {line_number}: expected 'key: value'")
        result[key] = value.strip("'\"")
    return result
