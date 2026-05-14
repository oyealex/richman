# tui-action-bar (delta)

## MODIFIED Requirements

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
