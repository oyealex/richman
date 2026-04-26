"""Tests for the shared domain model layer."""

from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from richman.domain import (
    DEMOLISH_RANGE,
    DICE_SIDES,
    JAIL_ROUNDS,
    START_BONUS,
    Action,
    BoardCellDefinition,
    CardDefinition,
    CardIntent,
    CardType,
    CellType,
    DeductMoneyIntent,
    GameConfig,
    GameEvent,
    GameEventType,
    GameSnapshot,
    GoToJailIntent,
    GrantMoneyIntent,
    HandCards,
    InternalGameState,
    MoveDirection,
    MoveIntent,
    ObtainCardIntent,
    Phase,
    PlayerState,
    PlayerView,
    PropertyRef,
    PropertyState,
    PropertyTemplate,
    PublicBoardInfo,
    PublicCellInfo,
    PublicPlayerInfo,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DOMAIN_ROOT = PROJECT_ROOT / "src" / "richman" / "domain"
FORBIDDEN_DOMAIN_IMPORTS = {
    "richman.board",
    "richman.rules",
    "richman.player",
    "richman.engine",
    "richman.render",
    "richman.adapters",
}


def _mutate_attribute(instance: object, name: str, value: object) -> None:
    setattr(instance, name, value)


def test_domain_public_api_exports_common_models() -> None:
    from richman.domain import Action, GameSnapshot, PlayerState

    assert Action.SKIP.value == "SKIP"
    assert PlayerState(name="Alice", cash=2_000).name == "Alice"
    assert GameSnapshot


def test_domain_source_does_not_import_higher_modules() -> None:
    imported_modules: set[str] = set()

    for path in DOMAIN_ROOT.glob("*.py"):
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
            for prefix in FORBIDDEN_DOMAIN_IMPORTS
        )
    }

    assert forbidden == set()


def test_enumerations_and_constants_match_design() -> None:
    assert {item.name for item in CellType} == {
        "START",
        "PROPERTY",
        "CHANCE",
        "GO_TO_JAIL",
        "JAIL_SPACE",
        "BLANK",
    }
    assert {item.name for item in CardType} == {
        "MONEY_GAIN",
        "MONEY_LOSS",
        "MOVE",
        "GO_TO_JAIL",
        "JAIL_PASS",
        "DEMOLISH",
    }
    assert {item.name for item in MoveDirection} == {"FORWARD", "BACKWARD", "RANDOM"}
    assert {item.name for item in Action} == {
        "BUY",
        "UPGRADE",
        "USE_DEMOLISH",
        "USE_JAIL_PASS",
        "ACCEPT_JAIL",
        "SKIP",
    }
    assert {item.name for item in Phase} == {
        "EFFECT_UPDATE",
        "DICE_ROLL",
        "LANDING",
        "ACTION",
        "END",
    }
    assert START_BONUS > 0
    assert JAIL_ROUNDS == 3
    assert DICE_SIDES == 6
    assert DEMOLISH_RANGE > 0


def test_templates_and_config_are_immutable() -> None:
    template = PropertyTemplate(
        name="中山路",
        price=300,
        rents=(30, 60, 120, 240),
        upgrade_cost=150,
    )
    card = CardDefinition(
        card_type=CardType.MOVE,
        description="前进 1 到 3 步",
        direction=MoveDirection.FORWARD,
        min_steps=1,
        max_steps=3,
    )
    config = GameConfig(
        board_cells=(BoardCellDefinition(CellType.PROPERTY, template),),
        cards=(card,),
    )

    with pytest.raises(FrozenInstanceError):
        _mutate_attribute(template, "price", 100)
    with pytest.raises(FrozenInstanceError):
        _mutate_attribute(card, "description", "修改")
    with pytest.raises(FrozenInstanceError):
        _mutate_attribute(config, "start_cash", 1)

    assert template.rents == (30, 60, 120, 240)
    assert card.direction is MoveDirection.FORWARD
    assert config.start_cash == 2_000
    assert config.start_bonus == START_BONUS
    assert config.jail_rounds == JAIL_ROUNDS
    assert config.demolish_range == DEMOLISH_RANGE
    assert config.dice_sides == DICE_SIDES


def test_card_intents_are_structured_and_side_effect_free() -> None:
    gain: CardIntent = GrantMoneyIntent(amount=100)
    loss: CardIntent = DeductMoneyIntent(amount=50)
    move: CardIntent = MoveIntent(
        direction=MoveDirection.RANDOM,
        min_steps=1,
        max_steps=6,
    )
    jail: CardIntent = GoToJailIntent()
    retain: CardIntent = ObtainCardIntent(card_type=CardType.DEMOLISH)

    assert gain == GrantMoneyIntent(amount=100)
    assert loss == DeductMoneyIntent(amount=50)
    assert move == MoveIntent(direction=MoveDirection.RANDOM, min_steps=1, max_steps=6)
    assert jail == GoToJailIntent()
    assert retain == ObtainCardIntent(card_type=CardType.DEMOLISH)


def test_player_holdings_reference_internal_property_state() -> None:
    property_state = PropertyState(
        position=3,
        owner_player_index=0,
        level=2,
        acquired_at=4,
        purchase_price=300,
        upgrade_invested=150,
    )
    player = PlayerState(
        name="Alice",
        cash=1_500,
        position=3,
        holdings=[PropertyRef(position=3)],
        hand=HandCards(jail_pass=1, demolish=2),
    )
    state = InternalGameState(
        players=[player],
        properties_by_position={3: property_state},
        event_log=[GameEvent(GameEventType.PROPERTY_BOUGHT, {"position": 3})],
        available_actions=[Action.UPGRADE],
    )

    holding = player.holdings[0]

    assert holding.position == 3
    assert not hasattr(holding, "level")
    assert not hasattr(holding, "owner_player_index")
    assert state.properties_by_position[3].level == 2
    assert state.properties_by_position[3].purchase_price == 300
    assert state.available_actions == [Action.UPGRADE]


def test_snapshot_and_player_view_separate_public_and_private_data() -> None:
    public_board = PublicBoardInfo(
        cells=(
            PublicCellInfo(
                position=0,
                cell_type=CellType.START,
            ),
            PublicCellInfo(
                position=3,
                cell_type=CellType.PROPERTY,
                property_name="中山路",
                owner_player_index=0,
                level=1,
            ),
        )
    )
    public_players = (
        PublicPlayerInfo(player_index=0, name="Alice", position=3),
        PublicPlayerInfo(player_index=1, name="Bob", position=6, jail_rounds_left=1),
    )
    viewer_private = PlayerState(
        name="Alice",
        cash=1_500,
        position=3,
        hand=HandCards(jail_pass=1, demolish=0),
    )
    viewer_property = PropertyState(
        position=3,
        owner_player_index=0,
        level=1,
        acquired_at=7,
        purchase_price=300,
        upgrade_invested=150,
    )
    event = GameEvent(GameEventType.WAIT_ACTION, {"available_actions": ("UPGRADE", "SKIP")})
    snapshot = GameSnapshot(
        turn=2,
        current_player_index=0,
        viewer_index=0,
        phase=Phase.ACTION,
        dice_value=4,
        public_board=public_board,
        public_players=public_players,
        viewer_private=viewer_private,
        viewer_private_properties=(viewer_property,),
        event_log=(event,),
        available_actions=(Action.UPGRADE, Action.SKIP),
    )
    view = PlayerView(
        turn=snapshot.turn,
        current_player_index=snapshot.current_player_index,
        viewer_index=snapshot.viewer_index,
        phase=snapshot.phase,
        dice_value=snapshot.dice_value,
        public_board=snapshot.public_board,
        public_players=snapshot.public_players,
        viewer_private=snapshot.viewer_private,
        viewer_private_properties=snapshot.viewer_private_properties,
        available_actions=(Action.UPGRADE, Action.SKIP),
    )

    assert not hasattr(snapshot.public_players[1], "cash")
    assert not hasattr(snapshot.public_players[1], "hand")
    assert snapshot.viewer_private.cash == 1_500
    assert snapshot.viewer_private_properties[0].upgrade_invested == 150
    assert view.viewer_private.hand.jail_pass == 1
    assert view.available_actions == (Action.UPGRADE, Action.SKIP)


def test_event_type_list_covers_module_design_events() -> None:
    expected_event_names = {
        "TURN_START",
        "TURN_END",
        "JAIL_TICKED",
        "JAIL_RELEASED",
        "WAIT_DICE",
        "DICE_ROLLED",
        "PLAYER_MOVED",
        "START_BONUS_GRANTED",
        "LANDED_ON",
        "PROPERTY_AVAILABLE",
        "PROPERTY_UPGRADABLE",
        "RENT_DUE",
        "RENT_PAID",
        "RENT_UNPAID_BANKRUPTCY",
        "RENT_SKIPPED_OWNER_IN_JAIL",
        "CARD_DRAWN",
        "MONEY_GAINED",
        "MONEY_LOST",
        "PLAYER_SENT_TO_JAIL",
        "JAIL_PASS_USED",
        "PROPERTY_BOUGHT",
        "PROPERTY_UPGRADED",
        "PROPERTY_DEMOLISHED",
        "PROPERTY_RECLAIMED",
        "PLAYER_BANKRUPT",
        "WAIT_ACTION",
        "ACTION_CHOSEN",
        "GAME_OVER",
    }

    assert {item.name for item in GameEventType} == expected_event_names
