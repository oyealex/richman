## ADDED Requirements

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
系统 SHALL 提供 app 层 engine 装配能力，将配置、棋盘、玩家、renderer 和随机种子连接到 `GameEngine.create`。

#### Scenario: Engine is assembled from app defaults
- **WHEN** 使用默认配置、默认玩家和 renderer 调用 app 层 engine 装配函数
- **THEN** 返回值 MUST 是已初始化的 `GameEngine`
- **AND** engine 的内部状态 MUST 包含对应数量的玩家和默认配置中的地块运行时状态

#### Scenario: Seed is forwarded to engine
- **WHEN** 使用相同 seed 调用 app 层 engine 装配函数两次
- **THEN** 两个 engine MUST 产生确定性的初始状态

### Requirement: App module runs a game
系统 SHALL 提供 app 层运行入口，用于启动已装配的 engine 并返回最终 `InternalGameState`。

#### Scenario: Game can run with max turn limit
- **WHEN** 调用 app 层运行入口并传入 `max_turns`
- **THEN** 系统 MUST 启动 engine 主循环
- **AND** 返回值 MUST 是 `InternalGameState`
- **AND** 运行回合数 MUST NOT 超过传入的 `max_turns`

### Requirement: CLI play command uses app assembly
系统 SHALL 让 `richman play` 命令通过 app 装配层启动游戏，而不是只启动静态 adapter shell。

#### Scenario: Play command accepts bounded run options
- **WHEN** 用户执行 `richman play --players 2 --max-turns 1 --seed 1`
- **THEN** CLI MUST 通过 app 装配层创建并启动游戏
- **AND** 命令 MUST 正常退出

#### Scenario: Play command rejects invalid player count
- **WHEN** 用户执行 `richman play --players 1`
- **THEN** CLI MUST 报告参数错误
- **AND** 游戏 MUST NOT 启动
