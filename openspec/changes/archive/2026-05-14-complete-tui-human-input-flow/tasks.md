## 1. ActionBar 按钮标签序号

- [x] 1.1 修改 ActionBar.watch_required_input，ACTION_CHOICE 和 JAIL_CHOICE 按钮标签改为 `[i+1] label` 格式
- [x] 1.2 更新 ActionBar DEMOLISH_TARGET 提示文字，增加 "Esc 取消" 指引
- [x] 1.3 更新已有 ActionBar 测试，验证新标签格式含序号前缀和取消提示

## 2. 引擎 DEMOLISH_TARGET 取消支持

- [x] 2.1 修改 engine.model.GameEngine._validate_input，DEMOLISH_TARGET 允许 target_position=None 视为取消
- [x] 2.2 修改 engine.model.GameEngine.advance 中 WAITING_FOR_DEMOLISH_TARGET 分支，target_position=None 时回到 READY_FOR_ACTION 而非报错
- [x] 2.3 编写 engine 单元测试验证取消后不消耗拆除卡、可用动作重新出现

## 3. BoardWidget 候选格高亮

- [x] 3.1 为 BoardWidget 添加 `highlight_positions: Reactive[frozenset[int]]` reactive 属性
- [x] 3.2 实现 highlight_positions watcher：遍历 CellWidget，候选格加 `candidate` class，非候选格移除
- [x] 3.3 为 CellWidget 添加 `candidate` CSS class 样式（高亮边框，区分于 `current`）
- [x] 3.4 编写 BoardWidget 高亮测试：设置/更新/清除 highlight_positions

## 4. GameScreen 人类输入等待机制

- [x] 4.1 为 GameScreen 添加 `_pending_human: asyncio.Event` 信号量
- [x] 4.2 修改 `_advance_loop`，人类输入点从 `return` 改为 `await self._pending_human.wait()`
- [x] 4.3 修改 `_submit_input`，提交后根据新 result 决定 `_pending_human.set()` 还是 `_pending_human.clear()` 继续等待
- [x] 4.4 在 `_apply_step_result` 中统一向 BoardWidget.set_highlight_positions() 传递候选格
- [x] 4.5 为 GameScreen 添加 Esc 键绑定，DEMOLISH_TARGET 阶段提交取消 EngineInput

## 5. 集成测试与验证

- [x] 5.1 编写 GameScreen 人类 ROLL_DICE → ACTION_CHOICE 完整交互链测试
- [x] 5.2 编写 GameScreen USE_DEMOLISH → DEMOLISH_TARGET（点击候选格）→ 继续推进 的完整交互链测试
- [x] 5.3 编写 GameScreen USE_DEMOLISH → Esc 取消 → 回到 ACTION_CHOICE 的测试
- [x] 5.4 运行全量测试（pytest + ruff + mypy）确保无回归
- [?] 5.5 使用 `richman tui --players 2 --seed 1` 手动 smoke test：人类玩家完成一整局不卡住
