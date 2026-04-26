"""Shared domain models for the Richman game.

This module intentionally contains only data definitions. Board movement,
rules, player decisions, engine mutation, rendering, and I/O live in other
modules.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum

START_BONUS = 200
JAIL_ROUNDS = 3
DICE_SIDES = 6
DEMOLISH_RANGE = 3


class CellType(StrEnum):
    """Board cell categories."""

    START = "START"
    PROPERTY = "PROPERTY"
    CHANCE = "CHANCE"
    GO_TO_JAIL = "GO_TO_JAIL"
    JAIL_SPACE = "JAIL_SPACE"
    BLANK = "BLANK"


class CardType(StrEnum):
    """Card categories in the chance deck."""

    MONEY_GAIN = "MONEY_GAIN"
    MONEY_LOSS = "MONEY_LOSS"
    MOVE = "MOVE"
    GO_TO_JAIL = "GO_TO_JAIL"
    JAIL_PASS = "JAIL_PASS"
    DEMOLISH = "DEMOLISH"


class MoveDirection(StrEnum):
    """Directions supported by movement cards."""

    FORWARD = "FORWARD"
    BACKWARD = "BACKWARD"
    RANDOM = "RANDOM"


class Action(StrEnum):
    """Player actions selected through the player boundary."""

    BUY = "BUY"
    UPGRADE = "UPGRADE"
    USE_DEMOLISH = "USE_DEMOLISH"
    USE_JAIL_PASS = "USE_JAIL_PASS"
    ACCEPT_JAIL = "ACCEPT_JAIL"
    SKIP = "SKIP"


class Phase(StrEnum):
    """Turn phases owned by the engine."""

    EFFECT_UPDATE = "EFFECT_UPDATE"
    DICE_ROLL = "DICE_ROLL"
    LANDING = "LANDING"
    ACTION = "ACTION"
    END = "END"


class GameEventType(StrEnum):
    """Event names emitted by the engine and displayed by renderers."""

    TURN_START = "TURN_START"
    TURN_END = "TURN_END"
    JAIL_TICKED = "JAIL_TICKED"
    JAIL_RELEASED = "JAIL_RELEASED"
    WAIT_DICE = "WAIT_DICE"
    DICE_ROLLED = "DICE_ROLLED"
    PLAYER_MOVED = "PLAYER_MOVED"
    START_BONUS_GRANTED = "START_BONUS_GRANTED"
    LANDED_ON = "LANDED_ON"
    PROPERTY_AVAILABLE = "PROPERTY_AVAILABLE"
    PROPERTY_UPGRADABLE = "PROPERTY_UPGRADABLE"
    RENT_DUE = "RENT_DUE"
    RENT_PAID = "RENT_PAID"
    RENT_UNPAID_BANKRUPTCY = "RENT_UNPAID_BANKRUPTCY"
    RENT_SKIPPED_OWNER_IN_JAIL = "RENT_SKIPPED_OWNER_IN_JAIL"
    CARD_DRAWN = "CARD_DRAWN"
    MONEY_GAINED = "MONEY_GAINED"
    MONEY_LOST = "MONEY_LOST"
    PLAYER_SENT_TO_JAIL = "PLAYER_SENT_TO_JAIL"
    JAIL_PASS_USED = "JAIL_PASS_USED"
    PROPERTY_BOUGHT = "PROPERTY_BOUGHT"
    PROPERTY_UPGRADED = "PROPERTY_UPGRADED"
    PROPERTY_DEMOLISHED = "PROPERTY_DEMOLISHED"
    PROPERTY_RECLAIMED = "PROPERTY_RECLAIMED"
    PLAYER_BANKRUPT = "PLAYER_BANKRUPT"
    WAIT_ACTION = "WAIT_ACTION"
    ACTION_CHOSEN = "ACTION_CHOSEN"
    GAME_OVER = "GAME_OVER"


@dataclass(frozen=True, slots=True)
class PropertyTemplate:
    """Immutable recipe for a property cell."""

    name: str
    price: int
    rents: tuple[int, int, int, int]
    upgrade_cost: int


@dataclass(frozen=True, slots=True)
class CardDefinition:
    """Immutable recipe for a chance card."""

    card_type: CardType
    description: str
    amount: int | None = None
    direction: MoveDirection | None = None
    min_steps: int | None = None
    max_steps: int | None = None


@dataclass(frozen=True, slots=True)
class BoardCellDefinition:
    """Static board cell configuration."""

    cell_type: CellType
    property_template: PropertyTemplate | None = None


@dataclass(frozen=True, slots=True)
class GameConfig:
    """Static game setup."""

    board_cells: tuple[BoardCellDefinition, ...]
    cards: tuple[CardDefinition, ...]
    start_cash: int = 2_000
    start_bonus: int = START_BONUS
    jail_rounds: int = JAIL_ROUNDS
    demolish_range: int = DEMOLISH_RANGE
    dice_sides: int = DICE_SIDES


@dataclass(frozen=True, slots=True)
class GrantMoneyIntent:
    """Intent to grant money to the active player."""

    amount: int


@dataclass(frozen=True, slots=True)
class DeductMoneyIntent:
    """Intent to deduct money from the active player."""

    amount: int


@dataclass(frozen=True, slots=True)
class MoveIntent:
    """Intent to move the active player."""

    direction: MoveDirection
    min_steps: int
    max_steps: int


@dataclass(frozen=True, slots=True)
class GoToJailIntent:
    """Intent to trigger the go-to-jail flow."""


@dataclass(frozen=True, slots=True)
class ObtainCardIntent:
    """Intent to add a retainable card to the active player's hand."""

    card_type: CardType


GrantMoney = GrantMoneyIntent
DeductMoney = DeductMoneyIntent
Move = MoveIntent
GoToJail = GoToJailIntent
ObtainCard = ObtainCardIntent
type CardIntent = (
    GrantMoneyIntent | DeductMoneyIntent | MoveIntent | GoToJailIntent | ObtainCardIntent
)


@dataclass(slots=True)
class PropertyState:
    """Runtime property state owned by InternalGameState."""

    position: int
    owner_player_index: int | None
    level: int = 0
    acquired_at: int = 0
    purchase_price: int = 0
    upgrade_invested: int = 0


@dataclass(frozen=True, slots=True)
class PropertyRef:
    """Reference from a player holding to the property state store."""

    position: int


@dataclass(slots=True)
class HandCards:
    """Retainable card counters held by a player."""

    jail_pass: int = 0
    demolish: int = 0


@dataclass(slots=True)
class PlayerState:
    """Complete runtime state for one player."""

    name: str
    cash: int
    position: int = 0
    holdings: list[PropertyRef] = field(default_factory=list)
    hand: HandCards = field(default_factory=HandCards)
    jail_rounds_left: int = 0
    bankrupt: bool = False


@dataclass(frozen=True, slots=True)
class ReclaimPlan:
    """Bankruptcy recovery plan calculated by rules."""

    reclaimed: tuple[tuple[int, int], ...]
    total_refund: int
    remaining_shortfall: int


@dataclass(frozen=True, slots=True)
class GameEvent:
    """A structured event emitted by the engine."""

    event_type: GameEventType
    data: Mapping[str, object] = field(default_factory=dict)


@dataclass(slots=True)
class InternalGameState:
    """The complete mutable state tree owned by the engine."""

    players: list[PlayerState]
    turn: int = 0
    current_player_index: int = 0
    phase: Phase = Phase.EFFECT_UPDATE
    dice_value: int | None = None
    properties_by_position: dict[int, PropertyState] = field(default_factory=dict)
    event_log: list[GameEvent] = field(default_factory=list)
    available_actions: list[Action] | None = None


@dataclass(frozen=True, slots=True)
class PublicCellInfo:
    """Publicly visible board cell information."""

    position: int
    cell_type: CellType
    property_name: str | None = None
    owner_player_index: int | None = None
    level: int | None = None


@dataclass(frozen=True, slots=True)
class PublicBoardInfo:
    """Public board information for a render snapshot or player view."""

    cells: tuple[PublicCellInfo, ...]


@dataclass(frozen=True, slots=True)
class PublicPlayerInfo:
    """Publicly visible player information."""

    player_index: int
    name: str
    position: int
    jail_rounds_left: int = 0
    bankrupt: bool = False


@dataclass(frozen=True, slots=True)
class PlayerView:
    """Decision-oriented view for a player."""

    turn: int
    current_player_index: int
    viewer_index: int
    phase: Phase
    dice_value: int | None
    public_board: PublicBoardInfo
    public_players: tuple[PublicPlayerInfo, ...]
    viewer_private: PlayerState
    viewer_private_properties: tuple[PropertyState, ...] = ()
    available_actions: tuple[Action, ...] = ()


@dataclass(frozen=True, slots=True)
class GameSnapshot:
    """Render-oriented snapshot generated for a specific viewer."""

    turn: int
    current_player_index: int
    viewer_index: int
    phase: Phase
    dice_value: int | None
    public_board: PublicBoardInfo
    public_players: tuple[PublicPlayerInfo, ...]
    viewer_private: PlayerState
    viewer_private_properties: tuple[PropertyState, ...]
    event_log: tuple[GameEvent, ...]
    available_actions: tuple[Action, ...] | None = None
