"""Tests for parser module."""

import tempfile
from pathlib import Path

from qc_tools.models import VideoFrame
from qc_tools.parser import (
    _float_or,
    _int_or,
    _parse_video_frame_tags,
)


class TestHelpers:
    def test_float_or_with_value(self):
        assert _float_or("3.14") == 3.14

    def test_float_or_with_none(self):
        assert _float_or(None) == 0.0

    def test_float_or_with_bad_string(self):
        assert _float_or("abc") == 0.0

    def test_int_or_with_value(self):
        assert _int_or("42") == 42

    def test_int_or_with_none(self):
        assert _int_or(None) == 0


class TestParseVideoFrameTags:
    def test_parses_basic_fields(self):
        tags = {
            "lavfi.signalstats.YMIN": "16",
            "lavfi.signalstats.YMAX": "235",
            "lavfi.signalstats.TOUT": "0.05",
            "lavfi.signalstats.BRNG": "0.1",
            "lavfi.signalstats.SATMAX": "120",
        }
        frame = _parse_video_frame_tags(tags, 0, 0.0)
        assert frame.y_min == 16
        assert frame.y_max == 235
        assert frame.tout == 0.05
        assert frame.brng == 0.1
        assert frame.sat_max == 120.0

    def test_defaults_for_missing(self):
        tags = {}
        frame = _parse_video_frame_tags(tags, 5, 0.2)
        assert frame.n == 5
        assert frame.media_time == 0.2
        assert frame.y_min == 0


class TestWriteQctoolsXmlGz:
    def test_roundtrip_basic(self):
        from qc_tools.models import Report, StreamInfo
        from qc_tools.parser import parse_qctools_xml, write_qctools_xml_gz

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "test.qctools.xml.gz"
            report = Report(
                source=Path("test.mkv"),
                stream=StreamInfo(
                    codec="ffv1",
                    width=720,
                    height=576,
                    fps=25.0,
                    duration=1.0,
                    total_frames=25,
                ),
                ffmpeg_version="n6.0",
            )
            report.video_frames = [
                VideoFrame(n=i, media_time=i * 0.04, y_min=16, y_max=235, tout=0.0)
                for i in range(25)
            ]
            write_qctools_xml_gz(report, path)
            assert path.exists()
            assert path.suffix == ".gz"

            parsed = parse_qctools_xml(path)
            assert len(parsed.video_frames) == 25
            assert parsed.video_frames[0].y_min == 16
