## ADDED Requirements

### Requirement: Engine advances through a step API
系统 SHALL 提供 `advance(input=None)` 作为主要交互入口，用于推进游戏到下一个展示点、输入请求或终局状态。

#### Scenario: Initial advance starts the first turn
- **WHEN** engine 创建后第一次调用 `advance(None)`
- **THEN** 返回 `StepResult`
- **AND** `StepResult.snapshot.turn` 反映已开始的当前回合
- **AND** 新增事件包含当前玩家的 `TURN_START`

#### Scenario: Advance returns required input instead of blocking
- **WHEN** 游戏推进到需要人类掷骰、选择动作、选择拆除目标或做入狱判决的节点
- **THEN** `advance(None)` 返回带有 `required_input` 的 `StepResult`
- **AND** engine MUST NOT 调用 renderer 或阻塞等待终端输入

#### Scenario: Advance accepts matching input
- **WHEN** 当前 `StepResult.required_input.kind` 为 `ACTION_CHOICE`
- **AND** 调用方提交匹配的 action input
- **THEN** engine 验证该动作合法并继续推进游戏

### Requirement: StepResult exposes frame data
系统 SHALL 通过 `StepResult` 暴露当前展示 frame 所需的数据。

#### Scenario: StepResult contains snapshot
- **WHEN** `advance()` 返回
- **THEN** `StepResult.snapshot` MUST 是当前 viewer 可展示的 `GameSnapshot` 或等价快照

#### Scenario: StepResult contains incremental events
- **WHEN** 本次 step 新增了事件
- **THEN** `StepResult.events` MUST 只包含本次 step 新增事件
- **AND** `StepResult.snapshot.event_log` 仍包含完整事件日志

#### Scenario: StepResult reports game over
- **WHEN** 游戏已经满足终局条件
- **THEN** `StepResult.game_over` MUST 为 true
- **AND** `StepResult.required_input` MUST 为 None

### Requirement: Engine validates structured input
系统 SHALL 校验提交给 `advance(input)` 的结构化输入与当前等待状态匹配。

#### Scenario: Unexpected input is rejected
- **WHEN** engine 当前未请求输入
- **AND** 调用方提交非空 input
- **THEN** engine MUST 报告调用错误

#### Scenario: Wrong input kind is rejected
- **WHEN** engine 当前请求 `ROLL_DICE`
- **AND** 调用方提交 `ACTION_CHOICE`
- **THEN** engine MUST 报告调用错误

#### Scenario: Wrong player input is rejected
- **WHEN** engine 当前请求 player 0 输入
- **AND** 调用方提交 player 1 的输入
- **THEN** engine MUST 报告调用错误

## MODIFIED Requirements

### Requirement: Engine factory creates validated engine instance
The system SHALL provide `GameEngine.create(config, board, players, seed=None)` that validates input and returns an initialized engine with a fresh InternalGameState and step cursor.

#### Scenario: Factory validates jail space existence
- **WHEN** create is called with a board that has no JAIL_SPACE cell
- **THEN** a ValueError is raised

#### Scenario: Factory validates single jail space
- **WHEN** create is called with a board that has exactly one JAIL_SPACE cell
- **THEN** the engine is created successfully

#### Scenario: Factory initializes state with correct player count
- **WHEN** create is called with N players
- **THEN** the engine's state contains exactly N PlayerState entries, each with name matching the player and cash equal to config.start_cash

#### Scenario: Factory initializes properties from board
- **WHEN** create is called with a board containing PROPERTY cells
- **THEN** the engine's state properties_by_position contains a PropertyState for each PROPERTY cell, all unowned (owner_player_index=None, level=0)

#### Scenario: Factory with seed produces deterministic state
- **WHEN** create is called twice with the same seed
- **THEN** both engine instances produce identical random sequences

#### Scenario: Factory does not require renderer
- **WHEN** create is called without a renderer argument
- **THEN** the engine is created successfully
- **AND** engine does not store or call a renderer

### Requirement: Engine starts and runs main loop
The system SHALL provide `start()` as a compatibility helper that executes the main game loop through the same step API until game over and returns the final InternalGameState.

#### Scenario: Start increments turn counter
- **WHEN** start() is called for an AI-only game
- **THEN** the turn counter advances for each non-bankrupt player that takes a turn

#### Scenario: Start skips bankrupt players
- **WHEN** a player is marked bankrupt
- **THEN** that player is skipped in subsequent turns

#### Scenario: Start ends when one player remains
- **WHEN** only one non-bankrupt player remains
- **THEN** the game ends and that player is the winner

#### Scenario: Start uses advance
- **WHEN** start() runs the game
- **THEN** it MUST progress by repeatedly calling the same step transition logic used by `advance()`
- **AND** it MUST NOT maintain a separate turn-processing implementation

#### Scenario: Start does not render directly
- **WHEN** start() detects game over
- **THEN** it returns the final state
- **AND** it MUST NOT call renderer game-over methods
