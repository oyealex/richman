# tui-event-line Specification

## Purpose
TBD - created by archiving change add-tui-player-event-bars. Update Purpose after archive.
## Requirements
### Requirement: EventLine renders latest event from snapshot

系统 SHALL 提供 `EventLine` widget（Textual `Widget` 子类），从 `GameSnapshot.event_log[-1]` 获取最新事件并渲染为单行文本。

#### Scenario: EventLine shows latest event

- **WHEN** `GameSnapshot.event_log` 包含至少一条事件
- **THEN** EventLine MUST 渲染最新事件（最后一条）的格式化文本

#### Scenario: EventLine shows placeholder when no events

- **WHEN** `GameSnapshot.event_log` 为空
- **THEN** EventLine MUST 渲染占位文本（如 "--" 或等效空状态）

#### Scenario: EventLine has fixed height of 1

- **WHEN** 检查 EventLine CSS
- **THEN** `height` MUST 为 1

### Requirement: EventLine emits OpenRequested message on click

系统 SHALL 在用户点击 EventLine 时发出 `EventLine.OpenRequested()` 冒泡消息。E 键触发由 GameScreen 级绑定负责（见 tui-game-screen spec），EventLine 自身不处理键盘事件。

#### Scenario: Click emits OpenRequested

- **WHEN** 用户点击 EventLine 区域
- **THEN** EventLine MUST 发出 `EventLine.OpenRequested` 消息

#### Scenario: OpenRequested is a Textual Message

- **WHEN** 检查 `EventLine.OpenRequested` 类
- **THEN** 它 MUST 继承 `textual.message.Message`

### Requirement: EventLine updates when snapshot changes

系统 SHALL 通过 `update_snapshot(snapshot: GameSnapshot)` 方法接收新快照并刷新渲染。

#### Scenario: Snapshot update refreshes event text

- **WHEN** 调用 `update_snapshot(new_snapshot)`，其中 event_log 有新事件
- **THEN** EventLine MUST 渲染新事件的内容

### Requirement: EventLine code is isolated in widgets package

系统 SHALL 确保 EventLine 源码位于 `richman.adapters.textual_tui.widgets.event_line` 模块。

#### Scenario: EventLine import path

- **WHEN** 导入 EventLine
- **THEN** 导入路径 MUST 为 `richman.adapters.textual_tui.widgets.event_line.EventLine`

