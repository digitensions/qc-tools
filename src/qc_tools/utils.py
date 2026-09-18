"""Timecode, frame number, and duration conversion utilities."""

from __future__ import annotations

from xml.etree.ElementTree import Element


def frame_to_timecode(frame: int, fps: float) -> str:
    """Convert frame number to SMPTE-style timecode HH:MM:SS:FF."""
    total_frames = max(0, frame)
    total_seconds = total_frames / fps
    hours = int(total_seconds // 3600)
    minutes = int((total_seconds % 3600) // 60)
    seconds = int(total_seconds % 60)
    frames = int(round((total_seconds - int(total_seconds)) * fps))
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}:{frames:02d}"


def timecode_to_frame(timecode: str, fps: float) -> int:
    """Convert SMPTE-style timecode HH:MM:SS:FF to frame number."""
    parts = timecode.strip().split(":")
    if len(parts) == 4:
        h, m, s, f = int(parts[0]), int(parts[1]), int(parts[2]), int(parts[3])
    elif len(parts) == 3:
        h, m, s = int(parts[0]), int(parts[1]), int(parts[2])
        f = 0
    else:
        return 0
    return int((h * 3600 + m * 60 + s) * fps + f)


def seconds_to_timecode(seconds: float) -> str:
    """Convert seconds to HH:MM:SS.mmm format."""
    total = max(0.0, seconds)
    hours = int(total // 3600)
    minutes = int((total % 3600) // 60)
    secs = total % 60
    return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"


def seconds_to_frame(seconds: float, fps: float) -> int:
    """Convert seconds to nearest frame number."""
    return max(0, round(seconds * fps))


def frame_to_seconds(frame: int, fps: float) -> float:
    """Convert frame number to seconds."""
    return max(0.0, frame / fps)


def _get_attr(source, key, default=None):
    """Get attribute from dict or XML Element."""
    if isinstance(source, Element):
        return source.get(key, default)
    if isinstance(source, dict):
        return source.get(key, default)
    return default


def parse_fps(
    stream_tags: dict | None = None, stream_elem: dict | Element | None = None
) -> float:
    """Extract frame rate from stream metadata, preferring average_frame_rate."""
    if stream_elem is not None:
        for key in ("avg_frame_rate", "r_frame_rate"):
            val = _get_attr(stream_elem, key)
            if val and "/" in str(val):
                num, den = str(val).split("/")
                den = int(den)
                if den > 0:
                    return int(num) / den
        val = _get_attr(stream_elem, "r_frame_rate") or _get_attr(
            stream_elem, "avg_frame_rate"
        )
        if val:
            try:
                return float(val)
            except (ValueError, TypeError):
                pass
    if stream_tags is not None:
        val = stream_tags.get("lavfi.signalstats.fps")
        if val:
            try:
                return float(val)
            except (ValueError, TypeError):
                pass
    return 25.0


def parse_duration(format_elem: dict | Element | None = None) -> float:
    """Extract duration in seconds from format/stream metadata."""
    if format_elem is not None:
        for key in ("duration", "Duration"):
            val = _get_attr(format_elem, key)
            if val:
                try:
                    return float(val)
                except (ValueError, TypeError):
                    pass
    return 0.0
