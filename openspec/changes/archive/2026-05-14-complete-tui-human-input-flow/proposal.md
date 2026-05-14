## Why

当前 TUI GameScreen 的 step API 驱动循环在遇到人类玩家 `RequiredInput` 时能停止并渲染 ActionBar，但多个输入阶段仍有交互缺口：按钮无快捷键序号标注、`DEMOLISH_TARGET` 阶段棋盘不标记候选格且无法取消退回、以及 `_advance_loop` 返回后缺少结构化恢复机制，导致一轮人类回合之后游戏可能停在无法交互的状态。本变更补齐这些缺口，使 `richman tui --players 2` 可以完整玩通一局。

## What Changes

- ActionBar 的 ACTION_CHOICE 和 JAIL_CHOICE 按钮标签增加序号前缀（如 `[1] 购买`），键盘快捷键 Enter / Space → 第 1 个按钮、数字键 1~9 → 对应序号按钮，逻辑已存在但标签缺失数字提示。
- GameScreen._advance_loop 中人类输入等待点改为 `asyncio.Event` 信号量阻塞（`await self._pending_human.wait()`），不再直接 return，确保 ActionSubmitted / CellClicked 提交后可继续推进循环，连续人类输入（如 USE_DEMOLISH → DEMOLISH_TARGET）也能稳定衔接。
- GameScreen 在 DEMOLISH_TARGET 阶段将 candidates 传入 BoardWidget，由 BoardWidget 为候选格设置 CSS class `candidate`，CellWidget 以高亮边框渲染。
- ActionBar 在 DEMOLISH_TARGET 阶段渲染取消提示（Esc），GameScreen 绑定 Esc 键，按下后构造一个特殊的取消 EngineInput 回到动作选择。
- 棋盘点击候选格提交拆除目标后，_submit_input 继续推进直到下一个 RequiredInput 或 game_over，若再次遇到人类输入则重新进入等待。

## Capabilities

### New Capabilities
- `tui-demolish-target-flow`: DEMOLISH_TARGET 阶段的棋盘高亮、候选格点击提交、Esc 取消回退

### Modified Capabilities
- `tui-action-bar`: 按钮标签增加序号前缀；DEMOLISH_TARGET 阶段增加 Esc 提示
- `tui-game-screen`: _advance_loop 等待人类输入的方式从 return 改为 asyncio.Event 阻塞；增加 Esc 取消 DEMOLISH_TARGET 逻辑
- `engine-turn-flow`: DEMOLISH_TARGET 阶段接受 target_position=None 作为取消信号，回退到 ACTION 阶段
- `tui-board-widget`: 新增候选格高亮能力，接收 candidates 集合并为对应 CellWidget 设置 CSS class

## Impact

- `richman.adapters.textual_tui.screens.game`：GameScreen 等待逻辑、Esc 绑定、candidates 传递
- `richman.adapters.textual_tui.widgets.action_bar`：按钮标签格式
- `richman.adapters.textual_tui.widgets.board`：BoardWidget 和 CellWidget 高亮
- `richman.domain.models`：不新增 InputKind，复用 `EngineInput(kind=DEMOLISH_TARGET, target_position=None)` 表达取消语义
- `richman.engine.model`：WAITING_FOR_DEMOLISH_TARGET 分支处理 target_position=None 取消（回到 READY_FOR_ACTION，不消耗拆除卡）
- 测试：`tests/test_textual_tui_game_screen.py`、新增相关测试
