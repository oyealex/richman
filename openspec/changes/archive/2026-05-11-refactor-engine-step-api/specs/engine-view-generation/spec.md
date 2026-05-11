## ADDED Requirements

### Requirement: StepResult carries renderable snapshot
系统 SHALL 在每个 StepResult 中携带当前 viewer 可展示的 `GameSnapshot`。

#### Scenario: Required input frame has snapshot
- **WHEN** engine 返回 RequiredInput
- **THEN** 同一个 StepResult MUST 包含当前局面的 GameSnapshot
- **AND** adapter 可以在不读取 InternalGameState 的情况下渲染等待输入画面

#### Scenario: Display-only frame has snapshot
- **WHEN** engine 返回骰子、移动、落点或回合结束展示点
- **THEN** StepResult MUST 包含反映该展示点后的 GameSnapshot

### Requirement: StepResult carries incremental event view
系统 SHALL 在 StepResult 中暴露本 step 新增事件，并继续在 GameSnapshot 中提供完整事件日志。

#### Scenario: Incremental events are exposed
- **WHEN** 本次 advance 记录了 DICE_ROLLED 和 PLAYER_MOVED
- **THEN** StepResult.events 包含这两个新增事件

#### Scenario: Snapshot keeps complete event log
- **WHEN** 已经发生多次 step
- **THEN** StepResult.snapshot.event_log 包含当前 viewer 可见的完整事件序列

## REMOVED Requirements

### Requirement: Engine input context only exposes prompt_choice
**Reason**: step API 用结构化 RequiredInput/EngineInput 替代 engine 内部阻塞输入上下文，engine 不再通过 renderer prompt 获取人类选择。

**Migration**: adapter 根据 RequiredInput 收集输入并调用 `advance(input)`；AI 策略仍可通过 player 模块在非阻塞路径中选择合法动作或目标。

#### Scenario: InputContext delegates to renderer
- **WHEN** a HumanPlayer calls context.prompt_choice("选择动作", ["BUY", "SKIP"])
- **THEN** the call is forwarded to renderer.prompt_choice("选择动作", ("BUY", "SKIP"))

#### Scenario: InputContext has no access to engine internals
- **WHEN** an InputContext is passed to a Player
- **THEN** the Player cannot access InternalGameState, engine mutation methods, or other players private data through it
