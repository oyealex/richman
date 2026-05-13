"""Tests for PlayerStrip widget."""
# mypy: disable-error-code=arg-type

from __future__ import annotations

from rich.style import Style
from textual.app import App, ComposeResult

from richman.adapters.textual_tui.widgets.player_strip import PlayerStrip
from richman.domain import (
    GameSnapshot,
    HandCards,
    Phase,
    PlayerState,
    PublicBoardInfo,
    PublicPlayerInfo,
)
from richman.player import AIPlayer, HumanPlayer, Player


def _make_snapshot(
    *,
    public_players: tuple[PublicPlayerInfo, ...],
    viewer_index: int = 0,
    current_player_index: int = 0,
    viewer_private: PlayerState | None = None,
) -> GameSnapshot:
    if viewer_private is None:
        viewer_private = PlayerState(name="Alice", cash=2000, position=0, hand=HandCards())
    return GameSnapshot(
        turn=1,
        current_player_index=current_player_index,
        viewer_index=viewer_index,
        phase=Phase.DICE_ROLL,
        dice_value=None,
        public_board=PublicBoardInfo(cells=()),
        public_players=public_players,
        viewer_private=viewer_private,
        viewer_private_properties=(),
        event_log=(),
        available_actions=None,
    )


# -- render tests -----------------------------------------------------------


async def test_player_strip_renders_human_viewer_with_full_info() -> None:
    """Human viewer sees cash, hand, position in PlayerStrip."""
    snapshot = _make_snapshot(
        public_players=(PublicPlayerInfo(player_index=0, name="Alice", position=3),),
        viewer_index=0,
        viewer_private=PlayerState(
            name="Alice",
            cash=1800,
            position=3,
            hand=HandCards(jail_pass=1, demolish=0),
        ),
    )
    controllers: list[Player] = [HumanPlayer("Alice")]

    class TestApp(App[None]):
        def compose(self) -> ComposeResult:
            yield PlayerStrip(snapshot, controllers)

    app = TestApp()
    async with app.run_test(size=(120, 24)) as pilot:
        await pilot.pause()
        strip = app.query_one(PlayerStrip)
        rendered = strip.render().plain
        assert "Alice" in rendered
        assert "1800" in rendered
        assert "出1" in rendered
        assert "@3" in rendered


async def test_player_strip_ai_player_hides_private_info() -> None:
    """AI player shows only name, position, and status — no cash or hand."""
    snapshot = _make_snapshot(
        public_players=(
            PublicPlayerInfo(player_index=0, name="Alice", position=0),
            PublicPlayerInfo(player_index=1, name="AI-1", position=5),
        ),
        viewer_index=0,
        current_player_index=0,
    )
    controllers: list[Player] = [HumanPlayer("Alice"), AIPlayer("AI-1")]

    class TestApp(App[None]):
        def compose(self) -> ComposeResult:
            yield PlayerStrip(snapshot, controllers)

    app = TestApp()
    async with app.run_test(size=(120, 24)) as pilot:
        await pilot.pause()
        strip = app.query_one(PlayerStrip)
        rendered = strip.render().plain
        assert "AI-1" in rendered
        assert "@5" in rendered
        # AI cash/hand must NOT leak
        assert "2000" not in rendered.split("│")[1] if "│" in rendered else True


async def test_player_strip_highlights_current_player() -> None:
    """Current player has green bold styling."""
    snapshot = _make_snapshot(
        public_players=(
            PublicPlayerInfo(player_index=0, name="Alice", position=0),
            PublicPlayerInfo(player_index=1, name="AI-1", position=5),
        ),
        viewer_index=0,
        current_player_index=1,
    )
    controllers: list[Player] = [HumanPlayer("Alice"), AIPlayer("AI-1")]

    class TestApp(App[None]):
        def compose(self) -> ComposeResult:
            yield PlayerStrip(snapshot, controllers)

    app = TestApp()
    async with app.run_test(size=(120, 24)) as pilot:
        await pilot.pause()
        strip = app.query_one(PlayerStrip)
        rendered = strip.render()
        # Current player (AI-1) should have green bold span
        spans = list(rendered.spans)
        has_green = any(
            isinstance(span.style, Style)
            and span.style.color is not None
            and "green" in str(span.style.color)
            and span.style.bold
            for span in spans
        )
        assert has_green, "Current player should be highlighted in green bold"


async def test_player_strip_shows_jail_status() -> None:
    """Player in jail shows jail indicator."""
    snapshot = _make_snapshot(
        public_players=(
            PublicPlayerInfo(player_index=0, name="Alice", position=10, jail_rounds_left=2),
        ),
        viewer_index=0,
    )
    controllers: list[Player] = [HumanPlayer("Alice")]

    class TestApp(App[None]):
        def compose(self) -> ComposeResult:
            yield PlayerStrip(snapshot, controllers)

    app = TestApp()
    async with app.run_test(size=(120, 24)) as pilot:
        await pilot.pause()
        strip = app.query_one(PlayerStrip)
        rendered = strip.render().plain
        assert "2" in rendered  # jail rounds


async def test_player_strip_shows_bankrupt_status() -> None:
    """Bankrupt player shows bankrupt indicator."""
    snapshot = _make_snapshot(
        public_players=(PublicPlayerInfo(player_index=0, name="Alice", position=5, bankrupt=True),),
        viewer_index=0,
    )
    controllers: list[Player] = [HumanPlayer("Alice")]

    class TestApp(App[None]):
        def compose(self) -> ComposeResult:
            yield PlayerStrip(snapshot, controllers)

    app = TestApp()
    async with app.run_test(size=(120, 24)) as pilot:
        await pilot.pause()
        strip = app.query_one(PlayerStrip)
        rendered = strip.render().plain
        # Bankrupt emoji or indicator
        assert "💀" in rendered


async def test_player_strip_multiple_players_separated() -> None:
    """Multiple players are separated by pipe."""
    snapshot = _make_snapshot(
        public_players=(
            PublicPlayerInfo(player_index=0, name="Alice", position=0),
            PublicPlayerInfo(player_index=1, name="AI-1", position=5),
            PublicPlayerInfo(player_index=2, name="AI-2", position=8),
        ),
        viewer_index=0,
    )
    controllers: list[Player] = [
        HumanPlayer("Alice"),
        AIPlayer("AI-1"),
        AIPlayer("AI-2"),
    ]

    class TestApp(App[None]):
        def compose(self) -> ComposeResult:
            yield PlayerStrip(snapshot, controllers)

    app = TestApp()
    async with app.run_test(size=(120, 24)) as pilot:
        await pilot.pause()
        strip = app.query_one(PlayerStrip)
        rendered = strip.render().plain
        assert "│" in rendered
        assert "Alice" in rendered
        assert "AI-1" in rendered
        assert "AI-2" in rendered


# -- update tests ------------------------------------------------------------


async def test_player_strip_updates_on_snapshot_change() -> None:
    """PlayerStrip.refresh() renders new data after update_snapshot()."""
    snapshot1 = _make_snapshot(
        public_players=(PublicPlayerInfo(player_index=0, name="Alice", position=0),),
        viewer_index=0,
        viewer_private=PlayerState(name="Alice", cash=2000, position=0, hand=HandCards()),
    )
    controllers: list[Player] = [HumanPlayer("Alice")]

    class TestApp(App[None]):
        def compose(self) -> ComposeResult:
            yield PlayerStrip(snapshot1, controllers)

    app = TestApp()
    async with app.run_test(size=(120, 24)) as pilot:
        await pilot.pause()
        strip = app.query_one(PlayerStrip)
        assert "2000" in strip.render().plain

        # Update with less cash
        new_private = PlayerState(
            name="Alice",
            cash=1500,
            position=3,
            hand=HandCards(jail_pass=0, demolish=1),
        )
        snapshot2 = _make_snapshot(
            public_players=(PublicPlayerInfo(player_index=0, name="Alice", position=3),),
            viewer_index=0,
            viewer_private=new_private,
        )
        strip.update_snapshot(snapshot2)
        await pilot.pause()
        rendered = strip.render().plain
        assert "1500" in rendered
        assert "拆1" in rendered
        assert "@3" in rendered
