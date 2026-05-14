# tui-demolish-target-flow

## Purpose

定义 DEMOLISH_TARGET 阶段 TUI 侧的交互流：GameScreen 将候选格传入 BoardWidget 驱动高亮，玩家点击候选格提交目标或按 Esc 取消回退。

## ADDED Requirements

### Requirement: GameScreen passes DEMOLISH_TARGET candidates to BoardWidget for highlighting

系统 SHALL 在 DEMOLISH_TARGET 阶段将 `required_input.candidates` 传入 `BoardWidget.highlight_positions`，由 BoardWidget 统一驱动候选格高亮（通用高亮机制见 tui-board-widget）。

#### Scenario: DEMOLISH_TARGET sets highlight positions from candidates

- **WHEN** `_apply_step_result` 收到 `required_input.kind=DEMOLISH_TARGET, candidates=(3,5)`
- **THEN** GameScreen MUST 调用 `BoardWidget.set_highlight_positions(frozenset({3, 5}))`

#### Scenario: Highlight is cleared when DEMOLISH_TARGET ends

- **WHEN** DEMOLISH_TARGET 阶段结束（提交目标或 Esc 取消）
- **THEN** GameScreen MUST 调用 `BoardWidget.set_highlight_positions(frozenset())`

#### Scenario: Highlight is cleared in non-DEMOLISH_TARGET phases

- **WHEN** `_apply_step_result` 收到 `required_input=None` 或 `required_input.kind != DEMOLISH_TARGET`
- **THEN** GameScreen MUST 调用 `BoardWidget.set_highlight_positions(frozenset())`

### Requirement: DEMOLISH_TARGET supports Esc cancellation via TUI

系统 SHALL 在 DEMOLISH_TARGET 阶段监听 Esc 键，提交 `target_position=None` 作为取消信号。引擎收到后不消耗拆除卡并退回动作选择（引擎侧行为见 engine-turn-flow delta）。

#### Scenario: Esc during DEMOLISH_TARGET submits cancel signal

- **WHEN** 当前 required_input.kind 为 DEMOLISH_TARGET 且用户按下 Esc
- **THEN** GameScreen MUST 提交 `EngineInput(kind=DEMOLISH_TARGET, player_index=required.player_index, target_position=None)`

#### Scenario: Esc has no effect in non-DEMOLISH_TARGET phases

- **WHEN** 当前 required_input.kind 不是 DEMOLISH_TARGET 且用户按下 Esc
- **THEN** GameScreen MUST NOT 提交 EngineInput

### Requirement: ActionBar shows cancel hint during DEMOLISH_TARGET

系统 SHALL 在 DEMOLISH_TARGET 阶段的 ActionBar 中显示取消提示。

#### Scenario: DEMOLISH_TARGET hint includes Esc instruction

- **WHEN** ActionBar 渲染 DEMOLISH_TARGET 的提示文字
- **THEN** 提示 MUST 包含 "Esc 取消" 或等效取消指引
- **AND** 候选格列表 MUST 仍然可见
