"""Data models for QCTools reports, frames, and anomalies."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

from .utils import frame_to_timecode, seconds_to_timecode

if TYPE_CHECKING:
    from .thresholds import Policy


@dataclass
class StreamInfo:
    """Metadata about the analysed media file."""

    codec: str = ""
    width: int = 0
    height: int = 0
    fps: float = 25.0
    duration: float = 0.0
    total_frames: int = 0
    has_audio: bool = False
    audio_codec: str | None = None
    audio_channels: int | None = None
    audio_sample_rate: int | None = None
    format_name: str = ""
    filename: str = ""

    def to_dict(self) -> dict:
        return {
            "codec": self.codec,
            "width": self.width,
            "height": self.height,
            "fps": self.fps,
            "duration": self.duration,
            "total_frames": self.total_frames,
            "has_audio": self.has_audio,
            "audio_codec": self.audio_codec,
            "audio_channels": self.audio_channels,
            "audio_sample_rate": self.audio_sample_rate,
            "format_name": self.format_name,
            "filename": self.filename,
        }


@dataclass
class VideoFrame:
    """Single video frame analysis data from signalstats and related filters."""

    n: int = 0
    media_time: float = 0.0
    pkt_duration_time: float = 0.0
    pkt_size: int = 0

    y_min: int = 0
    y_low: int = 0
    y_avg: int = 0
    y_high: int = 0
    y_max: int = 0

    u_min: int = 0
    u_low: int = 0
    u_avg: int = 0
    u_high: int = 0
    u_max: int = 0

    v_min: int = 0
    v_low: int = 0
    v_avg: int = 0
    v_high: int = 0
    v_max: int = 0

    y_dif: float = 0.0
    u_dif: float = 0.0
    v_dif: float = 0.0

    sat_avg: float = 0.0
    sat_max: float = 0.0

    hue_avg: float = 0.0

    tout: float = 0.0
    vrep: float = 0.0
    brng: float = 0.0

    crop_w: int = 0
    crop_h: int = 0

    psnrf: float = 0.0
    ssimf: float = 0.0
    msef: float = 0.0

    idet_single: str = ""
    idet_multi: str = ""
    idet_repeat: int = 0

    @property
    def timecode(self) -> str:
        fps = 25.0
        return frame_to_timecode(self.n, fps)

    @property
    def time_seconds(self) -> float:
        return self.media_time

    def metric(self, name: str) -> float | int | None:
        """Get a metric value by name for policy evaluation."""
        mapping = {
            "y_min": self.y_min,
            "y_low": self.y_low,
            "y_avg": self.y_avg,
            "y_high": self.y_high,
            "y_max": self.y_max,
            "u_min": self.u_min,
            "u_low": self.u_low,
            "u_avg": self.u_avg,
            "u_high": self.u_high,
            "u_max": self.u_max,
            "v_min": self.v_min,
            "v_low": self.v_low,
            "v_avg": self.v_avg,
            "v_high": self.v_high,
            "v_max": self.v_max,
            "y_dif": self.y_dif,
            "u_dif": self.u_dif,
            "v_dif": self.v_dif,
            "sat_avg": self.sat_avg,
            "satmax": self.sat_max,
            "sat_max": self.sat_max,
            "hue_avg": self.hue_avg,
            "tout": self.tout,
            "vrep": self.vrep,
            "brng": self.brng,
            "crop_w": self.crop_w,
            "crop_h": self.crop_h,
            "psnrf": self.psnrf,
            "ssimf": self.ssimf,
            "msef": self.msef,
            "pkt_duration_time": self.pkt_duration_time,
        }
        return mapping.get(name)

    def to_dict(self) -> dict:
        return {
            "n": self.n,
            "media_time": self.media_time,
            "timecode": self.timecode,
            "y_min": self.y_min,
            "y_low": self.y_low,
            "y_avg": self.y_avg,
            "y_high": self.y_high,
            "y_max": self.y_max,
            "u_min": self.u_min,
            "u_low": self.u_low,
            "u_avg": self.u_avg,
            "u_high": self.u_high,
            "u_max": self.u_max,
            "v_min": self.v_min,
            "v_low": self.v_low,
            "v_avg": self.v_avg,
            "v_high": self.v_high,
            "v_max": self.v_max,
            "y_dif": self.y_dif,
            "u_dif": self.u_dif,
            "v_dif": self.v_dif,
            "sat_avg": self.sat_avg,
            "sat_max": self.sat_max,
            "hue_avg": self.hue_avg,
            "tout": self.tout,
            "vrep": self.vrep,
            "brng": self.brng,
            "crop_w": self.crop_w,
            "crop_h": self.crop_h,
            "psnrf": self.psnrf,
            "ssimf": self.ssimf,
            "msef": self.msef,
            "pkt_duration_time": self.pkt_duration_time,
            "pkt_size": self.pkt_size,
        }


@dataclass
class AudioFrame:
    """Single audio frame analysis data from astats, ebur128, aphasemeter."""

    n: int = 0
    media_time: float = 0.0

    peak: float = 0.0
    rms: float = 0.0
    dc_offset: float = 0.0
    min_diff: float = 0.0
    max_diff: float = 0.0
    mean_diff: float = 0.0

    phase: float = 0.0

    momentary_loudness: float = 0.0
    short_term_loudness: float = 0.0
    integrated_loudness: float = 0.0
    loudness_range: float = 0.0

    @property
    def timecode(self) -> str:
        return seconds_to_timecode(self.media_time)

    @property
    def time_seconds(self) -> float:
        return self.media_time

    def metric(self, name: str) -> float | int | None:
        """Get a metric value by name for policy evaluation."""
        mapping = {
            "peak": self.peak,
            "rms": self.rms,
            "dc_offset": self.dc_offset,
            "min_diff": self.min_diff,
            "max_diff": self.max_diff,
            "mean_diff": self.mean_diff,
            "phase": self.phase,
            "momentary_loudness": self.momentary_loudness,
            "short_term_loudness": self.short_term_loudness,
            "integrated_loudness": self.integrated_loudness,
            "loudness_range": self.loudness_range,
        }
        return mapping.get(name)

    def to_dict(self) -> dict:
        return {
            "n": self.n,
            "media_time": self.media_time,
            "timecode": self.timecode,
            "peak": self.peak,
            "rms": self.rms,
            "dc_offset": self.dc_offset,
            "min_diff": self.min_diff,
            "max_diff": self.max_diff,
            "mean_diff": self.mean_diff,
            "phase": self.phase,
            "momentary_loudness": self.momentary_loudness,
            "short_term_loudness": self.short_term_loudness,
            "integrated_loudness": self.integrated_loudness,
            "loudness_range": self.loudness_range,
        }


@dataclass
class Anomaly:
    """A detected anomaly that exceeds a policy threshold."""

    type: str
    frame: int
    timecode: str
    time_seconds: float
    severity: str
    value: float
    threshold: float
    description: str
    is_audio: bool = False

    def to_dict(self) -> dict:
        return {
            "type": self.type,
            "frame": self.frame,
            "timecode": self.timecode,
            "time_seconds": self.time_seconds,
            "severity": self.severity,
            "value": self.value,
            "threshold": self.threshold,
            "description": self.description,
            "is_audio": self.is_audio,
        }


@dataclass
class Report:
    """Complete QC analysis report for a single media file."""

    source: Path
    stream: StreamInfo
    ffmpeg_version: str = ""
    video_frames: list[VideoFrame] = field(default_factory=list)
    audio_frames: list[AudioFrame] = field(default_factory=list)
    anomalies: list[Anomaly] = field(default_factory=list)
    policy: Policy | None = None

    @property
    def frames(self) -> list[VideoFrame]:
        return self.video_frames

    @property
    def temporal_outliers(self) -> list[Anomaly]:
        return [a for a in self.anomalies if a.type == "tout" and not a.is_audio]

    @property
    def broadcast_range(self) -> list[Anomaly]:
        return [a for a in self.anomalies if a.type == "brng" and not a.is_audio]

    @property
    def video_anomalies(self) -> list[Anomaly]:
        return [a for a in self.anomalies if not a.is_audio]

    @property
    def audio_anomalies(self) -> list[Anomaly]:
        return [a for a in self.anomalies if a.is_audio]

    def anomalies_by_type(self, anomaly_type: str) -> list[Anomaly]:
        return [a for a in self.anomalies if a.type == anomaly_type]

    def anomalies_by_severity(self, severity: str) -> list[Anomaly]:
        return [a for a in self.anomalies if a.severity == severity]

    def anomaly_summary(self) -> dict[str, dict]:
        summary: dict[str, dict] = {}
        for a in self.anomalies:
            if a.type not in summary:
                summary[a.type] = {
                    "count": 0,
                    "severity_breakdown": {},
                    "first_frame": a.frame,
                    "last_frame": a.frame,
                    "first_timecode": a.timecode,
                    "last_timecode": a.timecode,
                }
            s = summary[a.type]
            s["count"] += 1
            s["severity_breakdown"][a.severity] = (
                s["severity_breakdown"].get(a.severity, 0) + 1
            )
            s["last_frame"] = a.frame
            s["last_timecode"] = a.timecode
        return summary

    def to_dict(self) -> dict:
        return {
            "source": str(self.source),
            "stream": self.stream.to_dict(),
            "ffmpeg_version": self.ffmpeg_version,
            "policy": self.policy.name if self.policy else None,
            "total_video_frames": len(self.video_frames),
            "total_audio_frames": len(self.audio_frames),
            "total_anomalies": len(self.anomalies),
            "anomaly_summary": self.anomaly_summary(),
            "anomalies": [a.to_dict() for a in self.anomalies],
        }

    def to_json(self, path: str | Path) -> None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    def to_html(self, path: str | Path) -> None:
        from .html_report import generate_html_report

        Path(path).parent.mkdir(parents=True, exist_ok=True)
        html = generate_html_report(self)
        with open(path, "w") as f:
            f.write(html)

    def to_qctools_xml_gz(self, path: str | Path) -> None:
        from .parser import write_qctools_xml_gz

        Path(path).parent.mkdir(parents=True, exist_ok=True)
        write_qctools_xml_gz(self, path)
