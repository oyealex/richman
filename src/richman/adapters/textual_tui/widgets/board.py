"""BoardWidget — main container that renders the TUI board with cells and center panel."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.reactive import Reactive
from textual.widget import Widget
from textual.widgets import Static

from richman.adapters.textual_tui.layout import TuiLayoutGeometry
from richman.adapters.textual_tui.widgets.cell import CellWidget
from richman.adapters.textual_tui.widgets.center_panel import CenterPanel
from richman.domain import GameSnapshot, PublicCellInfo


class BoardWidget(Widget):
    """Renders the full board: cells at absolute positions + center info panel.

    Receives a GameSnapshot and precomputed TuiLayoutGeometry.  When the
    terminal is too small it renders an error message instead of the grid.
    """

    highlight_positions: Reactive[frozenset[int]] = Reactive(frozenset())

    DEFAULT_CSS = """
    BoardWidget {
        width: auto;
        height: auto;
    }
    """

    def __init__(
        self,
        snapshot: GameSnapshot,
        geometry: TuiLayoutGeometry,
        terminal_size: tuple[int, int] | None = None,
    ) -> None:
        super().__init__()
        self._snapshot = snapshot
        self._geometry = geometry
        self._terminal_size = terminal_size
        self._clicked_position: int | None = None
        # Build lookup dict keyed by PublicCellInfo.position (position may != index)
        self._cells_by_pos: dict[int, PublicCellInfo] = {
            c.position: c for c in snapshot.public_board.cells
        }

    @property
    def clicked_position(self) -> int | None:
        """The most recently clicked cell position, or None."""
        return self._clicked_position

    def compose(self) -> ComposeResult:
        # -- sufficiency check: use actual terminal_size when available ---
        insufficient = False
        if self._terminal_size is not None:
            rows_needed = self._geometry.min_terminal_rows
            cols_needed = self._geometry.min_terminal_cols
            cur_rows, cur_cols = self._terminal_size
            if cur_rows < rows_needed or cur_cols < cols_needed:
                insufficient = True
        else:
            # No terminal_size given (test / headless): trust precomputed flag
            insufficient = not self._geometry.is_terminal_sufficient

        if insufficient:
            self.styles.width = "100%"
            self.styles.height = "auto"
            yield self._build_error_static()
            return

        # -- set container dimensions to board minimum -------------------
        self.styles.width = self._geometry.min_terminal_cols
        self.styles.height = self._geometry.min_terminal_rows

        # Center panel
        c = self._geometry.center_rect
        center_top, center_left = c[0], c[1]
        center_width = c[3] - c[1]
        center_height = c[2] - c[0]
        center = CenterPanel(self._snapshot)
        center.styles.position = "absolute"
        center.styles.offset = (center_left, center_top)
        center.styles.width = center_width
        center.styles.height = center_height
        yield center

        # Cell widgets
        for pos, (top, left, _bottom, _right) in self._geometry.position_rects.items():
            cell_info = self._get_cell_info(pos)
            owner_name = self._resolve_owner_name(pos)
            players_on = self._resolve_players_on_cell(pos)
            is_current = self._snapshot.public_players[
                self._snapshot.current_player_index
            ].position == pos

            cell = CellWidget(
                position=pos,
                cell_info=cell_info,
                owner_name=owner_name,
                players_on_cell=players_on,
                is_current_player_cell=is_current,
            )
            cell.styles.position = "absolute"
            cell.styles.offset = (left, top)
            yield cell

    def update_snapshot(self, snapshot: GameSnapshot) -> None:
        """Refresh all child widgets with new snapshot data without recomposing."""
        self._snapshot = snapshot
        self._cells_by_pos = {
            c.position: c for c in snapshot.public_board.cells
        }

        # Update center panel
        for center in self.query(CenterPanel):
            center.update_snapshot(snapshot)

        # Update cell widgets
        for cell in self.query(CellWidget):
            pos = cell.position
            cell_info = self._get_cell_info(pos)
            owner_name = self._resolve_owner_name(pos)
            players_on = self._resolve_players_on_cell(pos)
            is_current = (
                snapshot.public_players[snapshot.current_player_index].position == pos
            )
            cell.update_data(cell_info, owner_name, players_on, is_current)

    def on_cell_widget_cell_clicked(self, message: CellWidget.CellClicked) -> None:
        self._clicked_position = message.position

    def set_highlight_positions(self, positions: frozenset[int]) -> None:
        """Sync entry: set reactive attribute to trigger watcher update."""
        self.highlight_positions = positions  # type: ignore[assignment]

    async def watch_highlight_positions(self, positions: frozenset[int]) -> None:
        """Add or remove candidate CSS class on CellWidgets."""
        for cell in self.query(CellWidget):
            cell.set_class(cell.position in positions, "candidate")

    def _build_error_static(self) -> Static:
        rows = self._geometry.min_terminal_rows
        cols = self._geometry.min_terminal_cols
        if self._terminal_size is not None:
            cur_rows, cur_cols = self._terminal_size
            msg = (
                f"终端尺寸不足，无法渲染棋盘。\n\n"
                f"当前终端: {cur_rows} 行 × {cur_cols} 列\n"
                f"最少需要: {rows} 行 × {cols} 列"
            )
        else:
            msg = f"终端尺寸不足，无法渲染棋盘。\n\n最少需要: {rows} 行 × {cols} 列"
        return Static(msg)

    def _get_cell_info(self, pos: int) -> PublicCellInfo | None:
        """Get PublicCellInfo for a position via dict lookup."""
        return self._cells_by_pos.get(pos)

    def _resolve_owner_name(self, pos: int) -> str | None:
        """Resolve owner name from owner_player_index via public_players."""
        cell_info = self._get_cell_info(pos)
        if cell_info is None or cell_info.owner_player_index is None:
            return None
        owner_idx = cell_info.owner_player_index
        for p in self._snapshot.public_players:
            if p.player_index == owner_idx:
                return p.name
        return None

    def _resolve_players_on_cell(self, pos: int) -> tuple[str, ...]:
        """Return names of all players whose position equals *pos*."""
        return tuple(
            p.name
            for p in self._snapshot.public_players
            if p.position == pos
        )
