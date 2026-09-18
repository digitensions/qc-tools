# qc-tools

Python wrapper for [MediaArea QCTools](https://mediaarea.net/QCTools) — quality control analysis for video and audio preservation workflows.

## Overview

`qc-tools` provides a Python API for running QCTools/FFprobe analysis on video and audio files, interpreting the results through configurable QC policies, and generating human-readable reports for archive staff.

### Use Cases

- **Videotape digitisation pipelines** — VHS, U-Matic, Betacam, Hi8
- **Born-digital file QC** — checking received files for corruption
- **Film scan analysis** — dust, scratches, flicker detection
- **Broadcast compliance** — strict luma/chroma range checking
- **Audio preservation** — EBU R128 loudness, clipping, phase analysis

## Installation

```bash
pip install qc-tools
```

### Prerequisites

You need one of these installed and available in your `PATH`:

- **qcli** (recommended): `brew install qcli` or download from [MediaArea](https://mediaarea.net/QCTools/Download)
- **ffprobe**: Install [FFmpeg](https://ffmpeg.org) — `qc-tools` will fall back to this automatically

## Quick Start

```python
from qc_tools import QCTools

qc = QCTools()  # uses "videotape" policy by default
report = qc.analyze("tape_capture.mkv")

# Access analysis results
print(report.frames)              # all video frames
print(report.temporal_outliers)   # frames with dropout/spike issues
print(report.broadcast_range)     # frames outside broadcast-safe range

# Export reports
report.to_json("report.json")
report.to_html("report.html")     # self-contained HTML with timeline
report.to_qctools_xml_gz("preservation.qctools.xml.gz")
```

## Policies

Policies define the thresholds used to flag anomalies. Five built-in policies are included:

| Policy | Use Case |
|--------|----------|
| `videotape` | Analog tape digitisation (VHS, U-Matic, Betacam) |
| `borndigital` | Born-digital file integrity checking |
| `film` | Film scan analysis (dust, scratches, flicker) |
| `broadcast` | Strict broadcast range compliance |
| `audio` | Audio-only QC (loudness, clipping, phase) |

```python
# Use a specific policy
qc = QCTools(policy="film")
report = qc.analyze("film_scan.mov")

# Use a custom policy from YAML
qc = QCTools(policy="my_policy.yaml")
report = qc.analyze("file.mkv")

# List available policies
from qc_tools import list_policies
print(list_policies())  # ['audio', 'borndigital', 'broadcast', 'film', 'videotape']
```

## Custom Policies

Create a YAML file with your own thresholds:

```yaml
name: my_archive
media_type: videotape
description: "Custom thresholds for our U-Matic collection"
rules:
  - metric: tout
    operator: gt
    value: 0.005
    severity: warning
    description: "Temporal outliers — possible tape crease"

  - metric: brng
    operator: gt
    value: 0.01
    severity: error
    description: "Broadcast range violations"
```

Supported metrics: `tout`, `brng`, `vrep`, `satmax`, `y_dif`, `y_max`, `y_min`, `u_max`, `u_min`, `v_max`, `v_min`, `msef`, `ssimf`, `psnrf`, `peak`, `dc_offset`, `phase`, `momentary_loudness`, `max_diff`, `rms`, `integrated_loudness`

Supported operators: `gt`, `gte`, `lt`, `lte`, `eq`

Supported severities: `info`, `warning`, `error`, `critical`

## Report Object

```python
report = qc.analyze("file.mkv")

# Properties
report.frames              # list of VideoFrame
report.video_frames        # same as .frames
report.audio_frames        # list of AudioFrame
report.temporal_outliers   # anomaly list filtered by type
report.broadcast_range     # anomaly list filtered by type
report.video_anomalies     # non-audio anomalies
report.audio_anomalies     # audio-only anomalies
report.anomaly_summary()   # dict of anomaly type summaries

# Export
report.to_json("out.json")
report.to_html("out.html")
report.to_dict()           # Python dict
report.to_qctools_xml_gz("preservation.qctools.xml.gz")

# Re-analyse existing XML with different policy
report2 = qc.analyze_existing("existing.qctools.xml.gz", policy="broadcast")
```

## HTML Report

The generated HTML report includes:

- **Dashboard** — frame count, duration, resolution, anomaly counts
- **Anomaly Timeline** — inline SVG showing anomaly distribution over time, color-coded by severity
- **Anomaly Summary Table** — counts and time ranges by type
- **Detailed Video Anomalies Table** — frame number, timecode, severity, metric value
- **Audio Anomalies Table** (if applicable) — loudness, clipping, phase issues

## Workflow Example

```python
from pathlib import Path
from qc_tools import QCTools

source_dir = Path("/path/to/digitised_files")
output_dir = Path("/path/to/qc_reports")
output_dir.mkdir(parents=True, exist_ok=True)

qc = QCTools(policy="videotape")

for media_file in sorted(source_dir.glob("*.mkv")):
    report = qc.analyze(media_file, output_dir=output_dir)
    report.to_json(output_dir / f"{media_file.stem}_report.json")
    report.to_html(output_dir / f"{media_file.stem}_report.html")
    print(f"{media_file.name}: {len(report.anomalies)} anomalies")
```

## Testing Guide

### 1. Run the unit tests

```bash
cd ~/git/qc-tools
pip install -e ".[dev]"
pytest tests/ -v
```

All 68 tests should pass.

### 2. Generate a test video file

If you don't have a real tape capture handy, create a short test file with FFmpeg:

```bash
# Generate 10 seconds of colour bars with a test tone
ffmpeg -f lavfi -i "color=c=blue:s=720x576:r=25:d=10,noise=alls=20:allf=t+u" \
  -f lavfi -i "sine=frequency=440:duration=10" \
  -c:v ffv1 -c:a pcm_s16le test_video.mkv -y
```

### 3. Run a quick analysis in the Python REPL

```python
from qc_tools import QCTools, list_policies

print(list_policies())

qc = QCTools(policy="videotape")
report = qc.analyze("test_video.mkv")

print(f"Frames analysed: {len(report.frames)}")
print(f"Anomalies found: {len(report.anomalies)}")
print(f"Temporal outliers: {len(report.temporal_outliers)}")
print(f"Broadcast range: {len(report.broadcast_range)}")

# Export
report.to_json("test_report.json")
report.to_html("test_report.html")
```

### 4. View the HTML report

Open `test_report.html` in your browser. You should see:
- Dashboard cards with frame count, duration, resolution
- An SVG timeline showing any anomalies across the file duration
- Summary and detailed anomaly tables

### 5. Try different policies on the same file

```python
qc = QCTools()  # default: videotape
r1 = qc.analyze("test_video.mkv")

r2 = qc.analyze("test_video.mkv", policy="broadcast")
r3 = qc.analyze("test_video.mkv", policy="borndigital")

print(f"videotape:  {len(r1.anomalies)} anomalies")
print(f"broadcast:  {len(r2.anomalies)} anomalies")
print(f"borndigital: {len(r3.anomalies)} anomalies")
```

### 6. Re-analyse an existing XML with a different policy

```python
# First run with one policy
qc1 = QCTools(policy="videotape")
qc1.analyze("test_video.mkv")

# Now re-analyse the saved XML with a stricter policy
qc2 = QCTools()
r2 = qc2.analyze_existing("test_video.qctools.xml.gz", policy="broadcast")
r2.to_html("broadcast_report.html")
```

## Development

```bash
git clone https://github.com/your-org/qc-tools
cd qc-tools
pip install -e ".[dev]"
pytest tests/ -v
ruff check src/ tests/
ruff format src/ tests/
```

## License

MIT
