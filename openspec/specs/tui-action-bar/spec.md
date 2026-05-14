# tui-action-bar

## Purpose

提供 `ActionBar` widget，根据 `RequiredInput` 动态渲染操作按钮（掷骰、动作选择、监狱选择、拆除目标），支持鼠标点击和键盘快捷键提交 `EngineInput`。
## Requirements
### Requirement: ActionBar renders input controls per RequiredInput kind

系统 SHALL 提供 `ActionBar` widget（Textual `Widget` 子类），通过 `required_input: Reactive[RequiredInput | None]` reactive 属性接收输入状态。`watch_required_input` watcher 异步清空子 widget 并重建对应按钮或提示文字。按钮标签包含数字快捷键序号。

#### Scenario: ActionBar renders ROLL_DICE button

- **WHEN** 传入 `RequiredInput(kind=ROLL_DICE, player_index=0)`
- **THEN** ActionBar MUST 渲染一个"掷骰"按钮
- **AND** 按钮按下 Enter / Space 时 MUST 发出 `ActionBar.ActionSubmitted` 消息

#### Scenario: ActionBar renders ACTION_CHOICE buttons

- **WHEN** 传入 `RequiredInput(kind=ACTION_CHOICE, player_index=0, options=(BUY, SKIP))`
- **THEN** ActionBar MUST 渲染两个按钮
- **AND** 第一个按钮标签 MUST 为 `[1] 购买`
- **AND** 第二个按钮标签 MUST 为 `[2] 跳过`
- **AND** 每个按钮点击时 MUST 发出包含对应 `Action` 的 `ActionSubmitted`

#### Scenario: ActionBar renders JAIL_CHOICE buttons

- **WHEN** 传入 `RequiredInput(kind=JAIL_CHOICE, player_index=0, options=(USE_JAIL_PASS, ACCEPT_JAIL))`
- **THEN** ActionBar MUST 渲染两个带序号前缀的按钮
- **AND** 每个按钮 MUST 发出包含对应 `Action` 的 `ActionSubmitted`

#### Scenario: ActionBar renders DEMOLISH_TARGET hint

- **WHEN** 传入 `RequiredInput(kind=DEMOLISH_TARGET, player_index=0, candidates=(3, 5))`
- **THEN** ActionBar MUST 渲染提示文字"请点击棋盘上的目标格子"
- **AND** MUST NOT 渲染操作按钮
- **AND** MUST 列出候选 position
- **AND** MUST 包含 "Esc 取消" 取消指引

#### Scenario: ActionBar clears when no input required

- **WHEN** 传入 `None` 或 `required_input` 为空
- **THEN** ActionBar MUST 清空所有按钮和提示

### Requirement: ActionBar emits ActionSubmitted message on user input

系统 SHALL 在用户点击按钮时发出 `ActionBar.ActionSubmitted(engine_input)` 冒泡消息，携带可提交给 `engine.advance()` 的 `EngineInput`。

#### Scenario: Button click emits ActionSubmitted

- **WHEN** 用户点击 ROLL_DICE 按钮
- **THEN** ActionBar MUST 发出 `ActionBar.ActionSubmitted(EngineInput(kind=ROLL_DICE, player_index=...))`

#### Scenario: ActionSubmitted contains correct EngineInput

- **WHEN** 用户点击 ACTION_CHOICE 中对应 `BUY` 的按钮
- **THEN** `ActionSubmitted.engine_input` MUST 为 `EngineInput(kind=ACTION_CHOICE, player_index=..., action=BUY)`

#### Scenario: ActionSubmitted message inherits Textual Message

- **WHEN** 检查 `ActionBar.ActionSubmitted` 类
- **THEN** 它 MUST 继承 `textual.message.Message`

### Requirement: ActionBar supports keyboard shortcuts

系统 SHALL 为 ActionBar 按钮提供键盘快捷键支持。Enter 或 Space 触发第一个（主）按钮；数字键 1-9 触发对应序号按钮。

#### Scenario: Enter triggers primary button

- **WHEN** ActionBar 渲染了 ROLL_DICE 按钮且用户按下 Enter
- **THEN** MUST 发出与点击该按钮相同的 `ActionSubmitted`

#### Scenario: Number key triggers corresponding button

- **WHEN** ActionBar 渲染了 3 个 ACTION_CHOICE 按钮且用户按下 "2"
- **THEN** MUST 发出与点击第 2 个按钮相同的 `ActionSubmitted`

### Requirement: ActionBar widget is isolated in widgets package

系统 SHALL 确保 ActionBar 源码位于 `richman.adapters.textual_tui.widgets.action_bar` 模块。

#### Scenario: ActionBar import path

- **WHEN** 导入 ActionBar
- **THEN** 导入路径 MUST 为 `richman.adapters.textual_tui.widgets.action_bar.ActionBar`

