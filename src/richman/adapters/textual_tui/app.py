"""Textual TUI adapter for Richman."""

from textual.app import App, ComposeResult
from textual.widgets import Footer, Header

from richman.adapters.textual_tui.layout import (
    TuiLayoutGeometry,
    compute_layout_geometry,
)
from richman.adapters.textual_tui.widgets.board import BoardWidget
from richman.app import build_default_config
from richman.domain import (
    GameConfig,
    GameSnapshot,
    HandCards,
    Phase,
    PlayerState,
    PublicBoardInfo,
    PublicCellInfo,
    PublicPlayerInfo,
)


class RichmanTuiApp(App[None]):
    """Textual TUI app that renders the board via BoardWidget."""

    CSS = """
    Screen {
        layout: vertical;
    }

    #board-container {
        height: 1fr;
    }
    """

    BINDINGS = [
        ("q", "quit", "退出"),
    ]

    def __init__(
        self,
        snapshot: GameSnapshot | None = None,
        config: GameConfig | None = None,
    ) -> None:
        super().__init__()
        self.config = config or build_default_config()
        self.snapshot = snapshot or _default_snapshot(self.config)
        self._geometry: TuiLayoutGeometry | None = None

    @property
    def geometry(self) -> TuiLayoutGeometry:
        if self._geometry is None:
            self._geometry = compute_layout_geometry(self.config)
        return self._geometry

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        terminal_size = (self.size.height, self.size.width)
        yield BoardWidget(
            self.snapshot,
            self.geometry,
            terminal_size=terminal_size,
        )
        yield Footer()

    def update_snapshot(self, snapshot: GameSnapshot) -> None:
        """Refresh the board with a new snapshot (called by step driver)."""
        self.snapshot = snapshot
        for board in self.query(BoardWidget):
            board.update_snapshot(snapshot)


def _default_snapshot(config: GameConfig) -> GameSnapshot:
    """Build a default snapshot whose board cells match *config*."""
    cells: list[PublicCellInfo] = []
    for i, cell_def in enumerate(config.board_cells):
        cells.append(
            PublicCellInfo(
                position=i,
                cell_type=cell_def.cell_type,
                property_name=(
                    cell_def.property_template.name
                    if cell_def.property_template is not None
                    else None
                ),
            )
        )

    player = PlayerState(
        name="玩家",
        cash=config.start_cash,
        position=0,
        hand=HandCards(),
    )
    return GameSnapshot(
        turn=0,
        current_player_index=0,
        viewer_index=0,
        phase=Phase.EFFECT_UPDATE,
        dice_value=None,
        public_board=PublicBoardInfo(cells=tuple(cells)),
        public_players=(PublicPlayerInfo(player_index=0, name=player.name, position=0),),
        viewer_private=player,
        viewer_private_properties=(),
        event_log=(),
        available_actions=None,
    )
