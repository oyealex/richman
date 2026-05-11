# render-adapter-architecture Specification

## Purpose
TBD - created by archiving change setup-project-dev-environment. Update Purpose after archive.
## Requirements
### Requirement: Render adapter boundary

系统 SHALL 定义面向渲染器的边界，使 render 实现消费 engine 生成的视图数据并提交用户决策，但不拥有或修改游戏状态。

#### Scenario: 渲染器接收快照数据

- **WHEN** render adapter 需要更新 UI
- **THEN** 它接收 `GameSnapshot` 或等价的 engine 生成视图模型，而不是 `InternalGameState`

#### Scenario: 渲染器提交决策

- **WHEN** 人类玩家选择一个可用动作或目标
- **THEN** render adapter 向 controller 或 engine 边界提交结构化决策，而不是直接执行该动作

### Requirement: UI-framework-neutral render contract

render 契约 SHALL 避免在 engine-facing 数据结构中出现 Textual、Rich、浏览器或传输层专属类型。

#### Scenario: Textual adapter 使用契约

- **WHEN** Textual TUI 渲染游戏
- **THEN** Textual 专属 widget、CSS、event 和 Rich renderable 保持在 Textual adapter 包内部

#### Scenario: 未来 Web adapter 使用相同契约

- **WHEN** 后续增加 Web adapter
- **THEN** 它可以消费同样的 snapshot 和 decision 契约，而不需要导入 Textual 模块

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

### Requirement: Textual TUI is the first render implementation

项目 SHALL 包含 Textual TUI adapter 作为首个 render 实现，同时保持 render 层可替换。

#### Scenario: TUI adapter 被隔离

- **WHEN** 检查初始 TUI 包
- **THEN** Textual 专属代码位于 adapter 实现内部，而不在 domain、board、rules、player 或 engine 模块中

#### Scenario: TUI app 可以在测试中构造

- **WHEN** TUI smoke test 在 headless 模式下构造 Textual app
- **THEN** app 构造成功，且不会启动阻塞式终端会话

### Requirement: Engine remains the state owner

系统 SHALL 保持 `engine` 是唯一修改 `InternalGameState` 的模块。

#### Scenario: Adapter 处理用户动作

- **WHEN** 用户通过 render adapter 选择 BUY、UPGRADE、USE_DEMOLISH、USE_JAIL_PASS、ACCEPT_JAIL 或 SKIP
- **THEN** adapter 将决策传递到 engine 边界，且自身不修改玩家、地块、阶段或事件日志状态

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

### Requirement: Render module dependency boundary

系统 SHALL 保持 `richman.render` 只依赖 `richman.domain` 和标准库，具体 UI 框架代码必须位于 adapter 实现内部。

#### Scenario: Render module avoids engine dependency

- **WHEN** 检查 `src/richman/render` 的源码导入
- **THEN** render 模块 MUST NOT 导入 `richman.engine`、`richman.board`、`richman.rules`、`richman.player` 或 `richman.adapters`

#### Scenario: Render module avoids UI framework dependency

- **WHEN** 检查 `src/richman/render` 的源码导入
- **THEN** render 模块 MUST NOT 导入 Textual、Rich widget、浏览器框架、终端事件对象或传输层专属类型

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

### Requirement: Event log privacy masking

系统 SHALL 在展示事件日志时按 viewer 隐私边界遮蔽非当前 viewer 的私密字段。

#### Scenario: Viewer private event details are visible

- **WHEN** render 为 `viewer_index` 对应玩家展示事件日志
- **THEN** 与该 viewer 自身相关的现金、手牌数量和持有地投入信息 MAY 被展示
- **AND** 展示内容 MUST 来自 `GameSnapshot.viewer_private`、`viewer_private_properties` 或同一 viewer 可见的事件字段

#### Scenario: Other players private event details are hidden

- **WHEN** render 为某个 viewer 展示包含其他玩家私密字段的事件
- **THEN** render MUST 隐藏其他玩家现金余额、手牌数量、购买价、累计升级投入和其他仅完整状态可见的数据

#### Scenario: Public event details remain visible

- **WHEN** 事件包含公开信息
- **THEN** render SHALL 展示事件类型、玩家名称、位置、地块名称、地块等级、卡牌描述、动作名称、破产结果或终局结果等公开字段

### Requirement: Render input primitives

系统 SHALL 提供框架无关输入原语，使 HumanPlayer 或 engine context 可以请求合法选项和数字输入。

#### Scenario: Choice prompt returns one option

- **WHEN** 调用 `prompt_choice(question, options)` 且 `options` 非空
- **THEN** 返回值 MUST 是 `options` 中的一个字符串

#### Scenario: Empty choice options are rejected

- **WHEN** 调用 `prompt_choice(question, options)` 且 `options` 为空
- **THEN** render 模块 MUST 报告调用错误

#### Scenario: Number prompt respects bounds

- **WHEN** 调用 `prompt_number(question, min_value, max_value)`
- **THEN** 返回值 MUST 是 `min_value` 与 `max_value` 之间的整数，包含边界值

#### Scenario: Invalid number bounds are rejected

- **WHEN** 调用 `prompt_number(question, min_value, max_value)` 且 `min_value` 大于 `max_value`
- **THEN** render 模块 MUST 报告调用错误

### Requirement: Textual adapter implements render boundary

系统 SHALL 保留 Textual TUI 作为首个 render adapter，并让 Textual 专属实现适配 `richman.render` 的框架无关契约。

#### Scenario: Textual adapter consumes render contract

- **WHEN** Textual TUI adapter 需要展示游戏局面
- **THEN** 它 SHALL 通过 `richman.render` 契约消费 `GameSnapshot` 或由该契约派生的展示模型
- **AND** Textual widget、CSS、事件对象和 Rich renderable MUST 保持在 `richman.adapters.textual_tui` 内部

#### Scenario: Textual app remains constructible in tests

- **WHEN** 测试在 headless 或非交互环境中构造 Textual app
- **THEN** app MUST 构造成功
- **AND** 它 MUST NOT 启动阻塞式终端会话

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

