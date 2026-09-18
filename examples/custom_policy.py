"""Example: Use a custom YAML policy for specialized QC thresholds."""

from pathlib import Path

from qc_tools import QCTools, Policy, load_policy

# Option 1: Load a custom policy from a YAML file
# policy = load_policy(Path("my_custom_policy.yaml"))

# Option 2: Create a policy programmatically
from qc_tools.thresholds import ThresholdRule

policy = Policy(
    name="my_archive",
    media_type="videotape",
    description="Custom policy for our U-Matic collection",
    rules=[
        ThresholdRule("tout", "gt", 0.005, "warning", "Minor temporal outliers"),
        ThresholdRule("tout", "gt", 0.03, "error", "Major temporal outliers"),
        ThresholdRule("brng", "gt", 0.005, "warning", "Minor broadcast violations"),
        ThresholdRule("vrep", "gt", 0.0, "warning", "Any vertical repetition"),
    ],
)

qc = QCTools(policy=policy)
report = qc.analyze("umatic_capture.mov")

print(f"Anomalies found with custom policy: {len(report.anomalies)}")
for a in report.anomalies[:10]:
    print(f"  Frame {a.frame} ({a.timecode}): {a.type} = {a.value:.4f} [{a.severity}]")

report.to_html("custom_policy_report.html")
