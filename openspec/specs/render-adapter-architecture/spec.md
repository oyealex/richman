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

engine 集成 SHALL 支持 step-based 推进，使 render adapter 可以从事件循环或请求周期驱动游戏流程。

#### Scenario: 请求人类输入

- **WHEN** 游戏到达需要人类输入的节点
- **THEN** engine/controller 边界暴露一个 decision request，而不是阻塞等待终端输入

#### Scenario: 人类输入恢复推进

- **WHEN** render adapter 提交有效决策
- **THEN** engine/controller 边界推进游戏，并产生下一个 snapshot、decision request 或终局结果

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

