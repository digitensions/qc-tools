"""CLI engine: runs qcli or ffprobe to generate QCTools analysis data."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from .models import Report
from .parser import parse_qctools_xml
from .thresholds import Policy


def find_qcli() -> str | None:
    """Find qcli in PATH."""
    return shutil.which("qcli")


def find_ffprobe() -> str | None:
    """Find ffprobe in PATH."""
    return shutil.which("ffprobe")


def check_dependencies() -> dict[str, str | None]:
    """Check for qcli and ffprobe availability."""
    return {
        "qcli": find_qcli(),
        "ffprobe": find_ffprobe(),
    }


def _build_ffprobe_cmd(input_path: Path, filters: list[str] | None = None) -> list[str]:
    """Build ffprobe command with signalstats filter chain."""
    if filters is None:
        video_filters = "signalstats=stat=tout+vrep+brng,cropdetect=reset=1:round=1,idet=half_life=1,deflicker=bypass=1,split[a][b];[a]field=top[a1];[b]field=bottom,split[b1][b2];[a1][b1]psnr[c1];[c1][b2]ssim"
        audio_filters = "ebur128=metadata=1,aformat=sample_fmts=flt|fltp:channel_layouts=stereo,astats=metadata=1:reset=1:length=0.4"
        lavfi = f"movie={input_path}:s=v+a[in0][in1],[in0]{video_filters}[out0];[in1]{audio_filters}[out1]"
    else:
        lavfi_filters = ",".join(filters)
        lavfi = f"movie={input_path}:{lavfi_filters}"

    return [
        "ffprobe",
        "-f",
        "lavfi",
        "-i",
        lavfi,
        "-show_frames",
        "-show_versions",
        "-of",
        "xml=x=1:q=1",
        "-noprivate",
    ]


def run_qcli(
    input_path: str | Path,
    output_path: str | Path | None = None,
    extra_args: list[str] | None = None,
) -> Path:
    """Run qcli to generate a .qctools.xml.gz report.

    Args:
        input_path: Path to the media file to analyse.
        output_path: Optional output path. Defaults to <input>.qctools.xml.gz.
        extra_args: Additional arguments to pass to qcli.

    Returns:
        Path to the generated .qctools.xml.gz file.
    """
    input_path = Path(input_path)
    qcli = find_qcli()
    if qcli is None:
        raise RuntimeError(
            "qcli not found in PATH. Install QCTools CLI: "
            "https://mediaarea.net/QCTools or brew install qcli"
        )

    if output_path is None:
        output_path = input_path.with_suffix(input_path.suffix + ".qctools.xml.gz")
    else:
        output_path = Path(output_path)

    cmd = [qcli, "-i", str(input_path), "-o", str(output_path)]
    if extra_args:
        cmd.extend(extra_args)

    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(
            f"qcli exited with code {result.returncode}:\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )

    return Path(output_path)


def run_ffprobe(
    input_path: str | Path,
    output_path: str | Path | None = None,
    filters: list[str] | None = None,
) -> Path:
    """Run ffprobe to generate QCTools analysis XML.

    Args:
        input_path: Path to the media file to analyse.
        output_path: Optional output path. Defaults to <input>.qctools.xml.gz.
        filters: Custom ffprobe filter list.

    Returns:
        Path to the generated .qctools.xml.gz file.
    """
    input_path = Path(input_path)
    ffprobe = find_ffprobe()
    if ffprobe is None:
        raise RuntimeError("ffprobe not found in PATH. Install FFmpeg.")

    if output_path is None:
        output_path = input_path.with_suffix(input_path.suffix + ".qctools.xml.gz")
    else:
        output_path = Path(output_path)

    import gzip

    cmd = _build_ffprobe_cmd(input_path, filters)
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(
            f"ffprobe exited with code {result.returncode}:\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )

    xml_output = result.stdout
    with gzip.open(output_path, "wt", encoding="utf-8") as f:
        f.write(xml_output)

    return Path(output_path)


def analyze(
    input_path: str | Path,
    output_path: str | Path | None = None,
    engine: str = "auto",
    policy: Policy | None = None,
    filters: list[str] | None = None,
    save_xml: bool = True,
) -> Report:
    """Run CLI analysis and return a Report.

    Args:
        input_path: Media file to analyse.
        output_path: Where to save the .qctools.xml.gz (auto-named if None).
        engine: "auto", "qcli", or "ffprobe".
        policy: QC policy for threshold evaluation.
        filters: Custom ffprobe filters (only used with ffprobe engine).
        save_xml: Whether to save the raw XML output file.

    Returns:
        A Report with frames and anomalies.
    """
    input_path = Path(input_path)

    if engine == "auto":
        if find_qcli():
            engine = "qcli"
        elif find_ffprobe():
            engine = "ffprobe"
        else:
            raise RuntimeError(
                "Neither qcli nor ffprobe found in PATH. "
                "Install QCTools CLI (brew install qcli) or FFmpeg."
            )

    if engine == "qcli":
        xml_path = run_qcli(input_path, output_path)
    elif engine == "ffprobe":
        xml_path = run_ffprobe(input_path, output_path, filters)
    else:
        raise ValueError(f"Unknown engine: {engine}. Use 'auto', 'qcli', or 'ffprobe'.")

    if not save_xml:
        from .parser import parse_qctools_xml

    report = parse_qctools_xml(xml_path, source_path=input_path, policy=policy)

    if not save_xml:
        xml_path.unlink(missing_ok=True)

    return report


def analyze_existing_xml(
    xml_path: str | Path,
    source_path: str | Path | None = None,
    policy: Policy | None = None,
) -> Report:
    """Analyse a pre-existing .qctools.xml.gz file without re-running the CLI."""
    return parse_qctools_xml(xml_path, source_path=source_path, policy=policy)
