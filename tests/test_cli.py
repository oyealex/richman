"""Smoke tests for command line entry points."""

from pathlib import Path

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
    calls: list[tuple[int, int | None, int | None, object | None]] = []

    def fake_run_game(
        players_count: int,
        max_turns: int | None,
        seed: int | None,
        config_path: object | None = None,
    ) -> InternalGameState:
        calls.append((players_count, max_turns, seed, config_path))
        return InternalGameState(players=[])

    monkeypatch.setattr(cli, "run_game", fake_run_game)

    result = runner.invoke(app, ["play", "--players", "2", "--max-turns", "1", "--seed", "5"])

    assert result.exit_code == 0
    assert calls == [(2, 1, 5, None)]


def test_play_command_forwards_config_path(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    runner = CliRunner()
    config_path = tmp_path / "game.json"
    config_path.write_text('{"board_cells": [], "cards": []}', encoding="utf-8")
    calls: list[object | None] = []

    def fake_run_game(
        players_count: int,
        max_turns: int | None,
        seed: int | None,
        config_path: object | None = None,
    ) -> InternalGameState:
        del players_count, max_turns, seed
        calls.append(config_path)
        return InternalGameState(players=[])

    monkeypatch.setattr(cli, "run_game", fake_run_game)

    result = runner.invoke(app, ["play", "--config", str(config_path), "--max-turns", "0"])

    assert result.exit_code == 0
    assert calls == [config_path]


def test_tui_command_uses_app_assembly(monkeypatch: pytest.MonkeyPatch) -> None:
    runner = CliRunner()
    calls: list[tuple[int, object | None, object | None]] = []

    def fake_run_tui(
        players_count: int,
        seed: int | None,
        config_path: object | None,
    ) -> None:
        calls.append((players_count, seed, config_path))

    monkeypatch.setattr(cli, "run_tui_game", fake_run_tui)

    result = runner.invoke(app, ["tui", "--players", "2", "--seed", "5"])

    assert result.exit_code == 0
    assert calls == [(2, 5, None)]


def test_tui_command_forwards_config_path(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    runner = CliRunner()
    config_path = tmp_path / "game.json"
    config_path.write_text('{"board_cells": [], "cards": []}', encoding="utf-8")
    calls: list[object | None] = []

    def fake_run_tui(
        players_count: int,
        seed: int | None,
        config_path: object | None,
    ) -> None:
        del players_count, seed
        calls.append(config_path)

    monkeypatch.setattr(cli, "run_tui_game", fake_run_tui)

    result = runner.invoke(app, ["tui", "--config", str(config_path)])

    assert result.exit_code == 0
    assert calls == [config_path]


def test_tui_command_uses_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    runner = CliRunner()
    calls: list[tuple[int, object | None, object | None]] = []

    def fake_run_tui(
        players_count: int,
        seed: int | None,
        config_path: object | None,
    ) -> None:
        calls.append((players_count, seed, config_path))

    monkeypatch.setattr(cli, "run_tui_game", fake_run_tui)

    result = runner.invoke(app, ["tui"])

    assert result.exit_code == 0
    assert calls == [(2, None, None)]


def test_tui_command_rejects_invalid_player_count(monkeypatch: pytest.MonkeyPatch) -> None:
    runner = CliRunner()
    called = False

    def fake_run_tui(players_count: int, seed: object | None, config_path: object | None) -> None:
        del seed, config_path
        nonlocal called
        called = True

    monkeypatch.setattr(cli, "run_tui_game", fake_run_tui)

    result = runner.invoke(app, ["tui", "--players", "1"])

    assert result.exit_code != 0
    assert not called


def test_play_command_rejects_invalid_player_count(monkeypatch: pytest.MonkeyPatch) -> None:
    runner = CliRunner()
    called = False

    def fake_run_game(
        players_count: int,
        max_turns: int | None,
        seed: int | None,
        config_path: object | None = None,
    ) -> InternalGameState:
        del config_path
        nonlocal called
        called = True
        return InternalGameState(players=[])

    monkeypatch.setattr(cli, "run_game", fake_run_game)

    result = runner.invoke(app, ["play", "--players", "1"])

    assert result.exit_code != 0
    assert not called
