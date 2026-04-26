"""Textual TUI adapter for Richman."""

from rich.panel import Panel
from textual.app import App, ComposeResult
from textual.containers import Vertical
from textual.widgets import Footer, Header, Static

from richman.render import DecisionRequest, GameSnapshotView


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
        snapshot: GameSnapshotView | None = None,
        decision_request: DecisionRequest | None = None,
    ) -> None:
        super().__init__()
        self.snapshot = snapshot or GameSnapshotView()
        self.decision_request = decision_request

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Vertical(id="content"):
            yield Static(self._snapshot_panel(), id="status")
            if self.decision_request is not None:
                yield Static(self._decision_panel(), id="decision")
        yield Footer()

    def _snapshot_panel(self) -> Panel:
        actions = ", ".join(self.snapshot.available_actions) or "无可用动作"
        body = f"{self.snapshot.message}\n\n可用动作: {actions}"
        return Panel(body, title=self.snapshot.title, border_style="green")

    def _decision_panel(self) -> Panel:
        request = self.decision_request
        if request is None:
            return Panel("无需输入", title="决策请求", border_style="blue")

        options = "\n".join(f"- {option}" for option in request.options) or "- 无"
        body = f"玩家: {request.player_name}\n{request.prompt}\n\n{options}"
        return Panel(body, title="决策请求", border_style="blue")
