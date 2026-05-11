## ADDED Requirements

### Requirement: AI strategy can satisfy engine input requests
系统 SHALL 允许 engine 或 driver 使用 AIPlayer 策略为 AI 当前玩家生成结构化 EngineInput。

#### Scenario: AI satisfies action choice
- **WHEN** RequiredInput.kind 为 ACTION_CHOICE 且当前玩家是 AI
- **THEN** AI 策略从 RequiredInput.options 中选择一个合法 Action
- **AND** 生成对应的 EngineInput

#### Scenario: AI satisfies demolish target choice
- **WHEN** RequiredInput.kind 为 DEMOLISH_TARGET 且当前玩家是 AI
- **THEN** AI 策略从 RequiredInput.candidates 中选择一个候选位置
- **AND** 生成对应的 EngineInput

#### Scenario: AI dice input has no strategy dependency
- **WHEN** RequiredInput.kind 为 ROLL_DICE 且当前玩家是 AI
- **THEN** engine 或 driver 可以生成确认掷骰的 EngineInput
- **AND** AIPlayer 不需要访问随机数源

### Requirement: Human decisions are submitted by adapters
系统 SHALL 让人类玩家的交互输入由 adapter 根据 RequiredInput 收集并提交。

#### Scenario: Human action input comes from adapter
- **WHEN** 当前人类玩家需要 ACTION_CHOICE
- **THEN** adapter 根据 RequiredInput.options 展示选择并提交 EngineInput
- **AND** engine MUST NOT 通过 HumanPlayer 阻塞获取选择

#### Scenario: Human target input comes from adapter
- **WHEN** 当前人类玩家需要 DEMOLISH_TARGET
- **THEN** adapter 根据 RequiredInput.candidates 展示候选目标并提交 EngineInput

## MODIFIED Requirements

### Requirement: Player public API
系统 SHALL 定义玩家决策接口，使 AI 策略和兼容人类玩家实现可以在不拥有游戏状态的情况下生成合法决策。

#### Scenario: Player interface exposes decision points
- **WHEN** engine 或 driver 需要 AI 选择动作或拆除目标
- **THEN** player 模块提供 `Player` 抽象接口
- **AND** 该接口包含 `name`、`decide(view, actions, engine_context)` 和 `choose_demolish_target(view, candidates, engine_context)`

#### Scenario: Dice wait is not required by step engine
- **WHEN** engine 使用 step API 进入 ROLL_DICE 输入点
- **THEN** engine 通过 RequiredInput 暴露掷骰请求
- **AND** engine MUST NOT 调用 `Player.wait_for_dice()` 阻塞等待

#### Scenario: Human and AI implementations are available
- **WHEN** app 或 engine 需要创建玩家
- **THEN** player 模块提供 `HumanPlayer` 和 `AIPlayer`
- **AND** 两者都实现 player 模块当前公开的决策接口或兼容接口

#### Scenario: Public API is exported from package root
- **WHEN** 后续模块执行 `from richman.player import Player, HumanPlayer, AIPlayer`
- **THEN** 导入成功且无需知道 player 内部源码文件布局

### Requirement: HumanPlayer delegates input through restricted context
系统 SHALL 将 `HumanPlayer` 的阻塞输入委托视为 console 兼容能力；step-driven TUI 不通过 HumanPlayer 获取人类输入。

#### Scenario: HumanPlayer waits for dice input
- **WHEN** 兼容 console 路径调用 HumanPlayer 的 `wait_for_dice()`
- **THEN** HumanPlayer 可以等待受限输入原语完成
- **AND** HumanPlayer 不修改游戏状态

#### Scenario: HumanPlayer requests action choice
- **WHEN** 兼容 console 路径调用 HumanPlayer 的 `decide(view, actions, engine_context)`
- **THEN** HumanPlayer 通过 `engine_context` 的输入原语展示由 `actions` 派生的选项
- **AND** HumanPlayer 返回用户选择对应的 `Action`

#### Scenario: HumanPlayer requests demolish target
- **WHEN** 兼容 console 路径调用 HumanPlayer 的 `choose_demolish_target(view, candidates, engine_context)`
- **THEN** HumanPlayer 通过 `engine_context` 的输入原语展示候选位置
- **AND** HumanPlayer 返回用户选择对应的候选位置

#### Scenario: Step-driven TUI bypasses HumanPlayer blocking input
- **WHEN** Textual TUI 需要人类输入
- **THEN** TUI adapter 根据 RequiredInput 收集输入并提交 EngineInput
- **AND** TUI MUST NOT 调用 HumanPlayer 的阻塞输入方法

#### Scenario: HumanPlayer has no render dependency
- **WHEN** HumanPlayer 需要获取输入
- **THEN** 它 SHALL 通过受限上下文或注入的输入原语完成
- **AND** 它 SHALL NOT 导入 Textual、Rich、render adapter 或 engine 实现

### Requirement: Player information boundary
系统 SHALL 确保 player 策略只能基于 `PlayerView`、RequiredInput 派生数据和 engine 显式传入的合法选项作出决策。

#### Scenario: Player receives a cropped view
- **WHEN** engine 或 driver 调用任意 `Player` 实现进行策略决策
- **THEN** player 接收 `PlayerView`
- **AND** player 不接收 `InternalGameState`

#### Scenario: Player does not inspect hidden private data
- **WHEN** `PlayerView.public_players` 只包含公开玩家信息
- **THEN** player 模块 SHALL NOT 尝试读取其他玩家现金、手牌数量或地块投入成本

#### Scenario: Engine context is opaque and restricted
- **WHEN** player 使用 `engine_context`
- **THEN** `engine_context` SHALL 只提供输入原语和必要展示辅助
- **AND** player SHALL NOT 通过该上下文访问 engine 状态写入 API、完整状态树、随机源或其他玩家私密字段

#### Scenario: Step input does not expose hidden data
- **WHEN** adapter 根据 RequiredInput 展示人类输入选项
- **THEN** RequiredInput MUST NOT 包含其他玩家现金、手牌数量或地块投入成本
