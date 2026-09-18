"""Example: Analyze a videotape digitization with the videotape policy."""

from pathlib import Path

from qc_tools import QCTools

input_file = Path("tape_capture.mkv")

qc = QCTools(policy="videotape")

report = qc.analyze(input_file)

print(f"Source: {report.source}")
print(f"Codec: {report.stream.codec}")
print(f"Resolution: {report.stream.width}x{report.stream.height}")
print(f"Duration: {report.stream.duration:.2f}s")
print(f"Total frames: {len(report.video_frames):,}")
print(f"Total anomalies: {len(report.anomalies):,}")

print(f"\nTemporal outliers: {len(report.temporal_outliers)}")
print(f"Broadcast range violations: {len(report.broadcast_range)}")

summary = report.anomaly_summary()
for atype, info in summary.items():
    print(f"  {atype}: {info['count']} occurrences")

report.to_json("report.json")
report.to_html("report.html")
report.to_qctools_xml_gz("preservation.qctools.xml.gz")
print("\nSaved: report.json, report.html, preservation.qctools.xml.gz")
