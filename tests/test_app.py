"""Tests for application-level assembly."""

from __future__ import annotations

import json
from io import StringIO
from pathlib import Path

import pytest

from richman.app import (
    MAX_PLAYERS,
    MIN_PLAYERS,
    _parse_simple_yaml,
    build_default_config,
    create_engine,
    create_players,
    load_config,
    run_game,
)
from richman.board import create as create_board
from richman.domain import CellType, GameConfig, InternalGameState
from richman.engine import GameEngine
from richman.player import AIPlayer
from richman.render import ConsoleRenderer


def _quiet_renderer() -> ConsoleRenderer:
    return ConsoleRenderer(output=StringIO())


def _config_payload() -> dict[str, object]:
    return {
        "start_cash": 900,
        "start_bonus": 75,
        "jail_rounds": 2,
        "demolish_range": 1,
        "dice_sides": 4,
        "board_cells": [
            {"type": "START"},
            {
                "type": "PROPERTY",
                "property": {
                    "name": "测试路",
                    "price": 100,
                    "rents": [10, 20, 40, 80],
                    "upgrade_cost": 50,
                },
            },
            {"type": "CHANCE"},
            {"type": "JAIL_SPACE"},
        ],
        "cards": [
            {"type": "MONEY_GAIN", "description": "获得奖金", "amount": 50},
            {
                "type": "MOVE",
                "description": "前进一步",
                "direction": "FORWARD",
                "min_steps": 1,
                "max_steps": 1,
            },
        ],
    }


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


def test_load_config_reads_json_config(tmp_path: Path) -> None:
    config_path = tmp_path / "game.json"
    config_path.write_text(json.dumps(_config_payload(), ensure_ascii=False), encoding="utf-8")

    config = load_config(config_path)
    board = create_board(config)

    assert config.start_cash == 900
    assert config.start_bonus == 75
    assert config.cards[1].min_steps == 1
    assert board.start_position == 0


def test_load_config_reads_yaml_config(tmp_path: Path) -> None:
    config_path = tmp_path / "game.yaml"
    config_path.write_text(
        """
start_cash: 900
start_bonus: 75
jail_rounds: 2
demolish_range: 1
dice_sides: 4
board_cells:
  - type: START
  - type: PROPERTY
    property:
      name: 测试路
      price: 100
      rents: [10, 20, 40, 80]
      upgrade_cost: 50
  - type: CHANCE
  - type: JAIL_SPACE
cards:
  - type: MONEY_GAIN
    description: 获得奖金
    amount: 50
  - type: MOVE
    description: 前进一步
    direction: FORWARD
    min_steps: 1
    max_steps: 1
""",
        encoding="utf-8",
    )

    config = load_config(config_path)

    assert config.start_cash == 900
    assert config.board_cells[1].property_template is not None
    assert config.board_cells[1].property_template.name == "测试路"


def test_simple_yaml_rejects_non_json_inline_mapping_cleanly() -> None:
    with pytest.raises(ValueError, match="inline collections"):
        _parse_simple_yaml("item: {key: value}")


def test_simple_yaml_sequence_keeps_plain_colon_scalars() -> None:
    parsed = _parse_simple_yaml(
        """
items:
  - 12:34
  - http://example.test/path
"""
    )

    assert parsed == {"items": ["12:34", "http://example.test/path"]}


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


def test_run_game_accepts_config_path(tmp_path: Path) -> None:
    config_path = tmp_path / "game.json"
    config_path.write_text(json.dumps(_config_payload(), ensure_ascii=False), encoding="utf-8")

    state = run_game(
        players_count=2,
        max_turns=0,
        seed=3,
        renderer=_quiet_renderer(),
        config_path=config_path,
    )

    assert [player.cash for player in state.players] == [900, 900]
