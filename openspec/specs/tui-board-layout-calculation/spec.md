# TUI Board Layout Calculation

## Purpose

根据 `TuiLayout` 配置计算终端字符几何信息——每个 position 的终端字符矩形、中心区位置、最小终端尺寸、尺寸充足性判断。纯逻辑层，不依赖 Textual 或任何 widget 框架。

## Requirements

### Requirement: Cell dimension constants are defined

系统 SHALL 在 `layout.py` 中定义固定 cell 尺寸常量 `CELL_WIDTH = 12`、`CELL_HEIGHT = 5`、`CELL_GAP = 1`，供所有布局计算使用。

#### Scenario: Constants exist and are positive

- **WHEN** 从 `richman.adapters.textual_tui.layout` 导入 `CELL_WIDTH`、`CELL_HEIGHT`、`CELL_GAP`
- **THEN** 三个常量 SHALL 均为正整数

### Requirement: TuiLayoutGeometry conveys computed layout geometry

系统 SHALL 提供 `TuiLayoutGeometry` 不可变 dataclass，包含 `position_rects`、`center_rect`、`min_terminal_rows`、`min_terminal_cols`、`is_terminal_sufficient` 字段。

#### Scenario: Geometry for valid layout contains all positions

- **WHEN** 使用合法 `GameConfig` 计算几何
- **THEN** `position_rects` MUST 为 `Mapping[int, tuple[int, int, int, int]]`，每个 position 映射到一个 `(top, left, bottom, right)` 元组，其中 `bottom` 和 `right` 为排他边界，且 mapping 本身不可变

#### Scenario: center_rect matches center region

- **WHEN** 计算几何
- **THEN** `center_rect` MUST 为 `(top, left, bottom, right)` 元组，表示中心展示区在终端字符坐标中的矩形范围

#### Scenario: is_terminal_sufficient is true when terminal is large enough

- **WHEN** 终端尺寸 >= `min_terminal_rows` × `min_terminal_cols`
- **THEN** `is_terminal_sufficient` MUST 为 `True`

#### Scenario: is_terminal_sufficient is false when terminal is too small

- **WHEN** 终端尺寸 < `min_terminal_rows` 或 < `min_terminal_cols`
- **THEN** `is_terminal_sufficient` MUST 为 `False`

### Requirement: compute_layout_geometry returns geometry from valid config

系统 SHALL 提供 `compute_layout_geometry(config: GameConfig, terminal_size: tuple[int, int] | None = None) -> TuiLayoutGeometry` 函数。

#### Scenario: Default layout produces correct geometry

- **WHEN** 使用 `build_default_config()` 调用 `compute_layout_geometry(config)`
- **THEN** 返回值 MUST 为 `TuiLayoutGeometry`，`is_terminal_sufficient` 为 `True`（terminal_size=None 时）
- **AND** `position_rects` MUST 包含所有 `board_cells` position
- **AND** `min_terminal_rows` 和 `min_terminal_cols` MUST 为正整数

#### Scenario: terminal_size=None skips sufficiency check

- **WHEN** `terminal_size=None`
- **THEN** `is_terminal_sufficient` MUST 为 `True`

### Requirement: compute_layout_geometry rejects invalid layout

系统 SHALL 在传入的 `GameConfig.tui_layout` 校验不通过时抛出 `ValueError`。

#### Scenario: Invalid layout raises ValueError

- **WHEN** 传入 `GameConfig` 且 `validate_tui_layout(config).errors` 非空
- **THEN** 函数 MUST 抛出 `ValueError`，异常信息包含所有校验错误

### Requirement: Position rect coordinates are derived from cell dimensions

系统 SHALL 根据 cell 尺寸常量计算每个 cell 的终端字符坐标范围。

#### Scenario: Cell at (row=0, col=0) maps to origin

- **WHEN** `TuiCellLayout(position=p, row=0, column=0)`
- **THEN** `position_rects[p]` MUST 为 `(0, 0, CELL_HEIGHT, CELL_WIDTH)`

#### Scenario: Cell at (row=1, col=2) maps to expected coordinates

- **WHEN** `TuiCellLayout(position=p, row=1, column=2)`
- **THEN** `position_rects[p]` MUST 为 `(CELL_HEIGHT, 2 * (CELL_WIDTH + CELL_GAP), 2 * CELL_HEIGHT, 2 * (CELL_WIDTH + CELL_GAP) + CELL_WIDTH)`

#### Scenario: No two positions overlap in rect coordinates

- **WHEN** 计算合法布局的几何
- **THEN** 任意两个不同 position 的终端字符矩形 MUST NOT 重叠

### Requirement: Center panel rectangle is derived from TuiRect in terminal coordinates

系统 SHALL 根据 `TuiLayout.center` 的 row/column/row_span/column_span 计算中心区在终端字符坐标中的矩形。

#### Scenario: Center rect coordinates match cell slot coordinate system

- **WHEN** `center = TuiRect(row=r, column=c, row_span=rs, column_span=cs)`
- **THEN** `center_rect` MUST 为 `(r * CELL_HEIGHT, c * (CELL_WIDTH + CELL_GAP), (r + rs) * CELL_HEIGHT, (c + cs) * (CELL_WIDTH + CELL_GAP) - CELL_GAP)`

### Requirement: Minimum terminal dimensions are computed from grid extents

系统 SHALL 根据 cell 最右和最下边缘计算最少需要的终端行列数。

#### Scenario: Default 9x13 layout reports minimum dimensions

- **WHEN** 使用默认布局（rows=9, columns=13）计算
- **THEN** `min_terminal_rows` MUST 为 `9 * CELL_HEIGHT`（45）
- **AND** `min_terminal_cols` MUST 为 `13 * CELL_WIDTH + 12 * CELL_GAP`（168）

#### Scenario: All cell position rects are within minimum dimensions

- **WHEN** 计算合法布局的几何
- **THEN** 所有 `position_rects` 的 `right` MUST <= `min_terminal_cols`
- **AND** 所有 `position_rects` 的 `bottom` MUST <= `min_terminal_rows`
