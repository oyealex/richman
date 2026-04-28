"""Framework-neutral render contracts and a standard console implementation."""

from __future__ import annotations

import sys
from collections.abc import Callable, Iterable, Sequence
from typing import Protocol, TextIO, runtime_checkable

from richman.domain import Action, GameEvent, GameSnapshot, PublicCellInfo, PublicPlayerInfo

HIDDEN_VALUE = "已隐藏"

_PRIVATE_DATA_KEYS = {
    "cash",
    "cash_balance",
    "balance",
    "hand",
    "hand_cards",
    "jail_pass",
    "demolish",
    "purchase_price",
    "upgrade_invested",
    "invested",
    "refund",
    "total_refund",
    "remaining_cash",
}
_PUBLIC_DATA_KEYS = {
    "action",
    "available_actions",
    "card",
    "card_description",
    "card_type",
    "cell_type",
    "crossings",
    "dice_value",
    "event",
    "level",
    "name",
    "owner_name",
    "phase",
    "player",
    "player_name",
    "position",
    "property_name",
    "result",
    "target",
    "target_position",
    "turn",
    "winner_name",
}


@runtime_checkable
class Renderer(Protocol):
    """Framework-neutral renderer boundary consumed by the engine and adapters."""

    def render_frame(self, snapshot: GameSnapshot) -> None:
        """Render one complete game frame."""

    def render_event_log(self, events: Iterable[GameEvent], viewer_index: int) -> None:
        """Render event log entries for a specific viewer."""

    def prompt_choice(self, question: str, options: Sequence[str]) -> str:
        """Prompt for one option and return the selected option value."""

    def prompt_number(self, question: str, min_value: int, max_value: int) -> int:
        """Prompt for an integer inside the inclusive bounds."""

    def render_game_over(self, winner_name: str) -> None:
        """Render the final winner state."""


class ConsoleRenderer:
    """Small standard-library renderer useful for tests and early engine integration."""

    def __init__(
        self,
        output: TextIO | None = None,
        input_reader: Callable[[str], str] | None = None,
    ) -> None:
        self._output = output if output is not None else sys.stdout
        self._input_reader = input_reader if input_reader is not None else input

    def render_frame(self, snapshot: GameSnapshot) -> None:
        self._write(format_snapshot(snapshot))

    def render_event_log(self, events: Iterable[GameEvent], viewer_index: int) -> None:
        self._write(format_event_log(events, viewer_index))

    def prompt_choice(self, question: str, options: Sequence[str]) -> str:
        choices = tuple(options)
        if not choices:
            raise ValueError("options must not be empty")

        prompt = _format_choice_prompt(question, choices)
        while True:
            selected = self._input_reader(prompt).strip()
            if selected.isdigit():
                index = int(selected) - 1
                if 0 <= index < len(choices):
                    return choices[index]
            if selected in choices:
                return selected

            self._write("输入无效，请选择列表中的选项。")

    def prompt_number(self, question: str, min_value: int, max_value: int) -> int:
        if min_value > max_value:
            raise ValueError("min_value must be less than or equal to max_value")

        prompt = f"{question} ({min_value}-{max_value}): "
        while True:
            raw_value = self._input_reader(prompt).strip()
            try:
                value = int(raw_value)
            except ValueError:
                self._write("输入无效，请输入整数。")
                continue

            if min_value <= value <= max_value:
                return value

            self._write(f"输入无效，请输入 {min_value} 到 {max_value} 之间的整数。")

    def render_game_over(self, winner_name: str) -> None:
        self._write(f"游戏结束\n胜者: {winner_name}")

    def _write(self, text: str) -> None:
        print(text, file=self._output)


_default_renderer = ConsoleRenderer()


def render_frame(snapshot: GameSnapshot) -> None:
    """Render one complete game frame using the default renderer."""

    _default_renderer.render_frame(snapshot)


def render_event_log(events: Iterable[GameEvent], viewer_index: int) -> None:
    """Render event log entries using the default renderer."""

    _default_renderer.render_event_log(events, viewer_index)


def prompt_choice(question: str, options: Sequence[str]) -> str:
    """Prompt for one option using the default renderer."""

    return _default_renderer.prompt_choice(question, options)


def prompt_number(question: str, min_value: int, max_value: int) -> int:
    """Prompt for a bounded integer using the default renderer."""

    return _default_renderer.prompt_number(question, min_value, max_value)


def render_game_over(winner_name: str) -> None:
    """Render the final winner state using the default renderer."""

    _default_renderer.render_game_over(winner_name)


def format_snapshot(snapshot: GameSnapshot) -> str:
    """Format a snapshot into plain text without mutating domain objects."""

    dice = snapshot.dice_value if snapshot.dice_value is not None else "未掷骰"
    actions = _format_actions(snapshot.available_actions)
    sections = [
        "终端大富翁",
        f"回合: {snapshot.turn}",
        f"阶段: {snapshot.phase.value}",
        f"当前玩家索引: {snapshot.current_player_index}",
        f"观察者索引: {snapshot.viewer_index}",
        f"骰子: {dice}",
        "",
        "棋盘:",
        *(_format_cell(cell) for cell in snapshot.public_board.cells),
        "",
        "玩家:",
        *(_format_public_player(player) for player in snapshot.public_players),
        "",
        "你的状态:",
        _format_private_player(snapshot),
        "",
        "你的地块:",
        *_format_private_properties(snapshot),
        "",
        f"可用动作: {actions}",
        "",
        "事件:",
        format_event_log(snapshot.event_log, snapshot.viewer_index),
    ]

    return "\n".join(sections)


def format_event_log(events: Iterable[GameEvent], viewer_index: int) -> str:
    """Format event entries with viewer-specific private data masking."""

    lines = [format_event(event, viewer_index) for event in events]
    return "\n".join(lines) if lines else "无事件"


def format_event(event: GameEvent, viewer_index: int) -> str:
    """Format one event with conservative privacy masking."""

    if not event.data:
        return f"- {event.event_type.value}"

    viewer_event = _belongs_to_viewer(event.data, viewer_index)
    details = [
        f"{key}={_format_event_value(key, value, viewer_event)}"
        for key, value in event.data.items()
        if _should_display_key(key)
    ]
    if not details:
        return f"- {event.event_type.value}"

    return f"- {event.event_type.value}: {', '.join(details)}"


def _format_actions(actions: Sequence[Action] | None) -> str:
    if not actions:
        return "无"
    return ", ".join(action.value for action in actions)


def _format_cell(cell: PublicCellInfo) -> str:
    label = f"  [{cell.position}] {cell.cell_type.value}"
    details: list[str] = []
    if cell.property_name is not None:
        details.append(cell.property_name)
    if cell.owner_player_index is not None:
        details.append(f"owner={cell.owner_player_index}")
    if cell.level is not None:
        details.append(f"level={cell.level}")
    if not details:
        return label
    return f"{label} ({', '.join(details)})"


def _format_public_player(player: PublicPlayerInfo) -> str:
    flags: list[str] = []
    if player.jail_rounds_left:
        flags.append(f"jail={player.jail_rounds_left}")
    if player.bankrupt:
        flags.append("bankrupt")
    suffix = f" ({', '.join(flags)})" if flags else ""
    return f"  #{player.player_index} {player.name} @ {player.position}{suffix}"


def _format_private_player(snapshot: GameSnapshot) -> str:
    player = snapshot.viewer_private
    return (
        f"  {player.name}: cash={player.cash}, position={player.position}, "
        f"jail_pass={player.hand.jail_pass}, demolish={player.hand.demolish}, "
        f"jail_rounds_left={player.jail_rounds_left}, bankrupt={player.bankrupt}"
    )


def _format_private_properties(snapshot: GameSnapshot) -> list[str]:
    if not snapshot.viewer_private_properties:
        return ["  无"]

    return [
        (
            f"  position={property_state.position}, level={property_state.level}, "
            f"purchase_price={property_state.purchase_price}, "
            f"upgrade_invested={property_state.upgrade_invested}"
        )
        for property_state in snapshot.viewer_private_properties
    ]


def _format_choice_prompt(question: str, options: Sequence[str]) -> str:
    lines = [question]
    lines.extend(f"{index}. {option}" for index, option in enumerate(options, start=1))
    lines.append("> ")
    return "\n".join(lines)


def _belongs_to_viewer(data: object, viewer_index: int) -> bool:
    if not isinstance(data, dict):
        return False

    player_index = data.get("player_index")
    if player_index == viewer_index:
        return True

    viewer = data.get("viewer_index")
    return viewer == viewer_index


def _should_display_key(key: object) -> bool:
    normalized = str(key).lower()
    return not normalized.startswith("_")


def _format_event_value(key: object, value: object, viewer_event: bool) -> str:
    normalized = str(key).lower()
    if _is_private_key(normalized) and not viewer_event:
        return HIDDEN_VALUE

    if isinstance(value, dict):
        return _format_mapping_value(value, viewer_event)
    if isinstance(value, (list, tuple)):
        items = (_format_event_value(normalized, item, viewer_event) for item in value)
        return "[" + ", ".join(items) + "]"
    if isinstance(value, Action):
        return value.value
    return str(value)


def _format_mapping_value(value: dict[object, object], viewer_event: bool) -> str:
    details = [
        f"{key}={_format_event_value(key, nested_value, viewer_event)}"
        for key, nested_value in value.items()
        if _should_display_key(key)
    ]
    return "{" + ", ".join(details) + "}"


def _is_private_key(normalized_key: str) -> bool:
    if normalized_key in _PUBLIC_DATA_KEYS:
        return False
    if normalized_key in _PRIVATE_DATA_KEYS:
        return True
    return any(token in normalized_key for token in ("cash", "hand", "invested", "refund"))
