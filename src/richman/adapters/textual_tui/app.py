"""Textual TUI adapter for Richman."""

from rich.panel import Panel
from textual.app import App, ComposeResult
from textual.containers import Vertical
from textual.widgets import Footer, Header, Static

from richman.domain import (
    CellType,
    GameSnapshot,
    HandCards,
    Phase,
    PlayerState,
    PublicBoardInfo,
    PublicCellInfo,
    PublicPlayerInfo,
)
from richman.render import format_snapshot


class RichmanTuiApp(App[None]):
    """Minimal Textual app shell backed by framework-neutral render data."""

    CSS = """
    Screen {
        layout: vertical;
    }

    #content {
        height: 1fr;
        padding: 1 2;
    }

    #status {
        height: auto;
        margin-bottom: 1;
    }

    #decision {
        height: auto;
    }
    """

    BINDINGS = [
        ("q", "quit", "退出"),
    ]

    def __init__(
        self,
        snapshot: GameSnapshot | None = None,
        decision_prompt: str | None = None,
        decision_options: tuple[str, ...] = (),
    ) -> None:
        super().__init__()
        self.snapshot = snapshot or _default_snapshot()
        self.decision_prompt = decision_prompt
        self.decision_options = decision_options

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Vertical(id="content"):
            yield Static(self._snapshot_panel(), id="status")
            if self.decision_prompt is not None:
                yield Static(self._decision_panel(), id="decision")
        yield Footer()

    def _snapshot_panel(self) -> Panel:
        return Panel(format_snapshot(self.snapshot), title="终端大富翁", border_style="green")

    def _decision_panel(self) -> Panel:
        if self.decision_prompt is None:
            return Panel("无需输入", title="决策请求", border_style="blue")

        options = "\n".join(f"- {option}" for option in self.decision_options) or "- 无"
        body = f"玩家: {self.snapshot.viewer_private.name}\n{self.decision_prompt}\n\n{options}"
        return Panel(body, title="决策请求", border_style="blue")


def _default_snapshot() -> GameSnapshot:
    player = PlayerState(
        name="玩家",
        cash=2_000,
        position=0,
        hand=HandCards(),
    )
    return GameSnapshot(
        turn=0,
        current_player_index=0,
        viewer_index=0,
        phase=Phase.EFFECT_UPDATE,
        dice_value=None,
        public_board=PublicBoardInfo(
            cells=(PublicCellInfo(position=0, cell_type=CellType.START),),
        ),
        public_players=(PublicPlayerInfo(player_index=0, name=player.name, position=0),),
        viewer_private=player,
        viewer_private_properties=(),
        event_log=(),
        available_actions=None,
    )
