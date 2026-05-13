"""Smoke tests for TUI app assembly and entry point."""

from pathlib import Path

import pytest

from richman.adapters.textual_tui import RichmanTuiApp
from richman.app import (
    build_default_config,
    create_engine,
    create_tui_players,
    run_tui_game,
)
from richman.domain import GameConfig
from richman.engine import GameEngine
from richman.player import AIPlayer, HumanPlayer, Player


def test_create_tui_players_returns_one_human() -> None:
    players = create_tui_players(2)
    assert len(players) == 2
    assert isinstance(players[0], HumanPlayer)
    assert isinstance(players[1], AIPlayer)


def test_create_tui_players_human_is_first() -> None:
    players = create_tui_players(3)
    assert players[0].name == "玩家"
    assert isinstance(players[0], HumanPlayer)
    assert all(isinstance(p, AIPlayer) for p in players[1:])


def test_create_tui_players_correct_ai_count() -> None:
    players = create_tui_players(4)
    human_count = sum(1 for p in players if isinstance(p, HumanPlayer))
    ai_count = sum(1 for p in players if isinstance(p, AIPlayer))
    assert human_count == 1
    assert ai_count == 3
    assert len(players) == 4


def test_create_tui_players_rejects_invalid_count() -> None:
    with pytest.raises(ValueError):
        create_tui_players(1)
    with pytest.raises(ValueError):
        create_tui_players(5)


def test_run_tui_game_creates_engine_with_default_config(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: list[tuple[GameConfig, tuple[Player, ...], int | None]] = []

    def fake_create_engine(
        config: GameConfig,
        players: tuple[Player, ...],
        seed: int | None = None,
    ) -> GameEngine:
        captured.append((config, tuple(players), seed))
        from richman.board import create as create_board
        from richman.domain import GameConfig as GC
        del GC
        board = create_board(config)
        return GameEngine.create(config, board, players, seed=seed)

    monkeypatch.setattr("richman.app.create_engine", fake_create_engine)

    class FakeRun:
        called = False

        def __call__(self) -> None:
            FakeRun.called = True

    monkeypatch.setattr(RichmanTuiApp, "run", FakeRun())

    run_tui_game(players_count=2, seed=42)

    assert len(captured) == 1
    config, players, seed = captured[0]
    assert isinstance(config, GameConfig)
    assert len(players) == 2
    assert isinstance(players[0], HumanPlayer)
    assert isinstance(players[1], AIPlayer)
    assert seed == 42
    assert FakeRun.called


def test_run_tui_game_uses_custom_config(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "game.json"
    default_config = build_default_config()
    config_path.write_text(
        '{"board_cells": [{"cell_type": "START"}, {"cell_type": "JAIL_SPACE"}], "cards": []}',
        encoding="utf-8",
    )

    captured_config: list[GameConfig] = []

    def fake_create_engine(
        config: GameConfig,
        players: tuple[Player, ...],
        seed: int | None = None,
    ) -> GameEngine:
        captured_config.append(config)
        from richman.board import create as create_board
        board = create_board(config)
        return GameEngine.create(config, board, players, seed=seed)

    monkeypatch.setattr("richman.app.create_engine", fake_create_engine)

    class FakeRun:
        called = False

        def __call__(self) -> None:
            FakeRun.called = True

    monkeypatch.setattr(RichmanTuiApp, "run", FakeRun())

    run_tui_game(players_count=2, config_path=config_path)

    assert len(captured_config) == 1
    assert captured_config[0] != default_config
    assert FakeRun.called


def test_run_tui_game_passes_correct_args_to_richtui_app(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: list[dict[str, object]] = []

    class FakeApp:
        def __init__(self, **kwargs: object) -> None:
            captured.append(kwargs)

        def run(self) -> None:
            pass

    monkeypatch.setattr("richman.adapters.textual_tui.app.RichmanTuiApp", FakeApp)
    monkeypatch.setattr(
        "richman.app.create_engine",
        lambda config, players, seed=None: object(),
    )

    run_tui_game(players_count=2, seed=7)

    assert len(captured) == 1
    kwargs = captured[0]
    assert "engine" in kwargs
    assert "config" in kwargs
    assert "player_controllers" in kwargs
    controllers = kwargs["player_controllers"]
    assert controllers is not None
    from collections.abc import Sequence as Seq
    assert isinstance(controllers, Seq)
    assert len(controllers) == 2


def test_richtui_app_constructs_without_engine() -> None:
    app = RichmanTuiApp()
    assert app._engine is None
    assert app._player_controllers is None


def test_richtui_app_constructs_with_engine() -> None:
    config = build_default_config()
    players: tuple[Player, ...] = (HumanPlayer("玩家"), AIPlayer("AI 1"))
    engine = create_engine(config, players)

    app = RichmanTuiApp(engine=engine, config=config, player_controllers=players)
    assert app._engine is engine
    assert app._player_controllers is players


async def test_richtui_app_on_mount_pushes_game_screen() -> None:
    from richman.adapters.textual_tui.screens.game import GameScreen

    config = build_default_config()
    players: tuple[Player, ...] = (HumanPlayer("玩家"), AIPlayer("AI 1"))
    engine = create_engine(config, players)

    app = RichmanTuiApp(engine=engine, config=config, player_controllers=players)

    async with app.run_test(size=(40, 120)) as pilot:
        await pilot.pause()
        assert isinstance(pilot.app.screen, GameScreen)


async def test_richtui_app_on_mount_skips_without_engine() -> None:
    from richman.adapters.textual_tui.screens.game import GameScreen

    app = RichmanTuiApp()

    async with app.run_test(size=(40, 120)) as pilot:
        await pilot.pause()
        assert not isinstance(pilot.app.screen, GameScreen)
