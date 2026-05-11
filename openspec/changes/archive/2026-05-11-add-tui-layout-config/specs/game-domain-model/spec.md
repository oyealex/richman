## ADDED Requirements

### Requirement: TUI layout domain types

系统 SHALL 在 `richman.domain` 中提供 `TuiCellLayout`、`TuiRect` 和 `TuiLayout` 三个不可变 dataclass，用于描述 TUI 棋盘的视觉布局配置。

#### Scenario: TUI layout types are importable from domain

- **WHEN** 开发者执行 `from richman.domain import TuiCellLayout, TuiRect, TuiLayout`
- **THEN** 导入 MUST 成功

#### Scenario: TUI layout types are immutable

- **WHEN** 创建 `TuiCellLayout`、`TuiRect` 或 `TuiLayout` 实例
- **THEN** 每个实例 MUST 为 frozen dataclass
- **AND** 创建后不可修改其字段

#### Scenario: TUI layout types use slots

- **WHEN** 检查 `TuiCellLayout`、`TuiRect`、`TuiLayout` 的定义
- **THEN** 每个类型 SHOULD 使用 `slots=True` 以减少内存开销

### Requirement: GameConfig extended with optional tui_layout

系统 SHALL 让 `GameConfig` 包含可选字段 `tui_layout: TuiLayout | None = None`。

#### Scenario: GameConfig.tui_layout defaults to None

- **WHEN** 构造 `GameConfig` 时不提供 `tui_layout` 参数
- **THEN** `config.tui_layout` MUST 为 `None`

#### Scenario: GameConfig with explicit tui_layout

- **WHEN** 构造 `GameConfig` 并提供 `tui_layout=TuiLayout(...)`
- **THEN** `config.tui_layout` MUST 为传入的 `TuiLayout` 实例
