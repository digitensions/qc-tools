"""Streaming XML parser for QCTools / ffprobe output."""

from __future__ import annotations

import gzip
import xml.etree.ElementTree as ET
from pathlib import Path

from .models import AudioFrame, Report, StreamInfo, VideoFrame
from .thresholds import Policy, evaluate_audio_frame, evaluate_video_frame
from .utils import parse_duration, parse_fps


def _float_or(val, default=0.0):
    if val is None:
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


def _int_or(val, default=0):
    if val is None:
        return default
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return default


def _read_tags(elem) -> dict:
    """Read key/value tags from an XML element."""
    tags = {}
    for child in elem:
        if child.tag == "tag":
            key = child.get("key", "")
            value = child.get("value", "")
            tags[key] = value
        elif child.tag == "tags":
            tags.update(_read_tags(child))
    return tags


def _parse_video_frame_tags(tags: dict, frame_n: int, media_time: float) -> VideoFrame:
    """Convert ffprobe tag dict to a VideoFrame."""
    prefix = "lavfi.signalstats."

    def s(key, default=0):
        return tags.get(f"{prefix}{key}", default)

    return VideoFrame(
        n=frame_n,
        media_time=media_time,
        pkt_duration_time=_float_or(tags.get("lavfi.pkt_duration_time")),
        pkt_size=_int_or(tags.get("lavfi.pkt_size")),
        y_min=_int_or(s("YMIN")),
        y_low=_int_or(s("YLOW")),
        y_avg=_int_or(s("YAVG")),
        y_high=_int_or(s("YHIGH")),
        y_max=_int_or(s("YMAX")),
        u_min=_int_or(s("UMIN")),
        u_low=_int_or(s("ULOW")),
        u_avg=_int_or(s("UAVG")),
        u_high=_int_or(s("UHIGH")),
        u_max=_int_or(s("UMAX")),
        v_min=_int_or(s("VMIN")),
        v_low=_int_or(s("VLOW")),
        v_avg=_int_or(s("VAVG")),
        v_high=_int_or(s("VHIGH")),
        v_max=_int_or(s("VMAX")),
        y_dif=_float_or(s("YDIF")),
        u_dif=_float_or(s("UDIF")),
        v_dif=_float_or(s("VDIF")),
        sat_avg=_float_or(s("SAT")),
        sat_max=_float_or(s("SATMAX")),
        hue_avg=_float_or(s("HUE")),
        tout=_float_or(s("TOUT")),
        vrep=_float_or(s("VREP")),
        brng=_float_or(s("BRNG")),
        crop_w=_int_or(s("CROP_W")),
        crop_h=_int_or(s("CROP_H")),
        psnrf=_float_or(s("PSNR")),
        ssimf=_float_or(s("SSIM")),
        msef=_float_or(s("MSE")),
        idet_single=tags.get("lavfi.idet.single.current_frame", ""),
        idet_multi=tags.get("lavfi.idet.multiple.current_frame", ""),
        idet_repeat=_int_or(tags.get("lavfi.idet.repeated.current_frame")),
    )


def _parse_audio_frame_tags(tags: dict, frame_n: int, media_time: float) -> AudioFrame:
    """Convert ffprobe tag dict to an AudioFrame."""

    def s(key, default=0):
        return tags.get(f"lavfi.astats.1.{key}", default)

    def ebur(key, default=0):
        return tags.get(f"lavfi.ebur128.{key}", default)

    return AudioFrame(
        n=frame_n,
        media_time=media_time,
        peak=_float_or(s("Peak_level")),
        rms=_float_or(s("RMS_level")),
        dc_offset=_float_or(s("DC_offset")),
        min_diff=_float_or(s("Min_difference")),
        max_diff=_float_or(s("Max_difference")),
        mean_diff=_float_or(s("Mean_difference")),
        phase=_float_or(tags.get("lavfi.aphasemeter.phase")),
        momentary_loudness=_float_or(ebur("M")),
        short_term_loudness=_float_or(ebur("S")),
        integrated_loudness=_float_or(ebur("I")),
        loudness_range=_float_or(ebur("LRA")),
    )


def _extract_stream_info(xml_root: ET.Element) -> StreamInfo:
    """Extract stream and format metadata from ffprobe XML."""
    stream = StreamInfo()

    for streams_elem in xml_root.findall("streams"):
        for s in streams_elem.findall("stream"):
            codec = s.get("codec_name", "")
            codec_type = s.get("codec_type", "")
            tags = _read_tags(s)

            if codec_type == "video":
                stream.codec = codec
                stream.width = _int_or(s.get("width"))
                stream.height = _int_or(s.get("height"))
                stream.fps = parse_fps(tags, s)
                stream.has_audio = stream.has_audio
            elif codec_type == "audio":
                stream.has_audio = True
                stream.audio_codec = codec
                stream.audio_channels = _int_or(s.get("channels"))
                stream.audio_sample_rate = _int_or(s.get("sample_rate"))

    for fmt in xml_root.findall("format"):
        stream.format_name = fmt.get("format_name", fmt.get("format_long_name", ""))
        stream.duration = parse_duration(fmt)
        if not stream.filename:
            stream.filename = fmt.get("filename", "")

    stream.total_frames = len(
        [
            f
            for f in xml_root.findall(".//frame")
            if f.get("media_type") == "video"
            or _read_tags(f).get("lavfi.signalstats.YMIN")
        ]
    )

    return stream


def _extract_ffmpeg_version(xml_root: ET.Element) -> str:
    for pv in xml_root.findall("program_version"):
        return pv.get("version", pv.get("identification", ""))
    return ""


def parse_qctools_xml(
    xml_path: str | Path,
    source_path: str | Path | None = None,
    policy: Policy | None = None,
) -> Report:
    """Parse a QCTools XML (.xml or .xml.gz) file into a Report."""
    xml_path = Path(xml_path)
    source = Path(source_path) if source_path else xml_path

    if xml_path.suffix == ".gz" or str(xml_path).endswith(".xml.gz"):
        with gzip.open(xml_path, "rb") as f:
            tree = ET.parse(f)
    else:
        tree = ET.parse(xml_path)

    root = tree.getroot()

    stream = _extract_stream_info(root)
    ffmpeg_version = _extract_ffmpeg_version(root)

    if not source_path and stream.filename:
        source = Path(stream.filename)

    video_frames: list[VideoFrame] = []
    audio_frames: list[AudioFrame] = []
    anomalies = []

    video_frame_n = 0
    audio_frame_n = 0

    for frame_elem in root.findall(".//frame"):
        media_time = _float_or(frame_elem.get("media_time"))
        media_type = frame_elem.get("media_type", "video")
        tags = _read_tags(frame_elem)

        is_video = media_type == "video" or "lavfi.signalstats.YMIN" in tags
        is_audio = media_type == "audio" or "lavfi.astats.1.Peak_level" in tags

        if is_video:
            vf = _parse_video_frame_tags(tags, video_frame_n, media_time)
            video_frames.append(vf)
            if policy:
                video_frame_n += 1
                anomalies.extend(evaluate_video_frame(vf, policy))
        elif is_audio:
            af = _parse_audio_frame_tags(tags, audio_frame_n, media_time)
            audio_frames.append(af)
            if policy:
                audio_frame_n += 1
                anomalies.extend(evaluate_audio_frame(af, policy))

    if not stream.total_frames:
        stream.total_frames = len(video_frames)

    return Report(
        source=source,
        stream=stream,
        ffmpeg_version=ffmpeg_version,
        video_frames=video_frames,
        audio_frames=audio_frames,
        anomalies=anomalies,
        policy=policy,
    )


def parse_qctools_xml_streaming(
    xml_path: str | Path,
    source_path: str | Path | None = None,
    policy: Policy | None = None,
) -> Report:
    """Parse a QCTools XML file using streaming iterparse for memory efficiency."""
    xml_path = Path(xml_path)
    source = Path(source_path) if source_path else xml_path

    if xml_path.suffix == ".gz" or str(xml_path).endswith(".xml.gz"):
        with gzip.open(xml_path, "rb") as f:
            raw = f.read()
        from io import BytesIO

        fh = BytesIO(raw)
    else:
        fh = open(xml_path, "rb")  # noqa: SIM115

    try:
        context = ET.iterparse(fh, events=("end",))
        root = None
        stream_info = None
        ffmpeg_version = ""
        video_frames: list[VideoFrame] = []
        audio_frames: list[AudioFrame] = []
        anomalies: list = []
        video_frame_n = 0
        audio_frame_n = 0

        for _event, elem in context:
            if root is None:
                root = elem

            if elem.tag == "program_version":
                ffmpeg_version = elem.get("version", elem.get("identification", ""))

            if elem.tag == "stream":
                if stream_info is None:
                    stream_info = StreamInfo()
                codec = elem.get("codec_name", "")
                codec_type = elem.get("codec_type", "")
                tags = _read_tags(elem)
                if codec_type == "video":
                    stream_info.codec = codec
                    stream_info.width = _int_or(elem.get("width"))
                    stream_info.height = _int_or(elem.get("height"))
                    stream_info.fps = parse_fps(tags, elem)
                elif codec_type == "audio":
                    stream_info.has_audio = True
                    stream_info.audio_codec = codec
                    stream_info.audio_channels = _int_or(elem.get("channels"))
                    stream_info.audio_sample_rate = _int_or(elem.get("sample_rate"))

            if elem.tag == "format":
                if stream_info is None:
                    stream_info = StreamInfo()
                stream_info.format_name = elem.get(
                    "format_name", elem.get("format_long_name", "")
                )
                stream_info.duration = parse_duration(elem)
                if not source_path and elem.get("filename"):
                    source = Path(elem.get("filename"))

            if elem.tag == "frame":
                media_time = _float_or(elem.get("media_time"))
                media_type = elem.get("media_type", "video")
                tags = _read_tags(elem)

                is_video = media_type == "video" or "lavfi.signalstats.YMIN" in tags
                is_audio = media_type == "audio" or "lavfi.astats.1.Peak_level" in tags

                if is_video:
                    vf = _parse_video_frame_tags(tags, video_frame_n, media_time)
                    video_frames.append(vf)
                    if policy:
                        anomalies.extend(evaluate_video_frame(vf, policy))
                    video_frame_n += 1
                elif is_audio:
                    af = _parse_audio_frame_tags(tags, audio_frame_n, media_time)
                    audio_frames.append(af)
                    if policy:
                        anomalies.extend(evaluate_audio_frame(af, policy))
                    audio_frame_n += 1

                elem.clear()

        if stream_info is None:
            stream_info = StreamInfo()
        stream_info.total_frames = len(video_frames)

        return Report(
            source=source,
            stream=stream_info,
            ffmpeg_version=ffmpeg_version,
            video_frames=video_frames,
            audio_frames=audio_frames,
            anomalies=anomalies,
            policy=policy,
        )
    finally:
        if not (xml_path.suffix == ".gz" or str(xml_path).endswith(".xml.gz")):
            fh.close()


def write_qctools_xml_gz(report: Report, output_path: str | Path) -> None:
    """Write a Report back to QCTools-compatible .qctools.xml.gz format for preservation."""
    output_path = Path(output_path)

    def _video_frame_tags(vf: VideoFrame) -> list[ET.Element]:
        tags = []
        mappings = {
            "YMIN": str(vf.y_min),
            "YLOW": str(vf.y_low),
            "YAVG": str(vf.y_avg),
            "YHIGH": str(vf.y_high),
            "YMAX": str(vf.y_max),
            "UMIN": str(vf.u_min),
            "ULOW": str(vf.u_low),
            "UAVG": str(vf.u_avg),
            "UHIGH": str(vf.u_high),
            "UMAX": str(vf.u_max),
            "VMIN": str(vf.v_min),
            "VLOW": str(vf.v_low),
            "VAVG": str(vf.v_avg),
            "VHIGH": str(vf.v_high),
            "VMAX": str(vf.v_max),
            "YDIF": str(vf.y_dif),
            "UDIF": str(vf.u_dif),
            "VDIF": str(vf.v_dif),
            "SAT": str(vf.sat_avg),
            "SATMAX": str(vf.sat_max),
            "HUE": str(vf.hue_avg),
            "TOUT": str(vf.tout),
            "VREP": str(vf.vrep),
            "BRNG": str(vf.brng),
            "CROP_W": str(vf.crop_w),
            "CROP_H": str(vf.crop_h),
            "PSNR": str(vf.psnrf),
            "SSIM": str(vf.ssimf),
            "MSE": str(vf.msef),
        }
        for key, val in mappings.items():
            if val and val != "0":
                t = ET.Element("tag", key=f"lavfi.signalstats.{key}", value=val)
                tags.append(t)
        if vf.pkt_duration_time:
            tags.append(
                ET.Element(
                    "tag",
                    key="lavfi.pkt_duration_time",
                    value=str(vf.pkt_duration_time),
                )
            )
        if vf.pkt_size:
            tags.append(ET.Element("tag", key="lavfi.pkt_size", value=str(vf.pkt_size)))
        return tags

    root = ET.Element("ffprobe")
    ET.SubElement(root, "program_version", version=report.ffmpeg_version or "qc-tools")

    streams = ET.SubElement(root, "streams")
    stream_el = ET.SubElement(
        streams, "stream", codec_type="video", codec_name=report.stream.codec
    )
    if report.stream.width:
        stream_el.set("width", str(report.stream.width))
    if report.stream.height:
        stream_el.set("height", str(report.stream.height))

    if report.stream.has_audio:
        astream = ET.SubElement(streams, "stream", codec_type="audio")
        if report.stream.audio_codec:
            astream.set("codec_name", report.stream.audio_codec)
        if report.stream.audio_channels:
            astream.set("channels", str(report.stream.audio_channels))

    fmt = ET.SubElement(root, "format", filename=str(report.source))
    if report.stream.format_name:
        fmt.set("format_name", report.stream.format_name)
    fmt.set("duration", str(report.stream.duration))

    frames_el = ET.SubElement(root, "frames")
    for vf in report.video_frames:
        frame_el = ET.Element(
            "frame",
            media_type="video",
            media_time=str(vf.media_time),
            key_frame="1",
        )
        frame_el.extend(_video_frame_tags(vf))
        frames_el.append(frame_el)

    xml_str = ET.tostring(root, encoding="unicode", xml_declaration=False)
    with gzip.open(output_path, "wt", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write(xml_str)
