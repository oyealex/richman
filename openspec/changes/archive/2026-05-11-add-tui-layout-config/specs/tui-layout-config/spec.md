## ADDED Requirements

### Requirement: TuiCellLayout represents a single cell visual coordinate

系统 SHALL 提供 `TuiCellLayout` 不可变 dataclass，描述单个棋盘格在 TUI slot 网格中的视觉位置。

#### Scenario: TuiCellLayout fields

- **WHEN** 构造 `TuiCellLayout(position=0, row=8, column=0)`
- **THEN** `position` MUST 为对应 `board_cells` 索引的整数
- **AND** `row` 和 `column` MUST 为该格子在 slot 网格中的左上角坐标（0 基）
- **AND** 创建后的实例 MUST 不可变

#### Scenario: TuiCellLayout equality

- **WHEN** 两个 `TuiCellLayout` 实例具有相同的 position、row 和 column
- **THEN** 它们 MUST 相等

### Requirement: TuiRect represents a rectangular region in the slot grid

系统 SHALL 提供 `TuiRect` 不可变 dataclass，描述 TUI slot 网格中的一个矩形区域。

#### Scenario: TuiRect fields

- **WHEN** 构造 `TuiRect(row=2, column=2, row_span=5, column_span=9)`
- **THEN** `row` 和 `column` MUST 为矩形左上角坐标
- **AND** `row_span` MUST 为矩形占用的行数
- **AND** `column_span` MUST 为矩形占用的列数
- **AND** 创建后的实例 MUST 不可变

### Requirement: TuiLayout represents the complete board visual layout

系统 SHALL 提供 `TuiLayout` 不可变 dataclass，描述 TUI 棋盘的完整视觉布局配置。

#### Scenario: TuiLayout fields

- **WHEN** 构造 `TuiLayout`
- **THEN** `rows` 和 `columns` MUST 为 slot 网格的总行数和总列数
- **AND** `center` MUST 为 `TuiRect`，表示中心展示区在网格中的位置和大小
- **AND** `cells` MUST 为 `tuple[TuiCellLayout, ...]`，包含所有棋盘格的视觉坐标
- **AND** 创建后的实例 MUST 不可变

#### Scenario: TuiLayout cells correspond to board_cells

- **WHEN** `TuiLayout` 被创建
- **THEN** `cells` 中的每个 `TuiCellLayout.position` 应唯一对应 `GameConfig.board_cells` 中的一个 position
- **AND** 游戏移动顺序由 `board_cells` 的 position 顺序决定，不受 `tui_layout.cells` 顺序影响

### Requirement: TUI layout types are framework-agnostic

系统 SHALL 确保 `TuiCellLayout`、`TuiRect`、`TuiLayout` 不依赖 Textual、Rich 或任何 UI 框架。

#### Scenario: No UI framework imports in TUI layout types

- **WHEN** 检查 `richman.domain.models` 中 TUI 布局类型的源码
- **THEN** 这些类型 MUST NOT 导入 Textual、Rich widget、浏览器框架或终端事件对象
- **AND** 它们 MUST 只使用 Python 标准库 dataclass

### Requirement: GameConfig optionally includes tui_layout

系统 SHALL 让 `GameConfig` 包含可选字段 `tui_layout: TuiLayout | None`，默认值为 `None`。

#### Scenario: Default GameConfig has no tui_layout

- **WHEN** 直接构造 `GameConfig(board_cells=..., cards=...)` 且不传入 `tui_layout`
- **THEN** `tui_layout` MUST 为 `None`

#### Scenario: GameConfig with tui_layout

- **WHEN** 构造 `GameConfig` 并传入 `tui_layout=TuiLayout(...)`
- **THEN** `tui_layout` MUST 为传入的布局实例
- **AND** `GameConfig` 的其它字段不受影响

#### Scenario: GameConfig remains immutable

- **WHEN** 已创建包含 `tui_layout` 的 `GameConfig`
- **THEN** 实例 MUST 不可变（`frozen=True`）
