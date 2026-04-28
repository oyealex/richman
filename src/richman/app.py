"""Application assembly for Richman.

The app layer wires configuration, board, players, renderer, and engine
together. It does not own or mutate game state directly.
"""

from __future__ import annotations

from collections.abc import Sequence

from richman.board import create as create_board
from richman.domain import (
    BoardCellDefinition,
    CardDefinition,
    CardType,
    CellType,
    GameConfig,
    InternalGameState,
    MoveDirection,
    PropertyTemplate,
)
from richman.engine import GameEngine
from richman.player import AIPlayer, Player
from richman.render import ConsoleRenderer, Renderer

MIN_PLAYERS = 2
MAX_PLAYERS = 4

_MAX_TURNS_MESSAGE = "max_turns reached before game over"


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
    )


def create_players(count: int) -> tuple[Player, ...]:
    """Create AI players for the default app mode."""

    if count < MIN_PLAYERS or count > MAX_PLAYERS:
        raise ValueError(f"players must be between {MIN_PLAYERS} and {MAX_PLAYERS}")

    return tuple(AIPlayer(f"AI {index}") for index in range(1, count + 1))


def create_engine(
    config: GameConfig,
    players: Sequence[Player],
    renderer: Renderer,
    seed: int | None = None,
) -> GameEngine:
    """Assemble a GameEngine from app-level dependencies."""

    board = create_board(config)
    return GameEngine.create(config, board, players, renderer, seed=seed)


def run_game(
    players_count: int = MIN_PLAYERS,
    max_turns: int | None = None,
    seed: int | None = None,
    renderer: Renderer | None = None,
    config: GameConfig | None = None,
) -> InternalGameState:
    """Run one assembled game and return the final or bounded state."""

    game_config = config if config is not None else build_default_config()
    game_renderer = renderer if renderer is not None else ConsoleRenderer()
    players = create_players(players_count)
    engine = create_engine(game_config, players, game_renderer, seed=seed)

    try:
        return engine.start(max_turns=max_turns)
    except RuntimeError as error:
        if str(error) != _MAX_TURNS_MESSAGE:
            raise
        return engine.get_state()
