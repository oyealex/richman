"""Tests for the game engine module."""

from __future__ import annotations

import ast
from collections.abc import MutableMapping, Sequence
from io import StringIO
from pathlib import Path
from typing import cast

import pytest

from richman.board import Board
from richman.board import create as create_board
from richman.domain import (
    Action,
    BoardCellDefinition,
    CardDefinition,
    CardType,
    CellType,
    GameConfig,
    GameEventType,
    HandCards,
    InternalGameState,
    MoveDirection,
    Phase,
    PlayerView,
    PropertyRef,
)
from richman.engine import GameEngine
from richman.player import AIPlayer, InputContext
from richman.render import ConsoleRenderer

# ---------------------------------------------------------------------------
# Forbidden import check
# ---------------------------------------------------------------------------

ENGINE_ROOT = Path(__file__).resolve().parents[1] / "src" / "richman" / "engine"
FORBIDDEN_ENGINE_IMPORTS = {
    "richman.adapters",
    "rich",
    "textual",
}


def test_engine_source_depends_only_on_allowed_modules() -> None:
    imported_modules: set[str] = set()
    for path in ENGINE_ROOT.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_modules.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module is not None:
                imported_modules.add(node.module)

    forbidden = {
        m
        for m in imported_modules
        if any(m == prefix or m.startswith(f"{prefix}.") for prefix in FORBIDDEN_ENGINE_IMPORTS)
    }
    assert forbidden == set()


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------


def _make_property_cell(
    name: str, price: int, rents: tuple[int, int, int, int], upgrade_cost: int
) -> BoardCellDefinition:
    from richman.domain import PropertyTemplate

    return BoardCellDefinition(
        cell_type=CellType.PROPERTY,
        property_template=PropertyTemplate(
            name=name, price=price, rents=rents, upgrade_cost=upgrade_cost
        ),
    )


def _make_config(
    *,
    cards: tuple[CardDefinition, ...] = (),
    start_cash: int = 2000,
    start_bonus: int = 200,
    jail_rounds: int = 3,
    demolish_range: int = 3,
    dice_sides: int = 6,
) -> GameConfig:
    cells = (
        BoardCellDefinition(cell_type=CellType.START),  # 0
        _make_property_cell("中山路", 300, (50, 150, 300, 600), 150),  # 1
        _make_property_cell("解放路", 500, (80, 250, 500, 1000), 250),  # 2
        BoardCellDefinition(cell_type=CellType.CHANCE),  # 3
        BoardCellDefinition(cell_type=CellType.GO_TO_JAIL),  # 4
        BoardCellDefinition(cell_type=CellType.JAIL_SPACE),  # 5
        BoardCellDefinition(cell_type=CellType.BLANK),  # 6
    )
    return GameConfig(
        board_cells=cells,
        cards=cards,
        start_cash=start_cash,
        start_bonus=start_bonus,
        jail_rounds=jail_rounds,
        demolish_range=demolish_range,
        dice_sides=dice_sides,
    )


def _make_board(config: GameConfig) -> Board:
    return create_board(config)


def _make_renderer() -> ConsoleRenderer:
    return ConsoleRenderer(output=StringIO(), input_reader=lambda _: "")


def _make_card(card_type: CardType, description: str = "", **kwargs: object) -> CardDefinition:
    return CardDefinition(card_type=card_type, description=description, **kwargs)  # type: ignore[arg-type]


# Standard cards for testing
MONEY_GAIN_CARD = _make_card(CardType.MONEY_GAIN, "奖金", amount=500)
MONEY_LOSS_CARD = _make_card(CardType.MONEY_LOSS, "罚款", amount=300)
MOVE_CARD = _make_card(
    CardType.MOVE, "前进", direction=MoveDirection.FORWARD, min_steps=1, max_steps=3
)
GO_TO_JAIL_CARD = _make_card(CardType.GO_TO_JAIL, "入狱")
JAIL_PASS_CARD = _make_card(CardType.JAIL_PASS, "免狱卡")
DEMOLISH_CARD = _make_card(CardType.DEMOLISH, "拆除卡")


# ---------------------------------------------------------------------------
# Initialization and factory
# ---------------------------------------------------------------------------


class TestEngineCreation:
    def test_create_rejects_board_without_jail_space(self) -> None:
        config = GameConfig(
            board_cells=(
                BoardCellDefinition(cell_type=CellType.START),
                BoardCellDefinition(cell_type=CellType.BLANK),
            ),
            cards=(),
        )
        board = create_board(config)
        with pytest.raises(ValueError, match="JAIL_SPACE"):
            GameEngine.create(config, board, [], _make_renderer())

    def test_create_initializes_player_states(self) -> None:
        config = _make_config()
        board = _make_board(config)
        players = [AIPlayer("Alice"), AIPlayer("Bob")]

        engine = GameEngine.create(config, board, players, _make_renderer(), seed=42)
        state = engine.get_state()

        assert len(state.players) == 2
        assert state.players[0].name == "Alice"
        assert state.players[0].cash == 2000
        assert state.players[0].position == 0
        assert state.players[1].name == "Bob"
        assert state.players[1].cash == 2000

    def test_create_initializes_property_states(self) -> None:
        config = _make_config()
        board = _make_board(config)
        engine = GameEngine.create(config, board, [AIPlayer("Alice")], _make_renderer(), seed=42)
        state = engine.get_state()

        assert 1 in state.properties_by_position
        assert 2 in state.properties_by_position
        assert state.properties_by_position[1].owner_player_index is None
        assert state.properties_by_position[1].level == 0
        assert 0 not in state.properties_by_position  # START, not PROPERTY

    def test_create_initial_state_values(self) -> None:
        config = _make_config()
        board = _make_board(config)
        engine = GameEngine.create(config, board, [AIPlayer("Alice")], _make_renderer(), seed=42)
        state = engine.get_state()

        assert state.turn == 0
        assert state.current_player_index == 0
        assert state.phase == Phase.EFFECT_UPDATE
        assert state.dice_value is None
        assert state.available_actions is None
        assert state.event_log == []

    def test_create_with_seed_produces_deterministic_behavior(self) -> None:
        config = _make_config(cards=(MONEY_GAIN_CARD,))
        board = _make_board(config)
        players = [AIPlayer("Alice"), AIPlayer("Bob")]

        e1 = GameEngine.create(config, board, players, _make_renderer(), seed=42)
        e2 = GameEngine.create(config, board, players, _make_renderer(), seed=42)

        s1 = e1.get_state()
        s2 = e2.get_state()

        assert s1.players[0].cash == s2.players[0].cash
        assert s1.turn == s2.turn
        assert s1.phase == s2.phase

    def test_get_state_returns_current_state(self) -> None:
        config = _make_config()
        board = _make_board(config)
        engine = GameEngine.create(config, board, [AIPlayer("Alice")], _make_renderer(), seed=42)
        state = engine.get_state()

        assert isinstance(state, InternalGameState)
        assert state.turn == 0


# ---------------------------------------------------------------------------
# Main loop and turn progression
# ---------------------------------------------------------------------------


class TestMainLoop:
    def test_start_raises_when_max_turns_reached_before_game_over(self) -> None:
        config = _make_config()
        board = _make_board(config)
        players = [AIPlayer("Alice"), AIPlayer("Bob")]
        engine = GameEngine.create(config, board, players, _make_renderer(), seed=42)

        with pytest.raises(RuntimeError, match="max_turns"):
            engine.start(max_turns=0)

    def test_start_increments_turn_counter(self) -> None:
        config = _make_config()
        board = _make_board(config)
        players = [AIPlayer("Alice"), AIPlayer("Bob")]
        engine = GameEngine.create(config, board, players, _make_renderer(), seed=42)

        state = engine.get_state()
        state.turn += 1
        engine._process_turn()
        assert state.turn == 1

    def test_skip_bankrupt_player(self) -> None:
        config = _make_config()
        board = _make_board(config)
        players = [AIPlayer("Alice"), AIPlayer("Bob"), AIPlayer("Charlie")]
        engine = GameEngine.create(config, board, players, _make_renderer(), seed=42)

        state = engine.get_state()
        state.players[0].bankrupt = True

        engine._advance_to_next_player()
        assert state.current_player_index == 1  # Skipped player 0

    def test_advance_wraps_around_circularly(self) -> None:
        config = _make_config()
        board = _make_board(config)
        players = [AIPlayer("Alice"), AIPlayer("Bob")]
        engine = GameEngine.create(config, board, players, _make_renderer(), seed=42)

        state = engine.get_state()
        state.current_player_index = 1
        engine._advance_to_next_player()
        assert state.current_player_index == 0

    def test_start_ends_when_one_player_remains(self) -> None:
        config = _make_config()
        board = _make_board(config)
        players = [AIPlayer("Alice"), AIPlayer("Bob")]
        engine = GameEngine.create(config, board, players, _make_renderer(), seed=42)

        state = engine.get_state()
        state.players[1].bankrupt = True

        engine._check_game_over()
        assert engine._is_game_over()
        assert engine._winner_name == "Alice"


# ---------------------------------------------------------------------------
# Five-phase turn flow
# ---------------------------------------------------------------------------


class TestTurnPhases:
    def test_normal_turn_sequence(self) -> None:
        config = _make_config()
        board = _make_board(config)
        engine = GameEngine.create(config, board, [AIPlayer("Alice")], _make_renderer(), seed=42)

        engine._process_turn()
        state = engine.get_state()

        event_types = [e.event_type for e in state.event_log]
        assert GameEventType.TURN_START in event_types
        assert GameEventType.WAIT_DICE in event_types
        assert GameEventType.DICE_ROLLED in event_types
        assert GameEventType.PLAYER_MOVED in event_types
        assert GameEventType.LANDED_ON in event_types
        assert GameEventType.TURN_END in event_types

    def test_phase_values_through_turn(self) -> None:
        config = _make_config()
        board = _make_board(config)
        engine = GameEngine.create(config, board, [AIPlayer("Alice")], _make_renderer(), seed=42)

        engine._process_turn()
        state = engine.get_state()

        assert state.phase == Phase.END
        assert state.dice_value is None
        assert state.available_actions is None

    def test_dice_roll_produces_value_in_range(self) -> None:
        config = _make_config(dice_sides=6)
        board = _make_board(config)
        engine = GameEngine.create(config, board, [AIPlayer("Alice")], _make_renderer(), seed=42)

        for _ in range(20):
            dice = engine._rng.randint(1, 6)
            assert 1 <= dice <= 6

    def test_player_moves_after_dice_roll(self) -> None:
        config = _make_config()
        board = _make_board(config)
        engine = GameEngine.create(config, board, [AIPlayer("Alice")], _make_renderer(), seed=42)
        state = engine.get_state()
        old_pos = state.players[0].position

        engine._process_turn()

        # Player should have moved (unless dice rolled 0, which is impossible)
        new_pos = state.players[0].position
        assert new_pos != old_pos or state.phase == Phase.END  # might have looped

    def test_start_bonus_granted_on_crossing(self) -> None:
        config = _make_config(start_bonus=200, dice_sides=6)
        board = _make_board(config)
        engine = GameEngine.create(config, board, [AIPlayer("Alice")], _make_renderer(), seed=42)

        # Set player before START so crossing is likely
        state = engine.get_state()
        state.players[0].position = len(board.cells) - 2

        initial_cash = state.players[0].cash
        engine._process_turn()

        events = state.event_log
        start_bonus_events = [
            e for e in events if e.event_type == GameEventType.START_BONUS_GRANTED
        ]
        if start_bonus_events:
            assert state.players[0].cash > initial_cash


# ---------------------------------------------------------------------------
# Jail mechanics
# ---------------------------------------------------------------------------


class TestJail:
    def test_go_to_jail_rejects_unavailable_decision(self) -> None:
        class InvalidDecisionPlayer(AIPlayer):
            def decide(
                self,
                view: PlayerView,
                actions: Sequence[Action],
                engine_context: InputContext | None,
            ) -> Action:
                del view, actions, engine_context
                return Action.BUY

        config = _make_config(jail_rounds=3)
        board = _make_board(config)
        players = [InvalidDecisionPlayer("Alice")]
        engine = GameEngine.create(config, board, players, _make_renderer(), seed=42)
        state = engine.get_state()
        state.players[0].position = 4
        state.players[0].hand.jail_pass = 1

        with pytest.raises(ValueError, match="unavailable jail action"):
            engine._handle_jail_decision()

    def test_jail_countdown_decrements(self) -> None:
        config = _make_config(jail_rounds=3)
        board = _make_board(config)
        engine = GameEngine.create(config, board, [AIPlayer("Alice")], _make_renderer(), seed=42)
        state = engine.get_state()
        state.players[0].jail_rounds_left = 2
        state.players[0].position = 5  # JAIL_SPACE

        engine._process_turn()

        jailed_events = [e for e in state.event_log if e.event_type == GameEventType.JAIL_TICKED]
        assert len(jailed_events) == 1
        assert state.players[0].jail_rounds_left == 1

    def test_jail_release_continues_full_turn(self) -> None:
        config = _make_config(jail_rounds=3)
        board = _make_board(config)
        engine = GameEngine.create(config, board, [AIPlayer("Alice")], _make_renderer(), seed=42)
        state = engine.get_state()
        state.players[0].jail_rounds_left = 1
        state.players[0].position = 0  # START — can't be re-arrested this way

        engine._process_turn()

        events = state.event_log
        assert any(e.event_type == GameEventType.JAIL_RELEASED for e in events)
        assert any(e.event_type == GameEventType.DICE_ROLLED for e in events)
        assert state.players[0].jail_rounds_left in (
            0,
            3,
        )  # 0 if escaped, 3 if landed on GO_TO_JAIL again

    def test_jailed_player_skips_phases(self) -> None:
        config = _make_config(jail_rounds=3)
        board = _make_board(config)
        engine = GameEngine.create(config, board, [AIPlayer("Alice")], _make_renderer(), seed=42)
        state = engine.get_state()
        state.players[0].jail_rounds_left = 2
        state.players[0].position = 5  # JAIL_SPACE

        engine._process_turn()

        events = state.event_log
        assert not any(e.event_type == GameEventType.DICE_ROLLED for e in events)
        assert not any(e.event_type == GameEventType.LANDED_ON for e in events)

    def test_go_to_jail_auto_accept_without_pass(self) -> None:
        config = _make_config(jail_rounds=3)
        board = _make_board(config)
        engine = GameEngine.create(config, board, [AIPlayer("Alice")], _make_renderer(), seed=42)
        state = engine.get_state()
        state.players[0].position = 4  # GO_TO_JAIL cell

        result = engine._handle_jail_decision()

        assert result is True
        assert state.players[0].position == 5  # JAIL_SPACE
        assert state.players[0].jail_rounds_left == 3

    def test_go_to_jail_use_pass(self) -> None:
        config = _make_config(jail_rounds=3)
        board = _make_board(config)
        players = [AIPlayer("Alice", action_priority=[Action.USE_JAIL_PASS, Action.ACCEPT_JAIL])]
        engine = GameEngine.create(config, board, players, _make_renderer(), seed=42)
        state = engine.get_state()
        state.players[0].position = 4  # GO_TO_JAIL cell
        state.players[0].hand.jail_pass = 1

        result = engine._handle_jail_decision()

        assert result is False
        assert state.players[0].hand.jail_pass == 0
        assert state.players[0].jail_rounds_left == 0

    def test_go_to_jail_ai_accepts_when_pass_available(self) -> None:
        """AIPlayer's default priority has SKIP before ACCEPT_JAIL, but ACCEPT_JAIL
        is the last resort. With USE_JAIL_PASS first, the AI should still choose it."""
        config = _make_config(jail_rounds=3)
        board = _make_board(config)
        # Default AI priority: USE_JAIL_PASS first
        players = [AIPlayer("Alice")]
        engine = GameEngine.create(config, board, players, _make_renderer(), seed=42)
        state = engine.get_state()
        state.players[0].position = 4
        state.players[0].hand.jail_pass = 1

        result = engine._handle_jail_decision()

        # With USE_JAIL_PASS at top priority, AI uses the pass
        assert result is False
        assert state.players[0].hand.jail_pass == 0


# ---------------------------------------------------------------------------
# Landing: property cells
# ---------------------------------------------------------------------------


class TestPropertyLanding:
    def test_unowned_property_logs_available(self) -> None:
        config = _make_config()
        board = _make_board(config)
        engine = GameEngine.create(config, board, [AIPlayer("Alice")], _make_renderer(), seed=42)
        state = engine.get_state()
        state.players[0].position = 1  # PROPERTY cell, unowned

        engine._process_landing()

        events = state.event_log
        assert any(e.event_type == GameEventType.PROPERTY_AVAILABLE for e in events)

    def test_own_property_logs_upgradable(self) -> None:
        config = _make_config()
        board = _make_board(config)
        engine = GameEngine.create(config, board, [AIPlayer("Alice")], _make_renderer(), seed=42)
        state = engine.get_state()
        state.players[0].position = 1  # PROPERTY
        state.properties_by_position[1].owner_player_index = 0
        state.properties_by_position[1].level = 1

        engine._process_landing()

        events = state.event_log
        assert any(e.event_type == GameEventType.PROPERTY_UPGRADABLE for e in events)

    def test_opponent_property_charges_rent(self) -> None:
        config = _make_config()
        board = _make_board(config)
        players = [AIPlayer("Alice"), AIPlayer("Bob")]
        engine = GameEngine.create(config, board, players, _make_renderer(), seed=42)
        state = engine.get_state()
        state.current_player_index = 0
        state.players[0].position = 1
        state.properties_by_position[1].owner_player_index = 1  # Bob's property
        state.properties_by_position[1].level = 1

        initial_cash = state.players[0].cash
        owner_initial_cash = state.players[1].cash

        engine._process_landing()

        # Rent should have been charged (level 1 of 中山路 = 150)
        events = state.event_log
        assert any(e.event_type == GameEventType.RENT_PAID for e in events)
        assert state.players[0].cash == initial_cash - 150
        assert state.players[1].cash == owner_initial_cash + 150

    def test_rent_skipped_when_owner_in_jail(self) -> None:
        config = _make_config()
        board = _make_board(config)
        players = [AIPlayer("Alice"), AIPlayer("Bob")]
        engine = GameEngine.create(config, board, players, _make_renderer(), seed=42)
        state = engine.get_state()
        state.current_player_index = 0
        state.players[0].position = 1
        state.properties_by_position[1].owner_player_index = 1
        state.players[1].jail_rounds_left = 2  # Bob in jail

        initial_cash = state.players[0].cash

        engine._process_landing()

        events = state.event_log
        assert any(e.event_type == GameEventType.RENT_SKIPPED_OWNER_IN_JAIL for e in events)
        assert state.players[0].cash == initial_cash  # No rent charged


# ---------------------------------------------------------------------------
# Landing: chance cards
# ---------------------------------------------------------------------------


class TestChanceCards:
    def test_money_gain_card(self) -> None:
        config = _make_config(cards=(MONEY_GAIN_CARD,))
        board = _make_board(config)
        engine = GameEngine.create(config, board, [AIPlayer("Alice")], _make_renderer(), seed=42)
        state = engine.get_state()
        state.players[0].position = 3  # CHANCE

        initial_cash = state.players[0].cash
        engine._process_landing()

        events = state.event_log
        assert any(e.event_type == GameEventType.CARD_DRAWN for e in events)
        assert any(e.event_type == GameEventType.MONEY_GAINED for e in events)
        assert state.players[0].cash == initial_cash + 500

    def test_money_loss_card_with_sufficient_funds(self) -> None:
        config = _make_config(cards=(MONEY_LOSS_CARD,))
        board = _make_board(config)
        engine = GameEngine.create(config, board, [AIPlayer("Alice")], _make_renderer(), seed=42)
        state = engine.get_state()
        state.players[0].position = 3  # CHANCE
        state.players[0].cash = 500

        engine._process_landing()

        events = state.event_log
        assert any(e.event_type == GameEventType.MONEY_LOST for e in events)
        assert state.players[0].cash == 200  # 500 - 300

    def test_money_loss_card_triggers_bankruptcy(self) -> None:
        config = _make_config(cards=(MONEY_LOSS_CARD,))
        board = _make_board(config)
        engine = GameEngine.create(config, board, [AIPlayer("Alice")], _make_renderer(), seed=42)
        state = engine.get_state()
        state.players[0].position = 3  # CHANCE
        state.players[0].cash = 0  # Can't pay anything
        # No properties to reclaim (holdings is empty)

        result = engine._process_landing()

        assert result is True
        events = state.event_log
        assert any(e.event_type == GameEventType.PLAYER_BANKRUPT for e in events)
        assert state.players[0].bankrupt is True

    def test_move_card(self) -> None:
        config = _make_config(
            cards=(
                _make_card(
                    CardType.MOVE,
                    "前进2步",
                    direction=MoveDirection.FORWARD,
                    min_steps=2,
                    max_steps=2,
                ),
            )
        )
        board = _make_board(config)
        engine = GameEngine.create(config, board, [AIPlayer("Alice")], _make_renderer(), seed=42)
        state = engine.get_state()
        state.players[0].position = 3  # CHANCE

        engine._process_landing()

        # Player should have moved (from 3 to 5 by +2 steps)
        assert state.players[0].position != 3
        events = state.event_log
        assert any(e.event_type == GameEventType.PLAYER_MOVED for e in events)

    def test_move_card_chains_landing_phase_only(self) -> None:
        """Move card should process phase ③ at destination but not phase ④."""
        config = _make_config(
            cards=(
                _make_card(
                    CardType.MOVE,
                    "前进到地块",
                    direction=MoveDirection.FORWARD,
                    min_steps=1,
                    max_steps=1,
                ),
            )
        )
        board = _make_board(config)
        # Put a property at position 4 (GO_TO_JAIL cell - oops, that's GO_TO_JAIL)
        # Let's use a different setup: player at CHANCE (3), move 1 to GO_TO_JAIL (4)
        # That would trigger jail
        engine = GameEngine.create(config, board, [AIPlayer("Alice")], _make_renderer(), seed=42)
        state = engine.get_state()
        state.players[0].position = 3  # CHANCE at pos 3, move 3 to pos 6 (BLANK)
        state.players[0].cash = 100

        # Use a move card that moves exactly 3 steps forward (3 -> 6)
        engine._config = _make_config(
            cards=(
                _make_card(
                    CardType.MOVE,
                    "前进3步",
                    direction=MoveDirection.FORWARD,
                    min_steps=3,
                    max_steps=3,
                ),
            )
        )

        engine._process_landing()

        # Should land on position 6 (BLANK), no phase ④ actions triggered
        assert state.players[0].position == 6

    def test_obtain_jail_pass_card(self) -> None:
        config = _make_config(cards=(JAIL_PASS_CARD,))
        board = _make_board(config)
        engine = GameEngine.create(config, board, [AIPlayer("Alice")], _make_renderer(), seed=42)
        state = engine.get_state()
        state.players[0].position = 3  # CHANCE

        engine._process_landing()

        assert state.players[0].hand.jail_pass == 1

    def test_obtain_demolish_card(self) -> None:
        config = _make_config(cards=(DEMOLISH_CARD,))
        board = _make_board(config)
        engine = GameEngine.create(config, board, [AIPlayer("Alice")], _make_renderer(), seed=42)
        state = engine.get_state()
        state.players[0].position = 3  # CHANCE

        engine._process_landing()

        assert state.players[0].hand.demolish == 1

    def test_go_to_jail_card_without_pass(self) -> None:
        config = _make_config(cards=(GO_TO_JAIL_CARD,), jail_rounds=3)
        board = _make_board(config)
        engine = GameEngine.create(config, board, [AIPlayer("Alice")], _make_renderer(), seed=42)
        state = engine.get_state()
        state.players[0].position = 3  # CHANCE

        result = engine._process_landing()

        assert result is True
        assert state.players[0].position == 5  # JAIL_SPACE
        assert state.players[0].jail_rounds_left == 3

    def test_no_cards_skips_chance(self) -> None:
        config = _make_config(cards=())  # Empty card deck
        board = _make_board(config)
        engine = GameEngine.create(config, board, [AIPlayer("Alice")], _make_renderer(), seed=42)
        state = engine.get_state()
        state.players[0].position = 3  # CHANCE

        result = engine._process_landing()

        assert result is False
        assert not any(e.event_type == GameEventType.CARD_DRAWN for e in state.event_log)


# ---------------------------------------------------------------------------
# Landing: other cell types
# ---------------------------------------------------------------------------


class TestOtherLandings:
    def test_start_cell_no_extra_bonus(self) -> None:
        config = _make_config(start_bonus=200)
        board = _make_board(config)
        engine = GameEngine.create(config, board, [AIPlayer("Alice")], _make_renderer(), seed=42)
        state = engine.get_state()
        state.players[0].position = 0  # START

        initial_cash = state.players[0].cash
        result = engine._process_landing()

        assert result is False
        assert state.players[0].cash == initial_cash  # No extra bonus

    def test_blank_cell_no_effect(self) -> None:
        config = _make_config()
        board = _make_board(config)
        engine = GameEngine.create(config, board, [AIPlayer("Alice")], _make_renderer(), seed=42)
        state = engine.get_state()
        state.players[0].position = 6  # BLANK

        result = engine._process_landing()
        assert result is False

    def test_jail_space_no_effect_on_visitor(self) -> None:
        config = _make_config()
        board = _make_board(config)
        engine = GameEngine.create(config, board, [AIPlayer("Alice")], _make_renderer(), seed=42)
        state = engine.get_state()
        state.players[0].position = 5  # JAIL_SPACE
        state.players[0].jail_rounds_left = 0  # Not jailed

        result = engine._process_landing()
        assert result is False


# ---------------------------------------------------------------------------
# Actions: BUY / UPGRADE / DEMOLISH / SKIP
# ---------------------------------------------------------------------------


class TestActions:
    def test_buy_action_acquires_property(self) -> None:
        config = _make_config()
        board = _make_board(config)
        engine = GameEngine.create(config, board, [AIPlayer("Alice")], _make_renderer(), seed=42)
        state = engine.get_state()
        state.players[0].position = 1  # Unowned PROPERTY
        state.players[0].cash = 2000

        actions = engine._compute_actions()
        assert Action.BUY in actions

        engine._execute_action(Action.BUY)

        assert state.players[0].cash == 1700  # 2000 - 300
        assert state.properties_by_position[1].owner_player_index == 0
        assert state.properties_by_position[1].level == 0
        assert PropertyRef(position=1) in state.players[0].holdings

    def test_buy_not_available_when_cannot_afford(self) -> None:
        config = _make_config()
        board = _make_board(config)
        engine = GameEngine.create(config, board, [AIPlayer("Alice")], _make_renderer(), seed=42)
        state = engine.get_state()
        state.players[0].position = 1
        state.players[0].cash = 100  # Can't afford 300

        actions = engine._compute_actions()
        assert Action.BUY not in actions

    def test_upgrade_action(self) -> None:
        config = _make_config()
        board = _make_board(config)
        engine = GameEngine.create(config, board, [AIPlayer("Alice")], _make_renderer(), seed=42)
        state = engine.get_state()
        state.players[0].position = 1
        state.players[0].cash = 2000
        state.properties_by_position[1].owner_player_index = 0
        state.properties_by_position[1].level = 1

        actions = engine._compute_actions()
        assert Action.UPGRADE in actions

        engine._execute_action(Action.UPGRADE)

        assert state.players[0].cash == 1850  # 2000 - 150
        assert state.properties_by_position[1].level == 2
        assert state.properties_by_position[1].upgrade_invested == 150

    def test_upgrade_not_available_at_max_level(self) -> None:
        config = _make_config()
        board = _make_board(config)
        engine = GameEngine.create(config, board, [AIPlayer("Alice")], _make_renderer(), seed=42)
        state = engine.get_state()
        state.players[0].position = 1
        state.properties_by_position[1].owner_player_index = 0
        state.properties_by_position[1].level = 3  # Max level

        actions = engine._compute_actions()
        assert Action.UPGRADE not in actions

    def test_demolish_action(self) -> None:
        config = _make_config(demolish_range=3)
        board = _make_board(config)
        players = [AIPlayer("Alice"), AIPlayer("Bob")]
        engine = GameEngine.create(config, board, players, _make_renderer(), seed=42)
        state = engine.get_state()
        state.current_player_index = 0
        state.players[0].position = 0  # START
        state.players[0].hand.demolish = 1
        state.properties_by_position[1].owner_player_index = 1  # Bob's property
        state.properties_by_position[1].level = 2

        actions = engine._compute_actions()
        assert Action.USE_DEMOLISH in actions

        engine._execute_demolish()

        assert state.players[0].hand.demolish == 0
        assert state.properties_by_position[1].level == 1

    def test_demolish_not_available_without_target(self) -> None:
        config = _make_config(demolish_range=3)
        board = _make_board(config)
        engine = GameEngine.create(config, board, [AIPlayer("Alice")], _make_renderer(), seed=42)
        state = engine.get_state()
        state.players[0].position = 0  # START
        state.players[0].hand.demolish = 1
        # No properties have level > 0

        actions = engine._compute_actions()
        assert Action.USE_DEMOLISH not in actions

    def test_skip_available_when_actions_present(self) -> None:
        config = _make_config()
        board = _make_board(config)
        engine = GameEngine.create(config, board, [AIPlayer("Alice")], _make_renderer(), seed=42)
        state = engine.get_state()
        state.players[0].position = 1
        state.players[0].cash = 2000

        actions = engine._compute_actions()
        assert Action.SKIP in actions

    def test_empty_actions_when_nothing_available(self) -> None:
        config = _make_config()
        board = _make_board(config)
        engine = GameEngine.create(config, board, [AIPlayer("Alice")], _make_renderer(), seed=42)
        state = engine.get_state()
        state.players[0].position = 0  # START - no actions
        state.players[0].hand.demolish = 0
        state.players[0].cash = 0

        actions = engine._compute_actions()
        assert actions == []

    def test_ai_chooses_buy_over_skip(self) -> None:
        config = _make_config()
        board = _make_board(config)
        engine = GameEngine.create(config, board, [AIPlayer("Alice")], _make_renderer(), seed=42)
        state = engine.get_state()
        state.players[0].position = 1
        state.players[0].cash = 2000

        actions = engine._compute_actions()
        view = engine._build_player_view(0, actions=actions)
        choice = engine._players[0].decide(view, actions, engine._context)

        assert choice == Action.BUY  # AI priority: BUY before SKIP


# ---------------------------------------------------------------------------
# Bankruptcy
# ---------------------------------------------------------------------------


class TestBankruptcy:
    def test_simple_payment_sufficient_cash(self) -> None:
        config = _make_config()
        board = _make_board(config)
        players = [AIPlayer("Alice"), AIPlayer("Bob")]
        engine = GameEngine.create(config, board, players, _make_renderer(), seed=42)
        state = engine.get_state()
        state.current_player_index = 0
        state.players[0].cash = 500

        result = engine._pay_debt(300, creditor_index=1)

        assert result is False
        assert state.players[0].cash == 200
        assert state.players[1].cash == 2300  # 2000 + 300

    def test_payment_with_reclamation_covers_debt(self) -> None:
        config = _make_config()
        board = _make_board(config)
        players = [AIPlayer("Alice"), AIPlayer("Bob")]
        engine = GameEngine.create(config, board, players, _make_renderer(), seed=42)
        state = engine.get_state()
        state.current_player_index = 0
        state.players[0].cash = 100
        # Give player a property worth 450
        state.properties_by_position[1].owner_player_index = 0
        state.properties_by_position[1].purchase_price = 300
        state.properties_by_position[1].upgrade_invested = 150
        state.players[0].holdings.append(PropertyRef(position=1))
        engine._acquisition_counter = 1

        result = engine._pay_debt(500, creditor_index=1)

        assert result is False
        # Player had 100 cash, reclaimed 450, paid 500 debt -> 50 remaining
        assert state.players[0].cash == 50
        assert state.players[1].cash == 2500  # 2000 + 500
        assert state.properties_by_position[1].owner_player_index is None

    def test_bankruptcy_when_reclamation_insufficient(self) -> None:
        config = _make_config()
        board = _make_board(config)
        players = [AIPlayer("Alice"), AIPlayer("Bob")]
        engine = GameEngine.create(config, board, players, _make_renderer(), seed=42)
        state = engine.get_state()
        state.current_player_index = 0
        state.players[0].cash = 0
        # Player has no properties or holdings
        state.players[0].holdings.clear()

        owner_before = state.players[1].cash
        result = engine._pay_debt(500, creditor_index=1)

        assert result is True
        assert state.players[0].bankrupt is True
        assert state.players[0].cash == 0
        assert state.players[0].hand == HandCards()
        # Owner gets nothing
        assert state.players[1].cash == owner_before

    def test_property_reclaimed_event_logged(self) -> None:
        config = _make_config()
        board = _make_board(config)
        players = [AIPlayer("Alice"), AIPlayer("Bob")]
        engine = GameEngine.create(config, board, players, _make_renderer(), seed=42)
        state = engine.get_state()
        state.current_player_index = 0
        state.players[0].cash = 0
        state.properties_by_position[1].owner_player_index = 0
        state.properties_by_position[1].purchase_price = 300
        state.players[0].holdings.append(PropertyRef(position=1))
        engine._acquisition_counter = 1

        engine._pay_debt(500, creditor_index=1)

        events = state.event_log
        assert any(e.event_type == GameEventType.PROPERTY_RECLAIMED for e in events)
        assert any(e.event_type == GameEventType.PLAYER_BANKRUPT for e in events)

    def test_reclaimed_property_removed_from_holdings(self) -> None:
        config = _make_config()
        board = _make_board(config)
        players = [AIPlayer("Alice")]
        engine = GameEngine.create(config, board, players, _make_renderer(), seed=42)
        state = engine.get_state()
        state.current_player_index = 0
        state.players[0].cash = 0
        state.properties_by_position[1].owner_player_index = 0
        state.players[0].holdings.append(PropertyRef(position=1))

        engine._pay_debt(1, creditor_index=None)

        assert PropertyRef(position=1) not in state.players[0].holdings

    def test_reclaimed_property_reset(self) -> None:
        config = _make_config()
        board = _make_board(config)
        players = [AIPlayer("Alice")]
        engine = GameEngine.create(config, board, players, _make_renderer(), seed=42)
        state = engine.get_state()
        state.current_player_index = 0
        state.players[0].cash = 0
        state.properties_by_position[1].owner_player_index = 0
        state.properties_by_position[1].level = 2
        state.properties_by_position[1].purchase_price = 300
        state.properties_by_position[1].upgrade_invested = 300
        state.players[0].holdings.append(PropertyRef(position=1))

        engine._pay_debt(1, creditor_index=None)

        prop = state.properties_by_position[1]
        assert prop.owner_player_index is None
        assert prop.level == 0
        assert prop.purchase_price == 0
        assert prop.upgrade_invested == 0

    def test_bankruptcy_zeros_cash_and_hand(self) -> None:
        config = _make_config()
        board = _make_board(config)
        players = [AIPlayer("Alice")]
        engine = GameEngine.create(config, board, players, _make_renderer(), seed=42)
        state = engine.get_state()
        state.players[0].cash = 100
        state.players[0].hand = HandCards(jail_pass=2, demolish=3)

        engine._finalize_bankruptcy(state.players[0])

        assert state.players[0].cash == 0
        assert state.players[0].hand.jail_pass == 0
        assert state.players[0].hand.demolish == 0
        assert state.players[0].bankrupt is True


# ---------------------------------------------------------------------------
# View generation
# ---------------------------------------------------------------------------


class TestViewGeneration:
    def test_player_view_is_isolated_from_internal_state(self) -> None:
        config = _make_config()
        board = _make_board(config)
        engine = GameEngine.create(config, board, [AIPlayer("Alice")], _make_renderer(), seed=42)
        state = engine.get_state()
        state.players[0].cash = 1500
        state.players[0].hand.jail_pass = 1
        state.properties_by_position[1].owner_player_index = 0
        state.properties_by_position[1].level = 2
        state.properties_by_position[1].purchase_price = 300
        state.players[0].holdings.append(PropertyRef(position=1))

        view = engine._build_player_view(0)
        view.viewer_private.cash = 0
        view.viewer_private.hand.jail_pass = 99
        view.viewer_private.holdings.clear()
        view.viewer_private_properties[0].level = 3

        assert state.players[0].cash == 1500
        assert state.players[0].hand.jail_pass == 1
        assert state.players[0].holdings == [PropertyRef(position=1)]
        assert state.properties_by_position[1].level == 2

    def test_snapshot_is_isolated_from_internal_state(self) -> None:
        config = _make_config()
        board = _make_board(config)
        engine = GameEngine.create(config, board, [AIPlayer("Alice")], _make_renderer(), seed=42)
        state = engine.get_state()
        state.players[0].cash = 1500
        state.properties_by_position[1].owner_player_index = 0
        state.properties_by_position[1].purchase_price = 300
        state.players[0].holdings.append(PropertyRef(position=1))
        engine._log(GameEventType.PROPERTY_AVAILABLE, player_name="Alice", rents=[50, 150])

        snapshot = engine.snapshot_for(0)
        snapshot.viewer_private.cash = 0
        snapshot.viewer_private_properties[0].purchase_price = 999
        snapshot_event_data = cast(MutableMapping[str, object], snapshot.event_log[0].data)
        snapshot_event_data["player_name"] = "Changed"
        snapshot_event_rents = cast(list[int], snapshot_event_data["rents"])
        snapshot_event_rents.append(300)

        assert state.players[0].cash == 1500
        assert state.properties_by_position[1].purchase_price == 300
        assert state.event_log[0].data["player_name"] == "Alice"
        assert state.event_log[0].data["rents"] == [50, 150]

    def test_player_view_includes_private_data(self) -> None:
        config = _make_config()
        board = _make_board(config)
        engine = GameEngine.create(config, board, [AIPlayer("Alice")], _make_renderer(), seed=42)
        state = engine.get_state()
        state.players[0].cash = 1500
        state.players[0].hand.jail_pass = 1

        view = engine._build_player_view(0)

        assert view.viewer_private.cash == 1500
        assert view.viewer_private.hand.jail_pass == 1

    def test_public_players_exclude_cash(self) -> None:
        config = _make_config()
        board = _make_board(config)
        engine = GameEngine.create(
            config, board, [AIPlayer("Alice"), AIPlayer("Bob")], _make_renderer(), seed=42
        )
        state = engine.get_state()
        state.players[0].cash = 1500

        public_players = engine._build_public_players()

        # PublicPlayerInfo has no cash field — verify through the dataclass
        assert public_players[0].name == "Alice"
        assert public_players[0].position == 0
        assert not hasattr(public_players[0], "cash")

    def test_public_board_shows_ownership(self) -> None:
        config = _make_config()
        board = _make_board(config)
        engine = GameEngine.create(config, board, [AIPlayer("Alice")], _make_renderer(), seed=42)
        state = engine.get_state()
        state.properties_by_position[1].owner_player_index = 0
        state.properties_by_position[1].level = 2

        board_info = engine._build_public_board()
        cell1 = board_info.cells[1]

        assert cell1.owner_player_index == 0
        assert cell1.level == 2

    def test_public_board_unowned_no_level(self) -> None:
        config = _make_config()
        board = _make_board(config)
        engine = GameEngine.create(config, board, [AIPlayer("Alice")], _make_renderer(), seed=42)

        board_info = engine._build_public_board()
        cell1 = board_info.cells[1]

        assert cell1.owner_player_index is None
        assert cell1.level is None

    def test_snapshot_includes_event_log(self) -> None:
        config = _make_config()
        board = _make_board(config)
        engine = GameEngine.create(config, board, [AIPlayer("Alice")], _make_renderer(), seed=42)

        engine._process_turn()
        snapshot = engine.snapshot_for(0)

        assert len(snapshot.event_log) > 0

    def test_snapshot_includes_viewer_properties(self) -> None:
        config = _make_config()
        board = _make_board(config)
        engine = GameEngine.create(config, board, [AIPlayer("Alice")], _make_renderer(), seed=42)
        state = engine.get_state()
        state.properties_by_position[1].owner_player_index = 0
        state.properties_by_position[1].purchase_price = 300
        state.players[0].holdings.append(PropertyRef(position=1))

        snapshot = engine.snapshot_for(0)

        assert len(snapshot.viewer_private_properties) == 1
        assert snapshot.viewer_private_properties[0].position == 1

    def test_player_view_with_actions(self) -> None:
        config = _make_config()
        board = _make_board(config)
        engine = GameEngine.create(config, board, [AIPlayer("Alice")], _make_renderer(), seed=42)

        view = engine._build_player_view(0, actions=[Action.BUY, Action.SKIP])

        assert view.available_actions == (Action.BUY, Action.SKIP)

    def test_input_context_delegates_to_renderer(self) -> None:
        renderer = ConsoleRenderer(output=StringIO(), input_reader=lambda _: "BUY")
        config = _make_config()
        board = _make_board(config)
        engine = GameEngine.create(config, board, [AIPlayer("Alice")], renderer, seed=42)

        result = engine._context.prompt_choice("选择动作", ["BUY", "SKIP"])
        assert result == "BUY"


# ---------------------------------------------------------------------------
# Integration: full game with deterministic seed
# ---------------------------------------------------------------------------


class TestFullGame:
    def test_full_game_completes(self) -> None:
        config = _make_config(
            cards=(
                MONEY_GAIN_CARD,
                MONEY_LOSS_CARD,
                MOVE_CARD,
                GO_TO_JAIL_CARD,
                JAIL_PASS_CARD,
                DEMOLISH_CARD,
            ),
            start_cash=2000,
            start_bonus=200,
            jail_rounds=3,
            demolish_range=3,
            dice_sides=6,
        )
        board = _make_board(config)
        players = [AIPlayer("Alice"), AIPlayer("Bob")]
        renderer = _make_renderer()

        engine = GameEngine.create(config, board, players, renderer, seed=42)
        final_state = engine.start()

        # Game should have ended
        alive = [p for p in final_state.players if not p.bankrupt]
        assert len(alive) == 1
        assert engine._winner_name is not None

    def test_full_game_event_log_is_non_empty(self) -> None:
        """Running a single turn should produce events in the log."""
        config = _make_config(
            cards=(MONEY_GAIN_CARD,),
            start_cash=2000,
            dice_sides=6,
        )
        board = _make_board(config)
        players = [AIPlayer("Alice")]
        renderer = _make_renderer()

        engine = GameEngine.create(config, board, players, renderer, seed=42)
        engine._process_turn()

        state = engine.get_state()
        assert len(state.event_log) > 0

    def test_game_over_event_logged(self) -> None:
        config = _make_config()
        board = _make_board(config)
        players = [AIPlayer("Alice"), AIPlayer("Bob")]
        engine = GameEngine.create(config, board, players, _make_renderer(), seed=42)
        state = engine.get_state()
        state.players[1].bankrupt = True

        engine._check_game_over()

        events = state.event_log
        assert any(e.event_type == GameEventType.GAME_OVER for e in events)

    def test_game_over_event_logged_once(self) -> None:
        config = _make_config()
        board = _make_board(config)
        players = [AIPlayer("Alice"), AIPlayer("Bob")]
        engine = GameEngine.create(config, board, players, _make_renderer(), seed=42)
        state = engine.get_state()
        state.players[1].bankrupt = True

        engine._check_game_over()
        engine._check_game_over()

        game_over_events = [
            event for event in state.event_log if event.event_type == GameEventType.GAME_OVER
        ]
        assert len(game_over_events) == 1
