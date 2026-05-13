# tui-game-screen (delta)

## ADDED Requirements

### Requirement: GameScreen composes PlayerStrip and EventLine in layout

系统 SHALL 在 `compose()` 中扩展布局，在 BoardWidget 之后插入 PlayerStrip 和 EventLine，最终顺序为 Header → BoardWidget → PlayerStrip → EventLine → ActionBar。棋盘可用高度扣减新增元素：Header（1行）、PlayerStrip（1行）、EventLine（1行）、ActionBar（5行）。

#### Scenario: GameScreen composes all widgets in correct order

- **WHEN** GameScreen 渲染布局
- **THEN** 子 widget 中 MUST 包含 `BoardWidget`、`PlayerStrip`、`EventLine`、`ActionBar`

#### Scenario: GameScreen deducts PlayerStrip and EventLine from board height

- **WHEN** GameScreen `compose()` 计算 BoardWidget 的 `board_terminal_size`
- **THEN** `board_terminal_size` MUST 为 `(self.size.height - 1 - 1 - 1 - 5, self.size.width)`
- **AND** 扣减值分别对应 Header、PlayerStrip、EventLine、ActionBar 的高度

### Requirement: GameScreen updates PlayerStrip and EventLine on step result

系统 SHALL 在 `_apply_step_result` 中同步更新 PlayerStrip 和 EventLine 的内容。

#### Scenario: Step result updates PlayerStrip

- **WHEN** `_apply_step_result(result)` 被调用
- **THEN** GameScreen MUST 查询 PlayerStrip 并调用 `update_snapshot(result.snapshot)`

#### Scenario: Step result updates EventLine

- **WHEN** `_apply_step_result(result)` 被调用
- **THEN** GameScreen MUST 查询 EventLine 并调用 `update_snapshot(result.snapshot)`

### Requirement: GameScreen handles E key for EventLine

系统 SHALL 在 GameScreen 级绑定 E 键，按下时发出 `EventLine.OpenRequested` 消息，无需 EventLine 获得焦点。

#### Scenario: E key emits OpenRequested at GameScreen level

- **WHEN** GameScreen 获得 E 键按下事件
- **THEN** GameScreen MUST 发出 `EventLine.OpenRequested` 消息

#### Scenario: Non-E keys do not emit OpenRequested

- **WHEN** GameScreen 收到非 E 键事件
- **THEN** GameScreen MUST NOT 发出 `EventLine.OpenRequested` 消息（除非用于其他绑定）
