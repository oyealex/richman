## ADDED Requirements

### Requirement: Player module boundary

系统 SHALL 提供 `richman.player` 作为玩家决策模块，并保持该模块只负责决策，不拥有、不读取、不修改完整游戏状态。

#### Scenario: Player package is importable

- **WHEN** 开发者导入 `richman.player`
- **THEN** 该包成功导入并导出 player 模块的公共 API

#### Scenario: Player depends only on domain and standard library

- **WHEN** 检查 `src/richman/player` 的源码导入
- **THEN** player 模块不导入 `richman.board`、`richman.rules`、`richman.engine`、`richman.render` 或 adapter 模块

#### Scenario: Player does not mutate game state

- **WHEN** player 模块接收 `PlayerView`、可选动作列表或拆除候选目标
- **THEN** player 模块 SHALL NOT 修改玩家现金、位置、手牌、地块状态、回合阶段、骰子值、事件日志或可选动作列表

### Requirement: Player public API

系统 SHALL 定义统一的玩家接口，使 engine 可以用相同方式调用人类玩家和 AI 玩家。

#### Scenario: Player interface exposes required decision points

- **WHEN** engine 需要等待掷骰、获取玩家动作或获取拆除目标
- **THEN** player 模块提供 `Player` 抽象接口
- **AND** 该接口包含 `name`、`wait_for_dice()`、`decide(view, actions, engine_context)` 和 `choose_demolish_target(view, candidates, engine_context)`

#### Scenario: Human and AI implementations are available

- **WHEN** app 或 engine 需要创建玩家
- **THEN** player 模块提供 `HumanPlayer` 和 `AIPlayer`
- **AND** 两者都实现 `Player` 接口

#### Scenario: Public API is exported from package root

- **WHEN** 后续模块执行 `from richman.player import Player, HumanPlayer, AIPlayer`
- **THEN** 导入成功且无需知道 player 内部源码文件布局

### Requirement: Legal action selection

系统 SHALL 保证玩家动作选择结果来自 engine 提供的合法动作列表。

#### Scenario: Player chooses one available action

- **WHEN** engine 调用 `decide(view, actions, engine_context)` 且 `actions` 非空
- **THEN** 返回值 MUST 是 `actions` 中的一个 `Action`

#### Scenario: Empty action list is rejected

- **WHEN** engine 调用 `decide(view, actions, engine_context)` 且 `actions` 为空
- **THEN** player 模块 MUST 报告调用错误

#### Scenario: Jail decision uses provided actions

- **WHEN** 入狱判决只提供 `[ACCEPT_JAIL]`
- **THEN** player 返回 `ACCEPT_JAIL`
- **AND** player 不自行添加 `USE_JAIL_PASS`

#### Scenario: Optional turn action uses provided actions

- **WHEN** 阶段四动作选择只提供 `BUY`、`UPGRADE`、`USE_DEMOLISH` 或 `SKIP` 的子集
- **THEN** player 只能返回该子集中的动作

### Requirement: HumanPlayer delegates input through restricted context

系统 SHALL 让 `HumanPlayer` 通过受限输入上下文获取用户选择，且不直接依赖具体 render 实现。

#### Scenario: HumanPlayer waits for dice input

- **WHEN** engine 调用 HumanPlayer 的 `wait_for_dice()`
- **THEN** HumanPlayer 等待受限输入原语完成
- **AND** HumanPlayer 不修改游戏状态

#### Scenario: HumanPlayer requests action choice

- **WHEN** engine 调用 HumanPlayer 的 `decide(view, actions, engine_context)`
- **THEN** HumanPlayer 通过 `engine_context` 的输入原语展示由 `actions` 派生的选项
- **AND** HumanPlayer 返回用户选择对应的 `Action`

#### Scenario: HumanPlayer requests demolish target

- **WHEN** engine 调用 HumanPlayer 的 `choose_demolish_target(view, candidates, engine_context)`
- **THEN** HumanPlayer 通过 `engine_context` 的输入原语展示候选位置
- **AND** HumanPlayer 返回用户选择对应的候选位置

#### Scenario: HumanPlayer has no render dependency

- **WHEN** HumanPlayer 需要获取输入
- **THEN** 它 SHALL 通过受限上下文或注入的输入原语完成
- **AND** 它 SHALL NOT 导入 Textual、Rich、render adapter 或 engine 实现

### Requirement: AIPlayer uses bounded deterministic decisions

系统 SHALL 提供基础 `AIPlayer`，该 AI 只使用传入的裁剪视图和合法选项做确定性决策。

#### Scenario: AIPlayer chooses a legal action

- **WHEN** engine 调用 AIPlayer 的 `decide(view, actions, engine_context)` 且 `actions` 非空
- **THEN** AIPlayer 返回 `actions` 中的一个动作
- **AND** AIPlayer 不读取 `InternalGameState`

#### Scenario: AIPlayer action choice is deterministic

- **WHEN** 使用相同 `PlayerView` 和相同 `actions` 多次调用 AIPlayer
- **THEN** AIPlayer 返回相同动作
- **AND** AIPlayer 不调用随机源

#### Scenario: AIPlayer accepts forced jail

- **WHEN** AIPlayer 收到的合法动作只有 `ACCEPT_JAIL`
- **THEN** AIPlayer 返回 `ACCEPT_JAIL`

#### Scenario: AIPlayer can use jail pass when offered

- **WHEN** AIPlayer 收到的合法动作包含 `USE_JAIL_PASS`
- **THEN** AIPlayer 可以选择 `USE_JAIL_PASS`
- **AND** 该选择必须来自传入的合法动作列表

### Requirement: Demolish target selection

系统 SHALL 保证拆除目标选择只从 engine 提供的候选位置中产生。

#### Scenario: Player chooses one candidate target

- **WHEN** engine 调用 `choose_demolish_target(view, candidates, engine_context)` 且 `candidates` 非空
- **THEN** 返回值 MUST 是 `candidates` 中的一个位置

#### Scenario: Empty demolish target list is rejected

- **WHEN** engine 调用 `choose_demolish_target(view, candidates, engine_context)` 且 `candidates` 为空
- **THEN** player 模块 MUST 报告调用错误

#### Scenario: AIPlayer target choice is stable

- **WHEN** 使用相同 `PlayerView` 和相同 `candidates` 多次调用 AIPlayer
- **THEN** AIPlayer 返回相同候选位置

### Requirement: Player information boundary

系统 SHALL 确保 player 只能基于 `PlayerView` 和 engine 显式传入的选项作出决策。

#### Scenario: Player receives a cropped view

- **WHEN** engine 调用任意 `Player` 实现
- **THEN** player 接收 `PlayerView`
- **AND** player 不接收 `InternalGameState`

#### Scenario: Player does not inspect hidden private data

- **WHEN** `PlayerView.public_players` 只包含公开玩家信息
- **THEN** player 模块 SHALL NOT 尝试读取其他玩家现金、手牌数量或地块投入成本

#### Scenario: Engine context is opaque and restricted

- **WHEN** player 使用 `engine_context`
- **THEN** `engine_context` SHALL 只提供输入原语和必要展示辅助
- **AND** player SHALL NOT 通过该上下文访问 engine 状态写入 API、完整状态树、随机源或其他玩家私密字段
