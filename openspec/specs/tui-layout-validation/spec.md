# TUI Layout Validation

## Purpose

校验 `GameConfig.tui_layout` 是否合法、可用于 TUI 棋盘渲染。校验层不依赖 engine 或任何 UI 框架，
在进入 BoardWidget 渲染前发现配置错误。

## Requirements

### Requirement: TuiLayoutValidationResult conveys validation outcome

系统 SHALL 提供 `TuiLayoutValidationResult` 不可变 dataclass，包含 `errors` 和 `warnings` 两个字段，用于从校验函数返回结构化校验结果。

#### Scenario: All valid — no errors or warnings

- **WHEN** 校验合法布局
- **THEN** `errors` MUST 为空 tuple
- **AND** `warnings` MUST 为空 tuple

#### Scenario: Errors present — layout invalid

- **WHEN** 校验包含错误的布局
- **THEN** `errors` MUST 为非空 tuple，每项为描述具体错误的字符串
- **AND** 调用方 SHOULD 拒绝进入 TUI 渲染

#### Scenario: Warnings present — layout usable

- **WHEN** 校验存在 warning 但无 error 的布局
- **THEN** `warnings` MUST 为非空 tuple
- **AND** `errors` MUST 为空 tuple
- **AND** 调用方 MAY 展示 warning 但不阻塞渲染

### Requirement: validate_tui_layout rejects missing layout

系统 SHALL 在 `GameConfig.tui_layout` 为 `None` 时返回错误。

#### Scenario: tui_layout is None

- **WHEN** 传入 `GameConfig` 且 `tui_layout` 为 `None`
- **THEN** 校验结果 MUST 包含一个 error，说明缺少 TUI 布局配置

### Requirement: validate_tui_layout rejects illegal grid dimensions

系统 SHALL 在 `TuiLayout.rows` 或 `columns` 非正整数值时返回错误。

#### Scenario: rows is zero

- **WHEN** `tui_layout.rows` 为 0 或负数
- **THEN** 校验结果 MUST 包含 error

#### Scenario: columns is zero

- **WHEN** `tui_layout.columns` 为 0 或负数
- **THEN** 校验结果 MUST 包含 error

### Requirement: validate_tui_layout rejects illegal center rectangle

系统 SHALL 在 center 矩形的 `row_span` 或 `column_span` 非正整数值、或矩形越界时返回错误。

#### Scenario: center row_span is zero

- **WHEN** `center.row_span` 为 0 或负数
- **THEN** 校验结果 MUST 包含 error

#### Scenario: center column_span is zero

- **WHEN** `center.column_span` 为 0 或负数
- **THEN** 校验结果 MUST 包含 error

#### Scenario: center row or column is negative

- **WHEN** `center.row < 0` 或 `center.column < 0`
- **THEN** 校验结果 MUST 包含 error

#### Scenario: center rectangle out of grid bounds

- **WHEN** `center.row + center.row_span > layout.rows` 或 `center.column + center.column_span > layout.columns`
- **THEN** 校验结果 MUST 包含 error

### Requirement: validate_tui_layout rejects position coverage issues

系统 SHALL 在 `tui_layout.cells` 的 position 集合与 `board_cells` 的 position 不完全匹配时返回错误。

#### Scenario: Missing board_cells position

- **WHEN** 某个 `board_cells` 索引没有对应 `TuiCellLayout`
- **THEN** 校验结果 MUST 包含 error，指明缺失的 position

#### Scenario: Extra position not in board_cells

- **WHEN** `tui_layout.cells` 包含 `board_cells` 中不存在的 position
- **THEN** 校验结果 MUST 包含 error，指明多余的 position

#### Scenario: Duplicate position in cells

- **WHEN** 两个或多个 `TuiCellLayout` 具有相同的 `position`
- **THEN** 校验结果 MUST 包含 error，指明重复的 position

### Requirement: validate_tui_layout rejects duplicate or out-of-bounds cell coordinates

系统 SHALL 在 cell 坐标越界或两个 cell 占据相同 slot 坐标时返回错误。

#### Scenario: Cell row out of bounds

- **WHEN** 某个 `TuiCellLayout` 的 `row` 为负数或 `>= layout.rows`
- **THEN** 校验结果 MUST 包含 error

#### Scenario: Cell column out of bounds

- **WHEN** 某个 `TuiCellLayout` 的 `column` 为负数或 `>= layout.columns`
- **THEN** 校验结果 MUST 包含 error

#### Scenario: Duplicate cell coordinates

- **WHEN** 两个不同 position 的 `TuiCellLayout` 具有相同 `(row, column)`
- **THEN** 校验结果 MUST 包含 error

### Requirement: validate_tui_layout rejects cell overlapping center rectangle

系统 SHALL 在任意 cell 坐标落入 center 矩形时返回错误。

#### Scenario: Cell inside center rectangle

- **WHEN** 某个 `TuiCellLayout` 的 `(row, column)` 满足 `center.row <= row < center.row + center.row_span` 且 `center.column <= column < center.column + center.column_span`
- **THEN** 校验结果 MUST 包含 error

### Requirement: Validation function is pure and framework-agnostic

系统 SHALL 确保 `validate_tui_layout` 不依赖 engine、不修改输入、不依赖任何 UI 框架。

#### Scenario: No engine dependency

- **WHEN** 检查 `layout.py` 源码导入
- **THEN** 它 MUST NOT 导入 `richman.engine`

#### Scenario: Input is not modified

- **WHEN** 调用 `validate_tui_layout(config)`
- **THEN** 传入的 `GameConfig` 及其嵌套结构 MUST NOT 被修改

#### Scenario: No UI framework imports

- **WHEN** 检查 `layout.py` 源码导入
- **THEN** 它 MUST NOT 导入 Textual、Rich widget 或终端事件对象
