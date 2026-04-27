"""Tests for the pure game rules module."""

from __future__ import annotations

import ast
from copy import deepcopy
from pathlib import Path

import pytest

from richman.domain import (
    CardDefinition,
    CardType,
    DeductMoneyIntent,
    GoToJailIntent,
    GrantMoneyIntent,
    MoveDirection,
    MoveIntent,
    ObtainCardIntent,
    PropertyState,
    PropertyTemplate,
    ReclaimPlan,
)
from richman.rules import (
    calculate_bankruptcy,
    calculate_rent,
    can_afford,
    can_upgrade,
    resolve_card_intent,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RULES_ROOT = PROJECT_ROOT / "src" / "richman" / "rules"
FORBIDDEN_RULES_IMPORTS = {
    "richman.board",
    "richman.player",
    "richman.engine",
    "richman.render",
    "richman.adapters",
}


def _property_template() -> PropertyTemplate:
    return PropertyTemplate(
        name="中山路",
        price=300,
        rents=(30, 60, 120, 240),
        upgrade_cost=150,
    )


def _property_state(
    position: int,
    *,
    level: int = 0,
    acquired_at: int = 0,
    purchase_price: int = 300,
    upgrade_invested: int = 0,
) -> PropertyState:
    return PropertyState(
        position=position,
        owner_player_index=0,
        level=level,
        acquired_at=acquired_at,
        purchase_price=purchase_price,
        upgrade_invested=upgrade_invested,
    )


def test_rules_public_api_exports_common_functions() -> None:
    from richman.rules import calculate_rent, can_afford, resolve_card_intent

    assert calculate_rent(_property_template(), 0) == 30
    assert can_afford(100, 100) is True
    assert resolve_card_intent(CardDefinition(CardType.GO_TO_JAIL, "去监狱")) == (GoToJailIntent())


def test_rules_source_does_not_import_higher_modules() -> None:
    imported_modules: set[str] = set()

    for path in RULES_ROOT.glob("*.py"):
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
            for prefix in FORBIDDEN_RULES_IMPORTS
        )
    }

    assert forbidden == set()


def test_rules_functions_do_not_mutate_property_inputs() -> None:
    template = _property_template()
    property_state = _property_state(1, level=1)
    properties = [
        _property_state(2, acquired_at=2, purchase_price=200, upgrade_invested=50),
        _property_state(3, acquired_at=1, purchase_price=100, upgrade_invested=25),
    ]
    property_state_before = deepcopy(property_state)
    properties_before = deepcopy(properties)

    assert can_upgrade(template, property_state) is True
    assert calculate_bankruptcy(properties, shortfall=150).total_refund == 375

    assert property_state == property_state_before
    assert properties == properties_before


@pytest.mark.parametrize(
    ("level", "rent"),
    [(0, 30), (1, 60), (2, 120), (3, 240)],
)
def test_calculate_rent_returns_rent_for_level(level: int, rent: int) -> None:
    assert calculate_rent(_property_template(), level) == rent


@pytest.mark.parametrize("level", [-1, 4])
def test_calculate_rent_rejects_invalid_level(level: int) -> None:
    with pytest.raises(ValueError):
        calculate_rent(_property_template(), level)


def test_can_upgrade_returns_true_below_max_and_false_at_max() -> None:
    template = _property_template()

    assert can_upgrade(template, _property_state(1, level=0)) is True
    assert can_upgrade(template, _property_state(1, level=2)) is True
    assert can_upgrade(template, _property_state(1, level=3)) is False


def test_can_upgrade_ignores_cash_constraints() -> None:
    template = _property_template()
    property_state = _property_state(1, level=2, purchase_price=0, upgrade_invested=0)

    assert can_upgrade(template, property_state) is True


@pytest.mark.parametrize("level", [-1, 4])
def test_can_upgrade_rejects_invalid_level(level: int) -> None:
    with pytest.raises(ValueError):
        can_upgrade(_property_template(), _property_state(1, level=level))


@pytest.mark.parametrize(
    ("card", "intent"),
    [
        (
            CardDefinition(CardType.MONEY_GAIN, "获得 100", amount=100),
            GrantMoneyIntent(amount=100),
        ),
        (
            CardDefinition(CardType.MONEY_LOSS, "损失 50", amount=50),
            DeductMoneyIntent(amount=50),
        ),
        (
            CardDefinition(
                CardType.MOVE,
                "后退 1 到 3 步",
                direction=MoveDirection.BACKWARD,
                min_steps=1,
                max_steps=3,
            ),
            MoveIntent(direction=MoveDirection.BACKWARD, min_steps=1, max_steps=3),
        ),
        (CardDefinition(CardType.GO_TO_JAIL, "直接入狱"), GoToJailIntent()),
        (
            CardDefinition(CardType.JAIL_PASS, "获得免狱卡"),
            ObtainCardIntent(card_type=CardType.JAIL_PASS),
        ),
        (
            CardDefinition(CardType.DEMOLISH, "获得拆除卡"),
            ObtainCardIntent(card_type=CardType.DEMOLISH),
        ),
    ],
)
def test_resolve_card_intent_maps_all_card_types(
    card: CardDefinition,
    intent: object,
) -> None:
    assert resolve_card_intent(card) == intent


@pytest.mark.parametrize(
    "card",
    [
        CardDefinition(CardType.MONEY_GAIN, "缺少金额"),
        CardDefinition(CardType.MONEY_LOSS, "负金额", amount=-1),
        CardDefinition(CardType.MOVE, "缺少方向", min_steps=1, max_steps=3),
        CardDefinition(
            CardType.MOVE,
            "缺少最小步数",
            direction=MoveDirection.FORWARD,
            max_steps=3,
        ),
        CardDefinition(
            CardType.MOVE,
            "缺少最大步数",
            direction=MoveDirection.FORWARD,
            min_steps=1,
        ),
        CardDefinition(
            CardType.MOVE,
            "负步数",
            direction=MoveDirection.FORWARD,
            min_steps=-1,
            max_steps=3,
        ),
        CardDefinition(
            CardType.MOVE,
            "反向范围",
            direction=MoveDirection.FORWARD,
            min_steps=4,
            max_steps=3,
        ),
    ],
)
def test_resolve_card_intent_rejects_invalid_card_parameters(
    card: CardDefinition,
) -> None:
    with pytest.raises(ValueError):
        resolve_card_intent(card)


def test_resolve_card_intent_does_not_mutate_card_definition() -> None:
    card = CardDefinition(
        CardType.MOVE,
        "随机移动",
        direction=MoveDirection.RANDOM,
        min_steps=0,
        max_steps=6,
    )

    assert resolve_card_intent(card) == MoveIntent(
        direction=MoveDirection.RANDOM,
        min_steps=0,
        max_steps=6,
    )
    assert card == CardDefinition(
        CardType.MOVE,
        "随机移动",
        direction=MoveDirection.RANDOM,
        min_steps=0,
        max_steps=6,
    )


@pytest.mark.parametrize(
    ("cash", "amount", "expected"),
    [(100, 100, True), (101, 100, True), (99, 100, False), (0, 0, True)],
)
def test_can_afford_checks_cash_against_amount(
    cash: int,
    amount: int,
    expected: bool,
) -> None:
    assert can_afford(cash, amount) is expected


@pytest.mark.parametrize(("cash", "amount"), [(-1, 0), (0, -1)])
def test_can_afford_rejects_negative_inputs(cash: int, amount: int) -> None:
    with pytest.raises(ValueError):
        can_afford(cash, amount)


def test_calculate_bankruptcy_reclaims_oldest_properties_until_shortfall_is_covered() -> None:
    properties = [
        _property_state(5, acquired_at=3, purchase_price=999),
        _property_state(1, acquired_at=1, purchase_price=100, upgrade_invested=25),
        _property_state(4, acquired_at=2, purchase_price=50, upgrade_invested=25),
    ]

    assert calculate_bankruptcy(properties, shortfall=150) == ReclaimPlan(
        reclaimed=((1, 125), (4, 75)),
        total_refund=200,
        remaining_shortfall=0,
    )


def test_calculate_bankruptcy_reports_remaining_shortfall_when_assets_are_insufficient() -> None:
    properties = [
        _property_state(1, acquired_at=1, purchase_price=80, upgrade_invested=20),
        _property_state(2, acquired_at=2, purchase_price=50, upgrade_invested=0),
    ]

    assert calculate_bankruptcy(properties, shortfall=200) == ReclaimPlan(
        reclaimed=((1, 100), (2, 50)),
        total_refund=150,
        remaining_shortfall=50,
    )


def test_calculate_bankruptcy_handles_zero_shortfall_without_reclaiming() -> None:
    properties = [_property_state(1, acquired_at=1, purchase_price=100)]

    assert calculate_bankruptcy(properties, shortfall=0) == ReclaimPlan(
        reclaimed=(),
        total_refund=0,
        remaining_shortfall=0,
    )


def test_calculate_bankruptcy_preserves_input_order_for_equal_acquired_at() -> None:
    properties = [
        _property_state(7, acquired_at=1, purchase_price=10),
        _property_state(3, acquired_at=1, purchase_price=20),
        _property_state(5, acquired_at=2, purchase_price=30),
    ]

    assert calculate_bankruptcy(properties, shortfall=60).reclaimed == (
        (7, 10),
        (3, 20),
        (5, 30),
    )


def test_calculate_bankruptcy_rejects_negative_shortfall() -> None:
    with pytest.raises(ValueError):
        calculate_bankruptcy([], shortfall=-1)
