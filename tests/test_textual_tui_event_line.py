"""Tests for EventLine widget."""
# mypy: disable-error-code=arg-type

from __future__ import annotations

from textual.app import App, ComposeResult
from textual.message import Message

from richman.adapters.textual_tui.widgets.event_line import EventLine
from richman.domain import (
    GameEvent,
    GameEventType,
    GameSnapshot,
    HandCards,
    Phase,
    PlayerState,
    PublicBoardInfo,
    PublicPlayerInfo,
)


def _make_snapshot(*, event_log: tuple[GameEvent, ...] = ()) -> GameSnapshot:
    return GameSnapshot(
        turn=1,
        current_player_index=0,
        viewer_index=0,
        phase=Phase.DICE_ROLL,
        dice_value=None,
        public_board=PublicBoardInfo(cells=()),
        public_players=(PublicPlayerInfo(player_index=0, name="Alice", position=0),),
        viewer_private=PlayerState(name="Alice", cash=2000, position=0, hand=HandCards()),
        viewer_private_properties=(),
        event_log=event_log,
        available_actions=None,
    )


# -- render tests -----------------------------------------------------------


async def test_event_line_renders_latest_event() -> None:
    """EventLine shows the last event from the log."""
    snapshot = _make_snapshot(
        event_log=(
            GameEvent(GameEventType.TURN_START, {"player_name": "Alice"}),
            GameEvent(GameEventType.DICE_ROLLED, {"player_name": "Alice", "value": 7}),
        )
    )

    class TestApp(App[None]):
        def compose(self) -> ComposeResult:
            yield EventLine(snapshot)

    app = TestApp()
    async with app.run_test(size=(120, 24)) as pilot:
        await pilot.pause()
        line = app.query_one(EventLine)
        rendered = line.render().plain
        assert "DICE_ROLLED" in rendered
        assert "Alice" in rendered


async def test_event_line_empty_log_shows_placeholder() -> None:
    """EventLine shows placeholder when no events."""
    snapshot = _make_snapshot(event_log=())

    class TestApp(App[None]):
        def compose(self) -> ComposeResult:
            yield EventLine(snapshot)

    app = TestApp()
    async with app.run_test(size=(120, 24)) as pilot:
        await pilot.pause()
        line = app.query_one(EventLine)
        rendered = line.render().plain
        assert "--" in rendered


# -- message tests ----------------------------------------------------------


async def test_event_line_click_emits_open_requested() -> None:
    """Clicking EventLine emits OpenRequested message."""
    captured: list[EventLine.OpenRequested] = []
    snapshot = _make_snapshot()

    class TestApp(App[None]):
        def compose(self) -> ComposeResult:
            yield EventLine(snapshot)

        def on_event_line_open_requested(self, message: EventLine.OpenRequested) -> None:
            captured.append(message)

    app = TestApp()
    async with app.run_test(size=(120, 24)) as pilot:
        await pilot.pause()
        line = app.query_one(EventLine)
        line.on_click()
        await pilot.pause()
        assert len(captured) == 1
        assert isinstance(captured[0], EventLine.OpenRequested)


async def test_open_requested_is_textual_message() -> None:
    """EventLine.OpenRequested inherits from textual.message.Message."""
    assert issubclass(EventLine.OpenRequested, Message)


# -- update tests ------------------------------------------------------------


async def test_event_line_updates_on_snapshot_change() -> None:
    """EventLine refreshes when snapshot changes with new event."""
    snapshot1 = _make_snapshot(
        event_log=(GameEvent(GameEventType.TURN_START, {"player_name": "Alice"}),)
    )

    class TestApp(App[None]):
        def compose(self) -> ComposeResult:
            yield EventLine(snapshot1)

    app = TestApp()
    async with app.run_test(size=(120, 24)) as pilot:
        await pilot.pause()
        line = app.query_one(EventLine)
        assert "TURN_START" in line.render().plain

        # New event arrives
        snapshot2 = _make_snapshot(
            event_log=(
                GameEvent(GameEventType.TURN_START, {"player_name": "Alice"}),
                GameEvent(GameEventType.PLAYER_MOVED, {"player_name": "Alice"}),
            )
        )
        line.update_snapshot(snapshot2)
        await pilot.pause()
        rendered = line.render().plain
        assert "PLAYER_MOVED" in rendered
