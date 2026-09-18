"""Tests for engine module."""

from unittest.mock import patch

from qc_tools.engine import check_dependencies, find_ffprobe, find_qcli


class TestFindCli:
    def test_find_qcli_returns_path_or_none(self):
        result = find_qcli()
        assert result is None or isinstance(result, str)

    def test_find_ffprobe_returns_path_or_none(self):
        result = find_ffprobe()
        assert result is None or isinstance(result, str)


class TestCheckDependencies:
    def test_returns_dict(self):
        result = check_dependencies()
        assert isinstance(result, dict)
        assert "qcli" in result
        assert "ffprobe" in result


class TestEngineErrors:
    def test_invalid_engine(self):
        from qc_tools.engine import analyze

        try:
            analyze("test.mkv", engine="invalid")
            raise AssertionError("Should have raised")
        except ValueError as e:
            assert "Unknown engine" in str(e)

    def test_raises_with_no_engine(self):
        from qc_tools.engine import analyze

        with (
            patch("qc_tools.engine.find_qcli", return_value=None),
            patch("qc_tools.engine.find_ffprobe", return_value=None),
        ):
            try:
                analyze("test.mkv")
                raise AssertionError("Should have raised")
            except RuntimeError as e:
                assert "Neither qcli nor ffprobe" in str(e)
