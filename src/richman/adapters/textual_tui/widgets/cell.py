"""CellWidget — a single board cell in the TUI board grid."""

from __future__ import annotations

from rich.text import Text
from textual.message import Message
from textual.widgets import Static

from richman.domain import CellType, PublicCellInfo

_CELL_EMOJI: dict[CellType, str] = {
    CellType.START: "🚩",
    CellType.PROPERTY: "🏠",
    CellType.CHANCE: "❓",
    CellType.GO_TO_JAIL: "👮",
    CellType.JAIL_SPACE: "🔒",
    CellType.BLANK: "⬜",
}

_LEVEL_DOT_FILLED = "●"
_LEVEL_DOT_EMPTY = "○"
_MAX_LEVEL_DOTS = 3


class CellWidget(Static):
    """A single board cell rendered at an absolute position in the grid."""

    class CellClicked(Message):
        """Posted when the user clicks this cell."""

        def __init__(self, position: int) -> None:
            self.position = position
            super().__init__()

    DEFAULT_CSS = """
    CellWidget {
        width: 12;
        height: 5;
        border: solid $border;
        content-align: center middle;
    }
    CellWidget.current {
        border: thick $success;
    }
    CellWidget.candidate {
        border: thick $warning;
    }
    """

    def __init__(
        self,
        position: int,
        cell_info: PublicCellInfo | None,
        owner_name: str | None,
        players_on_cell: tuple[str, ...],
        is_current_player_cell: bool = False,
    ) -> None:
        super().__init__()
        self.position = position
        self._cell_info = cell_info
        self._owner_name = owner_name
        self._players_on_cell = players_on_cell
        self._is_current_player = is_current_player_cell
        self.set_class(is_current_player_cell, "current")

    def on_click(self) -> None:
        self.post_message(self.CellClicked(self.position))

    def update_data(
        self,
        cell_info: PublicCellInfo | None,
        owner_name: str | None,
        players_on_cell: tuple[str, ...],
        is_current_player_cell: bool = False,
    ) -> None:
        self._cell_info = cell_info
        self._owner_name = owner_name
        self._players_on_cell = players_on_cell
        self._is_current_player = is_current_player_cell
        self.set_class(is_current_player_cell, "current")
        self.refresh()

    def render(self) -> Text:
        return self._build_content()

    def _build_content(self) -> Text:
        """Assemble the 3-line cell content."""
        line1 = self._build_line1()
        line2 = self._build_line2()
        line3 = self._build_line3()

        text = Text()
        text.append(line1)
        text.append("\n")
        text.append(line2)
        text.append("\n")
        text.append(line3)
        return text

    def _build_line1(self) -> str:
        pos_str = f"[{self.position:02d}]"
        emoji = ""
        if self._cell_info is not None:
            emoji = _CELL_EMOJI.get(self._cell_info.cell_type, "")
        return f"{pos_str}{emoji}"

    def _build_line2(self) -> str:
        if self._cell_info is None:
            return "· · ·"
        name = self._cell_info.property_name
        if name is None:
            cell_type = self._cell_info.cell_type
            # Return Chinese name for non-property types
            type_names: dict[CellType, str] = {
                CellType.START: "起点",
                CellType.CHANCE: "机会",
                CellType.GO_TO_JAIL: "入狱",
                CellType.JAIL_SPACE: "监狱",
                CellType.BLANK: "空地",
            }
            return type_names.get(cell_type, cell_type.value)
        if len(name) > 4:
            return name[:4] + "…"
        return name

    def _build_line3(self) -> str:
        parts: list[str] = []

        # Level dots (only for property cells)
        if self._cell_info is not None and self._cell_info.cell_type == CellType.PROPERTY:
            level = self._cell_info.level or 0
            dots = _LEVEL_DOT_FILLED * level + _LEVEL_DOT_EMPTY * (_MAX_LEVEL_DOTS - level)
            parts.append(dots)

        # Owner name
        if self._owner_name is not None:
            parts.append(self._owner_name)
        elif self._cell_info is not None and self._cell_info.cell_type == CellType.PROPERTY:
            parts.append("无主")

        # Players on cell
        if self._players_on_cell:
            if len(self._players_on_cell) <= 2:
                parts.extend(self._players_on_cell)
            else:
                parts.append(f"{self._players_on_cell[0]}+{len(self._players_on_cell) - 1}")

        return " ".join(parts) if parts else ""
