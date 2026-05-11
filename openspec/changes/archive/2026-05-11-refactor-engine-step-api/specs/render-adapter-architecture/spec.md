## ADDED Requirements

### Requirement: Adapters drive engine step flow
系统 SHALL 让 console、Textual TUI 和测试 adapter 通过 engine step API 驱动游戏流程。

#### Scenario: Adapter renders StepResult
- **WHEN** adapter 调用 `engine.advance(input)` 获得 StepResult
- **THEN** adapter 使用 StepResult.snapshot、StepResult.events、StepResult.required_input 和 StepResult.game_over 渲染或收集输入

#### Scenario: Adapter submits structured input
- **WHEN** 用户在 adapter 中完成掷骰、动作、拆除目标或入狱选择
- **THEN** adapter 将结构化 EngineInput 提交给 `engine.advance(input)`
- **AND** adapter MUST NOT 直接修改 InternalGameState

### Requirement: Console driver preserves CLI behavior
系统 SHALL 提供 console step driver，使现有命令行玩法在 step API 上运行。

#### Scenario: Console driver prompts for required input
- **WHEN** StepResult.required_input 非空且当前玩家需要人类输入
- **THEN** console driver 使用框架无关输入原语收集合法输入
- **AND** 将该输入提交给 engine

#### Scenario: Console driver renders game over
- **WHEN** StepResult.game_over 为 true
- **THEN** console driver 负责展示胜者和终局状态

## MODIFIED Requirements

### Requirement: Step-based engine interaction
engine 集成 SHALL 支持 step-based 推进，使 render adapter 可以从事件循环、终端循环或测试驱动中推进游戏流程。

#### Scenario: 请求人类输入
- **WHEN** 游戏到达需要人类输入的节点
- **THEN** engine 边界暴露 `RequiredInput`
- **AND** engine MUST NOT 阻塞等待终端输入

#### Scenario: 人类输入恢复推进
- **WHEN** render adapter 提交有效结构化输入
- **THEN** engine 边界推进游戏，并产生下一个 StepResult、RequiredInput 或终局结果

#### Scenario: 展示点无需输入
- **WHEN** 游戏到达骰子结果、移动、落点、租金、动作结果或回合结束展示点
- **THEN** engine 返回不带 required_input 的 StepResult
- **AND** adapter 可以在展示后自行决定何时继续调用 `advance(None)`

### Requirement: Render module public API
系统 SHALL 提供 `richman.render` 公共 API，使 console driver 和其他 adapter 可以通过框架无关工具格式化快照、展示事件、获取终端输入并展示终局；engine 不再直接依赖该 API。

#### Scenario: Render package exports public protocol
- **WHEN** 开发者执行 `from richman.render import Renderer, render_frame, render_event_log, prompt_choice, prompt_number, render_game_over`
- **THEN** 导入 MUST 成功且无需知道 render 内部源码文件布局

#### Scenario: Renderer protocol exposes legacy-compatible operations
- **WHEN** console driver 或兼容 adapter 需要使用 render 边界
- **THEN** render 模块 SHALL 提供协议或等价抽象
- **AND** 该边界 MUST 覆盖 `render_frame(snapshot)`、`render_event_log(events, viewer_index)`、`prompt_choice(question, options)`、`prompt_number(question, min_value, max_value)` 和 `render_game_over(winner_name)`

#### Scenario: Engine does not depend on render public API
- **WHEN** 检查 `src/richman/engine` 的源码导入
- **THEN** engine 模块 MUST NOT 导入 `richman.render`

### Requirement: GameSnapshot frame rendering
系统 SHALL 使用 `domain.GameSnapshot` 作为 adapter 的主要展示输入，并将公开棋盘、公开玩家、当前 viewer 私有信息、可用动作和事件日志转换为可展示内容。

#### Scenario: Adapter frame consumes domain snapshot
- **WHEN** adapter 需要展示游戏局面且收到 `GameSnapshot`
- **THEN** adapter SHALL 从快照读取回合、阶段、骰子、公开棋盘、公开玩家、viewer 私有信息和可选动作
- **AND** adapter MUST NOT 读取或要求 `InternalGameState`

#### Scenario: Render frame has no game mutation
- **WHEN** render 模块展示 `GameSnapshot`
- **THEN** 它 MUST NOT 修改玩家现金、位置、手牌、地块归属、地块等级、阶段、骰子、事件日志或可用动作

#### Scenario: Empty optional action list is displayable
- **WHEN** `GameSnapshot.available_actions` 为 `None` 或空集合
- **THEN** render 模块 SHALL 能展示当前局面
- **AND** 它 MUST NOT 伪造 `BUY`、`UPGRADE`、`USE_DEMOLISH`、`USE_JAIL_PASS`、`ACCEPT_JAIL` 或 `SKIP` 动作

### Requirement: Render game over display
系统 SHALL 提供终局展示能力，使 adapter 可以在游戏结束时通过 render 边界展示胜者。

#### Scenario: Winner is displayed
- **WHEN** adapter 收到 game-over StepResult 或 GAME_OVER 事件
- **THEN** render 模块 SHALL 展示胜者名称和终局状态
- **AND** 它 MUST NOT 修改游戏状态或重新计算胜利条件

#### Scenario: Engine does not invoke game-over display
- **WHEN** engine 检测到游戏结束
- **THEN** engine MUST 记录 GAME_OVER 并返回 game-over StepResult
- **AND** engine MUST NOT 调用 render_game_over
