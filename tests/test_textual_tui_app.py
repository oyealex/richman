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


def test_run_tui_game_launches_in_game_mode(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: list[dict[str, object]] = []

    class FakeApp:
        def __init__(self, **kwargs: object) -> None:
            captured.append(kwargs)

        def run(self) -> None:
            pass

    monkeypatch.setattr("richman.adapters.textual_tui.app.RichmanTuiApp", FakeApp)

    run_tui_game(players_count=3, seed=42)

    assert len(captured) == 1
    kwargs = captured[0]
    assert kwargs.get("run_game_mode") is True
    assert kwargs.get("seed") == 42
    assert kwargs.get("player_count") == 3
    assert isinstance(kwargs.get("config"), GameConfig)


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

    captured: list[dict[str, object]] = []

    class FakeApp:
        def __init__(self, **kwargs: object) -> None:
            captured.append(kwargs)

        def run(self) -> None:
            pass

    monkeypatch.setattr("richman.adapters.textual_tui.app.RichmanTuiApp", FakeApp)

    run_tui_game(players_count=2, config_path=config_path)

    assert len(captured) == 1
    loaded_config = captured[0]["config"]
    assert isinstance(loaded_config, GameConfig)
    assert loaded_config != default_config


def test_run_tui_game_does_not_create_engine(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    create_tui_called = False
    create_engine_called = False

    def fake_create_tui(players_count: int, human_name: str = "玩家") -> tuple[Player, ...]:
        nonlocal create_tui_called
        create_tui_called = True
        return ()

    def fail_create_engine(*args: object, **kwargs: object) -> object:
        raise AssertionError("should not be called")

    monkeypatch.setattr("richman.app.create_tui_players", fake_create_tui)
    monkeypatch.setattr("richman.app.create_engine", fail_create_engine)

    class FakeApp:
        def __init__(self, **kwargs: object) -> None:
            pass
        def run(self) -> None:
            pass

    monkeypatch.setattr("richman.adapters.textual_tui.app.RichmanTuiApp", FakeApp)

    run_tui_game(players_count=2)

    assert not create_tui_called
    assert not create_engine_called


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


# -- TitleScreen tests -------------------------------------------------------


async def test_title_screen_shows_welcome_text() -> None:
    from textual.widgets import Static

    from richman.adapters.textual_tui.screens.title import TitleScreen

    app = RichmanTuiApp(run_game_mode=True)
    async with app.run_test(size=(40, 120)) as pilot:
        await pilot.pause()
        assert isinstance(pilot.app.screen, TitleScreen)
        title_widget = pilot.app.screen.query_one(".title", Static)
        assert "大富翁" in str(title_widget.render())


async def test_title_screen_shows_start_hint() -> None:
    from textual.widgets import Static

    app = RichmanTuiApp(run_game_mode=True)
    async with app.run_test(size=(40, 120)) as pilot:
        await pilot.pause()
        hint = pilot.app.screen.query_one(".hint", Static)
        assert "Enter" in str(hint.render())


async def test_title_screen_enter_pushes_setup_screen() -> None:
    from richman.adapters.textual_tui.screens.setup import SetupScreen

    app = RichmanTuiApp(run_game_mode=True)
    async with app.run_test(size=(40, 120)) as pilot:
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()
        assert isinstance(pilot.app.screen, SetupScreen)


# -- SetupScreen tests -------------------------------------------------------


async def test_setup_screen_defaults() -> None:
    from textual.widgets import Input, Select, Static

    from richman.adapters.textual_tui.screens.setup import SetupScreen
    from richman.app import build_default_config

    config = build_default_config()
    screen = SetupScreen(config, seed=None, player_count=2)
    app = RichmanTuiApp(run_game_mode=True)
    async with app.run_test(size=(40, 120)) as pilot:
        await pilot.app.push_screen(screen)
        await pilot.pause()

        # Default player count is 2
        select = screen.query_one(Select)
        assert select.value == "2"

        # Default human name is "玩家"
        name_input = screen.query_one(Input)
        assert name_input.value == "玩家"

        # AI label shows 1 AI
        ai_label = screen.query_one(".ai-label", Static)
        assert "AI 1" in str(ai_label.render())


async def test_setup_screen_player_count_changes_ai_labels() -> None:
    from textual.widgets import Select, Static

    from richman.adapters.textual_tui.screens.setup import SetupScreen
    from richman.app import build_default_config

    config = build_default_config()
    screen = SetupScreen(config, player_count=2)
    app = RichmanTuiApp(run_game_mode=True)
    async with app.run_test(size=(40, 120)) as pilot:
        await pilot.app.push_screen(screen)
        await pilot.pause()

        select = screen.query_one(Select)
        select.value = "3"
        await pilot.pause()

        ai_label = screen.query_one(".ai-label", Static)
        ai_text = str(ai_label.render())
        assert "AI 1" in ai_text
        assert "AI 2" in ai_text
        assert "AI 3" not in ai_text


async def test_setup_screen_start_game_pushes_game_screen() -> None:
    from textual.widgets import Input

    from richman.adapters.textual_tui.screens.game import GameScreen
    from richman.adapters.textual_tui.screens.setup import SetupScreen
    from richman.app import build_default_config

    config = build_default_config()
    screen = SetupScreen(config, player_count=2)
    app = RichmanTuiApp(run_game_mode=True)
    async with app.run_test(size=(40, 120)) as pilot:
        await pilot.app.push_screen(screen)
        await pilot.pause()

        # Edit human name
        name_input = screen.query_one(Input)
        name_input.value = "小明"

        # Click start button
        await pilot.click("#start")
        await pilot.pause()

        assert isinstance(pilot.app.screen, GameScreen)


# -- create_tui_players human_name test --------------------------------------


def test_create_tui_players_custom_human_name() -> None:
    players = create_tui_players(2, human_name="小明")
    assert players[0].name == "小明"
    assert isinstance(players[0], HumanPlayer)
    assert players[1].name == "AI 1"


def test_create_tui_players_default_human_name() -> None:
    players = create_tui_players(3)
    assert players[0].name == "玩家"
