"""Main QCTools class — the public API entry point."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from .engine import analyze as _engine_analyze
from .engine import analyze_existing_xml
from .models import Report
from .thresholds import Policy, load_policy

if TYPE_CHECKING:
    pass


class QCTools:
    """Quality control analysis for video and audio files.

    Usage:
        qc = QCTools()
        report = qc.analyze("tape_capture.mkv")
        print(report.frames)
        print(report.temporal_outliers)
        print(report.broadcast_range)

    Args:
        policy: Built-in policy name ("videotape", "borndigital", "film",
            "broadcast", "audio") or a Policy object or path to custom YAML.
            Default: "videotape".
        engine: "auto" (prefers qcli, falls back to ffprobe), "qcli",
            or "ffprobe".
        filters: Custom ffprobe filter strings (only used with ffprobe engine).
    """

    def __init__(
        self,
        policy: str | Policy | Path = "videotape",
        engine: str = "auto",
        filters: list[str] | None = None,
    ):
        self._policy = policy
        self._engine = engine
        self._filters = filters
        self._resolved_policy: Policy | None = None

    def _resolve_policy(self) -> Policy | None:
        if self._resolved_policy is not None:
            return self._resolved_policy
        if self._policy is None:
            return None
        if isinstance(self._policy, Policy):
            self._resolved_policy = self._policy
        else:
            self._resolved_policy = load_policy(self._policy)
        return self._resolved_policy

    def analyze(
        self,
        input_path: str | Path,
        output_dir: str | Path | None = None,
        save_xml: bool = True,
        policy: str | Policy | Path | None = None,
    ) -> Report:
        """Analyse a media file and return a Report.

        Args:
            input_path: Path to the video or audio file.
            output_dir: Directory for the .qctools.xml.gz output.
                If None, output is placed next to the input file.
            save_xml: Whether to persist the raw XML file (default True).
            policy: Override the instance policy for this analysis.

        Returns:
            A Report with video/audio frames and anomalies.
        """
        policy_obj = self._resolve_policy()
        if policy is not None:
            policy_obj = policy if isinstance(policy, Policy) else load_policy(policy)

        input_path = Path(input_path)
        output_path = None
        if output_dir is not None:
            output_path = Path(output_dir) / f"{input_path.stem}.qctools.xml.gz"

        return _engine_analyze(
            input_path=input_path,
            output_path=output_path,
            engine=self._engine,
            policy=policy_obj,
            filters=self._filters,
            save_xml=save_xml,
        )

    def analyze_existing(
        self,
        xml_path: str | Path,
        source_path: str | Path | None = None,
        policy: str | Policy | Path | None = None,
    ) -> Report:
        """Analyse a pre-existing .qctools.xml.gz file.

        Useful for re-evaluating with different policies without re-running
        the CLI analysis.

        Args:
            xml_path: Path to the .qctools.xml.gz file.
            source_path: Original media file path (for reference).
            policy: Override the instance policy.

        Returns:
            A Report with video/audio frames and anomalies.
        """
        policy_obj = self._resolve_policy()
        if policy is not None:
            policy_obj = policy if isinstance(policy, Policy) else load_policy(policy)

        return analyze_existing_xml(
            xml_path, source_path=source_path, policy=policy_obj
        )
