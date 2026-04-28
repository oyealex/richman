"""Tests for application-level assembly."""

from __future__ import annotations

from io import StringIO

import pytest

from richman.app import (
    MAX_PLAYERS,
    MIN_PLAYERS,
    build_default_config,
    create_engine,
    create_players,
    run_game,
)
from richman.board import create as create_board
from richman.domain import CellType, GameConfig, InternalGameState
from richman.engine import GameEngine
from richman.player import AIPlayer
from richman.render import ConsoleRenderer


def _quiet_renderer() -> ConsoleRenderer:
    return ConsoleRenderer(output=StringIO())


def test_default_config_can_create_board_and_contains_playable_content() -> None:
    config = build_default_config()
    board = create_board(config)
    cell_types = tuple(cell.cell_type for cell in config.board_cells)

    assert isinstance(config, GameConfig)
    assert board.start_position == 0
    assert cell_types.count(CellType.START) == 1
    assert cell_types.count(CellType.JAIL_SPACE) == 1
    assert CellType.PROPERTY in cell_types
    assert CellType.CHANCE in cell_types
    assert config.cards


def test_create_players_returns_stably_named_ai_players() -> None:
    players = create_players(3)

    assert len(players) == 3
    assert all(isinstance(player, AIPlayer) for player in players)
    assert [player.name for player in players] == ["AI 1", "AI 2", "AI 3"]


@pytest.mark.parametrize("count", [MIN_PLAYERS - 1, MAX_PLAYERS + 1])
def test_create_players_rejects_invalid_count(count: int) -> None:
    with pytest.raises(ValueError, match="players"):
        create_players(count)


def test_create_engine_assembles_initialized_engine() -> None:
    config = build_default_config()
    players = create_players(2)
    engine = create_engine(config, players, _quiet_renderer(), seed=7)
    state = engine.get_state()
    property_count = sum(1 for cell in config.board_cells if cell.cell_type is CellType.PROPERTY)

    assert isinstance(engine, GameEngine)
    assert len(state.players) == 2
    assert [player.name for player in state.players] == ["AI 1", "AI 2"]
    assert len(state.properties_by_position) == property_count


def test_create_engine_forwards_seed_for_deterministic_initial_state() -> None:
    config = build_default_config()
    players = create_players(2)

    first = create_engine(config, players, _quiet_renderer(), seed=11).get_state()
    second = create_engine(config, players, _quiet_renderer(), seed=11).get_state()

    assert first.turn == second.turn
    assert [player.cash for player in first.players] == [player.cash for player in second.players]


def test_run_game_returns_bounded_state() -> None:
    state = run_game(players_count=2, max_turns=1, seed=3, renderer=_quiet_renderer())

    assert isinstance(state, InternalGameState)
    assert state.turn <= 1
