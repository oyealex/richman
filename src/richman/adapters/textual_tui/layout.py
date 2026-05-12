"""TUI layout validation for the Textual adapter.

Pure functions that validate a GameConfig's tui_layout before it reaches
the BoardWidget rendering layer. No Textual, Rich, or engine dependencies.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

from richman.domain import GameConfig, TuiLayout, TuiRect


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


# -- Cell dimension constants ------------------------------------------------

CELL_WIDTH = 12
CELL_HEIGHT = 5
CELL_GAP = 1


# -- Layout geometry ---------------------------------------------------------


@dataclass(frozen=True, slots=True)
class TuiLayoutGeometry:
    """Precomputed terminal-character geometry for a validated TuiLayout.

    All coordinate tuples use (top, left, bottom, right) half-open intervals,
    consistent with TuiRect's row_span / column_span semantics.
    """

    position_rects: Mapping[int, tuple[int, int, int, int]]
    center_rect: tuple[int, int, int, int]
    min_terminal_rows: int
    min_terminal_cols: int
    is_terminal_sufficient: bool


def compute_layout_geometry(
    config: GameConfig,
    terminal_size: tuple[int, int] | None = None,
) -> TuiLayoutGeometry:
    """Compute terminal-character geometry from a validated GameConfig.

    Args:
        config: GameConfig with a legal tui_layout.  If validation fails a
            ``ValueError`` is raised before any geometry is computed.
        terminal_size: ``(rows, cols)`` of the current terminal, or ``None``
            to skip the sufficiency check (``is_terminal_sufficient`` will be
            ``True`` unconditionally).

    Returns:
        TuiLayoutGeometry with position rects, center rect, minimum
        dimensions, and a sufficiency flag.
    """
    # -- validate first -------------------------------------------------
    validation = validate_tui_layout(config)
    if validation.errors:
        raise ValueError(
            "tui_layout 校验失败，无法计算布局几何:\n"
            + "\n".join(f"  - {e}" for e in validation.errors)
        )

    layout: TuiLayout = config.tui_layout  # type: ignore[assignment]

    # -- position rects -------------------------------------------------
    pos_rects: dict[int, tuple[int, int, int, int]] = {}
    for cell in layout.cells:
        top = cell.row * CELL_HEIGHT
        left = cell.column * (CELL_WIDTH + CELL_GAP)
        pos_rects[cell.position] = (top, left, top + CELL_HEIGHT, left + CELL_WIDTH)

    # -- center rect ----------------------------------------------------
    c = layout.center
    center_rect = (
        c.row * CELL_HEIGHT,
        c.column * (CELL_WIDTH + CELL_GAP),
        (c.row + c.row_span) * CELL_HEIGHT,
        (c.column + c.column_span) * (CELL_WIDTH + CELL_GAP) - CELL_GAP,
    )

    # -- minimum terminal dimensions ------------------------------------
    min_rows = layout.rows * CELL_HEIGHT
    min_cols = layout.columns * CELL_WIDTH + (layout.columns - 1) * CELL_GAP

    # -- sufficiency ----------------------------------------------------
    if terminal_size is None:
        is_sufficient = True
    else:
        term_rows, term_cols = terminal_size
        is_sufficient = term_rows >= min_rows and term_cols >= min_cols

    return TuiLayoutGeometry(
        position_rects=MappingProxyType(pos_rects),
        center_rect=center_rect,
        min_terminal_rows=min_rows,
        min_terminal_cols=min_cols,
        is_terminal_sufficient=is_sufficient,
    )
