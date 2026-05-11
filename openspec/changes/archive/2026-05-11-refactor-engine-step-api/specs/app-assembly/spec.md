## ADDED Requirements

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

## MODIFIED Requirements

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
