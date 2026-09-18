"""Tests for utils module."""

from qc_tools.utils import (
    frame_to_seconds,
    frame_to_timecode,
    parse_duration,
    parse_fps,
    seconds_to_frame,
    seconds_to_timecode,
    timecode_to_frame,
)


class TestFrameToTimecode:
    def test_zero_frame(self):
        assert frame_to_timecode(0, 25.0) == "00:00:00:00"

    def test_one_second_25fps(self):
        assert frame_to_timecode(25, 25.0) == "00:00:01:00"

    def test_one_minute_25fps(self):
        assert frame_to_timecode(1500, 25.0) == "00:01:00:00"

    def test_one_hour_25fps(self):
        assert frame_to_timecode(90000, 25.0) == "01:00:00:00"

    def test_2997_fps(self):
        result = frame_to_timecode(30, 29.97)
        assert result.startswith("00:00:01")


class TestTimecodeToFrame:
    def test_zero(self):
        assert timecode_to_frame("00:00:00:00", 25.0) == 0

    def test_one_second(self):
        assert timecode_to_frame("00:00:01:00", 25.0) == 25

    def test_one_minute(self):
        assert timecode_to_frame("00:01:00:00", 25.0) == 1500


class TestSecondsHelpers:
    def test_seconds_to_timecode_zero(self):
        assert seconds_to_timecode(0.0) == "00:00:00.000"

    def test_seconds_to_timecode_one_hour(self):
        assert seconds_to_timecode(3600.0) == "01:00:00.000"

    def test_seconds_to_frame(self):
        assert seconds_to_frame(1.0, 25.0) == 25

    def test_frame_to_seconds(self):
        assert frame_to_seconds(50, 25.0) == 2.0


class TestParseFps:
    def test_from_fraction(self):
        assert parse_fps(stream_elem={"avg_frame_rate": "25/1"}) == 25.0

    def test_from_ntsc(self):
        result = parse_fps(stream_elem={"avg_frame_rate": "30000/1001"})
        assert abs(result - 29.970029970) < 0.001

    def test_default(self):
        assert parse_fps() == 25.0


class TestParseDuration:
    def test_from_format(self):
        assert parse_duration({"duration": "120.5"}) == 120.5

    def test_default(self):
        assert parse_duration() == 0.0
