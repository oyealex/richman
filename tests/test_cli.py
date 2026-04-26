"""Smoke tests for command line entry points."""

from typer.testing import CliRunner

from richman.cli import app


def test_version_command() -> None:
    runner = CliRunner()

    result = runner.invoke(app, ["version"])

    assert result.exit_code == 0
    assert "richman 0.1.0" in result.stdout
