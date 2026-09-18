"""Example: Batch process a directory of files in a digitisation pipeline."""

from pathlib import Path

from qc_tools import QCTools, list_policies

print("Available policies:", list_policies())

source_dir = Path("/path/to/digitised_files")
output_dir = Path("/path/to/qc_reports")
output_dir.mkdir(parents=True, exist_ok=True)

policy_map = {
    ".mkv": "videotape",
    ".mov": "videotape",
    ".wav": "audio",
    ".mp4": "borndigital",
}

qc = QCTools(policy="videotape")

for media_file in sorted(source_dir.glob("*")):
    if media_file.suffix.lower() not in policy_map:
        continue

    policy = policy_map[media_file.suffix.lower()]
    print(f"Analysing: {media_file.name} (policy: {policy})")

    report = qc.analyze(media_file, output_dir=output_dir)

    report.to_json(output_dir / f"{media_file.stem}_report.json")
    report.to_html(output_dir / f"{media_file.stem}_report.html")

    n_issues = len(report.anomalies)
    print(f"  -> {n_issues} anomalies found")
    if n_issues > 0:
        for atype, info in report.anomaly_summary().items():
            print(f"     {atype}: {info['count']}")

print("\nBatch complete!")
