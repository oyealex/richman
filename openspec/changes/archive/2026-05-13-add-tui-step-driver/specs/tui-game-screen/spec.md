## ADDED Requirements

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

系统 SHALL 在遇到 `StepResult.required_input is None` 且 `game_over=False` 时自动继续推进，无需用户交互。

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
