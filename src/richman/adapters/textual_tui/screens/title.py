"""TitleScreen — welcome screen shown on TUI launch."""

from __future__ import annotations

from typing import TYPE_CHECKING

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Static

from richman.adapters.textual_tui.screens.setup import SetupScreen

if TYPE_CHECKING:
    from richman.adapters.textual_tui.app import RichmanTuiApp


class TitleScreen(Screen[None]):
    """Welcome screen with game title and start prompt."""

    DEFAULT_CSS = """
    TitleScreen {
        align: center middle;
    }

    TitleScreen Static.title {
        content-align: center middle;
        width: auto;
        height: auto;
    }

    TitleScreen Static.hint {
        content-align: center middle;
        width: auto;
        height: auto;
        margin-top: 2;
        color: $text-disabled;
    }
    """

    BINDINGS = [
        ("q", "quit", "退出"),
        ("enter", "start_setup", "开始设置"),
    ]

    def compose(self) -> ComposeResult:
        yield Static("大富翁", classes="title")
        yield Static("按 Enter 开始游戏", classes="hint")

    async def action_start_setup(self) -> None:
        app: RichmanTuiApp = self.app  # type: ignore[assignment]
        await self.app.push_screen(
            SetupScreen(
                config=app.config,
                seed=app.seed,
                player_count=app.player_count,
            )
        )
