"""SetupScreen — configure player count and human name before starting."""

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Button, Input, Label, Select, Static

from richman.adapters.textual_tui.screens.game import GameScreen
from richman.app import create_engine, create_tui_players
from richman.domain import GameConfig


class SetupScreen(Screen[None]):
    """Configure game settings before launching."""

    DEFAULT_CSS = """
    SetupScreen {
        align: center middle;
    }

    SetupScreen Vertical {
        width: 40;
        height: auto;
        border: solid $primary;
        padding: 1 2;
    }

    SetupScreen Label {
        height: auto;
        width: auto;
        margin-top: 1;
    }

    SetupScreen Select {
        width: 100%;
        margin-bottom: 1;
    }

    SetupScreen Input {
        width: 100%;
        margin-bottom: 1;
    }

    SetupScreen Static.ai-label {
        color: $text-disabled;
        height: auto;
        width: 100%;
    }

    SetupScreen Button {
        width: 100%;
        margin-top: 1;
    }
    """

    def __init__(
        self,
        config: GameConfig,
        seed: int | None = None,
        player_count: int = 2,
    ) -> None:
        super().__init__()
        self._config = config
        self._seed = seed
        self._player_count = player_count

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static("游戏设置", classes="title")
            yield Label("总玩家数")
            yield Select(
                (str(n), str(n)) for n in range(2, 5)
            )
            yield Label("玩家名称")
            yield Input(value="玩家", placeholder="输入你的名字")
            yield Static(self._ai_label_text(), classes="ai-label")
            yield Button("开始游戏", variant="primary", id="start")

    def on_mount(self) -> None:
        select = self.query_one(Select)
        select.value = str(self._player_count)

    def on_select_changed(self, event: Select.Changed) -> None:
        if not event.value:
            return
        self._player_count = int(str(event.value))
        # Update AI label
        ai_label = self.query_one(".ai-label", Static)
        ai_label.update(self._ai_label_text())

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id != "start":
            return
        event.stop()

        human_name = self.query_one(Input).value.strip() or "玩家"
        players = create_tui_players(self._player_count, human_name=human_name)
        engine = create_engine(self._config, players, seed=self._seed)

        await self.app.push_screen(
            GameScreen(engine, self._config, players)
        )

    def _ai_label_text(self) -> str:
        ai_names = [f"AI {i}" for i in range(1, self._player_count)]
        return "AI 玩家: " + "、".join(ai_names)
