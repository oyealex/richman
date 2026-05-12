"""Tests for TUI layout validation."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from richman.adapters.textual_tui.layout import (
    CELL_GAP,
    CELL_HEIGHT,
    CELL_WIDTH,
    TuiLayoutGeometry,
    TuiLayoutValidationResult,
    compute_layout_geometry,
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


# -- Layout geometry calculation tests ---------------------------------------


class TestCellConstants:
    def test_constants_are_positive_integers(self) -> None:
        assert isinstance(CELL_WIDTH, int)
        assert isinstance(CELL_HEIGHT, int)
        assert isinstance(CELL_GAP, int)
        assert CELL_WIDTH > 0
        assert CELL_HEIGHT > 0
        assert CELL_GAP >= 0


class TestTuiLayoutGeometryDataclass:
    def test_geometry_is_immutable(self) -> None:
        from types import MappingProxyType

        geo = TuiLayoutGeometry(
            position_rects=MappingProxyType({}),
            center_rect=(0, 0, 0, 0),
            min_terminal_rows=0,
            min_terminal_cols=0,
            is_terminal_sufficient=True,
        )

        with pytest.raises(FrozenInstanceError):
            geo.min_terminal_rows = 99  # type: ignore[misc]

    def test_position_rects_is_readonly(self) -> None:
        config = build_default_config()
        geo = compute_layout_geometry(config)

        with pytest.raises(TypeError):
            geo.position_rects[0] = (99, 99, 99, 99)  # type: ignore[index]


class TestDefaultLayoutGeometry:
    def test_default_layout_geometry_contains_all_positions(self) -> None:
        config = build_default_config()
        geo = compute_layout_geometry(config)

        board_len = len(config.board_cells)
        assert len(geo.position_rects) == board_len
        for pos in range(board_len):
            assert pos in geo.position_rects

    def test_default_layout_center_rect_nonzero(self) -> None:
        config = build_default_config()
        geo = compute_layout_geometry(config)

        top, left, bottom, right = geo.center_rect
        assert bottom > top
        assert right > left

    def test_default_layout_min_terminal_positive(self) -> None:
        config = build_default_config()
        geo = compute_layout_geometry(config)

        assert geo.min_terminal_rows > 0
        assert geo.min_terminal_cols > 0

    def test_default_layout_exact_min_dimensions(self) -> None:
        config = build_default_config()
        layout = config.tui_layout
        assert layout is not None

        geo = compute_layout_geometry(config)

        assert geo.min_terminal_rows == layout.rows * CELL_HEIGHT
        expected_cols = layout.columns * CELL_WIDTH + (layout.columns - 1) * CELL_GAP
        assert geo.min_terminal_cols == expected_cols

    def test_default_9x13_layout_min_dimensions_match_constants(self) -> None:
        config = build_default_config()
        geo = compute_layout_geometry(config)

        assert geo.min_terminal_rows == 45  # 9 * 5
        assert geo.min_terminal_cols == 168  # 13 * 12 + 12 * 1


class TestPositionRectMapping:
    def test_cell_at_origin_maps_to_zero_zero(self) -> None:
        layout = TuiLayout(
            rows=3,
            columns=3,
            center=TuiRect(row=1, column=1, row_span=1, column_span=1),
            cells=(
                TuiCellLayout(position=0, row=0, column=0),
            ),
        )
        config = _make_config(
            tui_layout=layout,
            board_cells=(BoardCellDefinition(CellType.START),),
        )
        geo = compute_layout_geometry(config)

        assert geo.position_rects[0] == (0, 0, CELL_HEIGHT, CELL_WIDTH)

    def test_cell_at_row1_col2_maps_to_expected(self) -> None:
        layout = TuiLayout(
            rows=3,
            columns=4,
            center=TuiRect(row=1, column=1, row_span=1, column_span=1),
            cells=(
                TuiCellLayout(position=0, row=1, column=2),
            ),
        )
        config = _make_config(
            tui_layout=layout,
            board_cells=(BoardCellDefinition(CellType.START),),
        )
        geo = compute_layout_geometry(config)

        expected_top = CELL_HEIGHT  # row=1 * 5
        expected_left = 2 * (CELL_WIDTH + CELL_GAP)  # col=2 * 13
        expected_bottom = 2 * CELL_HEIGHT  # 10
        expected_right = expected_left + CELL_WIDTH  # 26 + 12 = 38

        actual = geo.position_rects[0]
        assert actual == (expected_top, expected_left, expected_bottom, expected_right)

    def test_no_overlap_between_positions(self) -> None:
        config = build_default_config()
        geo = compute_layout_geometry(config)

        rects = list(geo.position_rects.values())
        for i in range(len(rects)):
            for j in range(i + 1, len(rects)):
                a_top, a_left, a_bottom, a_right = rects[i]
                b_top, b_left, b_bottom, b_right = rects[j]
                # Two rects overlap iff they overlap in both dimensions
                overlap_h = a_left < b_right and b_left < a_right
                overlap_v = a_top < b_bottom and b_top < a_bottom
                assert not (overlap_h and overlap_v), (
                    f"positions {i} and {j} rects overlap: {rects[i]} vs {rects[j]}"
                )


class TestCenterRect:
    def test_center_rect_matches_tui_rect_coordinates(self) -> None:
        layout = TuiLayout(
            rows=5,
            columns=7,
            center=TuiRect(row=1, column=2, row_span=3, column_span=3),
            cells=(
                TuiCellLayout(position=0, row=0, column=0),
            ),
        )
        config = _make_config(
            tui_layout=layout,
            board_cells=(BoardCellDefinition(CellType.START),),
        )
        geo = compute_layout_geometry(config)

        expected_top = 1 * CELL_HEIGHT  # 5
        expected_left = 2 * (CELL_WIDTH + CELL_GAP)  # 26
        expected_bottom = (1 + 3) * CELL_HEIGHT  # 20
        expected_right = (2 + 3) * (CELL_WIDTH + CELL_GAP) - CELL_GAP  # 65 - 1 = 64

        assert geo.center_rect == (expected_top, expected_left, expected_bottom, expected_right)


class TestMinimumTerminalDimensions:
    def test_default_9x13_min_dimensions(self) -> None:
        config = build_default_config()
        geo = compute_layout_geometry(config)

        assert geo.min_terminal_rows == 45
        assert geo.min_terminal_cols == 168

    def test_all_position_rects_within_min_terminal(self) -> None:
        config = build_default_config()
        geo = compute_layout_geometry(config)

        for pos, (_top, _left, bottom, right) in geo.position_rects.items():
            assert right <= geo.min_terminal_cols, (
                f"position {pos} right={right} exceeds min_terminal_cols={geo.min_terminal_cols}"
            )
            assert bottom <= geo.min_terminal_rows, (
                f"position {pos} bottom={bottom} exceeds min_terminal_rows={geo.min_terminal_rows}"
            )


class TestTerminalSufficiency:
    def test_terminal_size_sufficient(self) -> None:
        config = build_default_config()
        geo = compute_layout_geometry(config, terminal_size=(45, 168))

        assert geo.is_terminal_sufficient is True

    def test_terminal_size_insufficient_rows(self) -> None:
        config = build_default_config()
        geo = compute_layout_geometry(config, terminal_size=(30, 200))

        assert geo.is_terminal_sufficient is False

    def test_terminal_size_insufficient_cols(self) -> None:
        config = build_default_config()
        geo = compute_layout_geometry(config, terminal_size=(50, 100))

        assert geo.is_terminal_sufficient is False

    def test_terminal_size_none_is_sufficient(self) -> None:
        config = build_default_config()
        geo = compute_layout_geometry(config, terminal_size=None)

        assert geo.is_terminal_sufficient is True

    def test_terminal_size_exactly_min_is_sufficient(self) -> None:
        config = build_default_config()
        geo = compute_layout_geometry(config, terminal_size=(45, 168))

        assert geo.is_terminal_sufficient is True


class TestInvalidLayoutRejection:
    def test_none_layout_raises_valueerror(self) -> None:
        config = _make_config(tui_layout=None)

        with pytest.raises(ValueError, match="缺少 tui_layout"):
            compute_layout_geometry(config)

    def test_zero_rows_layout_raises_valueerror(self) -> None:
        layout = TuiLayout(
            rows=0,
            columns=13,
            center=TuiRect(row=0, column=0, row_span=1, column_span=1),
            cells=(),
        )
        config = _make_config(tui_layout=layout)

        with pytest.raises(ValueError, match="rows"):
            compute_layout_geometry(config)

    def test_valueerror_includes_all_errors(self) -> None:
        layout = TuiLayout(
            rows=0,
            columns=0,
            center=TuiRect(row=0, column=0, row_span=0, column_span=0),
            cells=(),
        )
        config = _make_config(tui_layout=layout)

        with pytest.raises(ValueError) as exc_info:
            compute_layout_geometry(config)

        msg = str(exc_info.value)
        assert "rows" in msg
        assert "columns" in msg
        assert "row_span" in msg
        assert "column_span" in msg
