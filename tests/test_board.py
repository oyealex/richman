"""Tests for the immutable board spatial model."""

from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from richman.board import (
    Board,
    MoveResult,
    create,
    get_cell_type,
    get_property_template,
    get_range,
    move,
    total_cells,
)
from richman.domain import BoardCellDefinition, CellType, GameConfig, PropertyTemplate

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BOARD_ROOT = PROJECT_ROOT / "src" / "richman" / "board"
FORBIDDEN_BOARD_IMPORTS = {
    "richman.rules",
    "richman.player",
    "richman.engine",
    "richman.render",
    "richman.adapters",
}


def _property_template(name: str = "中山路") -> PropertyTemplate:
    return PropertyTemplate(
        name=name,
        price=300,
        rents=(30, 60, 120, 240),
        upgrade_cost=150,
    )


def _sample_config() -> GameConfig:
    return GameConfig(
        board_cells=(
            BoardCellDefinition(CellType.START),
            BoardCellDefinition(CellType.PROPERTY, _property_template("中山路")),
            BoardCellDefinition(CellType.CHANCE),
            BoardCellDefinition(CellType.PROPERTY, _property_template("南京路")),
            BoardCellDefinition(CellType.GO_TO_JAIL),
            BoardCellDefinition(CellType.JAIL_SPACE),
            BoardCellDefinition(CellType.BLANK),
            BoardCellDefinition(CellType.PROPERTY, _property_template("解放路")),
        ),
        cards=(),
    )


def _mutate_attribute(instance: object, name: str, value: object) -> None:
    setattr(instance, name, value)


def test_board_public_api_exports_common_models() -> None:
    from richman.board import Board, MoveResult, create, get_cell_type

    board = create(_sample_config())

    assert isinstance(board, Board)
    assert MoveResult(new_position=1, start_crossings=0)
    assert get_cell_type(board, 0) is CellType.START


def test_board_source_does_not_import_higher_modules() -> None:
    imported_modules: set[str] = set()

    for path in BOARD_ROOT.glob("*.py"):
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
            for prefix in FORBIDDEN_BOARD_IMPORTS
        )
    }

    assert forbidden == set()


def test_board_is_created_from_config_and_is_immutable() -> None:
    board = create(_sample_config())

    assert isinstance(board, Board)
    assert total_cells(board) == 8
    assert board.start_position == 0
    assert board.cells[1].property_template == _property_template("中山路")

    with pytest.raises(FrozenInstanceError):
        _mutate_attribute(board, "start_position", 2)


@pytest.mark.parametrize(
    "board_cells",
    [
        (),
        (
            BoardCellDefinition(CellType.BLANK),
            BoardCellDefinition(CellType.PROPERTY, _property_template()),
        ),
        (
            BoardCellDefinition(CellType.START),
            BoardCellDefinition(CellType.START),
        ),
        (
            BoardCellDefinition(CellType.START),
            BoardCellDefinition(CellType.PROPERTY),
        ),
        (
            BoardCellDefinition(CellType.START, _property_template()),
            BoardCellDefinition(CellType.BLANK),
        ),
    ],
)
def test_create_rejects_invalid_static_config(
    board_cells: tuple[BoardCellDefinition, ...],
) -> None:
    with pytest.raises(ValueError):
        create(GameConfig(board_cells=board_cells, cards=()))


def test_static_queries_return_cell_type_and_property_template() -> None:
    board = create(_sample_config())

    assert total_cells(board) == 8
    assert get_cell_type(board, 0) is CellType.START
    assert get_cell_type(board, 1) is CellType.PROPERTY
    assert get_property_template(board, 1) == _property_template("中山路")
    assert get_property_template(board, 2) is None


@pytest.mark.parametrize("position", [-1, 8])
def test_static_queries_reject_invalid_positions(position: int) -> None:
    board = create(_sample_config())

    with pytest.raises(ValueError):
        get_cell_type(board, position)
    with pytest.raises(ValueError):
        get_property_template(board, position)


def test_move_handles_forward_backward_and_zero_steps() -> None:
    board = create(_sample_config())

    assert move(board, 6, 3) == MoveResult(new_position=1, start_crossings=1)
    assert move(board, 1, -3) == MoveResult(new_position=6, start_crossings=1)
    assert move(board, 4, 0) == MoveResult(new_position=4, start_crossings=0)


def test_move_counts_start_entries_without_counting_initial_start() -> None:
    board = create(_sample_config())

    assert move(board, 0, 1) == MoveResult(new_position=1, start_crossings=0)
    assert move(board, 0, 8) == MoveResult(new_position=0, start_crossings=1)
    assert move(board, 6, 10) == MoveResult(new_position=0, start_crossings=2)
    assert move(board, 1, -1) == MoveResult(new_position=0, start_crossings=1)


@pytest.mark.parametrize("position", [-1, 8])
def test_move_rejects_invalid_start_position(position: int) -> None:
    board = create(_sample_config())

    with pytest.raises(ValueError):
        move(board, position, 1)


def test_range_query_uses_stable_order_and_deduplicates_positions() -> None:
    board = create(_sample_config())

    assert get_range(board, 0, 0) == [0]
    assert get_range(board, 0, 2) == [0, 1, 2, 7, 6]
    assert get_range(board, 6, 3) == [6, 7, 0, 1, 5, 4, 3]
    assert get_range(board, 0, 8) == [0, 1, 2, 3, 4, 5, 6, 7]


def test_range_query_rejects_invalid_center_and_negative_radius() -> None:
    board = create(_sample_config())

    with pytest.raises(ValueError):
        get_range(board, -1, 1)
    with pytest.raises(ValueError):
        get_range(board, 8, 1)
    with pytest.raises(ValueError):
        get_range(board, 0, -1)
