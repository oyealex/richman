"""PlayerStrip — single-row player status bar showing all players compactly."""

from __future__ import annotations

from collections.abc import Sequence

from rich.style import Style
from rich.text import Text
from textual.widget import Widget

from richman.domain import GameSnapshot, PublicPlayerInfo
from richman.player import AIPlayer, Player


class PlayerStrip(Widget):
    """One-row horizontal strip showing compact player status.

    Human players (especially the viewer) see cash and hand cards.
    AI players only show public info: name, position, jail/bankrupt.
    """

    DEFAULT_CSS = """
    PlayerStrip {
        height: 1;
        layout: horizontal;
    }
    """

    def __init__(
        self,
        snapshot: GameSnapshot,
        player_controllers: Sequence[Player],
    ) -> None:
        super().__init__()
        self._snapshot = snapshot
        self._player_controllers = tuple(player_controllers)

    def update_snapshot(self, snapshot: GameSnapshot) -> None:
        self._snapshot = snapshot
        self.refresh()

    def render(self) -> Text:
        parts: list[Text | str] = []
        for i, pub in enumerate(self._snapshot.public_players):
            if i > 0:
                parts.append(Text(" │ ", style=Style(dim=True)))
            is_current = i == self._snapshot.current_player_index
            is_human = not isinstance(self._player_controllers[i], AIPlayer)
            is_viewer = i == self._snapshot.viewer_index
            parts.append(self._render_player(pub, is_human, is_viewer, is_current))
        return Text.assemble(*parts)

    def _render_player(
        self,
        pub: PublicPlayerInfo,
        is_human: bool,
        is_viewer: bool,
        is_current: bool,
    ) -> Text:
        style = Style(bold=True, color="green") if is_current else Style()

        text = Text()
        prefix = "▶ " if is_current else ""
        text.append(f"{prefix}{pub.name}", style=style)

        # Cash and hand cards — only for human viewer
        if is_human and is_viewer:
            private = self._snapshot.viewer_private
            text.append(f" ${private.cash}")
            card_parts = []
            if private.hand.jail_pass > 0:
                card_parts.append(f"出{private.hand.jail_pass}")
            if private.hand.demolish > 0:
                card_parts.append(f"拆{private.hand.demolish}")
            if card_parts:
                text.append(f" {'/'.join(card_parts)}")

        # Position
        text.append(f" @{pub.position}")

        # Status indicators
        if pub.bankrupt:
            text.append(" \U0001f480", style=Style(color="red"))
        elif pub.jail_rounds_left > 0:
            text.append(
                f" \U0001f512{pub.jail_rounds_left}",
                style=Style(color="yellow"),
            )

        return text
