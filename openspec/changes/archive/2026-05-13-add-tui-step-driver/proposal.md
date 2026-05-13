## Why

当前 TUI（RichmanTuiApp）只能静态展示初始快照，无法推进游戏。需要让 TUI 持有 GameEngine 并通过 step API（advance/EngineInput）驱动完整回合循环，使 TUI 成为可交互的游戏客户端。

## What Changes

- 新增 `GameScreen`（Textual Screen），持有 `GameEngine`、`GameConfig`、当前 `StepResult`
- 新增 `ActionBar` widget，根据 `RequiredInput.kind` 动态显示操作按钮（掷骰、动作选择、监狱选择、拆除目标）
- `GameScreen` 实现 step 自动推进：非输入 step 连续通过，遇到 `required_input` 时判断玩家类型——AI 自动提交、人类等待交互
- `BoardWidget` 的 `CellClicked` 消息接入 `DEMOLISH_TARGET` 输入流
- `game_over=True` 时停止推进并展示终局信息
- 全套行为测试覆盖上述流程

## Capabilities

### New Capabilities

- `tui-game-screen`: GameScreen 负责持有 GameEngine、驱动 step API、自动推进、AI 输入自动提交、game over 停止
- `tui-action-bar`: ActionBar widget 根据 RequiredInput 动态渲染操作按钮，支持鼠标点击和键盘快捷键提交 EngineInput

### Modified Capabilities

（无——BoardWidget 已发出 CellClicked，本次只在 GameScreen 中消费该消息，不改变 BoardWidget 的规格。）

## Impact

- 新增 `src/richman/adapters/textual_tui/screens/game.py`（GameScreen + 辅助方法）
- 新增 `src/richman/adapters/textual_tui/widgets/action_bar.py`（ActionBar widget）
- 新增 `tests/test_textual_tui_game_screen.py`（行为测试，含 fake engine）
- `src/richman/adapters/textual_tui/app.py` 暂不修改（richman tui 入口留给后续 change）
- 依赖 `src/richman/engine/model.py`（GameEngine.advance）、`src/richman/domain/models.py`（StepResult, EngineInput, RequiredInput, InputKind, Action）、`src/richman/player/model.py`（Player, AIPlayer 类型检测）
