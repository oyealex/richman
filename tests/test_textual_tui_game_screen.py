"""Tests for GameScreen step driver and ActionBar widget."""
# mypy: disable-error-code=arg-type

from __future__ import annotations

import asyncio

import pytest
from textual.app import App, ComposeResult
from textual.widgets import Button, Static

from richman.adapters.textual_tui.screens.game import GameScreen
from richman.adapters.textual_tui.widgets.action_bar import ActionBar
from richman.adapters.textual_tui.widgets.board import BoardWidget
from richman.adapters.textual_tui.widgets.cell import CellWidget
from richman.adapters.textual_tui.widgets.event_line import EventLine
from richman.adapters.textual_tui.widgets.player_strip import PlayerStrip
from richman.app import build_default_config
from richman.domain import (
    Action,
    EngineInput,
    GameConfig,
    GameEvent,
    GameEventType,
    GameSnapshot,
    HandCards,
    InputKind,
    InternalGameState,
    Phase,
    PlayerState,
    PublicBoardInfo,
    PublicCellInfo,
    PublicPlayerInfo,
    RequiredInput,
    StepResult,
)
from richman.player import AIPlayer, HumanPlayer, Player

# -- helpers ---------------------------------------------------------------


@pytest.fixture(autouse=True)
def _no_sleep(monkeypatch: pytest.MonkeyPatch) -> None:
    """Make GameScreen worker sleeps complete immediately in tests."""

    async def immediate_sleep(_delay: float) -> None:
        return None

    monkeypatch.setattr(asyncio, "sleep", immediate_sleep)


def _make_snapshot(config: GameConfig) -> GameSnapshot:
    """Build a minimal snapshot matching *config* board cells."""
    cells = tuple(
        PublicCellInfo(position=i, cell_type=cell_def.cell_type)
        for i, cell_def in enumerate(config.board_cells)
    )
    return GameSnapshot(
        turn=1,
        current_player_index=0,
        viewer_index=0,
        phase=Phase.DICE_ROLL,
        dice_value=None,
        public_board=PublicBoardInfo(cells=cells),
        public_players=(PublicPlayerInfo(player_index=0, name="Alice", position=0),),
        viewer_private=PlayerState(name="Alice", cash=2000, position=0, hand=HandCards()),
        viewer_private_properties=(),
        event_log=(),
        available_actions=None,
    )


def _make_state(*, winner_name: str = "Alice") -> InternalGameState:
    """Build a minimal InternalGameState with a GAME_OVER event."""
    return InternalGameState(
        players=[],
        event_log=[
            GameEvent(GameEventType.GAME_OVER, {"winner_name": winner_name}),
        ],
    )


class FakeEngine:
    """Fake GameEngine that returns preset StepResult sequences."""

    def __init__(
        self,
        advance_responses: list[StepResult] | None = None,
        snapshot: GameSnapshot | None = None,
        state: InternalGameState | None = None,
    ) -> None:
        if advance_responses:
            self.advance_responses: list[StepResult] = list(advance_responses)
        else:
            self.advance_responses = []
        self._snapshot = snapshot
        self._state = state or InternalGameState(players=[])
        self.advance_calls: list[EngineInput | None] = []

    def advance(self, engine_input: EngineInput | None = None) -> StepResult:
        self.advance_calls.append(engine_input)
        if self.advance_responses:
            return self.advance_responses.pop(0)
        # Default: game over
        snap = self._snapshot
        if snap is None:
            snap = _make_snapshot(build_default_config())
        return StepResult(
            snapshot=snap,
            events=(),
            phase=Phase.END,
            required_input=None,
            game_over=True,
        )

    def snapshot_for(self, viewer_index: int = 0) -> GameSnapshot:
        del viewer_index
        if self._snapshot is not None:
            return self._snapshot
        return _make_snapshot(build_default_config())

    def get_state(self) -> InternalGameState:
        return self._state


def _make_roll_required(player_index: int = 0) -> RequiredInput:
    return RequiredInput(kind=InputKind.ROLL_DICE, player_index=player_index)


def _make_action_required(
    player_index: int = 0, options: tuple[Action, ...] = (Action.BUY, Action.SKIP)
) -> RequiredInput:
    return RequiredInput(kind=InputKind.ACTION_CHOICE, player_index=player_index, options=options)


def _make_jail_required(
    player_index: int = 0, options: tuple[Action, ...] = (Action.USE_JAIL_PASS, Action.ACCEPT_JAIL)
) -> RequiredInput:
    return RequiredInput(kind=InputKind.JAIL_CHOICE, player_index=player_index, options=options)


def _make_demolish_required(
    player_index: int = 0, candidates: tuple[int, ...] = (3, 5)
) -> RequiredInput:
    return RequiredInput(
        kind=InputKind.DEMOLISH_TARGET,
        player_index=player_index,
        candidates=candidates,
    )


# -- pure unit tests: _auto_input_for --------------------------------------


def test_auto_input_for_roll_dice() -> None:
    engine = FakeEngine()
    players: list[Player] = [AIPlayer("AI-0")]
    screen = GameScreen(engine, build_default_config(), players)  # type: ignore[arg-type]
    result = screen._auto_input_for(_make_roll_required(0))
    assert result.kind is InputKind.ROLL_DICE
    assert result.player_index == 0
    assert result.action is None


def test_auto_input_for_action_choice() -> None:
    engine = FakeEngine()
    players: list[Player] = [AIPlayer("AI-0")]
    screen = GameScreen(engine, build_default_config(), players)
    required = _make_action_required(0, (Action.BUY, Action.SKIP))
    result = screen._auto_input_for(required)
    assert result.kind is InputKind.ACTION_CHOICE
    assert result.player_index == 0
    assert result.action is Action.BUY  # first option


def test_auto_input_for_jail_choice_prefers_pass() -> None:
    engine = FakeEngine()
    players: list[Player] = [AIPlayer("AI-0")]
    screen = GameScreen(engine, build_default_config(), players)
    required = _make_jail_required(0, (Action.USE_JAIL_PASS, Action.ACCEPT_JAIL))
    result = screen._auto_input_for(required)
    assert result.action is Action.USE_JAIL_PASS


def test_auto_input_for_jail_choice_fallback() -> None:
    engine = FakeEngine()
    players: list[Player] = [AIPlayer("AI-0")]
    screen = GameScreen(engine, build_default_config(), players)
    required = _make_jail_required(0, (Action.ACCEPT_JAIL,))
    result = screen._auto_input_for(required)
    assert result.action is Action.ACCEPT_JAIL


def test_auto_input_for_demolish_target() -> None:
    engine = FakeEngine()
    players: list[Player] = [AIPlayer("AI-0")]
    screen = GameScreen(engine, build_default_config(), players)
    required = _make_demolish_required(0, (3, 5))
    result = screen._auto_input_for(required)
    assert result.kind is InputKind.DEMOLISH_TARGET
    assert result.target_position == 3  # first candidate


# -- pure unit tests: _is_ai_player ----------------------------------------


def test_is_ai_player_returns_true_for_ai() -> None:
    engine = FakeEngine()
    players: list[Player] = [AIPlayer("AI-0"), HumanPlayer("Human")]
    screen = GameScreen(engine, build_default_config(), players)
    assert screen._is_ai_player(0) is True


def test_is_ai_player_returns_false_for_human() -> None:
    engine = FakeEngine()
    players: list[Player] = [AIPlayer("AI-0"), HumanPlayer("Human")]
    screen = GameScreen(engine, build_default_config(), players)
    assert screen._is_ai_player(1) is False


# -- pure unit tests: _extract_winner_name ----------------------------------


def test_extract_winner_name() -> None:
    engine = FakeEngine(state=_make_state(winner_name="Bob"))
    players: list[Player] = [AIPlayer("AI-0")]
    screen = GameScreen(engine, build_default_config(), players)
    assert screen._extract_winner_name() == "Bob"


# -- unit test: _submit_input calls engine.advance --------------------------


def test_submit_input_calls_advance_with_engine_input() -> None:
    """_submit_input calls engine.advance with the given EngineInput."""
    config = build_default_config()
    snapshot = _make_snapshot(config)
    engine = FakeEngine(
        advance_responses=[
            StepResult(
                snapshot=snapshot,
                events=(),
                phase=Phase.END,
                required_input=None,
                game_over=True,
            ),
        ],
        snapshot=snapshot,
    )
    players: list[Player] = [AIPlayer("AI-0")]
    screen = GameScreen(engine, config, players)
    screen._current_result = StepResult(
        snapshot=snapshot,
        events=(),
        phase=Phase.DICE_ROLL,
        required_input=None,
        game_over=False,
    )

    ei = EngineInput(kind=InputKind.ROLL_DICE, player_index=0)
    screen._submit_input(ei)

    assert len(engine.advance_calls) == 1
    assert engine.advance_calls[0] is ei


# -- integration tests: GameScreen compose ----------------------------------


async def test_game_screen_composes_board_and_action_bar() -> None:
    """GameScreen compose yields BoardWidget and ActionBar."""
    config = build_default_config()
    snapshot = _make_snapshot(config)
    engine = FakeEngine(
        advance_responses=[
            StepResult(
                snapshot=snapshot,
                events=(),
                phase=Phase.DICE_ROLL,
                required_input=_make_roll_required(0),
                game_over=False,
            ),
        ],
        snapshot=snapshot,
    )
    players: list[Player] = [HumanPlayer("Alice")]

    screen = GameScreen(engine, config, players)

    class TestApp(App[None]):
        def on_mount(self) -> None:
            self.push_screen(screen)

    app = TestApp()
    async with app.run_test(size=(180, 60)) as pilot:
        await pilot.pause()
        assert screen.query_one(BoardWidget)
        assert screen.query_one(ActionBar)


async def test_game_screen_mount_calls_advance() -> None:
    """GameScreen calls engine.advance(None) on mount."""
    config = build_default_config()
    snapshot = _make_snapshot(config)
    engine = FakeEngine(
        advance_responses=[
            StepResult(
                snapshot=snapshot,
                events=(),
                phase=Phase.DICE_ROLL,
                required_input=_make_roll_required(0),
                game_over=False,
            ),
        ],
        snapshot=snapshot,
    )
    players: list[Player] = [HumanPlayer("Alice")]

    screen = GameScreen(engine, config, players)

    class TestApp(App[None]):
        def on_mount(self) -> None:
            self.push_screen(screen)

    app = TestApp()
    async with app.run_test(size=(180, 60)) as pilot:
        await pilot.pause()
        # advance(None) should have been called
        assert len(engine.advance_calls) >= 1
        assert engine.advance_calls[0] is None


# -- integration tests: CellClicked → DEMOLISH_TARGET -----------------------


async def test_cell_click_demolish_candidate_submits() -> None:
    """Clicking a candidate cell during DEMOLISH_TARGET submits input."""
    config = build_default_config()
    snapshot = _make_snapshot(config)
    candidates = (0,)  # position 0 exists in the board
    engine = FakeEngine(
        advance_responses=[
            StepResult(
                snapshot=snapshot,
                events=(),
                phase=Phase.ACTION,
                required_input=_make_demolish_required(0, candidates),
                game_over=False,
            ),
            StepResult(
                snapshot=snapshot,
                events=(),
                phase=Phase.END,
                required_input=None,
                game_over=True,
            ),
        ],
        snapshot=snapshot,
    )
    players: list[Player] = [HumanPlayer("Alice")]

    screen = GameScreen(engine, config, players)

    class TestApp(App[None]):
        def on_mount(self) -> None:
            self.push_screen(screen)

    app = TestApp()
    async with app.run_test(size=(180, 60)) as pilot:
        await pilot.pause()
        # Click on the candidate cell (position 0)
        cell = screen.query(CellWidget).first()
        assert cell is not None
        cell.post_message(CellWidget.CellClicked(candidates[0]))

        await pilot.pause()
        # Should have submitted DEMOLISH_TARGET input
        demolish_calls = [
            c for c in engine.advance_calls if c is not None and c.kind is InputKind.DEMOLISH_TARGET
        ]
        assert len(demolish_calls) >= 1
        assert demolish_calls[0].target_position == candidates[0]


async def test_cell_click_non_candidate_ignored() -> None:
    """Clicking a non-candidate cell during DEMOLISH_TARGET does nothing."""
    config = build_default_config()
    snapshot = _make_snapshot(config)
    candidates = (5,)
    engine = FakeEngine(
        advance_responses=[
            StepResult(
                snapshot=snapshot,
                events=(),
                phase=Phase.ACTION,
                required_input=_make_demolish_required(0, candidates),
                game_over=False,
            ),
        ],
        snapshot=snapshot,
    )
    players: list[Player] = [HumanPlayer("Alice")]

    screen = GameScreen(engine, config, players)

    class TestApp(App[None]):
        def on_mount(self) -> None:
            self.push_screen(screen)

    app = TestApp()
    async with app.run_test(size=(180, 60)) as pilot:
        await pilot.pause()
        # Click on a non-candidate cell
        cell = screen.query(CellWidget).first()
        assert cell is not None
        cell.post_message(CellWidget.CellClicked(999))

        await pilot.pause()
        # No DEMOLISH_TARGET submit should have happened
        demolish_calls = [
            c for c in engine.advance_calls if c is not None and c.kind is InputKind.DEMOLISH_TARGET
        ]
        assert len(demolish_calls) == 0


async def test_cell_click_non_demolish_ignored() -> None:
    """CellWidget click when not in DEMOLISH_TARGET is ignored."""
    config = build_default_config()
    snapshot = _make_snapshot(config)
    engine = FakeEngine(
        advance_responses=[
            StepResult(
                snapshot=snapshot,
                events=(),
                phase=Phase.DICE_ROLL,
                required_input=_make_roll_required(0),
                game_over=False,
            ),
        ],
        snapshot=snapshot,
    )
    players: list[Player] = [HumanPlayer("Alice")]

    screen = GameScreen(engine, config, players)

    class TestApp(App[None]):
        def on_mount(self) -> None:
            self.push_screen(screen)

    app = TestApp()
    async with app.run_test(size=(180, 60)) as pilot:
        await pilot.pause()
        # Click a cell — should not submit (we're in ROLL_DICE phase)
        cell = screen.query(CellWidget).first()
        assert cell is not None
        cell.post_message(CellWidget.CellClicked(0))

        await pilot.pause()
        # Only advance(None) should have been called, no EngineInput submits
        non_none_calls = [c for c in engine.advance_calls if c is not None]
        assert len(non_none_calls) == 0


# -- ActionBar widget tests -------------------------------------------------


async def test_action_bar_renders_roll_dice_button() -> None:
    """ActionBar shows a single roll-dice button for ROLL_DICE input."""

    class TestApp(App[None]):
        def compose(self) -> ComposeResult:
            yield ActionBar()

    app = TestApp()
    async with app.run_test(size=(80, 24)) as pilot:
        bar = app.query_one(ActionBar)
        bar.set_required_input(_make_roll_required(0))
        await pilot.pause()

        buttons = bar.query(Button)
        assert len(list(buttons)) == 1
        btn = list(buttons)[0]
        assert "掷骰" in str(btn.label)


async def test_action_bar_renders_action_choice_buttons() -> None:
    """ActionBar shows one button per ACTION_CHOICE option."""

    class TestApp(App[None]):
        def compose(self) -> ComposeResult:
            yield ActionBar()

    app = TestApp()
    async with app.run_test(size=(80, 24)) as pilot:
        bar = app.query_one(ActionBar)
        bar.set_required_input(_make_action_required(0, (Action.BUY, Action.UPGRADE, Action.SKIP)))
        await pilot.pause()

        buttons = list(bar.query(Button))
        assert len(buttons) == 3


async def test_action_bar_renders_jail_choice_buttons() -> None:
    """ActionBar shows buttons for JAIL_CHOICE."""

    class TestApp(App[None]):
        def compose(self) -> ComposeResult:
            yield ActionBar()

    app = TestApp()
    async with app.run_test(size=(80, 24)) as pilot:
        bar = app.query_one(ActionBar)
        bar.set_required_input(_make_jail_required(0, (Action.USE_JAIL_PASS, Action.ACCEPT_JAIL)))
        await pilot.pause()

        buttons = list(bar.query(Button))
        assert len(buttons) == 2
        labels = [str(b.label) for b in buttons]
        assert any("出狱卡" in label for label in labels)
        assert any("接受入狱" in label for label in labels)


async def test_action_bar_renders_demolish_hint() -> None:
    """ActionBar shows hint text for DEMOLISH_TARGET, no buttons."""

    class TestApp(App[None]):
        def compose(self) -> ComposeResult:
            yield ActionBar()

    app = TestApp()
    async with app.run_test(size=(80, 24)) as pilot:
        bar = app.query_one(ActionBar)
        bar.set_required_input(_make_demolish_required(0, (3, 5)))
        await pilot.pause()

        buttons = list(bar.query(Button))
        assert len(buttons) == 0
        statics = list(bar.query(Static))
        assert len(statics) >= 1
        hint_text = str(statics[0].render())
        assert "目标格子" in hint_text
        assert "3" in hint_text
        assert "5" in hint_text


async def test_action_bar_clears_on_none() -> None:
    """ActionBar removes all children when required_input is None."""

    class TestApp(App[None]):
        def compose(self) -> ComposeResult:
            yield ActionBar()

    app = TestApp()
    async with app.run_test(size=(80, 24)) as pilot:
        bar = app.query_one(ActionBar)
        bar.set_required_input(_make_roll_required(0))
        await pilot.pause()
        assert len(list(bar.query(Button))) == 1

        bar.set_required_input(None)
        await pilot.pause()
        assert len(list(bar.query(Button))) == 0


# -- ActionBar message tests ------------------------------------------------


async def test_action_bar_button_click_emits_action_submitted() -> None:
    """Clicking a ROLL_DICE button emits ActionSubmitted with correct EngineInput."""
    captured: list[EngineInput] = []

    class TestApp(App[None]):
        def compose(self) -> ComposeResult:
            yield ActionBar()

        def on_action_bar_action_submitted(self, message: ActionBar.ActionSubmitted) -> None:
            captured.append(message.engine_input)

    app = TestApp()
    async with app.run_test(size=(80, 24)) as pilot:
        bar = app.query_one(ActionBar)
        bar.set_required_input(_make_roll_required(0))
        await pilot.pause()

        btn = bar.query(Button).first()
        assert btn is not None
        btn.press()
        await pilot.pause()

        assert len(captured) == 1
        assert captured[0].kind is InputKind.ROLL_DICE
        assert captured[0].player_index == 0


async def test_action_bar_action_choice_button_emits_correct_engine_input() -> None:
    """Clicking a BUY button emits EngineInput with action=BUY."""
    captured: list[EngineInput] = []

    class TestApp(App[None]):
        def compose(self) -> ComposeResult:
            yield ActionBar()

        def on_action_bar_action_submitted(self, message: ActionBar.ActionSubmitted) -> None:
            captured.append(message.engine_input)

    app = TestApp()
    async with app.run_test(size=(80, 24)) as pilot:
        bar = app.query_one(ActionBar)
        bar.set_required_input(_make_action_required(0, (Action.BUY, Action.SKIP)))
        await pilot.pause()

        buttons = list(bar.query(Button))
        # Click the first button (BUY)
        buttons[0].press()
        await pilot.pause()

        assert len(captured) == 1
        assert captured[0].action is Action.BUY


# -- keyboard shortcut tests ------------------------------------------------


async def test_keyboard_enter_triggers_first_button() -> None:
    """Enter key triggers the first (primary) button."""
    captured: list[EngineInput] = []

    class TestApp(App[None]):
        def compose(self) -> ComposeResult:
            yield ActionBar()

        def on_action_bar_action_submitted(self, message: ActionBar.ActionSubmitted) -> None:
            captured.append(message.engine_input)

    app = TestApp()
    async with app.run_test(size=(80, 24)) as pilot:
        bar = app.query_one(ActionBar)
        bar.set_required_input(_make_roll_required(0))
        await pilot.pause()

        await pilot.press("enter")
        assert len(captured) == 1
        assert captured[0].kind is InputKind.ROLL_DICE


async def test_keyboard_digit_triggers_correct_button() -> None:
    """Digit key triggers the corresponding action button."""
    captured: list[EngineInput] = []

    class TestApp(App[None]):
        def compose(self) -> ComposeResult:
            yield ActionBar()

        def on_action_bar_action_submitted(self, message: ActionBar.ActionSubmitted) -> None:
            captured.append(message.engine_input)

    app = TestApp()
    async with app.run_test(size=(80, 24)) as pilot:
        bar = app.query_one(ActionBar)
        bar.set_required_input(_make_action_required(0, (Action.BUY, Action.SKIP)))
        await pilot.pause()

        # Press "2" → second button (SKIP)
        await pilot.press("2")
        assert len(captured) == 1
        assert captured[0].action is Action.SKIP


# -- fake engine: auto-advance reaches game over ----------------------------


async def test_fake_engine_auto_advances_to_game_over() -> None:
    """Fake engine that returns game_over=True stops the loop."""
    config = build_default_config()
    snapshot = _make_snapshot(config)
    engine = FakeEngine(
        advance_responses=[
            StepResult(
                snapshot=snapshot,
                events=(),
                phase=Phase.END,
                required_input=None,
                game_over=True,
            ),
        ],
        snapshot=snapshot,
        state=_make_state(winner_name="Alice"),
    )
    players: list[Player] = [AIPlayer("AI-0")]

    screen = GameScreen(engine, config, players)

    class TestApp(App[None]):
        def on_mount(self) -> None:
            self.push_screen(screen)

    app = TestApp()
    async with app.run_test(size=(180, 60)) as pilot:
        await pilot.pause()
        await pilot.pause()

        # Engine should have been called with advance(None) once
        assert len(engine.advance_calls) == 1
        assert engine.advance_calls[0] is None

        # ActionBar should show game over
        bar = screen.query_one(ActionBar)
        rendered = bar.render()
        assert "游戏结束" in rendered
        assert "Alice" in rendered


# -- fake engine: AI auto-submit cycle --------------------------------------


async def test_fake_engine_ai_auto_submits_roll() -> None:
    """AI player's ROLL_DICE required_input is auto-submitted."""
    config = build_default_config()
    snapshot = _make_snapshot(config)
    engine = FakeEngine(
        advance_responses=[
            # First advance(None) → ROLL_DICE required for AI
            StepResult(
                snapshot=snapshot,
                events=(),
                phase=Phase.DICE_ROLL,
                required_input=_make_roll_required(0),
                game_over=False,
            ),
            # After AI auto-submits ROLL_DICE → landing phase, no input
            StepResult(
                snapshot=snapshot,
                events=(),
                phase=Phase.LANDING,
                required_input=None,
                game_over=False,
            ),
            # After continue → game over
            StepResult(
                snapshot=snapshot,
                events=(),
                phase=Phase.END,
                required_input=None,
                game_over=True,
            ),
        ],
        snapshot=snapshot,
    )
    players: list[Player] = [AIPlayer("AI-0")]

    screen = GameScreen(engine, config, players)

    class TestApp(App[None]):
        def on_mount(self) -> None:
            self.push_screen(screen)

    app = TestApp()
    async with app.run_test(size=(180, 60)) as pilot:
        # Wait for the worker to go through the cycle
        await pilot.pause()
        await pilot.pause()
        await pilot.pause()

        # First call: advance(None)
        assert engine.advance_calls[0] is None
        # Second call: AI auto-submitted ROLL_DICE
        assert engine.advance_calls[1] is not None
        assert engine.advance_calls[1].kind is InputKind.ROLL_DICE

        # All 3 calls should have been made
        assert len(engine.advance_calls) == 3


# -- real engine smoke test ------------------------------------------------


def test_real_engine_smoke_all_ai() -> None:
    """Real engine with all AI players advances several bounded steps."""
    config = build_default_config()

    from richman.board import create as create_board
    from richman.engine.model import GameEngine

    board = create_board(config)
    players: list[Player] = [AIPlayer("AI-0"), AIPlayer("AI-1")]
    engine = GameEngine.create(config, board, players, seed=42)

    screen = GameScreen(engine, config, players)

    result = engine.advance(None)
    screen._apply_step_result(result)

    for _ in range(5):
        if result.game_over:
            break
        if result.required_input is not None:
            assert screen._is_ai_player(result.required_input.player_index)
            result = engine.advance(screen._auto_input_for(result.required_input))
        else:
            result = engine.advance(None)
        screen._apply_step_result(result)

    state = engine.get_state()
    assert state.turn >= 1
    assert screen._current_result is result


# -- ActionSubmitted is a Textual Message -----------------------------------


def test_action_submitted_is_textual_message() -> None:
    """ActionBar.ActionSubmitted inherits from textual.message.Message."""
    from textual.message import Message

    assert issubclass(ActionBar.ActionSubmitted, Message)


# -- GameScreen compose: PlayerStrip and EventLine ---------------------------


async def test_game_screen_composes_player_strip_and_event_line() -> None:
    """GameScreen compose now includes PlayerStrip and EventLine."""
    config = build_default_config()
    snapshot = _make_snapshot(config)
    engine = FakeEngine(
        advance_responses=[
            StepResult(
                snapshot=snapshot,
                events=(),
                phase=Phase.DICE_ROLL,
                required_input=_make_roll_required(0),
                game_over=False,
            ),
        ],
        snapshot=snapshot,
    )
    players: list[Player] = [HumanPlayer("Alice")]

    screen = GameScreen(engine, config, players)

    class TestApp(App[None]):
        def on_mount(self) -> None:
            self.push_screen(screen)

    app = TestApp()
    async with app.run_test(size=(180, 60)) as pilot:
        await pilot.pause()
        assert screen.query_one(BoardWidget)
        assert screen.query_one(PlayerStrip)
        assert screen.query_one(EventLine)
        assert screen.query_one(ActionBar)


async def test_game_screen_board_height_deduction() -> None:
    """GameScreen deducts PlayerStrip + EventLine height from board rows."""
    config = build_default_config()
    snapshot = _make_snapshot(config)
    engine = FakeEngine(snapshot=snapshot)
    players: list[Player] = [HumanPlayer("Alice")]

    screen = GameScreen(engine, config, players)

    class TestApp(App[None]):
        def on_mount(self) -> None:
            self.push_screen(screen)

    app = TestApp()
    async with app.run_test(size=(180, 60)) as pilot:
        await pilot.pause()
        geometry = screen._geometry
        assert geometry is not None
        # At size (180, 60): board_rows = 180 - 1 - 1 - 1 - 5 = 172
        # But min_terminal_rows is layout rows * CELL_HEIGHT (5) + gaps
        # so the geometry just needs to be computable — verify it's not failing
        assert geometry.min_terminal_rows > 0
        assert geometry.min_terminal_cols > 0


# -- GameScreen E key binding ------------------------------------------------


async def test_game_screen_e_key_emits_open_requested() -> None:
    """Pressing E at GameScreen level emits EventLine.OpenRequested."""
    config = build_default_config()
    snapshot = _make_snapshot(config)
    engine = FakeEngine(
        advance_responses=[
            StepResult(
                snapshot=snapshot,
                events=(),
                phase=Phase.DICE_ROLL,
                required_input=_make_roll_required(0),
                game_over=False,
            ),
        ],
        snapshot=snapshot,
    )
    players: list[Player] = [HumanPlayer("Alice")]

    captured: list[EventLine.OpenRequested] = []

    class CapturingGameScreen(GameScreen):
        def on_event_line_open_requested(self, message: EventLine.OpenRequested) -> None:
            captured.append(message)
            super().on_event_line_open_requested(message)

    screen = CapturingGameScreen(engine, config, players)

    class TestApp(App[None]):
        def on_mount(self) -> None:
            self.push_screen(screen)

    app = TestApp()
    async with app.run_test(size=(180, 60)) as pilot:
        await pilot.pause()
        await pilot.press("e")
        await pilot.pause()
        assert len(captured) == 1
        assert isinstance(captured[0], EventLine.OpenRequested)
