# tui-game-screen

## Purpose

提供 `GameScreen`（Textual Screen），持有 `GameEngine`、`GameConfig`、`player_controllers`，通过 `engine.advance()` 驱动游戏循环：非输入 step 自动推进，AI 玩家自动提交输入，人类玩家等待交互，`game_over` 时停止并展示终局信息。
## Requirements
### Requirement: GameScreen holds GameEngine and drives step API

系统 SHALL 提供 `GameScreen`（Textual `Screen` 子类），接收 `GameEngine`、`GameConfig` 和 `player_controllers: Sequence[Player]`，通过 `engine.advance()` 驱动游戏循环，在 `on_mount` 中通过 `run_worker` 启动异步推进循环。

#### Scenario: GameScreen constructor receives engine, config, and player controllers

- **WHEN** 创建 `GameScreen(engine, config, player_controllers)`
- **THEN** GameScreen MUST 存储三者为实例属性
- **AND** `player_controllers` 的索引顺序 MUST 与 `engine.get_state().players` 一致

#### Scenario: GameScreen mounts and starts advance worker

- **WHEN** GameScreen 被 mount 到 App
- **THEN** GameScreen MUST 通过 `self.run_worker(self._advance_loop(), exclusive=True)` 启动异步推进循环
- **AND** MUST 用返回的 `StepResult.snapshot` 更新 BoardWidget

#### Scenario: GameScreen computes board terminal size from available space

- **WHEN** GameScreen `compose()` 构建 BoardWidget
- **THEN** `board_terminal_size` MUST 为 `(self.size.height - header_height - action_bar_height, self.size.width)`
- **AND** MUST 将此尺寸传给 `compute_layout_geometry` 和 `BoardWidget`

#### Scenario: GameScreen composes BoardWidget and ActionBar

- **WHEN** GameScreen 渲染布局
- **THEN** 子 widget 中 MUST 包含一个 `BoardWidget`
- **AND** MUST 包含一个 `ActionBar`

#### Scenario: GameScreen does not modify InternalGameState

- **WHEN** GameScreen 调用 `engine.advance()`
- **THEN** GameScreen MUST NOT 直接修改 `engine.get_state()` 返回的 `InternalGameState`
- **AND** 所有状态变更 MUST 通过 `engine.advance(engine_input)` 完成

### Requirement: GameScreen auto-advances non-input steps

系统 SHALL 在遇到 `StepResult.required_input is None` 且 `game_over=False` 时自动继续推进，无需用户交互。遇到人类玩家 RequiredInput 时阻塞在 asyncio.Event 上等待 UI 交互，而非退出 worker。

#### Scenario: Non-input step advances automatically

- **WHEN** `engine.advance(None)` 返回 `StepResult(required_input=None, game_over=False)`
- **THEN** GameScreen MUST 自动再次调用 `engine.advance(None)`
- **AND** MUST 在两次 advance 之间 `await asyncio.sleep(0.3)` 以允许 UI 刷新

#### Scenario: Auto-advance stops at required_input

- **WHEN** 自动推进遇到 `StepResult(required_input=RequiredInput(...))`
- **THEN** GameScreen MUST 停止自动推进
- **AND** MUST 更新 ActionBar 以显示对应的输入控件

#### Scenario: Auto-advance stops at game over

- **WHEN** 自动推进遇到 `StepResult(game_over=True)`
- **THEN** GameScreen MUST 停止自动推进
- **AND** MUST NOT 再次调用 `engine.advance()`

#### Scenario: Human input worker waits on asyncio.Event

- **WHEN** `required_input.player_index` 对应玩家不是 `AIPlayer`
- **THEN** `_advance_loop` MUST `await self._pending_human.wait()` 阻塞等待
- **AND** MUST NOT 直接 `return`

#### Scenario: Worker clears event after wake-up before continuing loop

- **WHEN** `_advance_loop` 被 `_pending_human.set()` 唤醒
- **THEN** `_advance_loop` MUST 在继续推进前调用 `self._pending_human.clear()`
- **AND** 确保下一次遇到人类输入等待时 `wait()` 会真正阻塞

#### Scenario: Human input submission resumes worker when no further input needed

- **WHEN** 人类玩家提交 EngineInput 后 `engine.advance()` 返回 `required_input=None, game_over=False`
- **THEN** `_pending_human` Event MUST 被 set
- **AND** `_advance_loop` MUST 继续自动推进

#### Scenario: Human input submission waits again when further input needed

- **WHEN** 人类玩家提交 USE_DEMOLISH 后引擎返回 DEMOLISH_TARGET required_input
- **THEN** `_pending_human` Event MUST NOT 被 set
- **AND** ActionBar MUST 显示 DEMOLISH_TARGET 提示
- **AND** GameScreen MUST 等待用户点击候选格或按 Esc

### Requirement: GameScreen detects AI players via player_controllers and auto-submits input

系统 SHALL 通过 `isinstance(self._player_controllers[required.player_index], AIPlayer)` 检测 AI 玩家，在确认后自动构造并提交 `EngineInput`，不等待用户交互。

#### Scenario: AI ROLL_DICE auto-submitted

- **WHEN** `required_input.kind` 为 `ROLL_DICE` 且当前玩家是 `AIPlayer`
- **THEN** GameScreen MUST 自动提交 `EngineInput(kind=ROLL_DICE, player_index=required.player_index)`

#### Scenario: AI ACTION_CHOICE auto-submitted

- **WHEN** `required_input.kind` 为 `ACTION_CHOICE` 且当前玩家是 `AIPlayer`
- **THEN** GameScreen MUST 自动提交 `EngineInput(kind=ACTION_CHOICE, player_index=required.player_index, action=options[0])`

#### Scenario: AI JAIL_CHOICE auto-submitted

- **WHEN** `required_input.kind` 为 `JAIL_CHOICE` 且当前玩家是 `AIPlayer`
- **THEN** GameScreen MUST 自动提交 `EngineInput` 包含 `USE_JAIL_PASS`（如果可选）或 `ACCEPT_JAIL`

#### Scenario: AI DEMOLISH_TARGET auto-submitted

- **WHEN** `required_input.kind` 为 `DEMOLISH_TARGET` 且当前玩家是 `AIPlayer`
- **THEN** GameScreen MUST 自动提交 `EngineInput(kind=DEMOLISH_TARGET, player_index=required.player_index, target_position=candidates[0])`

#### Scenario: Human player input waits for interaction

- **WHEN** `required_input.player_index` 对应玩家不是 `AIPlayer`
- **THEN** GameScreen MUST 停止自动推进
- **AND** MUST 等待用户通过 ActionBar 或棋盘点击提交输入

### Requirement: GameScreen handles CellClicked for DEMOLISH_TARGET

系统 SHALL 在 `required_input.kind` 为 `DEMOLISH_TARGET` 时响应 `CellWidget.CellClicked` 消息，验证 position 在 candidates 中后提交输入。

#### Scenario: Click on candidate cell submits demolish target

- **WHEN** 当前 `required_input.kind` 为 `DEMOLISH_TARGET` 且用户点击 `position=5` 的 CellWidget
- **AND** `5` 在 `required_input.candidates` 中
- **THEN** GameScreen MUST 提交 `EngineInput(kind=DEMOLISH_TARGET, player_index=required.player_index, target_position=5)`

#### Scenario: Click on non-candidate cell does nothing

- **WHEN** 当前 `required_input.kind` 为 `DEMOLISH_TARGET` 且用户点击 `position=9` 的 CellWidget
- **AND** `9` 不在 `required_input.candidates` 中
- **THEN** GameScreen MUST NOT 提交输入

#### Scenario: Click when no DEMOLISH_TARGET required does nothing

- **WHEN** 当前 `required_input` 为 None 或 kind 不是 `DEMOLISH_TARGET`
- **THEN** CellWidget 点击 MUST NOT 触发输入提交

### Requirement: GameScreen stops advancing on game over

系统 SHALL 在 `StepResult.game_over=True` 时停止推进游戏，在 ActionBar 中展示终局信息。

#### Scenario: Game over stops advance

- **WHEN** `engine.advance()` 返回 `StepResult(game_over=True)`
- **THEN** GameScreen MUST NOT 再次调用 `engine.advance()`

#### Scenario: Game over shows winner in ActionBar

- **WHEN** 游戏结束有赢家（event_log 包含 `GAME_OVER` 事件）
- **THEN** ActionBar MUST 展示赢家名称

### Requirement: GameScreen code is isolated in screens package

系统 SHALL 确保 GameScreen 源码位于 `richman.adapters.textual_tui.screens` 包内。

#### Scenario: GameScreen import path

- **WHEN** 导入 GameScreen
- **THEN** 导入路径 MUST 为 `richman.adapters.textual_tui.screens.game.GameScreen`

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

### Requirement: GameScreen binds Esc to cancel DEMOLISH_TARGET

系统 SHALL 在 GameScreen 级绑定 Esc 键，当处于 DEMOLISH_TARGET 阶段时提交取消输入。

#### Scenario: Esc during DEMOLISH_TARGET submits cancel input

- **WHEN** 当前 `required_input.kind` 为 `DEMOLISH_TARGET` 且用户按下 Esc
- **THEN** GameScreen MUST 提交 `EngineInput(kind=DEMOLISH_TARGET, player_index=required.player_index, target_position=None)`
- **AND** MUST NOT 提交其他类型的 EngineInput

#### Scenario: Esc during non-DEMOLISH_TARGET phase is ignored

- **WHEN** 当前无 required_input 或 required_input.kind 不是 DEMOLISH_TARGET
- **THEN** GameScreen MUST NOT 因 Esc 键提交任何 EngineInput

### Requirement: GameScreen passes highlight positions to BoardWidget

系统 SHALL 在 DEMOLISH_TARGET 阶段将候选格集合传入 BoardWidget 以驱动高亮。

#### Scenario: DEMOLISH_TARGET sets BoardWidget highlight_positions

- **WHEN** `_apply_step_result` 收到 `required_input.kind=DEMOLISH_TARGET, candidates=(3,5)`
- **THEN** GameScreen MUST 调用 `BoardWidget.set_highlight_positions(frozenset({3, 5}))`

#### Scenario: Non-DEMOLISH_TARGET clears highlight positions

- **WHEN** `_apply_step_result` 收到 `required_input=None` 或 `required_input.kind != DEMOLISH_TARGET`
- **THEN** GameScreen MUST 调用 `BoardWidget.set_highlight_positions(frozenset())`

