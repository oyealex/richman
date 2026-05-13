"""GameScreen — drives the GameEngine step API and renders the board."""

from __future__ import annotations

import asyncio
from collections.abc import Sequence

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header

from richman.adapters.textual_tui.layout import (
    TuiLayoutGeometry,
    compute_layout_geometry,
)
from richman.adapters.textual_tui.widgets.action_bar import ActionBar
from richman.adapters.textual_tui.widgets.board import BoardWidget
from richman.adapters.textual_tui.widgets.cell import CellWidget
from richman.adapters.textual_tui.widgets.event_line import EventLine
from richman.adapters.textual_tui.widgets.player_strip import PlayerStrip
from richman.domain import (
    Action,
    EngineInput,
    GameConfig,
    GameEventType,
    InputKind,
    RequiredInput,
    StepResult,
)
from richman.engine.model import GameEngine
from richman.player import AIPlayer, Player

_HEADER_HEIGHT = 1
_PLAYER_STRIP_HEIGHT = 1
_EVENT_LINE_HEIGHT = 1
_ACTION_BAR_HEIGHT = 5


class GameScreen(Screen[None]):
    """Drives the engine step API and renders board + action bar.

    Receives a pre-built engine, config, and the player controller list
    (used to detect AI vs human players).  The screen starts the advance
    loop on mount and yields to the user when human input is required.
    """

    DEFAULT_CSS = """
    GameScreen {
        layout: vertical;
    }
    """

    def __init__(
        self,
        engine: GameEngine,
        config: GameConfig,
        player_controllers: Sequence[Player],
    ) -> None:
        super().__init__()
        self._engine = engine
        self._config = config
        self._player_controllers = tuple(player_controllers)
        self._current_result: StepResult | None = None
        self._geometry: TuiLayoutGeometry | None = None

    # -- compose -----------------------------------------------------------

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)

        # Calculate board-available terminal size (subtract header + bars)
        board_rows = (
            self.size.height
            - _HEADER_HEIGHT
            - _PLAYER_STRIP_HEIGHT
            - _EVENT_LINE_HEIGHT
            - _ACTION_BAR_HEIGHT
        )
        board_cols = self.size.width
        board_terminal_size = (board_rows, board_cols)

        geometry = compute_layout_geometry(self._config, terminal_size=board_terminal_size)
        self._geometry = geometry

        snapshot = self._engine.snapshot_for(0)
        yield BoardWidget(snapshot, geometry, terminal_size=board_terminal_size)
        yield PlayerStrip(snapshot, self._player_controllers)
        yield EventLine(snapshot)
        yield ActionBar()

    # -- mount -------------------------------------------------------------

    def on_mount(self) -> None:
        self.run_worker(self._advance_loop(), exclusive=True)

    # -- advance loop ------------------------------------------------------

    async def _advance_loop(self) -> None:
        """Async worker: advance through non-input steps, stop on human input or game over."""
        while True:
            # Advance through steps that don't require input
            while True:
                result = self._engine.advance(None)
                self._apply_step_result(result)

                if result.game_over:
                    return
                if result.required_input is not None:
                    break
                await asyncio.sleep(0.3)

            # We have required input — check if AI or human
            if self._is_ai_player(result.required_input.player_index):
                engine_input = self._auto_input_for(result.required_input)
                result = self._engine.advance(engine_input)
                self._apply_step_result(result)
                if result.game_over:
                    return
                # Continue the outer loop (advance None again)
            else:
                # Human input needed — stop and wait for UI interaction
                return

    # -- step result application -------------------------------------------

    def _apply_step_result(self, result: StepResult) -> None:
        """Store result and refresh BoardWidget + ActionBar + PlayerStrip + EventLine."""
        self._current_result = result

        for board in self.query(BoardWidget):
            board.update_snapshot(result.snapshot)

        for player_strip in self.query(PlayerStrip):
            player_strip.update_snapshot(result.snapshot)

        for event_line in self.query(EventLine):
            event_line.update_snapshot(result.snapshot)

        for action_bar in self.query(ActionBar):
            if result.game_over:
                winner_name = self._extract_winner_name()
                action_bar.set_game_over(winner_name)
            else:
                action_bar.set_required_input(result.required_input)

    # -- AI detection ------------------------------------------------------

    def _is_ai_player(self, player_index: int) -> bool:
        return isinstance(self._player_controllers[player_index], AIPlayer)

    # -- AI auto-input -----------------------------------------------------

    def _auto_input_for(self, required: RequiredInput) -> EngineInput:
        """Build an EngineInput automatically for AI players."""
        if required.kind is InputKind.ROLL_DICE:
            return EngineInput(
                kind=InputKind.ROLL_DICE,
                player_index=required.player_index,
            )
        if required.kind is InputKind.ACTION_CHOICE:
            return EngineInput(
                kind=InputKind.ACTION_CHOICE,
                player_index=required.player_index,
                action=required.options[0],
            )
        if required.kind is InputKind.JAIL_CHOICE:
            action = (
                Action.USE_JAIL_PASS
                if Action.USE_JAIL_PASS in required.options
                else required.options[0]
            )
            return EngineInput(
                kind=InputKind.JAIL_CHOICE,
                player_index=required.player_index,
                action=action,
            )
        if required.kind is InputKind.DEMOLISH_TARGET:
            return EngineInput(
                kind=InputKind.DEMOLISH_TARGET,
                player_index=required.player_index,
                target_position=required.candidates[0],
            )
        raise ValueError(f"unsupported input kind for auto-input: {required.kind}")

    # -- human input submission --------------------------------------------

    def _submit_input(self, engine_input: EngineInput) -> None:
        """Advance the engine with user input, then continue auto-advancing."""
        result = self._engine.advance(engine_input)
        self._apply_step_result(result)
        if result.required_input is None and not result.game_over:
            self.run_worker(self._advance_loop(), exclusive=True)

    # -- BoardWidget click → DEMOLISH_TARGET --------------------------------

    def on_cell_widget_cell_clicked(self, message: CellWidget.CellClicked) -> None:
        """Handle cell clicks for DEMOLISH_TARGET input."""
        if self._current_result is None:
            return
        required = self._current_result.required_input
        if required is None or required.kind is not InputKind.DEMOLISH_TARGET:
            return
        if message.position in required.candidates:
            message.stop()
            self._submit_input(
                EngineInput(
                    kind=InputKind.DEMOLISH_TARGET,
                    player_index=required.player_index,
                    target_position=message.position,
                )
            )

    # -- ActionBar button → submit input -----------------------------------

    def on_action_bar_action_submitted(self, message: ActionBar.ActionSubmitted) -> None:
        """Handle action button presses from ActionBar."""
        message.stop()
        self._submit_input(message.engine_input)

    # -- EventLine message handlers ------------------------------------------

    def on_event_line_open_requested(self, message: EventLine.OpenRequested) -> None:
        """Handle OpenRequested from EventLine click or E key binding."""
        message.stop()
        # Future: push EventLogModal screen

    BINDINGS = [("e", "open_event_log", "事件日志")]

    # -- E key handler -------------------------------------------------------

    def action_open_event_log(self) -> None:
        """E key binding: post EventLine.OpenRequested at screen level."""
        self.post_message(EventLine.OpenRequested())

    # -- helpers -----------------------------------------------------------

    def _extract_winner_name(self) -> str | None:
        state = self._engine.get_state()
        for event in reversed(state.event_log):
            if event.event_type is GameEventType.GAME_OVER:
                return str(event.data.get("winner_name", "?"))
        return None
