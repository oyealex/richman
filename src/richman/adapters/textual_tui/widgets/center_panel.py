"""CenterPanel — displays current game state in the center area of the board."""

from __future__ import annotations

from rich.panel import Panel
from textual.widgets import Static

from richman.domain import GameEvent, GameSnapshot

_PHASE_NAMES: dict[str, str] = {
    "EFFECT_UPDATE": "状态更新",
    "DICE_ROLL": "等待掷骰",
    "LANDING": "落点结算",
    "ACTION": "行动阶段",
    "END": "回合结束",
}

_MAX_EVENTS = 5


class CenterPanel(Static):
    """Displays turn, phase, current player, dice, and recent events."""

    DEFAULT_CSS = """
    CenterPanel {
        border: solid $accent;
        content-align: center middle;
    }
    """

    def __init__(self, snapshot: GameSnapshot) -> None:
        super().__init__()
        self._snapshot = snapshot

    def update_snapshot(self, snapshot: GameSnapshot) -> None:
        self._snapshot = snapshot
        self.refresh()

    def render(self) -> Panel:
        return self._build_panel()

    def _build_panel(self) -> Panel:
        s = self._snapshot
        current_player = s.public_players[s.current_player_index]

        body_lines: list[str] = []
        body_lines.append(f"回合 {s.turn}  ·  {_PHASE_NAMES.get(s.phase.value, s.phase.value)}")
        body_lines.append(f"当前: {current_player.name}")

        dice_str = str(s.dice_value) if s.dice_value is not None else "-"
        body_lines.append(f"骰子: {dice_str}")

        # Recent events
        recent = s.event_log[-_MAX_EVENTS:]
        if recent:
            body_lines.append("")
            body_lines.append("── 最近事件 ──")
            for ev in recent:
                body_lines.append(_format_event(ev))

        body = "\n".join(body_lines)
        return Panel(body, title="终端大富翁", border_style="green")


def _format_event(event: GameEvent) -> str:
    """Format a single event as one short line."""
    name = event.event_type.value
    data = dict(event.data)
    # Show player name and key fields compactly
    player_name = data.get("player_name", "")
    if player_name:
        return f"· {player_name}: {name}"
    return f"· {name}"
