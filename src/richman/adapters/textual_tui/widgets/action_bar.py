"""ActionBar — bottom-of-screen input bar with dynamic action buttons."""

from __future__ import annotations

from textual import events
from textual.message import Message
from textual.reactive import Reactive
from textual.widget import Widget
from textual.widgets import Button, Static

from richman.domain import Action, EngineInput, InputKind, RequiredInput

_ACTION_LABELS: dict[Action, str] = {
    Action.BUY: "购买",
    Action.UPGRADE: "升级",
    Action.USE_DEMOLISH: "拆除",
    Action.USE_JAIL_PASS: "出狱卡",
    Action.ACCEPT_JAIL: "接受入狱",
    Action.SKIP: "跳过",
}


class ActionBar(Widget):
    """Bottom bar that shows input controls based on RequiredInput kind."""

    can_focus = True

    class ActionSubmitted(Message):
        """Posted when the user clicks an action button."""

        def __init__(self, engine_input: EngineInput) -> None:
            self.engine_input = engine_input
            super().__init__()

    DEFAULT_CSS = """
    ActionBar {
        height: 5;
        layout: horizontal;
        align: center middle;
        border: solid $panel;
    }
    ActionBar Static {
        width: auto;
        height: auto;
    }
    ActionBar Button {
        margin: 0 1;
    }
    """

    required_input: Reactive[RequiredInput | None] = Reactive(None)

    def __init__(self) -> None:
        super().__init__()
        self._button_inputs: dict[str, EngineInput] = {}
        self._game_over = False
        self._winner_name: str | None = None

    def on_mount(self) -> None:
        """Take focus so keyboard shortcuts work without focusing a button first."""
        self.focus()

    def set_required_input(self, required: RequiredInput | None) -> None:
        """Sync entry: set reactive attribute to trigger watcher rebuild."""
        self._game_over = False
        self._winner_name = None
        self.required_input = required  # type: ignore[assignment]

    def set_game_over(self, winner_name: str | None) -> None:
        """Display game-over state with optional winner name."""
        self._game_over = True
        self._winner_name = winner_name
        self.required_input = None  # type: ignore[assignment]
        self.refresh()

    async def watch_required_input(self, required: RequiredInput | None) -> None:
        """Rebuild children when required_input changes."""
        await self.remove_children()
        self._button_inputs.clear()

        if self._game_over:
            return

        if required is None:
            return

        if required.kind is InputKind.ROLL_DICE:
            btn_id = "btn-roll"
            btn = Button("掷骰 [Enter]", id=btn_id)
            ei = EngineInput(kind=InputKind.ROLL_DICE, player_index=required.player_index)
            self._button_inputs[btn_id] = ei
            await self.mount(btn)

        elif required.kind in (InputKind.ACTION_CHOICE, InputKind.JAIL_CHOICE):
            for i, action in enumerate(required.options):
                btn_id = f"btn-action-{i}"
                label = _ACTION_LABELS.get(action, action.value)
                btn = Button(f"[{i + 1}] {label}", id=btn_id)
                ei = EngineInput(
                    kind=required.kind,
                    player_index=required.player_index,
                    action=action,
                )
                self._button_inputs[btn_id] = ei
                await self.mount(btn)

        elif required.kind is InputKind.DEMOLISH_TARGET:
            candidates_str = ", ".join(str(c) for c in required.candidates)
            hint = Static(f"请点击棋盘上的目标格子: {candidates_str}   [Esc 取消]")
            await self.mount(hint)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Forward button presses as ActionSubmitted messages."""
        btn_id = event.button.id
        if btn_id is not None and btn_id in self._button_inputs:
            event.stop()
            self.post_message(self.ActionSubmitted(self._button_inputs[btn_id]))

    def on_key(self, event: events.Key) -> None:
        """Keyboard shortcuts for action buttons."""
        button_ids = list(self._button_inputs)
        if not button_ids:
            return

        if event.key in ("enter", "space"):
            self.post_message(self.ActionSubmitted(self._button_inputs[button_ids[0]]))
            event.stop()
        elif event.key.isdigit():
            idx = int(event.key) - 1
            if 0 <= idx < len(button_ids):
                self.post_message(self.ActionSubmitted(self._button_inputs[button_ids[idx]]))
                event.stop()

    def render(self) -> str:
        """Show game-over message when in terminal state."""
        if self._game_over:
            name = self._winner_name or "?"
            return f"  游戏结束  ·  赢家: {name}"
        return ""
