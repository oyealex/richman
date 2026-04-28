"""Smoke tests for command line entry points."""

import pytest
from typer.testing import CliRunner

from richman import cli
from richman.cli import app
from richman.domain import InternalGameState


def test_version_command() -> None:
    runner = CliRunner()

    result = runner.invoke(app, ["version"])

    assert result.exit_code == 0
    assert "richman 0.1.0" in result.stdout


def test_play_command_uses_app_assembly(monkeypatch: pytest.MonkeyPatch) -> None:
    runner = CliRunner()
    calls: list[tuple[int, int | None, int | None]] = []

    def fake_run_game(
        players_count: int,
        max_turns: int | None,
        seed: int | None,
    ) -> InternalGameState:
        calls.append((players_count, max_turns, seed))
        return InternalGameState(players=[])

    monkeypatch.setattr(cli, "run_game", fake_run_game)

    result = runner.invoke(app, ["play", "--players", "2", "--max-turns", "1", "--seed", "5"])

    assert result.exit_code == 0
    assert calls == [(2, 1, 5)]


def test_play_command_rejects_invalid_player_count(monkeypatch: pytest.MonkeyPatch) -> None:
    runner = CliRunner()
    called = False

    def fake_run_game(
        players_count: int,
        max_turns: int | None,
        seed: int | None,
    ) -> InternalGameState:
        nonlocal called
        called = True
        return InternalGameState(players=[])

    monkeypatch.setattr(cli, "run_game", fake_run_game)

    result = runner.invoke(app, ["play", "--players", "1"])

    assert result.exit_code != 0
    assert not called
