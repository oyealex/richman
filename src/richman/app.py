"""Application assembly for Richman.

The app layer wires configuration, board, players, renderer, and engine
together. It does not own or mutate game state directly.
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from pathlib import Path

from richman.board import create as create_board
from richman.domain import (
    DEMOLISH_RANGE,
    DICE_SIDES,
    JAIL_ROUNDS,
    START_BONUS,
    Action,
    BoardCellDefinition,
    CardDefinition,
    CardType,
    CellType,
    EngineInput,
    GameConfig,
    GameEventType,
    InputKind,
    InternalGameState,
    MoveDirection,
    Phase,
    PropertyTemplate,
    RequiredInput,
    TuiCellLayout,
    TuiLayout,
    TuiRect,
)
from richman.engine import GameEngine
from richman.player import AIPlayer, Player
from richman.render import ConsoleRenderer, Renderer

MIN_PLAYERS = 2
MAX_PLAYERS = 4

_MAX_TURNS_MESSAGE = "max_turns reached before game over"
_DEFAULT_START_CASH = 2_000
_YAML_SUFFIXES = {".yaml", ".yml"}


def build_default_config() -> GameConfig:
    """Build a complete default game configuration."""

    south = PropertyTemplate(name="南街", price=180, rents=(30, 60, 120, 240), upgrade_cost=100)
    east = PropertyTemplate(name="东街", price=220, rents=(40, 80, 160, 320), upgrade_cost=120)
    west = PropertyTemplate(name="西街", price=260, rents=(50, 100, 200, 400), upgrade_cost=140)
    north = PropertyTemplate(name="北街", price=320, rents=(60, 120, 240, 480), upgrade_cost=160)

    return GameConfig(
        board_cells=(
            BoardCellDefinition(CellType.START),
            BoardCellDefinition(CellType.PROPERTY, south),
            BoardCellDefinition(CellType.CHANCE),
            BoardCellDefinition(CellType.PROPERTY, east),
            BoardCellDefinition(CellType.BLANK),
            BoardCellDefinition(CellType.JAIL_SPACE),
            BoardCellDefinition(CellType.PROPERTY, west),
            BoardCellDefinition(CellType.CHANCE),
            BoardCellDefinition(CellType.GO_TO_JAIL),
            BoardCellDefinition(CellType.PROPERTY, north),
        ),
        cards=(
            CardDefinition(CardType.MONEY_GAIN, "获得奖金", amount=200),
            CardDefinition(CardType.MONEY_LOSS, "支付罚金", amount=100),
            CardDefinition(
                CardType.MOVE,
                "前进 2 步",
                direction=MoveDirection.FORWARD,
                min_steps=2,
                max_steps=2,
            ),
            CardDefinition(CardType.JAIL_PASS, "获得免狱卡"),
            CardDefinition(CardType.DEMOLISH, "获得拆除卡"),
        ),
        tui_layout=_default_tui_layout(),
    )


def _default_tui_layout() -> TuiLayout:
    """Build the default TUI board layout for the 10-cell board.

    Cells form a counter-clockwise ring around the center display area.
    """
    return TuiLayout(
        rows=9,
        columns=13,
        center=TuiRect(row=2, column=2, row_span=5, column_span=9),
        cells=(
            TuiCellLayout(position=0, row=8, column=0),
            TuiCellLayout(position=1, row=8, column=2),
            TuiCellLayout(position=2, row=8, column=4),
            TuiCellLayout(position=3, row=6, column=12),
            TuiCellLayout(position=4, row=4, column=12),
            TuiCellLayout(position=5, row=0, column=11),
            TuiCellLayout(position=6, row=0, column=8),
            TuiCellLayout(position=7, row=0, column=5),
            TuiCellLayout(position=8, row=0, column=2),
            TuiCellLayout(position=9, row=2, column=0),
        ),
    )


def load_config(path: str | Path) -> GameConfig:
    """Load a game configuration from a JSON or small YAML file."""

    config_path = Path(path)
    suffix = config_path.suffix.lower()
    raw_text = config_path.read_text(encoding="utf-8")

    if suffix == ".json":
        raw_config = json.loads(raw_text)
    elif suffix in _YAML_SUFFIXES:
        raw_config = _parse_simple_yaml(raw_text)
    else:
        raise ValueError("config file must use .json, .yaml, or .yml")

    if not isinstance(raw_config, Mapping):
        raise ValueError("config root must be a mapping")

    return _parse_game_config(raw_config)


def create_players(count: int) -> tuple[Player, ...]:
    """Create AI players for the default app mode."""

    if count < MIN_PLAYERS or count > MAX_PLAYERS:
        raise ValueError(f"players must be between {MIN_PLAYERS} and {MAX_PLAYERS}")

    return tuple(AIPlayer(f"AI {index}") for index in range(1, count + 1))


def create_engine(
    config: GameConfig,
    players: Sequence[Player],
    renderer: Renderer | None = None,
    seed: int | None = None,
) -> GameEngine:
    """Assemble a GameEngine from app-level dependencies."""

    del renderer
    board = create_board(config)
    return GameEngine.create(config, board, players, seed=seed)


def run_game(
    players_count: int = MIN_PLAYERS,
    max_turns: int | None = None,
    seed: int | None = None,
    renderer: Renderer | None = None,
    config: GameConfig | None = None,
    config_path: str | Path | None = None,
) -> InternalGameState:
    """Run one assembled game and return the final or bounded state."""

    if config is not None and config_path is not None:
        raise ValueError("config and config_path are mutually exclusive")

    if config is not None:
        game_config = config
    elif config_path is not None:
        game_config = load_config(config_path)
    else:
        game_config = build_default_config()

    players = create_players(players_count)
    engine = create_engine(game_config, players, seed=seed)

    try:
        return run_console_game(engine, renderer=renderer, max_turns=max_turns)
    except RuntimeError as error:
        if str(error) != _MAX_TURNS_MESSAGE:
            raise
        return engine.get_state()


def run_console_game(
    engine: GameEngine,
    renderer: Renderer | None = None,
    max_turns: int | None = None,
) -> InternalGameState:
    """Run an engine through the step-compatible console path."""

    game_renderer = renderer if renderer is not None else ConsoleRenderer()
    result = None

    while not engine.get_state().event_log or result is None or not result.game_over:
        state = engine.get_state()
        if (
            max_turns is not None
            and state.turn >= max_turns
            and (state.turn == 0 or state.phase is Phase.END)
        ):
            break

        result = engine.advance()
        game_renderer.render_frame(result.snapshot)

        while result.required_input is not None and not result.game_over:
            engine_input = _resolve_console_input(engine, game_renderer, result.required_input)
            result = engine.advance(engine_input)
            game_renderer.render_frame(result.snapshot)

        if result.game_over:
            break

    state = engine.get_state()
    game_over_events = [
        event for event in state.event_log if event.event_type is GameEventType.GAME_OVER
    ]
    if game_over_events:
        winner_name = str(game_over_events[-1].data.get("winner_name", ""))
        game_renderer.render_game_over(winner_name)
    return state


def _resolve_console_input(
    engine: GameEngine,
    renderer: Renderer,
    required: RequiredInput,
) -> EngineInput:
    player = engine.get_state().players[required.player_index]
    # The default app mode creates AI players; auto-satisfy their input so
    # bounded CLI runs remain non-interactive.
    if player.name.startswith("AI "):
        return engine._auto_input_for(required)

    if required.kind is InputKind.ROLL_DICE:
        renderer.prompt_choice("按 Enter 掷骰", ("ROLL_DICE",))
        return EngineInput(kind=required.kind, player_index=required.player_index)

    if required.kind in {InputKind.ACTION_CHOICE, InputKind.JAIL_CHOICE}:
        options = tuple(action.value for action in required.options)
        selected = renderer.prompt_choice("选择动作", options)
        return EngineInput(
            kind=required.kind,
            player_index=required.player_index,
            action=Action(selected),
        )

    if required.kind is InputKind.DEMOLISH_TARGET:
        options = tuple(str(candidate) for candidate in required.candidates)
        selected = renderer.prompt_choice("选择拆除目标", options)
        return EngineInput(
            kind=required.kind,
            player_index=required.player_index,
            target_position=int(selected),
        )

    raise ValueError(f"unsupported input kind: {required.kind.value}")


def _parse_game_config(raw_config: Mapping[object, object]) -> GameConfig:
    board_cells = tuple(
        _parse_board_cell(raw_cell, index)
        for index, raw_cell in enumerate(_required_sequence(raw_config, "board_cells"))
    )
    cards = tuple(
        _parse_card(raw_card, index)
        for index, raw_card in enumerate(_optional_sequence(raw_config, "cards"))
    )

    return GameConfig(
        board_cells=board_cells,
        cards=cards,
        start_cash=_optional_int(raw_config, "start_cash", _DEFAULT_START_CASH),
        start_bonus=_optional_int(raw_config, "start_bonus", START_BONUS),
        jail_rounds=_optional_int(raw_config, "jail_rounds", JAIL_ROUNDS),
        demolish_range=_optional_int(
            raw_config,
            "demolish_range",
            DEMOLISH_RANGE,
        ),
        dice_sides=_optional_int(raw_config, "dice_sides", DICE_SIDES),
        tui_layout=_parse_tui_layout(raw_config),
    )


def _parse_board_cell(raw_cell: object, index: int) -> BoardCellDefinition:
    data = _as_mapping(raw_cell, f"board_cells[{index}]")
    cell_type = CellType(_required_str(data, ("cell_type", "type"), f"board_cells[{index}]"))
    raw_template = _optional_value(data, ("property_template", "property"))

    if cell_type is CellType.PROPERTY:
        if raw_template is None:
            raise ValueError(f"PROPERTY cell at index {index} requires property template")
        return BoardCellDefinition(
            cell_type=cell_type,
            property_template=_parse_property_template(raw_template, index),
        )

    if raw_template is not None:
        raise ValueError(f"non-PROPERTY cell at index {index} must not define property template")

    return BoardCellDefinition(cell_type=cell_type)


def _parse_property_template(raw_template: object, index: int) -> PropertyTemplate:
    data = _as_mapping(raw_template, f"board_cells[{index}].property")
    rents = tuple(_required_sequence(data, "rents"))
    if len(rents) != 4:
        raise ValueError("property rents must define exactly four levels")

    return PropertyTemplate(
        name=_required_str(data, ("name",), "property"),
        price=_required_int(data, "price"),
        rents=(
            _as_int(rents[0], "rents[0]"),
            _as_int(rents[1], "rents[1]"),
            _as_int(rents[2], "rents[2]"),
            _as_int(rents[3], "rents[3]"),
        ),
        upgrade_cost=_required_int(data, "upgrade_cost"),
    )


def _parse_card(raw_card: object, index: int) -> CardDefinition:
    data = _as_mapping(raw_card, f"cards[{index}]")
    card_type = CardType(_required_str(data, ("card_type", "type"), f"cards[{index}]"))
    raw_direction = _optional_value(data, ("direction",))
    direction = MoveDirection(str(raw_direction)) if raw_direction is not None else None

    return CardDefinition(
        card_type=card_type,
        description=_required_str(data, ("description",), f"cards[{index}]"),
        amount=_optional_int_or_none(data, "amount"),
        direction=direction,
        min_steps=_optional_int_or_none(data, "min_steps"),
        max_steps=_optional_int_or_none(data, "max_steps"),
    )


def _parse_tui_layout(raw_config: Mapping[object, object]) -> TuiLayout | None:
    """Parse optional tui_layout section from a game config dict."""
    raw_layout = raw_config.get("tui_layout")
    if raw_layout is None:
        return None

    data = _as_mapping(raw_layout, "tui_layout")
    rows = _required_int(data, "rows")
    columns = _required_int(data, "columns")

    raw_center = _required_mapping(data, "center", "tui_layout.center")
    center = TuiRect(
        row=_required_int(raw_center, "row"),
        column=_required_int(raw_center, "column"),
        row_span=_required_int(raw_center, "row_span"),
        column_span=_required_int(raw_center, "column_span"),
    )

    raw_cells = _required_sequence(data, "cells")
    cells: list[TuiCellLayout] = []
    for i, raw_cell in enumerate(raw_cells):
        cell_data = _as_mapping(raw_cell, f"tui_layout.cells[{i}]")
        cells.append(
            TuiCellLayout(
                position=_required_int(cell_data, "position"),
                row=_required_int(cell_data, "row"),
                column=_required_int(cell_data, "column"),
            )
        )

    return TuiLayout(rows=rows, columns=columns, center=center, cells=tuple(cells))


def _required_mapping(
    data: Mapping[object, object],
    key: str,
    context: str,
) -> Mapping[object, object]:
    value = data.get(key)
    if value is None:
        raise ValueError(f"{context} requires {key}")
    return _as_mapping(value, f"{context}.{key}")


def _required_sequence(data: Mapping[object, object], key: str) -> Sequence[object]:
    value = data.get(key)
    if value is None:
        raise ValueError(f"config requires {key}")
    return _as_sequence(value, key)


def _optional_sequence(data: Mapping[object, object], key: str) -> Sequence[object]:
    value = data.get(key)
    if value is None:
        return ()
    return _as_sequence(value, key)


def _required_str(
    data: Mapping[object, object],
    keys: tuple[str, ...],
    context: str,
) -> str:
    value = _optional_value(data, keys)
    if not isinstance(value, str) or not value:
        raise ValueError(f"{context} requires {keys[0]}")
    return value


def _required_int(data: Mapping[object, object], key: str) -> int:
    value = data.get(key)
    if value is None:
        raise ValueError(f"config requires {key}")
    return _as_int(value, key)


def _optional_int(data: Mapping[object, object], key: str, default: int) -> int:
    value = data.get(key)
    if value is None:
        return default
    return _as_int(value, key)


def _optional_int_or_none(data: Mapping[object, object], key: str) -> int | None:
    value = data.get(key)
    if value is None:
        return None
    return _as_int(value, key)


def _optional_value(data: Mapping[object, object], keys: tuple[str, ...]) -> object | None:
    for key in keys:
        if key in data:
            return data[key]
    return None


def _as_mapping(value: object, context: str) -> Mapping[object, object]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{context} must be a mapping")
    return value


def _as_sequence(value: object, context: str) -> Sequence[object]:
    if isinstance(value, str) or not isinstance(value, Sequence):
        raise ValueError(f"{context} must be a sequence")
    return value


def _as_int(value: object, context: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{context} must be an integer")
    return value


def _parse_simple_yaml(raw_text: str) -> object:
    lines = _yaml_lines(raw_text)
    if not lines:
        return {}

    value, index = _parse_yaml_block(lines, 0, lines[0][0])
    if index != len(lines):
        raise ValueError("invalid YAML indentation")
    return value


def _yaml_lines(raw_text: str) -> list[tuple[int, str]]:
    lines: list[tuple[int, str]] = []
    for raw_line in raw_text.splitlines():
        line = raw_line.rstrip()
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if "\t" in line:
            raise ValueError("YAML indentation must use spaces")
        indent = len(line) - len(line.lstrip(" "))
        lines.append((indent, line.strip()))
    return lines


def _parse_yaml_block(
    lines: Sequence[tuple[int, str]],
    index: int,
    indent: int,
) -> tuple[object, int]:
    if index >= len(lines):
        return {}, index

    line_indent, text = lines[index]
    if line_indent != indent:
        raise ValueError("invalid YAML indentation")

    if text.startswith("- "):
        return _parse_yaml_sequence(lines, index, indent)
    return _parse_yaml_mapping(lines, index, indent)


def _parse_yaml_mapping(
    lines: Sequence[tuple[int, str]],
    index: int,
    indent: int,
) -> tuple[dict[str, object], int]:
    result: dict[str, object] = {}

    while index < len(lines):
        line_indent, text = lines[index]
        if line_indent < indent:
            break
        if line_indent > indent or text.startswith("- "):
            raise ValueError("invalid YAML mapping")

        key, raw_value = _split_yaml_key_value(text)
        index += 1
        if raw_value:
            result[key] = _parse_yaml_scalar(raw_value)
        elif index < len(lines) and lines[index][0] > indent:
            result[key], index = _parse_yaml_block(lines, index, lines[index][0])
        else:
            result[key] = {}

    return result, index


def _parse_yaml_sequence(
    lines: Sequence[tuple[int, str]],
    index: int,
    indent: int,
) -> tuple[list[object], int]:
    result: list[object] = []

    while index < len(lines):
        line_indent, text = lines[index]
        if line_indent < indent:
            break
        if line_indent > indent or not text.startswith("- "):
            raise ValueError("invalid YAML sequence")

        rest = text[2:].strip()
        index += 1
        if not rest:
            if index < len(lines) and lines[index][0] > indent:
                item, index = _parse_yaml_block(lines, index, lines[index][0])
            else:
                item = None
        elif _looks_like_yaml_key_value(rest):
            item, index = _parse_yaml_sequence_mapping_item(lines, index, indent, rest)
        else:
            item = _parse_yaml_scalar(rest)

        result.append(item)

    return result, index


def _parse_yaml_sequence_mapping_item(
    lines: Sequence[tuple[int, str]],
    index: int,
    sequence_indent: int,
    rest: str,
) -> tuple[dict[str, object], int]:
    key, raw_value = _split_yaml_key_value(rest)
    item: dict[str, object] = {
        key: _parse_yaml_scalar(raw_value) if raw_value else {},
    }

    if index < len(lines) and lines[index][0] > sequence_indent:
        nested, index = _parse_yaml_block(lines, index, lines[index][0])
        if not isinstance(nested, dict):
            raise ValueError("YAML sequence mapping continuation must be a mapping")
        item.update(nested)

    return item, index


def _looks_like_yaml_key_value(text: str) -> bool:
    if text.startswith(("'", '"', "[", "{")):
        return False

    colon_index = text.find(":")
    if colon_index <= 0:
        return False
    return colon_index == len(text) - 1 or text[colon_index + 1].isspace()


def _split_yaml_key_value(text: str) -> tuple[str, str]:
    if ":" not in text:
        raise ValueError("YAML mapping entry requires ':'")
    key, raw_value = text.split(":", 1)
    key = key.strip()
    if not key:
        raise ValueError("YAML mapping key must not be empty")
    return key, raw_value.strip()


def _parse_yaml_scalar(raw_value: str) -> object:
    value = raw_value.strip()
    if value in {"null", "Null", "NULL", "~"}:
        return None
    if value in {"true", "True", "TRUE"}:
        return True
    if value in {"false", "False", "FALSE"}:
        return False
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    if value.startswith(("[", "{")):
        try:
            return json.loads(value)
        except json.JSONDecodeError as error:
            raise ValueError("YAML inline collections must use JSON syntax") from error
    try:
        return int(value)
    except ValueError:
        return value
