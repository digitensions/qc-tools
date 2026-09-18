"""HTML report generator with timeline visualization and anomaly tables."""

from __future__ import annotations

import datetime
from html import escape

from .models import Report

_SEVERITY_COLORS = {
    "info": "#17a2b8",
    "warning": "#ffc107",
    "error": "#dc3545",
    "critical": "#721c24",
}

_SEVERITY_BG = {
    "info": "#d1ecf1",
    "warning": "#fff3cd",
    "error": "#f8d7da",
    "critical": "#d6d8d9",
}

_METRIC_LABELS = {
    "tout": "Temporal Outliers",
    "brng": "Broadcast Range",
    "vrep": "Vertical Repetitions",
    "satmax": "Max Saturation",
    "sat_avg": "Avg Saturation",
    "msef": "MSE Between Fields",
    "ssimf": "SSIM Between Fields",
    "psnrf": "PSNR Between Fields",
    "y_dif": "Luma Difference",
    "y_max": "Max Luma",
    "y_min": "Min Luma",
    "peak": "Audio Peak",
    "dc_offset": "DC Offset",
    "phase": "Audio Phase",
    "momentary_loudness": "Momentary Loudness",
    "max_diff": "Max Sample Diff",
    "rms": "RMS Level",
    "integrated_loudness": "Integrated Loudness",
    "pkt_duration_time": "Frame Duration",
}


def _generate_svg_timeline(anomalies: list, duration: float) -> str:
    """Generate an inline SVG timeline showing anomaly positions."""
    if not anomalies or duration <= 0:
        return ""

    width = 1000
    height = 50
    bar_height = 20
    y_offset = (height - bar_height) // 2

    rows: dict[str, list] = {}
    for a in anomalies:
        key = a.severity
        if key not in rows:
            rows[key] = []
        rows[key].append(a)

    svg_parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'style="width:100%;max-width:{width}px;height:{height}px;">',
        f'<rect x="0" y="{y_offset}" width="{width}" height="{bar_height}" '
        f'fill="#e9ecef" rx="2"/>',
    ]

    for severity, items in rows.items():
        color = _SEVERITY_COLORS.get(severity, "#6c757d")
        for a in items:
            x = (a.time_seconds / duration) * width
            x = max(0, min(x, width - 1))
            svg_parts.append(
                f'<rect x="{x}" y="{y_offset}" width="2" height="{bar_height}" '
                f'fill="{color}" opacity="0.8">'
                f"<title>{escape(a.timecode)} — {a.type}: {a.value:.4f} "
                f"({a.severity})</title>"
                f"</rect>"
            )

    svg_parts.append("</svg>")
    return "".join(svg_parts)


def _severity_badge(severity: str) -> str:
    color = _SEVERITY_COLORS.get(severity, "#6c757d")
    bg = _SEVERITY_BG.get(severity, "#e9ecef")
    return (
        f'<span style="display:inline-block;padding:2px 8px;border-radius:3px;'
        f"background:{bg};color:{color};font-size:0.85em;font-weight:600;"
        f'text-transform:uppercase">{escape(severity)}</span>'
    )


def _metric_label(metric: str) -> str:
    return _METRIC_LABELS.get(metric, metric)


def _anomaly_detail_rows(anomalies: list) -> str:
    rows = []
    for a in anomalies:
        rows.append(
            f"<tr>"
            f"<td>{a.frame}</td>"
            f"<td><code>{escape(a.timecode)}</code></td>"
            f"<td>{seconds_to_hhmmss(a.time_seconds)}</td>"
            f"<td>{_severity_badge(a.severity)}</td>"
            f"<td>{_metric_label(a.type)}</td>"
            f"<td><code>{a.value:.4f}</code></td>"
            f"<td>{a.threshold}</td>"
            f"<td>{escape(a.description)}</td>"
            f"</tr>"
        )
    return "\n".join(rows)


def seconds_to_hhmmss(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:06.3f}"


def generate_html_report(report: Report) -> str:
    """Generate a self-contained HTML report from a Report."""
    stream = report.stream
    policy_name = report.policy.name if report.policy else "None"
    policy_desc = report.policy.description if report.policy else ""
    analysis_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    summary = report.anomaly_summary()
    total_anomalies = len(report.anomalies)
    video_anomalies = report.video_anomalies
    audio_anomalies = report.audio_anomalies

    severity_counts = {}
    for a in report.anomalies:
        severity_counts[a.severity] = severity_counts.get(a.severity, 0) + 1

    svg_timeline = _generate_svg_timeline(report.anomalies, stream.duration)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>QC Report — {escape(stream.filename)}</title>
<style>
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
       background: #f4f6f9; color: #212529; padding: 24px; line-height: 1.5; }}
.container {{ max-width: 1200px; margin: 0 auto; }}
h1 {{ font-size: 1.5rem; margin-bottom: 4px; }}
h2 {{ font-size: 1.2rem; margin: 24px 0 12px; color: #495057; }}
h3 {{ font-size: 1rem; margin: 16px 0 8px; color: #495057; }}
.subtitle {{ color: #6c757d; font-size: 0.9rem; margin-bottom: 20px; }}
.card {{ background: #fff; border-radius: 8px; padding: 16px 20px; margin-bottom: 16px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
.card-header {{ font-size: 0.85rem; text-transform: uppercase; color: #6c757d;
                font-weight: 600; margin-bottom: 8px; }}
.meta-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
              gap: 8px 24px; }}
.meta-grid dt {{ font-weight: 600; color: #495057; }}
.meta-grid dd {{ color: #212529; margin-bottom: 4px; }}
.stats {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
          gap: 12px; margin: 16px 0; }}
.stat {{ background: #fff; border-radius: 8px; padding: 16px; text-align: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
.stat-value {{ font-size: 2rem; font-weight: 700; color: #212529; }}
.stat-label {{ font-size: 0.8rem; text-transform: uppercase; color: #6c757d; }}
.timeline {{ background: #fff; border-radius: 8px; padding: 16px 20px; margin-bottom: 16px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
table {{ width: 100%; border-collapse: collapse; font-size: 0.9rem; }}
th {{ background: #f8f9fa; text-align: left; padding: 8px 12px; font-weight: 600;
     border-bottom: 2px solid #dee2e6; position: sticky; top: 0; }}
td {{ padding: 6px 12px; border-bottom: 1px solid #e9ecef; vertical-align: top; }}
tr:hover {{ background: #f8f9fa; }}
.badge-info {{ color: #17a2b8; background: #d1ecf1; }}
.badge-warning {{ color: #856404; background: #fff3cd; }}
.badge-error {{ color: #721c24; background: #f8d7da; }}
.badge-critical {{ color: #721c24; background: #d6d8d9; }}
.summary-table {{ margin-bottom: 16px; }}
.section {{ margin-bottom: 24px; }}
.legend {{ display: flex; gap: 16px; flex-wrap: wrap; margin: 8px 0; font-size: 0.85rem; }}
.legend-item {{ display: flex; align-items: center; gap: 4px; }}
.legend-dot {{ width: 12px; height: 12px; border-radius: 2px; }}
</style>
</head>
<body>
<div class="container">

<h1>QC Report — {escape(stream.filename)}</h1>
<p class="subtitle">Generated {analysis_date} | Policy: {escape(policy_name)}</p>

<div class="stats">
<div class="stat">
<div class="stat-value">{stream.total_frames:,}</div>
<div class="stat-label">Video Frames</div>
</div>
<div class="stat">
<div class="stat-value">{seconds_to_hhmmss(stream.duration)}</div>
<div class="stat-label">Duration</div>
</div>
<div class="stat">
<div class="stat-value" style="color:#dc3545">{total_anomalies:,}</div>
<div class="stat-label">Total Anomalies</div>
</div>
<div class="stat">
<div class="stat-value">{stream.width}x{stream.height}</div>
<div class="stat-label">Resolution</div>
</div>
<div class="stat">
<div class="stat-value">{stream.fps:.2f}</div>
<div class="stat-label">Frame Rate</div>
</div>
<div class="stat">
<div class="stat-value">{escape(stream.codec)}</div>
<div class="stat-label">Codec</div>
</div>
</div>

<div class="card">
<div class="card-header">File Metadata</div>
<dl class="meta-grid">
<dt>Format</dt><dd>{escape(stream.format_name)}</dd>
<dt>Video Codec</dt><dd>{escape(stream.codec)}</dd>
<dt>Resolution</dt><dd>{stream.width} x {stream.height}</dd>
<dt>Frame Rate</dt><dd>{stream.fps:.2f} fps</dd>
<dt>Duration</dt><dd>{seconds_to_hhmmss(stream.duration)}</dd>
<dt>Total Frames</dt><dd>{stream.total_frames:,}</dd>
<dt>Has Audio</dt><dd>{"Yes" if stream.has_audio else "No"}</dd>
"""

    if stream.has_audio:
        html += f"""
<dt>Audio Codec</dt><dd>{escape(stream.audio_codec or "Unknown")}</dd>
<dt>Audio Channels</dt><dd>{stream.audio_channels or "N/A"}</dd>
<dt>Sample Rate</dt><dd>{stream.audio_sample_rate or "N/A"} Hz</dd>
"""

    html += f"""
<dt>FFmpeg Version</dt><dd>{escape(report.ffmpeg_version)}</dd>
<dt>Policy</dt><dd>{escape(policy_name)} — {escape(policy_desc)}</dd>
</dl>
</div>

<div class="timeline">
<h2>Anomaly Timeline</h2>
<p style="font-size:0.85rem;color:#6c757d;margin-bottom:8px;">
Anomalies plotted over the duration of the file. Hover for details.
</p>
<div class="legend">
"""
    for sev, color in _SEVERITY_COLORS.items():
        count = severity_counts.get(sev, 0)
        if count > 0:
            html += (
                f'<div class="legend-item">'
                f'<div class="legend-dot" style="background:{color}"></div>'
                f"<span>{sev.capitalize()} ({count})</span></div>"
            )
    html += "</div>\n"
    html += svg_timeline
    html += (
        """
<p style="font-size:0.8rem;color:#6c757d;margin-top:4px;">
0:00:00.000 ───────────────────────────────────────────────────────────────────────────▶
"""
        + seconds_to_hhmmss(stream.duration)
        + """
</p>
</div>
"""
    )

    if summary:
        html += """
<div class="card">
<h2>Anomaly Summary</h2>
<table class="summary-table">
<thead><tr>
<th>Type</th><th>Count</th><th>First Frame</th><th>Last Frame</th>
<th>First Timecode</th><th>Last Timecode</th><th>By Severity</th>
</tr></thead>
<tbody>
"""
        for atype, info in sorted(summary.items(), key=lambda x: -x[1]["count"]):
            sev_str = ", ".join(
                f"{s}: {c}" for s, c in sorted(info["severity_breakdown"].items())
            )
            html += (
                f"<tr>"
                f"<td>{_metric_label(atype)}</td>"
                f"<td>{info['count']:,}</td>"
                f"<td>{info['first_frame']}</td>"
                f"<td>{info['last_frame']}</td>"
                f"<td><code>{escape(info['first_timecode'])}</code></td>"
                f"<td><code>{escape(info['last_timecode'])}</code></td>"
                f"<td>{sev_str}</td>"
                f"</tr>"
            )
        html += "</tbody></table>\n</div>\n"

    if video_anomalies:
        html += f"""
<div class="section">
<h2>Video Anomalies ({len(video_anomalies):,})</h2>
<div style="max-height:600px;overflow-y:auto;background:#fff;border-radius:8px;
            box-shadow:0 1px 3px rgba(0,0,0,0.1);">
<table>
<thead><tr>
<th>Frame</th><th>Timecode</th><th>Time</th><th>Severity</th>
<th>Type</th><th>Value</th><th>Threshold</th><th>Description</th>
</tr></thead>
<tbody>
{_anomaly_detail_rows(video_anomalies)}
</tbody>
</table>
</div>
</div>
"""

    if audio_anomalies:
        html += f"""
<div class="section">
<h2>Audio Anomalies ({len(audio_anomalies):,})</h2>
<div style="max-height:400px;overflow-y:auto;background:#fff;border-radius:8px;
            box-shadow:0 1px 3px rgba(0,0,0,0.1);">
<table>
<thead><tr>
<th>Frame</th><th>Timecode</th><th>Time</th><th>Severity</th>
<th>Type</th><th>Value</th><th>Threshold</th><th>Description</th>
</tr></thead>
<tbody>
{_anomaly_detail_rows(audio_anomalies)}
</tbody>
</table>
</div>
</div>
"""

    html += f"""
<div class="card" style="margin-top:24px;font-size:0.8rem;color:#6c757d;">
<p>Generated by <strong>qc-tools</strong> | Policy: {escape(policy_name)} | Source: {escape(str(report.source))}</p>
</div>
</div>
</body>
</html>"""

    return html
