"""Tests for TUI layout validation."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from richman.adapters.textual_tui.layout import (
    TuiLayoutValidationResult,
    validate_tui_layout,
)
from richman.app import build_default_config
from richman.domain import (
    BoardCellDefinition,
    CellType,
    GameConfig,
    TuiCellLayout,
    TuiLayout,
    TuiRect,
)


def _make_config(
    tui_layout: TuiLayout | None = None,
    board_cells: tuple[BoardCellDefinition, ...] | None = None,
) -> GameConfig:
    if board_cells is None:
        board_cells = (
            BoardCellDefinition(CellType.START),
            BoardCellDefinition(CellType.JAIL_SPACE),
        )
    return GameConfig(board_cells=board_cells, cards=(), tui_layout=tui_layout)


class TestValidLayout:
    def test_default_layout_passes_validation(self) -> None:
        config = build_default_config()
        result = validate_tui_layout(config)

        assert result.errors == ()
        assert result.warnings == ()

    def test_validation_result_is_immutable(self) -> None:
        result = TuiLayoutValidationResult()

        with pytest.raises(FrozenInstanceError):
            result.errors = ("oops",)  # type: ignore[misc]


class TestMissingLayout:
    def test_tui_layout_none_returns_error(self) -> None:
        config = _make_config(tui_layout=None)
        result = validate_tui_layout(config)

        assert len(result.errors) == 1
        assert "缺少 tui_layout" in result.errors[0]
        assert result.warnings == ()


class TestGridDimensions:
    def test_rows_zero_rejected(self) -> None:
        layout = TuiLayout(
            rows=0,
            columns=13,
            center=TuiRect(row=0, column=0, row_span=1, column_span=1),
            cells=(TuiCellLayout(position=0, row=1, column=1),),
        )
        config = _make_config(tui_layout=layout)
        result = validate_tui_layout(config)

        assert any("rows" in e for e in result.errors)

    def test_rows_negative_rejected(self) -> None:
        layout = TuiLayout(
            rows=-1,
            columns=13,
            center=TuiRect(row=0, column=0, row_span=1, column_span=1),
            cells=(TuiCellLayout(position=0, row=1, column=1),),
        )
        config = _make_config(tui_layout=layout)
        result = validate_tui_layout(config)

        assert any("rows" in e for e in result.errors)

    def test_columns_zero_rejected(self) -> None:
        layout = TuiLayout(
            rows=9,
            columns=0,
            center=TuiRect(row=0, column=0, row_span=1, column_span=1),
            cells=(TuiCellLayout(position=0, row=1, column=1),),
        )
        config = _make_config(tui_layout=layout)
        result = validate_tui_layout(config)

        assert any("columns" in e for e in result.errors)


class TestCenterValidation:
    def test_center_row_negative_rejected(self) -> None:
        layout = TuiLayout(
            rows=9,
            columns=13,
            center=TuiRect(row=-1, column=0, row_span=5, column_span=10),
            cells=(TuiCellLayout(position=0, row=8, column=0),),
        )
        config = _make_config(tui_layout=layout)
        result = validate_tui_layout(config)

        assert any("center.row" in e for e in result.errors)

    def test_center_column_negative_rejected(self) -> None:
        layout = TuiLayout(
            rows=9,
            columns=13,
            center=TuiRect(row=0, column=-2, row_span=5, column_span=10),
            cells=(TuiCellLayout(position=0, row=8, column=0),),
        )
        config = _make_config(tui_layout=layout)
        result = validate_tui_layout(config)

        assert any("center.column" in e for e in result.errors)

    def test_center_row_span_zero_rejected(self) -> None:
        layout = TuiLayout(
            rows=9,
            columns=13,
            center=TuiRect(row=0, column=0, row_span=0, column_span=10),
            cells=(TuiCellLayout(position=0, row=8, column=0),),
        )
        config = _make_config(tui_layout=layout)
        result = validate_tui_layout(config)

        assert any("row_span" in e for e in result.errors)

    def test_center_column_span_zero_rejected(self) -> None:
        layout = TuiLayout(
            rows=9,
            columns=13,
            center=TuiRect(row=0, column=0, row_span=5, column_span=0),
            cells=(TuiCellLayout(position=0, row=8, column=0),),
        )
        config = _make_config(tui_layout=layout)
        result = validate_tui_layout(config)

        assert any("column_span" in e for e in result.errors)

    def test_center_out_of_bounds_row(self) -> None:
        layout = TuiLayout(
            rows=5,
            columns=13,
            center=TuiRect(row=3, column=0, row_span=3, column_span=1),
            cells=(TuiCellLayout(position=0, row=0, column=12),),
        )
        config = _make_config(tui_layout=layout)
        result = validate_tui_layout(config)

        assert any("center 矩形越界" in e for e in result.errors)

    def test_center_out_of_bounds_column(self) -> None:
        layout = TuiLayout(
            rows=9,
            columns=5,
            center=TuiRect(row=0, column=3, row_span=1, column_span=3),
            cells=(TuiCellLayout(position=0, row=8, column=0),),
        )
        config = _make_config(tui_layout=layout)
        result = validate_tui_layout(config)

        assert any("center 矩形越界" in e for e in result.errors)


class TestPositionCoverage:
    def test_missing_position_rejected(self) -> None:
        layout = TuiLayout(
            rows=9,
            columns=13,
            center=TuiRect(row=0, column=0, row_span=1, column_span=1),
            cells=(TuiCellLayout(position=0, row=8, column=0),),
        )
        config = _make_config(
            tui_layout=layout,
            board_cells=(
                BoardCellDefinition(CellType.START),
                BoardCellDefinition(CellType.JAIL_SPACE),
            ),
        )
        result = validate_tui_layout(config)

        assert any("缺失" in e and "position 1" in e for e in result.errors)

    def test_extra_position_rejected(self) -> None:
        layout = TuiLayout(
            rows=9,
            columns=13,
            center=TuiRect(row=0, column=0, row_span=1, column_span=1),
            cells=(
                TuiCellLayout(position=0, row=8, column=0),
                TuiCellLayout(position=1, row=8, column=2),
                TuiCellLayout(position=99, row=6, column=0),
            ),
        )
        config = _make_config(
            tui_layout=layout,
            board_cells=(
                BoardCellDefinition(CellType.START),
                BoardCellDefinition(CellType.JAIL_SPACE),
            ),
        )
        result = validate_tui_layout(config)

        assert any("不存在的 position 99" in e for e in result.errors)

    def test_duplicate_position_rejected(self) -> None:
        layout = TuiLayout(
            rows=9,
            columns=13,
            center=TuiRect(row=0, column=0, row_span=1, column_span=1),
            cells=(
                TuiCellLayout(position=0, row=8, column=0),
                TuiCellLayout(position=0, row=8, column=2),
            ),
        )
        config = _make_config(
            tui_layout=layout,
            board_cells=(
                BoardCellDefinition(CellType.START),
                BoardCellDefinition(CellType.JAIL_SPACE),
            ),
        )
        result = validate_tui_layout(config)

        assert any("position 0" in e and "重复" in e for e in result.errors)


class TestCellCoordinates:
    def test_row_out_of_bounds_rejected(self) -> None:
        layout = TuiLayout(
            rows=5,
            columns=13,
            center=TuiRect(row=0, column=0, row_span=1, column_span=1),
            cells=(TuiCellLayout(position=0, row=5, column=0),),
        )
        config = _make_config(tui_layout=layout)
        result = validate_tui_layout(config)

        assert any("row=5" in e and "越界" in e for e in result.errors)

    def test_row_negative_rejected(self) -> None:
        layout = TuiLayout(
            rows=9,
            columns=13,
            center=TuiRect(row=0, column=0, row_span=1, column_span=1),
            cells=(TuiCellLayout(position=0, row=-1, column=0),),
        )
        config = _make_config(tui_layout=layout)
        result = validate_tui_layout(config)

        assert any("row=-1" in e and "越界" in e for e in result.errors)

    def test_column_out_of_bounds_rejected(self) -> None:
        layout = TuiLayout(
            rows=9,
            columns=5,
            center=TuiRect(row=0, column=0, row_span=1, column_span=1),
            cells=(TuiCellLayout(position=0, row=0, column=5),),
        )
        config = _make_config(tui_layout=layout)
        result = validate_tui_layout(config)

        assert any("column=5" in e and "越界" in e for e in result.errors)

    def test_duplicate_coordinates_rejected(self) -> None:
        layout = TuiLayout(
            rows=9,
            columns=13,
            center=TuiRect(row=0, column=0, row_span=1, column_span=1),
            cells=(
                TuiCellLayout(position=0, row=8, column=0),
                TuiCellLayout(position=1, row=8, column=0),
            ),
        )
        config = _make_config(
            tui_layout=layout,
            board_cells=(
                BoardCellDefinition(CellType.START),
                BoardCellDefinition(CellType.JAIL_SPACE),
            ),
        )
        result = validate_tui_layout(config)

        assert any("相同 slot 坐标" in e for e in result.errors)

    def test_cell_in_center_rejected(self) -> None:
        layout = TuiLayout(
            rows=9,
            columns=13,
            center=TuiRect(row=0, column=0, row_span=5, column_span=10),
            cells=(TuiCellLayout(position=0, row=2, column=3),),
        )
        config = _make_config(tui_layout=layout)
        result = validate_tui_layout(config)

        assert any("落入 center" in e for e in result.errors)


class TestImmutability:
    def test_validation_does_not_modify_config(self) -> None:
        config = build_default_config()
        original_rows = config.tui_layout.rows  # type: ignore[union-attr]
        original_center_row = config.tui_layout.center.row  # type: ignore[union-attr]

        validate_tui_layout(config)

        assert config.tui_layout.rows == original_rows  # type: ignore[union-attr]
        assert config.tui_layout.center.row == original_center_row  # type: ignore[union-attr]


class TestMultipleErrors:
    def test_multiple_errors_collected(self) -> None:
        layout = TuiLayout(
            rows=0,
            columns=0,
            center=TuiRect(row=0, column=0, row_span=0, column_span=0),
            cells=(),
        )
        config = _make_config(tui_layout=layout)
        result = validate_tui_layout(config)

        assert len(result.errors) > 1
