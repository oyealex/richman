"""Pure game-rule calculations for Richman.

Rules functions intentionally return computed values only. State mutation,
randomness, event logging, player decisions, and rendering are owned by higher
modules.
"""

from __future__ import annotations

from typing import Literal

from richman.domain import (
    CardDefinition,
    CardIntent,
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


def calculate_rent(template: PropertyTemplate, level: int) -> int:
    """Return the rent for a property template at the given level."""

    _validate_level(template, level, allow_max=True)
    return template.rents[level]


def can_upgrade(template: PropertyTemplate, property_state: PropertyState) -> bool:
    """Return whether a property can advance to the next level."""

    level = property_state.level
    max_level = _max_property_level(template)
    if level < 0 or level > max_level:
        raise ValueError(f"property level must be between 0 and {max_level}")
    return level < max_level


def resolve_card_intent(card: CardDefinition) -> CardIntent:
    """Convert a card definition into a structured effect intent."""

    match card.card_type:
        case CardType.MONEY_GAIN:
            return GrantMoneyIntent(_required_non_negative_amount(card))
        case CardType.MONEY_LOSS:
            return DeductMoneyIntent(_required_non_negative_amount(card))
        case CardType.MOVE:
            return MoveIntent(
                direction=_required_direction(card),
                min_steps=_required_steps(card, "min_steps"),
                max_steps=_required_steps(card, "max_steps"),
            )
        case CardType.GO_TO_JAIL:
            return GoToJailIntent()
        case CardType.JAIL_PASS | CardType.DEMOLISH:
            return ObtainCardIntent(card.card_type)
    raise ValueError(f"unsupported card type: {card.card_type}")


def calculate_bankruptcy(
    properties: list[PropertyState],
    shortfall: int,
) -> ReclaimPlan:
    """Calculate a deterministic reclaim plan for covering a cash shortfall."""

    if shortfall < 0:
        raise ValueError("shortfall must be non-negative")
    if shortfall == 0:
        return ReclaimPlan(reclaimed=(), total_refund=0, remaining_shortfall=0)

    reclaimed: list[tuple[int, int]] = []
    total_refund = 0

    for property_state in sorted(properties, key=lambda item: item.acquired_at):
        refund = property_state.purchase_price + property_state.upgrade_invested
        reclaimed.append((property_state.position, refund))
        total_refund += refund
        if total_refund >= shortfall:
            break

    return ReclaimPlan(
        reclaimed=tuple(reclaimed),
        total_refund=total_refund,
        remaining_shortfall=max(shortfall - total_refund, 0),
    )


def can_afford(cash: int, amount: int) -> bool:
    """Return whether non-negative cash can cover a non-negative amount."""

    if cash < 0:
        raise ValueError("cash must be non-negative")
    if amount < 0:
        raise ValueError("amount must be non-negative")
    return cash >= amount


def _validate_level(
    template: PropertyTemplate,
    level: int,
    *,
    allow_max: bool,
) -> None:
    max_level = _max_property_level(template)
    upper_bound = max_level if allow_max else max_level - 1
    if level < 0 or level > upper_bound:
        raise ValueError(f"property level must be between 0 and {upper_bound}")


def _max_property_level(template: PropertyTemplate) -> int:
    if len(template.rents) == 0:
        raise ValueError("property template must define at least one rent level")
    return len(template.rents) - 1


def _required_non_negative_amount(card: CardDefinition) -> int:
    if card.amount is None:
        raise ValueError(f"{card.card_type} card requires amount")
    if card.amount < 0:
        raise ValueError("card amount must be non-negative")
    return card.amount


def _required_direction(card: CardDefinition) -> MoveDirection:
    if card.direction is None:
        raise ValueError("MOVE card requires direction")
    return card.direction


def _required_steps(card: CardDefinition, field_name: Literal["min_steps", "max_steps"]) -> int:
    value = card.min_steps if field_name == "min_steps" else card.max_steps
    if value is None:
        raise ValueError(f"MOVE card requires {field_name}")
    if value < 0:
        raise ValueError("MOVE card steps must be non-negative")

    if field_name == "max_steps" and card.min_steps is not None and value < card.min_steps:
        raise ValueError("MOVE card max_steps must be greater than or equal to min_steps")

    return value
