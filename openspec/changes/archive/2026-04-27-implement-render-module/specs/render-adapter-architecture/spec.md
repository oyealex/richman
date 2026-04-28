## ADDED Requirements

### Requirement: Render module public API

系统 SHALL 提供 `richman.render` 公共 API，使 engine 和 HumanPlayer 输入上下文可以通过框架无关边界展示游戏状态、展示事件、获取输入并展示终局。

#### Scenario: Render package exports public protocol

- **WHEN** 开发者执行 `from richman.render import Renderer, render_frame, render_event_log, prompt_choice, prompt_number, render_game_over`
- **THEN** 导入 MUST 成功且无需知道 render 内部源码文件布局

#### Scenario: Renderer protocol exposes required operations

- **WHEN** engine 或 adapter 需要实现 render 边界
- **THEN** render 模块 SHALL 提供协议或等价抽象
- **AND** 该边界 MUST 覆盖 `render_frame(snapshot)`、`render_event_log(events, viewer_index)`、`prompt_choice(question, options)`、`prompt_number(question, min_value, max_value)` 和 `render_game_over(winner_name)`

### Requirement: Render module dependency boundary

系统 SHALL 保持 `richman.render` 只依赖 `richman.domain` 和标准库，具体 UI 框架代码必须位于 adapter 实现内部。

#### Scenario: Render module avoids engine dependency

- **WHEN** 检查 `src/richman/render` 的源码导入
- **THEN** render 模块 MUST NOT 导入 `richman.engine`、`richman.board`、`richman.rules`、`richman.player` 或 `richman.adapters`

#### Scenario: Render module avoids UI framework dependency

- **WHEN** 检查 `src/richman/render` 的源码导入
- **THEN** render 模块 MUST NOT 导入 Textual、Rich widget、浏览器框架、终端事件对象或传输层专属类型

### Requirement: GameSnapshot frame rendering

系统 SHALL 使用 `domain.GameSnapshot` 作为 render 的主要展示输入，并将公开棋盘、公开玩家、当前 viewer 私有信息、可用动作和事件日志转换为可展示内容。

#### Scenario: Render frame consumes domain snapshot

- **WHEN** engine 调用 `render_frame(snapshot)` 且传入 `GameSnapshot`
- **THEN** render 模块 SHALL 从快照读取回合、阶段、骰子、公开棋盘、公开玩家、viewer 私有信息和可选动作
- **AND** render 模块 MUST NOT 读取或要求 `InternalGameState`

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

系统 SHALL 提供终局展示能力，使 engine 可以在游戏结束时通过 render 边界展示胜者。

#### Scenario: Winner is displayed

- **WHEN** engine 调用 `render_game_over(winner_name)`
- **THEN** render 模块 SHALL 展示胜者名称和终局状态
- **AND** 它 MUST NOT 修改游戏状态或重新计算胜利条件
