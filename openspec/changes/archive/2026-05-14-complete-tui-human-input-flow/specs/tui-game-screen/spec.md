# tui-game-screen (delta)

## ADDED Requirements

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

## MODIFIED Requirements

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
