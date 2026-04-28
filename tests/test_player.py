"""Tests for the player decision boundary."""

from __future__ import annotations

import ast
from collections.abc import Sequence
from copy import deepcopy
from dataclasses import dataclass, field
from pathlib import Path

import pytest

from richman.domain import (
    Action,
    CellType,
    HandCards,
    Phase,
    PlayerState,
    PlayerView,
    PropertyRef,
    PropertyState,
    PublicBoardInfo,
    PublicCellInfo,
    PublicPlayerInfo,
)
from richman.player import AIPlayer, HumanPlayer, InputContext, Player, PlayerDecisionError

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PLAYER_ROOT = PROJECT_ROOT / "src" / "richman" / "player"
FORBIDDEN_PLAYER_IMPORTS = {
    "richman.board",
    "richman.rules",
    "richman.engine",
    "richman.render",
    "richman.adapters",
    "random",
}


@dataclass(slots=True)
class FakeInputContext:
    choices: list[str]
    prompts: list[tuple[str, tuple[str, ...]]] = field(default_factory=list)

    def prompt_choice(self, question: str, options: Sequence[str]) -> str:
        self.prompts.append((question, tuple(options)))
        return self.choices.pop(0)


def _sample_view() -> PlayerView:
    private_player = PlayerState(
        name="Alice",
        cash=2_000,
        position=1,
        holdings=[PropertyRef(position=1)],
        hand=HandCards(jail_pass=1, demolish=1),
    )
    private_property = PropertyState(
        position=1,
        owner_player_index=0,
        level=1,
        acquired_at=3,
        purchase_price=300,
        upgrade_invested=150,
    )

    return PlayerView(
        turn=4,
        current_player_index=0,
        viewer_index=0,
        phase=Phase.ACTION,
        dice_value=None,
        public_board=PublicBoardInfo(
            cells=(
                PublicCellInfo(position=0, cell_type=CellType.START),
                PublicCellInfo(
                    position=1,
                    cell_type=CellType.PROPERTY,
                    property_name="中山路",
                    owner_player_index=0,
                    level=1,
                ),
            ),
        ),
        public_players=(
            PublicPlayerInfo(player_index=0, name="Alice", position=1),
            PublicPlayerInfo(player_index=1, name="Bob", position=3),
        ),
        viewer_private=private_player,
        viewer_private_properties=(private_property,),
        available_actions=(Action.UPGRADE, Action.USE_DEMOLISH, Action.SKIP),
    )


def test_player_public_api_exports_common_models() -> None:
    from richman.player import AIPlayer, HumanPlayer, Player

    human = HumanPlayer(name="Alice")
    ai = AIPlayer(name="Bot")

    assert isinstance(human, Player)
    assert isinstance(ai, Player)
    assert human.name == "Alice"
    assert ai.name == "Bot"


def test_player_source_does_not_import_higher_modules_or_random() -> None:
    imported_modules: set[str] = set()

    for path in PLAYER_ROOT.glob("*.py"):
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
            for prefix in FORBIDDEN_PLAYER_IMPORTS
        )
    }

    assert forbidden == set()


def test_player_interface_exposes_required_decision_points() -> None:
    assert hasattr(Player, "name")
    assert hasattr(Player, "wait_for_dice")
    assert hasattr(Player, "decide")
    assert hasattr(Player, "choose_demolish_target")
    assert isinstance(HumanPlayer("Alice"), Player)
    assert isinstance(AIPlayer("Bot"), Player)


def test_input_context_protocol_describes_prompt_choice_boundary() -> None:
    context: InputContext = FakeInputContext(["BUY"])

    assert context.prompt_choice("选择动作", ("BUY", "SKIP")) == "BUY"


def test_human_player_wait_for_dice_delegates_to_injected_waiter() -> None:
    calls: list[str] = []
    player = HumanPlayer("Alice", dice_waiter=lambda: calls.append("waited"))

    player.wait_for_dice()

    assert calls == ["waited"]


def test_human_player_decide_prompts_for_action_and_returns_selected_action() -> None:
    context = FakeInputContext(["UPGRADE"])
    player = HumanPlayer("Alice")

    decision = player.decide(
        _sample_view(),
        [Action.BUY, Action.UPGRADE, Action.SKIP],
        context,
    )

    assert decision is Action.UPGRADE
    assert context.prompts == [("选择动作", ("BUY", "UPGRADE", "SKIP"))]


def test_human_player_decide_rejects_invalid_action_inputs() -> None:
    player = HumanPlayer("Alice")

    with pytest.raises(PlayerDecisionError):
        player.decide(_sample_view(), [], FakeInputContext(["SKIP"]))

    with pytest.raises(PlayerDecisionError):
        player.decide(_sample_view(), [Action.SKIP], None)

    with pytest.raises(PlayerDecisionError):
        player.decide(_sample_view(), [Action.SKIP], FakeInputContext(["BUY"]))


def test_human_player_choose_demolish_target_prompts_for_candidate() -> None:
    context = FakeInputContext(["7"])
    player = HumanPlayer("Alice")

    target = player.choose_demolish_target(_sample_view(), [3, 7], context)

    assert target == 7
    assert context.prompts == [("选择拆除目标", ("3", "7"))]


def test_human_player_choose_demolish_target_rejects_invalid_inputs() -> None:
    player = HumanPlayer("Alice")

    with pytest.raises(PlayerDecisionError):
        player.choose_demolish_target(_sample_view(), [], FakeInputContext(["3"]))

    with pytest.raises(PlayerDecisionError):
        player.choose_demolish_target(_sample_view(), [3], None)

    with pytest.raises(PlayerDecisionError):
        player.choose_demolish_target(_sample_view(), [3], FakeInputContext(["9"]))


def test_ai_player_wait_for_dice_returns_without_side_effects() -> None:
    player = AIPlayer("Bot")

    player.wait_for_dice()

    assert player.name == "Bot"


def test_ai_player_chooses_deterministic_legal_action() -> None:
    player = AIPlayer("Bot")
    view = _sample_view()
    actions = [Action.SKIP, Action.UPGRADE, Action.BUY]

    first = player.decide(view, actions, None)
    second = player.decide(view, actions, None)

    assert first is Action.BUY
    assert second is Action.BUY


def test_ai_player_handles_jail_decisions_from_available_actions() -> None:
    player = AIPlayer("Bot")
    view = _sample_view()

    assert player.decide(view, [Action.ACCEPT_JAIL], None) is Action.ACCEPT_JAIL
    assert (
        player.decide(view, [Action.ACCEPT_JAIL, Action.USE_JAIL_PASS], None)
        is Action.USE_JAIL_PASS
    )


def test_ai_player_rejects_empty_actions_and_chooses_stable_target() -> None:
    player = AIPlayer("Bot")
    view = _sample_view()

    with pytest.raises(PlayerDecisionError):
        player.decide(view, [], None)

    assert player.choose_demolish_target(view, [9, 4, 1], None) == 9
    assert player.choose_demolish_target(view, [9, 4, 1], None) == 9

    with pytest.raises(PlayerDecisionError):
        player.choose_demolish_target(view, [], None)


def test_player_decisions_do_not_mutate_player_view_data() -> None:
    view = _sample_view()
    before = deepcopy(view)

    assert (
        HumanPlayer("Alice").decide(
            view,
            [Action.USE_DEMOLISH, Action.SKIP],
            FakeInputContext(["SKIP"]),
        )
        is Action.SKIP
    )
    assert AIPlayer("Bot").choose_demolish_target(view, [5, 6], None) == 5

    assert view == before


def test_player_decisions_need_only_player_view_and_explicit_options() -> None:
    view = _sample_view()

    assert AIPlayer("Bot").decide(view, [Action.SKIP], None) is Action.SKIP
    assert (
        HumanPlayer("Alice").choose_demolish_target(
            view,
            [2],
            FakeInputContext(["2"]),
        )
        == 2
    )
