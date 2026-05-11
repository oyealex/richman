# app-assembly Specification

## Purpose
Define how the application layer builds configuration, players, engine instances, and CLI game runs.
## Requirements
### Requirement: App module provides default game configuration
系统 SHALL 提供 app 层默认配置构造能力，用于创建一局无需外部配置文件即可运行的游戏。

#### Scenario: Default config is valid for board creation
- **WHEN** 调用 app 层默认配置构造函数
- **THEN** 返回值 MUST 是 `GameConfig`
- **AND** 该配置 MUST 能被 `board.create(config)` 成功创建为 `Board`

#### Scenario: Default config contains playable content
- **WHEN** 检查默认 `GameConfig`
- **THEN** 配置 MUST 包含一个 START 格、一个 JAIL_SPACE 格、至少一个 PROPERTY 格和至少一个 CHANCE 格
- **AND** 配置 MUST 包含至少一张机会卡

### Requirement: App module creates players
系统 SHALL 提供 app 层玩家创建能力，用于按调用参数创建可传给 engine 的玩家对象。

#### Scenario: AI players are created with stable names
- **WHEN** 调用 app 层玩家创建函数并请求 N 名 AI 玩家
- **THEN** 返回的玩家数量 MUST 等于 N
- **AND** 每个玩家名称 MUST 稳定且可展示

#### Scenario: Invalid player count is rejected
- **WHEN** 调用 app 层玩家创建函数并请求少于 2 名或多于 4 名玩家
- **THEN** 系统 MUST 报告调用错误

### Requirement: App module assembles engine
系统 SHALL 提供 app 层 engine 装配能力，将配置、棋盘、玩家和随机种子连接到 `GameEngine.create`。

#### Scenario: Engine is assembled from app defaults
- **WHEN** 使用默认配置和默认玩家调用 app 层 engine 装配函数
- **THEN** 返回值 MUST 是已初始化的 `GameEngine`
- **AND** engine 的内部状态 MUST 包含对应数量的玩家和默认配置中的地块运行时状态

#### Scenario: Seed is forwarded to engine
- **WHEN** 使用相同 seed 调用 app 层 engine 装配函数两次
- **THEN** 两个 engine MUST 产生确定性的初始状态

#### Scenario: Renderer is not required for engine assembly
- **WHEN** app 层创建 `GameEngine`
- **THEN** 它 MUST NOT 向 `GameEngine.create` 传入 renderer

### Requirement: App module runs a game
系统 SHALL 提供 app 层运行入口，用于启动已装配的 engine step driver 并返回最终 `InternalGameState`。

#### Scenario: Game can run with max turn limit
- **WHEN** 调用 app 层运行入口并传入 `max_turns`
- **THEN** 系统 MUST 通过 step driver 推进 engine
- **AND** 返回值 MUST 是 `InternalGameState`
- **AND** 运行回合数 MUST NOT 超过传入的 `max_turns`

#### Scenario: Game run uses step API
- **WHEN** app 层运行入口启动游戏
- **THEN** 它 MUST 通过 `GameEngine.advance(input)` 推进流程
- **AND** 它 MUST NOT 依赖 engine 直接调用 renderer

### Requirement: CLI play command uses app assembly
系统 SHALL 让 `richman play` 命令通过 app 装配层和 console step driver 启动游戏，而不是只启动静态 adapter shell。

#### Scenario: Play command accepts bounded run options
- **WHEN** 用户执行 `richman play --players 2 --max-turns 1 --seed 1`
- **THEN** CLI MUST 通过 app 装配层创建并启动游戏
- **AND** 命令 MUST 正常退出

#### Scenario: Play command rejects invalid player count
- **WHEN** 用户执行 `richman play --players 1`
- **THEN** CLI MUST 报告参数错误
- **AND** 游戏 MUST NOT 启动

#### Scenario: Play command preserves existing semantics
- **WHEN** 用户使用现有 `richman play` 选项启动游戏
- **THEN** 命令行参数含义 MUST 与变更前保持一致
- **AND** 内部实现 MAY 使用 step driver 替代旧同步循环

### Requirement: App module provides console step driver
系统 SHALL 提供 console 运行驱动，用于通过 `GameEngine.advance(input)` 推进游戏并保持现有 `richman play` 行为。

#### Scenario: Console driver renders each frame
- **WHEN** console driver 收到 StepResult
- **THEN** 它使用 StepResult.snapshot 展示当前局面

#### Scenario: Console driver supplies required input
- **WHEN** StepResult.required_input 非空且当前玩家需要人类输入
- **THEN** console driver 收集合法输入并提交给 `advance(input)`

#### Scenario: Console driver auto-advances display-only frames
- **WHEN** StepResult.required_input 为空且 game_over 为 false
- **THEN** console driver 可以继续调用 `advance(None)` 推进到下一个 frame

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

