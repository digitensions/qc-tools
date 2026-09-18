"""Tests for thresholds / policy system."""

import pytest

from qc_tools.models import AudioFrame, VideoFrame
from qc_tools.thresholds import (
    Policy,
    ThresholdRule,
    evaluate_audio_frame,
    evaluate_video_frame,
    list_policies,
    load_policy,
)


class TestThresholdRule:
    def test_gt_true(self):
        rule = ThresholdRule("tout", "gt", 0.009, "warning", "desc")
        assert rule.evaluate(0.05) is True

    def test_gt_false(self):
        rule = ThresholdRule("tout", "gt", 0.009, "warning", "desc")
        assert rule.evaluate(0.001) is False

    def test_lt_true(self):
        rule = ThresholdRule("ssimf", "lt", 0.95, "warning", "desc")
        assert rule.evaluate(0.90) is True

    def test_none_value(self):
        rule = ThresholdRule("tout", "gt", 0.009, "warning", "desc")
        assert rule.evaluate(None) is False


class TestPolicy:
    def test_from_dict(self):
        data = {
            "name": "test",
            "media_type": "test",
            "description": "test policy",
            "rules": [
                {
                    "metric": "tout",
                    "operator": "gt",
                    "value": 0.01,
                    "severity": "warning",
                    "description": "test",
                }
            ],
        }
        policy = Policy.from_dict(data)
        assert policy.name == "test"
        assert len(policy.rules) == 1

    def test_to_dict(self):
        policy = Policy(name="x", media_type="y", rules=[])
        d = policy.to_dict()
        assert d["name"] == "x"


class TestLoadPolicy:
    def test_builtin_videotape(self):
        policy = load_policy("videotape")
        assert policy.name == "videotape"
        assert len(policy.rules) > 0

    def test_builtin_audio(self):
        policy = load_policy("audio")
        assert policy.media_type == "audio"

    def test_builtin_film(self):
        policy = load_policy("film")
        assert policy.media_type == "film"

    def test_builtin_broadcast(self):
        policy = load_policy("broadcast")
        assert policy.media_type == "broadcast"

    def test_builtin_borndigital(self):
        policy = load_policy("borndigital")
        assert policy.media_type == "borndigital"

    def test_from_path(self, tmp_path):
        yaml_file = tmp_path / "custom.yaml"
        yaml_file.write_text("name: custom\nmedia_type: custom\nrules: []\n")
        policy = load_policy(yaml_file)
        assert policy.name == "custom"

    def test_not_found(self):
        with pytest.raises(FileNotFoundError):
            load_policy("nonexistent_policy_xyz")


class TestListPolicies:
    def test_has_expected_policies(self):
        names = list_policies()
        assert "videotape" in names
        assert "audio" in names
        assert "film" in names
        assert "broadcast" in names
        assert "borndigital" in names


class TestEvaluateVideoFrame:
    def test_tout_above_threshold(self):
        policy = Policy(
            name="t",
            media_type="t",
            rules=[ThresholdRule("tout", "gt", 0.009, "warning", "test")],
        )
        frame = VideoFrame(n=10, media_time=0.4, tout=0.05)
        anomalies = evaluate_video_frame(frame, policy)
        assert len(anomalies) == 1
        assert anomalies[0].frame == 10
        assert anomalies[0].is_audio is False

    def test_no_anomalies(self):
        policy = Policy(
            name="t",
            media_type="t",
            rules=[ThresholdRule("tout", "gt", 0.009, "warning", "test")],
        )
        frame = VideoFrame(n=5, media_time=0.2, tout=0.001)
        anomalies = evaluate_video_frame(frame, policy)
        assert len(anomalies) == 0

    def test_multiple_rules(self):
        policy = Policy(
            name="t",
            media_type="t",
            rules=[
                ThresholdRule("tout", "gt", 0.009, "warning", "test tout"),
                ThresholdRule("brng", "gt", 0.01, "warning", "test brng"),
            ],
        )
        frame = VideoFrame(n=1, media_time=0.04, tout=0.1, brng=0.5)
        anomalies = evaluate_video_frame(frame, policy)
        assert len(anomalies) == 2


class TestEvaluateAudioFrame:
    def test_peak_above_threshold(self):
        policy = Policy(
            name="t",
            media_type="t",
            rules=[ThresholdRule("peak", "gt", 0.0, "error", "clipping")],
        )
        frame = AudioFrame(n=0, media_time=0.0, peak=1.5)
        anomalies = evaluate_audio_frame(frame, policy)
        assert len(anomalies) == 1
        assert anomalies[0].is_audio is True
