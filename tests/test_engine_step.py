"""Tests for the step-based game engine API."""

from __future__ import annotations

import pytest

from richman.board import create as create_board
from richman.domain import (
    Action,
    BoardCellDefinition,
    CellType,
    EngineInput,
    GameConfig,
    GameEventType,
    InputKind,
    PropertyRef,
    PropertyTemplate,
)
from richman.engine import GameEngine
from richman.player import AIPlayer


def _property(name: str = "测试路") -> BoardCellDefinition:
    return BoardCellDefinition(
        CellType.PROPERTY,
        PropertyTemplate(name=name, price=100, rents=(10, 20, 40, 80), upgrade_cost=50),
    )


def _config_for_action() -> GameConfig:
    return GameConfig(
        board_cells=(
            BoardCellDefinition(CellType.START),
            _property(),
            BoardCellDefinition(CellType.JAIL_SPACE),
        ),
        cards=(),
        dice_sides=1,
    )


def _config_for_jail() -> GameConfig:
    return GameConfig(
        board_cells=(
            BoardCellDefinition(CellType.START),
            BoardCellDefinition(CellType.GO_TO_JAIL),
            BoardCellDefinition(CellType.JAIL_SPACE),
        ),
        cards=(),
        dice_sides=1,
    )


def _engine(config: GameConfig) -> GameEngine:
    return GameEngine.create(
        config,
        create_board(config),
        [AIPlayer("AI 1"), AIPlayer("AI 2")],
        seed=7,
    )


def _roll(engine: GameEngine) -> None:
    result = engine.advance()
    assert result.required_input is not None
    assert result.required_input.kind is InputKind.ROLL_DICE
    engine.advance(
        EngineInput(
            kind=InputKind.ROLL_DICE,
            player_index=result.required_input.player_index,
        )
    )


def test_initial_advance_starts_turn_and_requests_roll() -> None:
    engine = _engine(_config_for_action())

    result = engine.advance()

    assert result.phase.value == "DICE_ROLL"
    assert result.required_input is not None
    assert result.required_input.kind is InputKind.ROLL_DICE
    assert result.snapshot.turn == 1
    assert [event.event_type for event in result.events] == [
        GameEventType.TURN_START,
        GameEventType.WAIT_DICE,
    ]


def test_roll_input_advances_to_dice_display_point() -> None:
    engine = _engine(_config_for_action())
    first = engine.advance()
    assert first.required_input is not None

    result = engine.advance(
        EngineInput(kind=InputKind.ROLL_DICE, player_index=first.required_input.player_index)
    )

    assert result.required_input is None
    assert result.snapshot.dice_value == 1
    assert [event.event_type for event in result.events] == [
        GameEventType.DICE_ROLLED,
        GameEventType.PLAYER_MOVED,
    ]


def test_action_choice_required_and_illegal_action_rejected() -> None:
    engine = _engine(_config_for_action())
    _roll(engine)
    engine.advance()  # LANDING display frame

    result = engine.advance()

    assert result.required_input is not None
    assert result.required_input.kind is InputKind.ACTION_CHOICE
    assert result.required_input.options == (Action.BUY, Action.SKIP)

    with pytest.raises(ValueError, match="action is not available"):
        engine.advance(
            EngineInput(
                kind=InputKind.ACTION_CHOICE,
                player_index=result.required_input.player_index,
                action=Action.UPGRADE,
            )
        )


def test_demolish_target_required_and_candidate_validated() -> None:
    engine = _engine(_config_for_action())
    state = engine.get_state()
    state.players[0].hand.demolish = 1
    state.properties_by_position[1].owner_player_index = 1
    state.properties_by_position[1].level = 1
    state.players[1].holdings.append(PropertyRef(position=1))

    _roll(engine)
    engine.advance()
    action_request = engine.advance()
    assert action_request.required_input is not None

    target_request = engine.advance(
        EngineInput(
            kind=InputKind.ACTION_CHOICE,
            player_index=action_request.required_input.player_index,
            action=Action.USE_DEMOLISH,
        )
    )

    assert target_request.required_input is not None
    assert target_request.required_input.kind is InputKind.DEMOLISH_TARGET
    assert target_request.required_input.candidates == (1,)

    with pytest.raises(ValueError, match="target is not available"):
        engine.advance(
            EngineInput(
                kind=InputKind.DEMOLISH_TARGET,
                player_index=target_request.required_input.player_index,
                target_position=2,
            )
        )

    result = engine.advance(
        EngineInput(
            kind=InputKind.DEMOLISH_TARGET,
            player_index=target_request.required_input.player_index,
            target_position=1,
        )
    )

    assert result.required_input is None
    assert state.properties_by_position[1].level == 0


def test_jail_choice_required_when_pass_available() -> None:
    engine = _engine(_config_for_jail())
    state = engine.get_state()
    state.players[0].hand.jail_pass = 1
    _roll(engine)

    result = engine.advance()

    assert result.required_input is not None
    assert result.required_input.kind is InputKind.JAIL_CHOICE
    assert result.required_input.options == (Action.USE_JAIL_PASS, Action.ACCEPT_JAIL)

    result = engine.advance(
        EngineInput(
            kind=InputKind.JAIL_CHOICE,
            player_index=result.required_input.player_index,
            action=Action.USE_JAIL_PASS,
        )
    )

    assert result.required_input is None
    assert state.players[0].hand.jail_pass == 0
    assert any(event.event_type is GameEventType.JAIL_PASS_USED for event in result.events)


def test_go_to_jail_without_pass_ends_turn_without_input() -> None:
    engine = _engine(_config_for_jail())
    state = engine.get_state()
    _roll(engine)

    result = engine.advance()

    assert result.required_input is None
    assert state.players[0].position == 2
    assert state.players[0].jail_rounds_left == 3
    assert any(event.event_type is GameEventType.PLAYER_SENT_TO_JAIL for event in result.events)


def test_ai_only_start_auto_advances_to_game_over() -> None:
    engine = _engine(_config_for_action())
    state = engine.get_state()
    state.players[1].bankrupt = True

    final_state = engine.start()

    assert final_state is state
    assert any(event.event_type is GameEventType.GAME_OVER for event in state.event_log)
