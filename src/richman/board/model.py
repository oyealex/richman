"""Immutable board spatial model and circular movement helpers."""

from __future__ import annotations

from dataclasses import dataclass

from richman.domain import BoardCellDefinition, CellType, GameConfig, PropertyTemplate


@dataclass(frozen=True, slots=True)
class Board:
    """Immutable static board layout."""

    cells: tuple[BoardCellDefinition, ...]
    start_position: int


@dataclass(frozen=True, slots=True)
class MoveResult:
    """Result of moving around the circular board."""

    new_position: int
    start_crossings: int


def create(config: GameConfig) -> Board:
    """Create an immutable board from static game configuration."""

    cells = tuple(config.board_cells)
    if not cells:
        raise ValueError("board must contain at least one cell")

    start_positions = [
        position for position, cell in enumerate(cells) if cell.cell_type is CellType.START
    ]
    if len(start_positions) != 1:
        raise ValueError("board must contain exactly one START cell")

    for position, cell in enumerate(cells):
        if cell.cell_type is CellType.PROPERTY and cell.property_template is None:
            raise ValueError(f"PROPERTY cell at position {position} requires a template")
        if cell.cell_type is not CellType.PROPERTY and cell.property_template is not None:
            raise ValueError(f"non-PROPERTY cell at position {position} must not define a template")

    return Board(cells=cells, start_position=start_positions[0])


def total_cells(board: Board) -> int:
    """Return the number of cells in the board."""

    return len(board.cells)


def get_cell_type(board: Board, position: int) -> CellType:
    """Return the cell type at a valid board position."""

    _validate_position(board, position)
    return board.cells[position].cell_type


def get_property_template(board: Board, position: int) -> PropertyTemplate | None:
    """Return the property template at a valid board position, if any."""

    _validate_position(board, position)
    return board.cells[position].property_template


def move(board: Board, position: int, steps: int) -> MoveResult:
    """Move from position by signed steps and count START entries along the path."""

    _validate_position(board, position)
    if steps == 0:
        return MoveResult(new_position=position, start_crossings=0)

    cell_count = total_cells(board)
    direction = 1 if steps > 0 else -1
    current = position
    start_crossings = 0

    for _ in range(abs(steps)):
        current = (current + direction) % cell_count
        if current == board.start_position:
            start_crossings += 1

    return MoveResult(new_position=current, start_crossings=start_crossings)


def get_range(board: Board, center: int, radius: int) -> list[int]:
    """Return center plus clockwise and counterclockwise positions within radius."""

    _validate_position(board, center)
    if radius < 0:
        raise ValueError("radius must be greater than or equal to 0")

    cell_count = total_cells(board)
    positions: list[int] = []
    seen: set[int] = set()

    def append_once(position: int) -> None:
        if position not in seen:
            positions.append(position)
            seen.add(position)

    append_once(center)

    for offset in range(1, radius + 1):
        append_once((center + offset) % cell_count)

    for offset in range(1, radius + 1):
        append_once((center - offset) % cell_count)

    return positions


def _validate_position(board: Board, position: int) -> None:
    if position < 0 or position >= total_cells(board):
        raise ValueError(f"position {position} is outside board range")
