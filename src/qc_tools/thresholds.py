"""Policy system: YAML loading, threshold rules, and frame evaluation."""

from __future__ import annotations

import operator
from dataclasses import dataclass, field
from pathlib import Path

import yaml

_OPERATORS = {
    "gt": operator.gt,
    "gte": operator.ge,
    "lt": operator.lt,
    "lte": operator.le,
    "eq": operator.eq,
}

_POLICIES_DIR = Path(__file__).parent / "policies"


@dataclass
class ThresholdRule:
    """A single threshold rule within a policy."""

    metric: str
    operator: str
    value: float
    severity: str
    description: str

    def evaluate(self, metric_value: float | int | None) -> bool:
        if metric_value is None:
            return False
        op = _OPERATORS.get(self.operator)
        if op is None:
            return False
        try:
            return op(float(metric_value), self.value)
        except (ValueError, TypeError):
            return False

    def to_dict(self) -> dict:
        return {
            "metric": self.metric,
            "operator": self.operator,
            "value": self.value,
            "severity": self.severity,
            "description": self.description,
        }


@dataclass
class Policy:
    """A QC policy with a name, media type, and a list of threshold rules."""

    name: str
    media_type: str
    description: str = ""
    rules: list[ThresholdRule] = field(default_factory=list)
    custom: dict = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict) -> Policy:
        rules = []
        for r in data.get("rules", []):
            rules.append(
                ThresholdRule(
                    metric=r["metric"],
                    operator=r.get("operator", "gt"),
                    value=float(r["value"]),
                    severity=r.get("severity", "warning"),
                    description=r.get("description", ""),
                )
            )
        return cls(
            name=data.get("name", "custom"),
            media_type=data.get("media_type", "custom"),
            description=data.get("description", ""),
            rules=rules,
            custom={
                k: v
                for k, v in data.items()
                if k
                not in (
                    "name",
                    "media_type",
                    "description",
                    "rules",
                )
            },
        )

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "media_type": self.media_type,
            "description": self.description,
            "rules": [r.to_dict() for r in self.rules],
            "custom": self.custom,
        }


def _load_yaml(path: Path) -> dict:
    with open(path) as f:
        return yaml.safe_load(f) or {}


def load_policy(name_or_path: str | Path) -> Policy:
    """Load a built-in policy by name, or a custom policy from a YAML file path."""
    path = Path(name_or_path)
    if path.is_file():
        data = _load_yaml(path)
        return Policy.from_dict(data)

    builtin = _POLICIES_DIR / f"{name_or_path}.yaml"
    if builtin.is_file():
        data = _load_yaml(builtin)
        return Policy.from_dict(data)

    raise FileNotFoundError(
        f"Policy '{name_or_path}' not found. Built-in policies: {list_policies()}"
    )


def list_policies() -> list[str]:
    """Return names of all built-in policies."""
    return sorted(p.stem for p in _POLICIES_DIR.glob("*.yaml") if p.stem != "__init__")


def evaluate_video_frame(frame, policy: Policy):
    """Evaluate a VideoFrame against a policy, returning matching Anomaly objects."""
    from .models import Anomaly

    anomalies = []
    for rule in policy.rules:
        val = frame.metric(rule.metric)
        if val is None:
            continue
        if rule.evaluate(val):
            anomalies.append(
                Anomaly(
                    type=rule.metric,
                    frame=frame.n,
                    timecode=frame.timecode,
                    time_seconds=frame.media_time,
                    severity=rule.severity,
                    value=float(val),
                    threshold=rule.value,
                    description=rule.description,
                    is_audio=False,
                )
            )
    return anomalies


def evaluate_audio_frame(frame, policy: Policy):
    """Evaluate an AudioFrame against a policy, returning matching Anomaly objects."""
    from .models import Anomaly

    anomalies = []
    for rule in policy.rules:
        val = frame.metric(rule.metric)
        if val is None:
            continue
        if rule.evaluate(val):
            anomalies.append(
                Anomaly(
                    type=rule.metric,
                    frame=frame.n,
                    timecode=frame.timecode,
                    time_seconds=frame.media_time,
                    severity=rule.severity,
                    value=float(val),
                    threshold=rule.value,
                    description=rule.description,
                    is_audio=True,
                )
            )
    return anomalies
