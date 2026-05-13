## 1. 搭建 screens 包和 GameScreen 骨架

- [x] 创建 `src/richman/adapters/textual_tui/screens/__init__.py`
- [x] 创建 `src/richman/adapters/textual_tui/screens/game.py`，定义 `GameScreen(Screen[None])` 类
- [x] `__init__` 接收 `engine: GameEngine`、`config: GameConfig`、`player_controllers: Sequence[Player]`，存储为实例属性
- [x] `compose()` 中计算 `board_terminal_size = (self.size.height - header_height - action_bar_height, self.size.width)`（header=1, action_bar=5），传给 `compute_layout_geometry(config, terminal_size=board_terminal_size)` 和 `BoardWidget(snapshot, geometry, terminal_size=board_terminal_size)`
- [x] `compose()` 产出 Header（`show_clock=True`）、`BoardWidget`（用初始 snapshot 和计算后的 geometry/terminal_size）、`ActionBar`（初始 `required_input=None`）
- [x] `on_mount()` 中用 `self.run_worker(self._advance_loop(), exclusive=True)` 启动异步推进循环
- [x] `_advance_loop()` 为 `async` 方法：循环调用 `engine.advance(None)` → 调 `_apply_step_result(result)` → 遇到 required_input 或 game_over 时 break；非输入 step 间 `await asyncio.sleep(0.3)`

## 2. 实现 _apply_step_result

- [x] `_apply_step_result(result: StepResult)`: 存储 `self._current_result`，调用 `board.update_snapshot(result.snapshot)`，调用 `action_bar.set_required_input(result.required_input)`
- [x] 处理 `result.game_over` 时为 ActionBar 传入特殊终局状态

## 3. 实现 ActionBar widget

- [x] 创建 `src/richman/adapters/textual_tui/widgets/action_bar.py`
- [x] 定义 `ActionBar(Widget)`，含 `DEFAULT_CSS`（固定高度 5 行，底部水平排列）
- [x] 定义 `required_input: Reactive[RequiredInput | None] = Reactive(None)` reactive 属性
- [x] 定义 `ActionBar.ActionSubmitted(Message)`，携带 `engine_input: EngineInput` 字段
- [x] `set_required_input(required: RequiredInput | None)`: 同步入口，设置 `self.required_input = required`，触发 watcher
- [x] `watch_required_input(required)`: async watcher，先 `await self.remove_children()` 清空，再 `await self.mount(...)` 构建新按钮
- [x] ROLL_DICE: 单个 "掷骰" 按钮
- [x] ACTION_CHOICE: 每个 `options` 中的 action 生成一个按钮，中文标签
- [x] JAIL_CHOICE: 每个选项生成按钮
- [x] DEMOLISH_TARGET: 提示文字 Static + 候选 position 列表，不生成按钮
- [x] None: 清空（remove_children 后不 mount 任何内容）
- [x] 按钮点击时 `post_message(ActionSubmitted(engine_input))`

## 4. 实现 AI 自动输入

- [x] GameScreen 中检测 AI 玩家：`isinstance(self._player_controllers[required.player_index], AIPlayer)`
- [x] `_auto_input_for(required: RequiredInput) -> EngineInput` 构造自动输入
  - ROLL_DICE → `EngineInput(kind=ROLL_DICE, player_index=required.player_index)`
  - ACTION_CHOICE → `EngineInput(kind=ACTION_CHOICE, player_index=required.player_index, action=required.options[0])`
  - JAIL_CHOICE → 优先 `USE_JAIL_PASS` 否则 `ACCEPT_JAIL`
  - DEMOLISH_TARGET → `EngineInput(kind=DEMOLISH_TARGET, player_index=required.player_index, target_position=required.candidates[0])`
- [x] 在 `_advance_loop` 中：遇到 AI 的 required_input 时自动提交后继续循环

## 5. 实现人类输入提交

- [x] GameScreen 处理 `ActionBar.ActionSubmitted` 消息
- [x] `_submit_input(engine_input)`: 调用 `result = engine.advance(engine_input)` → `_apply_step_result(result)` → 如果无 required_input 且非 game_over 则继续 `_advance_loop()`

## 6. 实现键盘快捷键

- [x] ActionBar 上绑定 Enter/Space → 触发第一个按钮的 `ActionSubmitted`
- [x] 绑定数字键 1-9 → 触发对应序号按钮

## 7. 接入 BoardWidget 点击

- [x] GameScreen 处理 `CellWidget.CellClicked` 消息
- [x] 仅当 `required_input.kind == DEMOLISH_TARGET` 且 `message.position in candidates` 时提交
- [x] 非候选格点击忽略

## 8. 实现 Game Over 处理

- [x] `_apply_step_result` 中检测 `game_over=True`
- [x] 从 `engine.get_state().event_log` 中提取 `GAME_OVER` 事件的 `winner_name`
- [x] ActionBar 展示终局状态（赢家名称 + "游戏结束"）

## 9. 测试

- [x] 创建 `tests/test_textual_tui_game_screen.py`
- [x] 所有测试中 monkeypatch `asyncio.sleep` 为立即返回的 async mock，避免测试变慢
- [x] Fake engine 测试：`_apply_step_result` 更新 BoardWidget 和 ActionBar
- [x] Fake engine 测试：`_auto_input_for` 四种 InputKind 的正确输出
- [x] Fake engine 测试：`on_cell_widget_cell_clicked` 的 DEMOLISH_TARGET 候选/非候选/非 DEMOLISH 三种分支
- [x] Fake engine 测试：`_submit_input` 调用 `engine.advance(engine_input)`
- [x] Fake engine 测试：game_over 不再调用 advance
- [x] Fake engine 测试：全 AI 完整推进逻辑（fake engine 返回预设序列，验证循环直到 game_over）
- [x] 真实 engine smoke test：全 AI 玩家，推进有限步（如 5 步）验证 engine 集成正常
- [x] 集成测试：真实 engine 单人类玩家，验证 ROLL_DICE ActionBar 渲染和按钮点击提交流程
- [x] 集成测试：ActionBar 不同 kind 的按钮渲染和数量
- [x] 集成测试：键盘 Enter 触发掷骰按钮
- [x] 集成测试：数字键触发对应动作按钮
