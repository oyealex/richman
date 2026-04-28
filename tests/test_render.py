"""Tests for the framework-neutral render boundary."""

from __future__ import annotations

import ast
from collections.abc import Callable, Iterator
from copy import deepcopy
from io import StringIO
from pathlib import Path

import pytest

from richman.domain import (
    Action,
    CellType,
    GameEvent,
    GameEventType,
    GameSnapshot,
    HandCards,
    Phase,
    PlayerState,
    PropertyRef,
    PropertyState,
    PublicBoardInfo,
    PublicCellInfo,
    PublicPlayerInfo,
)
from richman.render import (
    ConsoleRenderer,
    Renderer,
    format_event,
    format_event_log,
    format_snapshot,
    prompt_choice,
    prompt_number,
    render_event_log,
    render_frame,
    render_game_over,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RENDER_ROOT = PROJECT_ROOT / "src" / "richman" / "render"
FORBIDDEN_RENDER_IMPORTS = {
    "richman.engine",
    "richman.board",
    "richman.rules",
    "richman.player",
    "richman.adapters",
    "rich",
    "textual",
}


def _sample_snapshot(
    actions: tuple[Action, ...] | None = (Action.UPGRADE, Action.SKIP),
) -> GameSnapshot:
    viewer_private = PlayerState(
        name="Alice",
        cash=1_500,
        position=3,
        holdings=[PropertyRef(position=3)],
        hand=HandCards(jail_pass=1, demolish=2),
    )
    viewer_property = PropertyState(
        position=3,
        owner_player_index=0,
        level=1,
        acquired_at=7,
        purchase_price=300,
        upgrade_invested=150,
    )

    return GameSnapshot(
        turn=2,
        current_player_index=0,
        viewer_index=0,
        phase=Phase.ACTION,
        dice_value=4,
        public_board=PublicBoardInfo(
            cells=(
                PublicCellInfo(position=0, cell_type=CellType.START),
                PublicCellInfo(
                    position=3,
                    cell_type=CellType.PROPERTY,
                    property_name="中山路",
                    owner_player_index=0,
                    level=1,
                ),
            ),
        ),
        public_players=(
            PublicPlayerInfo(player_index=0, name="Alice", position=3),
            PublicPlayerInfo(player_index=1, name="Bob", position=6, jail_rounds_left=1),
        ),
        viewer_private=viewer_private,
        viewer_private_properties=(viewer_property,),
        event_log=(
            GameEvent(
                GameEventType.ACTION_CHOSEN,
                {
                    "player_index": 0,
                    "player_name": "Alice",
                    "action": Action.UPGRADE,
                    "cash": 1_500,
                },
            ),
        ),
        available_actions=actions,
    )


def test_render_public_api_exports_contract_and_functions() -> None:
    renderer = ConsoleRenderer(output=StringIO(), input_reader=lambda prompt: "1")

    assert isinstance(renderer, Renderer)
    assert callable(render_frame)
    assert callable(render_event_log)
    assert callable(prompt_choice)
    assert callable(prompt_number)
    assert callable(render_game_over)
    assert callable(format_snapshot)
    assert callable(format_event)
    assert callable(format_event_log)


def test_render_source_depends_only_on_domain_and_standard_library() -> None:
    imported_modules: set[str] = set()

    for path in RENDER_ROOT.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_modules.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module is not None:
                imported_modules.add(node.module)

    forbidden = {
        module
        for module in imported_modules
        if any(
            module == prefix or module.startswith(f"{prefix}.")
            for prefix in FORBIDDEN_RENDER_IMPORTS
        )
    }

    assert forbidden == set()


def test_render_frame_formats_snapshot_data() -> None:
    output = StringIO()
    snapshot = _sample_snapshot()

    ConsoleRenderer(output=output).render_frame(snapshot)

    rendered = output.getvalue()
    assert "回合: 2" in rendered
    assert "阶段: ACTION" in rendered
    assert "骰子: 4" in rendered
    assert "中山路" in rendered
    assert "#0 Alice @ 3" in rendered
    assert "cash=1500" in rendered
    assert "jail_pass=1" in rendered
    assert "purchase_price=300" in rendered
    assert "可用动作: UPGRADE, SKIP" in rendered


@pytest.mark.parametrize("actions", [None, ()])
def test_render_frame_handles_empty_actions_without_fabricating_actions(
    actions: tuple[Action, ...] | None,
) -> None:
    rendered = format_snapshot(_sample_snapshot(actions=actions))

    assert "可用动作: 无" in rendered
    assert "BUY" not in rendered
    assert "USE_DEMOLISH" not in rendered


def test_rendering_does_not_mutate_snapshot_or_events() -> None:
    snapshot = _sample_snapshot()
    before_snapshot = deepcopy(snapshot)
    events = list(snapshot.event_log)
    before_events = deepcopy(events)

    renderer = ConsoleRenderer(output=StringIO())
    renderer.render_frame(snapshot)
    renderer.render_event_log(events, viewer_index=0)

    assert snapshot == before_snapshot
    assert events == before_events


def test_event_formatting_masks_other_players_private_fields() -> None:
    event = GameEvent(
        GameEventType.PROPERTY_BOUGHT,
        {
            "player_index": 0,
            "player_name": "Alice",
            "property_name": "中山路",
            "position": 3,
            "level": 1,
            "cash": 1_500,
            "hand_cards": {"jail_pass": 1, "demolish": 2},
            "purchase_price": 300,
            "upgrade_invested": 150,
            "action": Action.BUY,
        },
    )

    viewer_line = format_event(event, viewer_index=0)
    other_line = format_event(event, viewer_index=1)

    assert "cash=1500" in viewer_line
    assert "purchase_price=300" in viewer_line
    assert "upgrade_invested=150" in viewer_line
    assert "property_name=中山路" in other_line
    assert "position=3" in other_line
    assert "action=BUY" in other_line
    assert "cash=已隐藏" in other_line
    assert "purchase_price=已隐藏" in other_line
    assert "upgrade_invested=已隐藏" in other_line
    assert "hand_cards=已隐藏" in other_line


def test_prompt_choice_rejects_empty_options_and_accepts_number_or_text() -> None:
    renderer_by_number = ConsoleRenderer(output=StringIO(), input_reader=lambda prompt: "2")
    renderer_by_text = ConsoleRenderer(output=StringIO(), input_reader=lambda prompt: "SKIP")

    assert renderer_by_number.prompt_choice("选择动作", ("BUY", "UPGRADE", "SKIP")) == "UPGRADE"
    assert renderer_by_text.prompt_choice("选择动作", ("BUY", "UPGRADE", "SKIP")) == "SKIP"

    with pytest.raises(ValueError):
        renderer_by_number.prompt_choice("选择动作", ())


def test_prompt_number_rejects_invalid_bounds_and_respects_range() -> None:
    responses = iter(("not-a-number", "9", "3"))
    renderer = ConsoleRenderer(output=StringIO(), input_reader=_next_response(responses))

    assert renderer.prompt_number("选择目标", 1, 5) == 3

    with pytest.raises(ValueError):
        renderer.prompt_number("选择目标", 5, 1)


def test_render_game_over_prints_winner_without_state() -> None:
    output = StringIO()

    ConsoleRenderer(output=output).render_game_over("Alice")

    assert "游戏结束" in output.getvalue()
    assert "胜者: Alice" in output.getvalue()


def _next_response(responses: Iterator[str]) -> Callable[[str], str]:
    def read(_prompt: str) -> str:
        return next(responses)

    return read
