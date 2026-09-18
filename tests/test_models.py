"""Tests for models."""

from pathlib import Path

from qc_tools.models import Anomaly, AudioFrame, Report, StreamInfo, VideoFrame


class TestVideoFrame:
    def test_metric_lookup(self):
        frame = VideoFrame(y_max=240, tout=0.05, brng=0.1)
        assert frame.metric("y_max") == 240
        assert frame.metric("tout") == 0.05
        assert frame.metric("brng") == 0.1

    def test_metric_unknown(self):
        frame = VideoFrame()
        assert frame.metric("nonexistent") is None

    def test_to_dict(self):
        frame = VideoFrame(n=1, media_time=0.04, y_max=240)
        d = frame.to_dict()
        assert d["n"] == 1
        assert d["y_max"] == 240


class TestAudioFrame:
    def test_metric_lookup(self):
        frame = AudioFrame(peak=-0.5, dc_offset=0.02)
        assert frame.metric("peak") == -0.5
        assert frame.metric("dc_offset") == 0.02


class TestAnomaly:
    def test_to_dict(self):
        a = Anomaly("tout", 10, "00:00:00:10", 0.4, "warning", 0.05, 0.009, "desc")
        d = a.to_dict()
        assert d["type"] == "tout"
        assert d["frame"] == 10
        assert d["is_audio"] is False


class TestReport:
    def make_report(self):
        return Report(
            source=Path("test.mkv"),
            stream=StreamInfo(
                codec="ffv1", width=720, height=576, fps=25.0, duration=10.0
            ),
        )

    def test_frames_alias(self):
        r = self.make_report()
        r.video_frames = [VideoFrame(n=0), VideoFrame(n=1)]
        assert len(r.frames) == 2

    def test_temporal_outliers(self):
        r = self.make_report()
        r.anomalies = [
            Anomaly("tout", 0, "00:00:00:00", 0.0, "warning", 0.05, 0.009, "t"),
            Anomaly("brng", 1, "00:00:00:01", 0.04, "warning", 0.5, 0.01, "b"),
        ]
        assert len(r.temporal_outliers) == 1

    def test_broadcast_range(self):
        r = self.make_report()
        r.anomalies = [
            Anomaly("brng", 1, "00:00:00:01", 0.04, "warning", 0.5, 0.01, "b"),
        ]
        assert len(r.broadcast_range) == 1

    def test_anomaly_summary(self):
        r = self.make_report()
        r.anomalies = [
            Anomaly("tout", 0, "00:00:00:00", 0.0, "warning", 0.05, 0.009, "t"),
            Anomaly("tout", 5, "00:00:00:05", 0.2, "error", 0.1, 0.009, "t"),
        ]
        summary = r.anomaly_summary()
        assert summary["tout"]["count"] == 2

    def test_to_dict(self):
        r = self.make_report()
        r.video_frames = [VideoFrame(n=0)]
        d = r.to_dict()
        assert d["total_video_frames"] == 1
        assert d["source"] == "test.mkv"

    def test_video_vs_audio_anomalies(self):
        r = self.make_report()
        r.anomalies = [
            Anomaly(
                "tout",
                0,
                "00:00:00:00",
                0.0,
                "warning",
                0.05,
                0.009,
                "t",
                is_audio=False,
            ),
            Anomaly(
                "peak", 0, "00:00:00.000", 0.0, "error", 1.0, 0.0, "clip", is_audio=True
            ),
        ]
        assert len(r.video_anomalies) == 1
        assert len(r.audio_anomalies) == 1
