"""TUI layout validation for the Textual adapter.

Pure functions that validate a GameConfig's tui_layout before it reaches
the BoardWidget rendering layer. No Textual, Rich, or engine dependencies.
"""

from __future__ import annotations

from dataclasses import dataclass

from richman.domain import GameConfig, TuiRect


@dataclass(frozen=True, slots=True)
class TuiLayoutValidationResult:
    """Structured result of tui_layout validation."""

    errors: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()


def validate_tui_layout(config: GameConfig) -> TuiLayoutValidationResult:
    """Validate that GameConfig.tui_layout is legal and renderable.

    Returns errors for any hard blockers. The warnings field is reserved
    for future non-blocking concerns.
    """
    errors: list[str] = []

    layout = config.tui_layout
    if layout is None:
        return TuiLayoutValidationResult(
            errors=("缺少 tui_layout 配置：TUI 模式需要 GameConfig 包含 tui_layout",)
        )

    board_len = len(config.board_cells)

    # --- grid dimensions ---
    if layout.rows <= 0:
        errors.append(f"tui_layout.rows 必须为正整数，当前值: {layout.rows}")
    if layout.columns <= 0:
        errors.append(f"tui_layout.columns 必须为正整数，当前值: {layout.columns}")

    # --- center rectangle ---
    _validate_center(layout.rows, layout.columns, layout.center, errors)

    # --- position coverage ---
    positions_seen: set[int] = set()
    for cell in layout.cells:
        if cell.position in positions_seen:
            errors.append(f"position {cell.position} 在 tui_layout.cells 中重复出现")
        positions_seen.add(cell.position)

    board_positions = set(range(board_len))
    layout_positions = {cell.position for cell in layout.cells}

    missing = board_positions - layout_positions
    for pos in sorted(missing):
        errors.append(f"board_cells position {pos} 在 tui_layout.cells 中缺失")

    extra = layout_positions - board_positions
    for pos in sorted(extra):
        errors.append(
            f"tui_layout.cells 包含不存在的 position {pos}"
            f"（board_cells 共 {board_len} 格）"
        )

    # --- cell coordinate validation ---
    seen_coords: dict[tuple[int, int], int] = {}
    center_r_start = layout.center.row
    center_r_end = layout.center.row + layout.center.row_span
    center_c_start = layout.center.column
    center_c_end = layout.center.column + layout.center.column_span

    for cell in layout.cells:
        if cell.row < 0 or cell.row >= layout.rows:
            errors.append(
                f"position {cell.position} 的 row={cell.row} 越界 "
                f"（有效范围: 0~{layout.rows - 1}）"
            )
        if cell.column < 0 or cell.column >= layout.columns:
            errors.append(
                f"position {cell.position} 的 column={cell.column} 越界 "
                f"（有效范围: 0~{layout.columns - 1}）"
            )

        coord = (cell.row, cell.column)
        if coord in seen_coords:
            errors.append(
                f"position {cell.position} 和 position {seen_coords[coord]} "
                f"占据相同 slot 坐标 ({cell.row}, {cell.column})"
            )
        seen_coords[coord] = cell.position

        if (
            center_r_start <= cell.row < center_r_end
            and center_c_start <= cell.column < center_c_end
        ):
            errors.append(
                f"position {cell.position} 在 ({cell.row}, {cell.column}) "
                f"落入 center 矩形区域"
            )

    return TuiLayoutValidationResult(
        errors=tuple(errors),
    )


def _validate_center(
    grid_rows: int,
    grid_cols: int,
    center: TuiRect,
    errors: list[str],
) -> None:
    """Validate the center rectangle of a TuiLayout."""
    if center.row < 0:
        errors.append(f"center.row 不能为负数，当前值: {center.row}")
    if center.column < 0:
        errors.append(f"center.column 不能为负数，当前值: {center.column}")
    if center.row_span <= 0:
        errors.append(f"center.row_span 必须为正整数，当前值: {center.row_span}")
    if center.column_span <= 0:
        errors.append(f"center.column_span 必须为正整数，当前值: {center.column_span}")

    # Only check bounds if grid dimensions are valid
    if grid_rows > 0 and center.row_span > 0:
        if center.row + center.row_span > grid_rows:
            errors.append(
                f"center 矩形越界：row({center.row}) + row_span({center.row_span}) "
                f"= {center.row + center.row_span} > rows({grid_rows})"
            )
    if grid_cols > 0 and center.column_span > 0:
        if center.column + center.column_span > grid_cols:
            errors.append(
                f"center 矩形越界：column({center.column}) + "
                f"column_span({center.column_span}) = "
                f"{center.column + center.column_span} > columns({grid_cols})"
            )
