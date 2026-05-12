"""Tests for the Textual render adapter and BoardWidget."""

from __future__ import annotations

from textual.app import App, ComposeResult
from textual.widgets import Static

from richman.adapters.textual_tui import RichmanTuiApp
from richman.adapters.textual_tui.layout import (
    CELL_WIDTH,
    TuiLayoutGeometry,
    compute_layout_geometry,
)
from richman.adapters.textual_tui.widgets.board import BoardWidget
from richman.adapters.textual_tui.widgets.cell import CellWidget
from richman.adapters.textual_tui.widgets.center_panel import CenterPanel
from richman.app import build_default_config
from richman.domain import (
    Action,
    CellType,
    GameEvent,
    GameEventType,
    GameSnapshot,
    HandCards,
    Phase,
    PlayerState,
    PublicBoardInfo,
    PublicCellInfo,
    PublicPlayerInfo,
)


def _make_snapshot(
    *,
    turn: int = 1,
    phase: Phase = Phase.ACTION,
    dice_value: int | None = None,
    board_cells: tuple[PublicCellInfo, ...] = (
        PublicCellInfo(position=0, cell_type=CellType.START),
    ),
    public_players: tuple[PublicPlayerInfo, ...] = (
        PublicPlayerInfo(player_index=0, name="Alice", position=0),
    ),
    current_player_index: int = 0,
    event_log: tuple[GameEvent, ...] = (),
    available_actions: tuple[Action, ...] | None = None,
) -> GameSnapshot:
    viewer_idx = current_player_index
    player = PlayerState(
        name=public_players[viewer_idx].name,
        cash=2_000,
        position=public_players[viewer_idx].position,
        hand=HandCards(),
    )
    return GameSnapshot(
        turn=turn,
        current_player_index=current_player_index,
        viewer_index=viewer_idx,
        phase=phase,
        dice_value=dice_value,
        public_board=PublicBoardInfo(cells=board_cells),
        public_players=public_players,
        viewer_private=player,
        viewer_private_properties=(),
        event_log=event_log,
        available_actions=available_actions,
    )


# -- Smoke tests (updated for BoardWidget) ----------------------------------


async def test_textual_app_constructs_headless() -> None:
    config = build_default_config()
    snapshot = _make_snapshot(
        board_cells=tuple(
            PublicCellInfo(position=i, cell_type=CellType.START)
            for i in range(len(config.board_cells))
        ),
    )
    tui = RichmanTuiApp(snapshot=snapshot, config=config)

    async with tui.run_test() as pilot:
        assert tui.query_one(BoardWidget)
        await pilot.press("q")


async def test_textual_app_constructs_with_defaults() -> None:
    tui = RichmanTuiApp()

    async with tui.run_test() as pilot:
        assert tui.query_one(BoardWidget)
        await pilot.press("q")


# -- CellWidget render tests ------------------------------------------------


async def test_cell_widget_renders_position_and_type() -> None:
    cell = CellWidget(
        position=3,
        cell_info=PublicCellInfo(position=3, cell_type=CellType.START),
        owner_name=None,
        players_on_cell=(),
    )
    rendered = cell._build_content().plain
    assert "03" in rendered or "3" in rendered


async def test_cell_widget_renders_property_name() -> None:
    cell = CellWidget(
        position=0,
        cell_info=PublicCellInfo(
            position=0, cell_type=CellType.PROPERTY, property_name="海滨别墅"
        ),
        owner_name=None,
        players_on_cell=(),
    )
    rendered = cell._build_content().plain
    assert "海滨别墅" in rendered


async def test_cell_widget_renders_owner_name() -> None:
    cell = CellWidget(
        position=0,
        cell_info=PublicCellInfo(
            position=0, cell_type=CellType.PROPERTY, owner_player_index=0
        ),
        owner_name="AI-1",
        players_on_cell=(),
    )
    rendered = cell._build_content().plain
    assert "AI-1" in rendered


async def test_cell_widget_renders_unowned_property() -> None:
    cell = CellWidget(
        position=0,
        cell_info=PublicCellInfo(position=0, cell_type=CellType.PROPERTY),
        owner_name=None,
        players_on_cell=(),
    )
    rendered = cell._build_content().plain
    assert "无主" in rendered


async def test_cell_widget_renders_level_dots() -> None:
    cell = CellWidget(
        position=0,
        cell_info=PublicCellInfo(
            position=0, cell_type=CellType.PROPERTY, level=2
        ),
        owner_name="Bob",
        players_on_cell=(),
    )
    rendered = cell._build_content().plain
    assert "●●" in rendered
    assert "○" in rendered
    assert "Bob" in rendered


async def test_cell_widget_renders_players_on_cell() -> None:
    cell = CellWidget(
        position=0,
        cell_info=PublicCellInfo(position=0, cell_type=CellType.START),
        owner_name=None,
        players_on_cell=("Alice", "Bob"),
    )
    rendered = cell._build_content().plain
    assert "Alice" in rendered
    assert "Bob" in rendered


async def test_cell_widget_renders_null_cell_info_as_placeholder() -> None:
    cell = CellWidget(
        position=0,
        cell_info=None,
        owner_name=None,
        players_on_cell=(),
    )
    rendered = cell._build_content().plain
    # Should not crash; should show position and placeholder
    assert "00" in rendered


async def test_cell_widget_truncates_long_name() -> None:
    cell = CellWidget(
        position=0,
        cell_info=PublicCellInfo(
            position=0,
            cell_type=CellType.PROPERTY,
            property_name="非常长的房产名称",
        ),
        owner_name=None,
        players_on_cell=(),
    )
    rendered = cell._build_content().plain
    assert "非常长的" in rendered
    assert "…" in rendered
    assert "房产名称" not in rendered


# -- CellWidget click test --------------------------------------------------


class _CellClickTestApp(App[None]):
    def __init__(self) -> None:
        super().__init__()
        self._clicked: int | None = None

    def compose(self) -> ComposeResult:
        cell = CellWidget(
            position=5,
            cell_info=PublicCellInfo(position=5, cell_type=CellType.START),
            owner_name=None,
            players_on_cell=(),
        )
        yield cell

    def on_cell_widget_cell_clicked(self, msg: CellWidget.CellClicked) -> None:
        msg.stop()
        self._clicked = msg.position


async def test_cell_widget_click_posts_message() -> None:
    app = _CellClickTestApp()
    async with app.run_test() as pilot:
        assert app._clicked is None
        await pilot.click(CellWidget)
        assert app._clicked == 5


# -- CellWidget update_data test --------------------------------------------


async def test_cell_widget_update_data_refreshes() -> None:
    cell = CellWidget(
        position=0,
        cell_info=PublicCellInfo(position=0, cell_type=CellType.PROPERTY),
        owner_name=None,
        players_on_cell=(),
    )
    rendered_before = cell._build_content().plain

    cell.update_data(
        cell_info=PublicCellInfo(
            position=0,
            cell_type=CellType.PROPERTY,
            property_name="新名称",
            level=3,
        ),
        owner_name="Alice",
        players_on_cell=("Bob",),
    )
    rendered_after = cell._build_content().plain

    assert "新名称" in rendered_after
    assert "Alice" in rendered_after
    assert "Bob" in rendered_after
    assert rendered_after != rendered_before


# -- CenterPanel render tests -----------------------------------------------


async def test_center_panel_renders_phase_and_player() -> None:
    snapshot = _make_snapshot(
        phase=Phase.DICE_ROLL,
        public_players=(
            PublicPlayerInfo(player_index=0, name="Alice", position=3),
        ),
    )
    panel = CenterPanel(snapshot)
    rendered = panel._build_panel().renderable
    text = str(rendered)
    assert "等待掷骰" in text or "DICE_ROLL" in text
    assert "Alice" in text


async def test_center_panel_renders_dice_dash_when_none() -> None:
    snapshot = _make_snapshot(dice_value=None)
    panel = CenterPanel(snapshot)
    rendered = panel._build_panel().renderable
    text = str(rendered)
    assert "-" in text


async def test_center_panel_renders_dice_value() -> None:
    snapshot = _make_snapshot(dice_value=7)
    panel = CenterPanel(snapshot)
    rendered = panel._build_panel().renderable
    text = str(rendered)
    assert "7" in text


async def test_center_panel_renders_recent_events() -> None:
    events: list[GameEvent] = [
        GameEvent(GameEventType.DICE_ROLLED, {"player_name": "Alice", "value": 5}),
        GameEvent(GameEventType.PLAYER_MOVED, {"player_name": "Alice", "to": 5}),
    ] * 10  # 20 events, should show last 5
    snapshot = _make_snapshot(event_log=tuple(events))
    panel = CenterPanel(snapshot)
    rendered = panel._build_panel().renderable
    text = str(rendered)
    assert "DICE_ROLLED" in text
    assert "PLAYER_MOVED" in text


# -- BoardWidget compose tests ----------------------------------------------


async def test_board_widget_composes_cells_and_center() -> None:
    config = build_default_config()
    geometry = compute_layout_geometry(config)
    snapshot = _make_snapshot(
        board_cells=tuple(
            PublicCellInfo(position=i, cell_type=CellType.START)
            for i in range(len(config.board_cells))
        ),
    )

    board = BoardWidget(snapshot, geometry)

    # Collect children yielded by compose()
    children = list(board.compose())
    center_count = sum(1 for c in children if isinstance(c, CenterPanel))
    cell_count = sum(1 for c in children if isinstance(c, CellWidget))

    assert center_count == 1
    assert cell_count == len(config.board_cells)


async def test_board_widget_insufficient_terminal_shows_error() -> None:
    from types import MappingProxyType

    geometry = TuiLayoutGeometry(
        position_rects=MappingProxyType({}),
        center_rect=(0, 0, 0, 0),
        min_terminal_rows=50,
        min_terminal_cols=200,
        is_terminal_sufficient=False,
    )
    snapshot = _make_snapshot()
    board = BoardWidget(snapshot, geometry, terminal_size=(30, 100))

    # Offline compose: validate error content and no cells
    children = list(board.compose())
    assert len(children) == 1
    assert isinstance(children[0], Static)
    error_text = str(children[0].render())
    assert "50" in error_text
    assert "200" in error_text
    assert "30" in error_text
    assert "100" in error_text


async def test_board_widget_insufficient_terminal_error_is_visible() -> None:
    """When mounted in an app, the error Static must have a non-zero region."""
    from types import MappingProxyType

    geometry = TuiLayoutGeometry(
        position_rects=MappingProxyType({}),
        center_rect=(0, 0, 0, 0),
        min_terminal_rows=50,
        min_terminal_cols=200,
        is_terminal_sufficient=False,
    )
    snapshot = _make_snapshot()
    board = BoardWidget(snapshot, geometry, terminal_size=(30, 100))

    class _ErrorTestApp(App[None]):
        def compose(self) -> ComposeResult:
            yield board

    app = _ErrorTestApp()
    async with app.run_test(size=(40, 120)):
        assert board.region.width > 0, f"board region width is 0: {board.region}"
        assert board.region.height > 0, f"board region height is 0: {board.region}"
        error_static = board.query_one(Static)
        assert error_static.region.width > 0
        assert error_static.region.height > 0


async def test_board_widget_clicked_position() -> None:
    config = build_default_config()
    geometry = compute_layout_geometry(config)
    snapshot = _make_snapshot(
        board_cells=tuple(
            PublicCellInfo(position=i, cell_type=CellType.START)
            for i in range(len(config.board_cells))
        ),
    )
    board = BoardWidget(snapshot, geometry)
    assert board.clicked_position is None

    board.on_cell_widget_cell_clicked(CellWidget.CellClicked(3))
    assert board.clicked_position == 3


# -- BoardWidget update_snapshot test ---------------------------------------


async def test_board_widget_update_snapshot_updates_children() -> None:
    config = build_default_config()
    geometry = compute_layout_geometry(config)
    initial = _make_snapshot(
        board_cells=tuple(
            PublicCellInfo(position=i, cell_type=CellType.START)
            for i in range(len(config.board_cells))
        ),
        public_players=(
            PublicPlayerInfo(player_index=0, name="Alice", position=0),
        ),
    )

    board = BoardWidget(initial, geometry)
    # Mount into a minimal app to enable query()
    class _TestApp(App[None]):
        def compose(self) -> ComposeResult:
            yield board

    app = _TestApp()
    async with app.run_test():
        # Update with new snapshot
        new_snapshot = _make_snapshot(
            turn=2,
            phase=Phase.DICE_ROLL,
            dice_value=6,
            board_cells=tuple(
                PublicCellInfo(position=i, cell_type=CellType.START)
                for i in range(len(config.board_cells))
            ),
            public_players=(
                PublicPlayerInfo(player_index=0, name="Alice", position=3),
            ),
            event_log=(GameEvent(GameEventType.DICE_ROLLED, {"value": 6}),),
        )
        board.update_snapshot(new_snapshot)

        # Center panel should exist
        assert board.query_one(CenterPanel)

        # All cells should still exist
        cells = board.query(CellWidget)
        assert len(list(cells)) == len(config.board_cells)


# -- Cell dimension constants test ------------------------------------------


def test_cell_dimension_constants_match_layout() -> None:
    assert CELL_WIDTH == 12


# -- BoardWidget CSS test ---------------------------------------------------


def test_board_widget_has_default_css() -> None:
    assert BoardWidget.DEFAULT_CSS != ""
    assert CellWidget.DEFAULT_CSS != ""
    assert CenterPanel.DEFAULT_CSS != ""
