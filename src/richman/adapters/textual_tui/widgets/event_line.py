"""EventLine — single-row latest event display with click-to-open support."""

from __future__ import annotations

from rich.text import Text
from textual.message import Message
from textual.widget import Widget

from richman.domain import GameEvent, GameSnapshot


def _format_event_one_line(event: GameEvent) -> str:
    """Format a single event as one short line."""
    data = dict(event.data)
    player_name = data.get("player_name", "")
    if player_name:
        return f"{player_name}: {event.event_type.value}"
    return event.event_type.value


class EventLine(Widget):
    """One-row latest event display. Click to request event log modal."""

    class OpenRequested(Message):
        """Posted when user requests to open the event log."""

    DEFAULT_CSS = """
    EventLine {
        height: 1;
    }
    """

    def __init__(self, snapshot: GameSnapshot) -> None:
        super().__init__()
        self._snapshot = snapshot

    def update_snapshot(self, snapshot: GameSnapshot) -> None:
        self._snapshot = snapshot
        self.refresh()

    def on_click(self) -> None:
        self.post_message(self.OpenRequested())

    def render(self) -> Text:
        if not self._snapshot.event_log:
            return Text("--", style="dim")
        latest = self._snapshot.event_log[-1]
        formatted = _format_event_one_line(latest)
        return Text(formatted)
