"""Tests for HTML report generation."""

from pathlib import Path

from qc_tools.html_report import generate_html_report
from qc_tools.models import Anomaly, Report, StreamInfo, VideoFrame
from qc_tools.thresholds import Policy


def _make_report():
    r = Report(
        source=Path("test.mkv"),
        stream=StreamInfo(
            codec="ffv1",
            width=720,
            height=576,
            fps=25.0,
            duration=10.0,
            total_frames=250,
            has_audio=True,
            audio_codec="pcm_s16le",
            audio_channels=2,
            audio_sample_rate=48000,
            format_name="matroska",
            filename="test.mkv",
        ),
        policy=Policy(name="videotape", media_type="videotape"),
    )
    r.video_frames = [VideoFrame(n=i, media_time=i * 0.04) for i in range(5)]
    r.anomalies = [
        Anomaly("tout", 2, "00:00:00:02", 0.08, "warning", 0.05, 0.009, "temporal"),
        Anomaly("brng", 3, "00:00:00:03", 0.12, "error", 0.3, 0.01, "broadcast"),
        Anomaly(
            "peak", 0, "00:00:00.000", 0.0, "error", 1.5, 0.0, "clip", is_audio=True
        ),
    ]
    return r


class TestGenerateHtmlReport:
    def test_returns_html_string(self):
        report = _make_report()
        html = generate_html_report(report)
        assert isinstance(html, str)
        assert "<!DOCTYPE html>" in html

    def test_contains_filename(self):
        report = _make_report()
        html = generate_html_report(report)
        assert "test.mkv" in html

    def test_contains_anomaly_count(self):
        report = _make_report()
        html = generate_html_report(report)
        assert "3" in html

    def test_contains_policy_name(self):
        report = _make_report()
        html = generate_html_report(report)
        assert "videotape" in html

    def test_contains_severity_badges(self):
        report = _make_report()
        html = generate_html_report(report)
        assert "warning" in html
        assert "error" in html

    def test_contains_svg_timeline(self):
        report = _make_report()
        html = generate_html_report(report)
        assert "<svg" in html
        assert "</svg>" in html

    def test_video_anomaly_table(self):
        report = _make_report()
        html = generate_html_report(report)
        assert "Video Anomalies" in html

    def test_audio_anomaly_table(self):
        report = _make_report()
        html = generate_html_report(report)
        assert "Audio Anomalies" in html

    def test_empty_report(self):
        r = Report(
            source=Path("empty.mkv"),
            stream=StreamInfo(
                codec="h264", width=1920, height=1080, fps=30.0, duration=0
            ),
        )
        html = generate_html_report(r)
        assert "<!DOCTYPE html>" in html
