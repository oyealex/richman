## ADDED Requirements

### Requirement: Default config includes tui_layout

系统 SHALL 让 `build_default_config()` 返回的 `GameConfig` 包含非空的 `tui_layout`。

#### Scenario: Default config has tui_layout

- **WHEN** 调用 `build_default_config()`
- **THEN** 返回值的 `tui_layout` MUST NOT 为 `None`
- **AND** `tui_layout` MUST 为 `TuiLayout` 实例

#### Scenario: Default tui_layout covers all board_cells positions

- **WHEN** 检查默认配置的 `tui_layout`
- **THEN** `tui_layout.cells` 中的 position 集合 MUST 等于 `range(len(board_cells))`

#### Scenario: Default tui_layout has valid structure

- **WHEN** 检查默认配置的 `tui_layout`
- **THEN** `rows` 和 `columns` MUST 为正整数
- **AND** `center` MUST 为 `TuiRect`，且 `row_span` 和 `column_span` 均为正整数
- **AND** `cells` MUST 为非空 tuple
- **AND** 每个 cell 的 `row` 和 `column` MUST 在网格范围内
- **AND** 没有 cell 的坐标落入 `center` 矩形

### Requirement: Config file parsing supports tui_layout

系统 SHALL 让 `load_config()` 从 JSON 或 YAML 配置文件中解析可选的 `tui_layout` 段。

#### Scenario: JSON config with tui_layout

- **WHEN** JSON 配置文件包含 `tui_layout` 键，且内部字段完整有效
- **THEN** `load_config()` 返回的 `GameConfig.tui_layout` MUST 为解析得到的 `TuiLayout`

#### Scenario: YAML config with tui_layout

- **WHEN** YAML 配置文件包含 `tui_layout` 段，且内部字段完整有效
- **THEN** `load_config()` 返回的 `GameConfig.tui_layout` MUST 为解析得到的 `TuiLayout`

#### Scenario: Config without tui_layout

- **WHEN** JSON 或 YAML 配置文件不包含 `tui_layout` 键
- **THEN** `load_config()` 返回的 `GameConfig.tui_layout` MUST 为 `None`

#### Scenario: Parsed tui_layout preserves all fields

- **WHEN** 从配置文件解析 `tui_layout`
- **THEN** 解析后的 `TuiLayout` MUST 包含 `rows`、`columns`、`center`（含 `row`、`column`、`row_span`、`column_span`）和 `cells`（每个含 `position`、`row`、`column`）
