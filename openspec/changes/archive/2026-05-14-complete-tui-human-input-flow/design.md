## Context

当前 TUI GameScreen 通过 `_advance_loop` worker 驱动 `engine.advance()`。遇到人类玩家 `RequiredInput` 时 worker 直接 `return`，后续由 `_submit_input` → `_apply_step_result` 更新 ActionBar，若新结果无 `required_input` 则重新 `run_worker` 启动循环。

已有能力：
- `ActionBar` 根据 `RequiredInput.kind` 渲染按钮/hint，Enter/Space/数字键触发提交
- `GameScreen.on_cell_widget_cell_clicked` 处理 DEMOLISH_TARGET 的候选格点击
- `_submit_input` 调用 `engine.advance(engine_input)` 并更新 UI

尚存缺口：
- 按钮无序号标注，用户不知道数字快捷键
- `DEMOLISH_TARGET` 阶段棋盘不标记候选格
- `DEMOLISH_TARGET` 无取消机制，误选 USE_DEMOLISH 后无法退出
- `_advance_loop` 对连续人类输入的衔接依赖 `_submit_input` 的分支判断，缺少统一的事件驱动恢复机制

## Goals / Non-Goals

**Goals:**
- ActionBar ACTION_CHOICE / JAIL_CHOICE 按钮显示 `[1]`、`[2]` 序号前缀
- BoardWidget 在 DEMOLISH_TARGET 阶段高亮候选格（CSS class `candidate`）
- Esc 键取消 DEMOLISH_TARGET，退回动作选择
- 人类玩家从 ROLL_DICE 到 ACTION_CHOICE（含 USE_DEMOLISH → 取消/提交）的完整交互链稳定连通
- AI 玩家回合继续无阻塞
- 所有状态变更仍通过 `engine.advance(EngineInput)` 完成

**Non-Goals:**
- 骰子动画、视觉 polish、事件日志 Modal、棋子动画
- JAIL_CHOICE Modal（按钮方案已可用）
- DEMOLISH_TARGET 以外的高亮需求
- 控制台（console adapter）路径的任何改动

## Decisions

### 1. 人类输入等待：从 `return` 改为 `asyncio.Event` 信号量模式

当前 `_advance_loop` 在人类输入时直接 `return`，后续由 `_submit_input` 根据结果是否含 `required_input` 决定是否 `run_worker` 恢复。这个分支容易漏掉连续人类输入场景（如 USE_DEMOLISH → DEMOLISH_TARGET → 仍需人类输入）。

**方案**：使用 `asyncio.Event` 信号量。`_advance_loop` 在人类输入点 `await self._human_input_event.wait()` 阻塞，`_submit_input` 推进后根据新状态决定 `_human_input_event.set()` 还是保持等待。

**替代方案考虑**：
- Textual `wait_for` 机制：依赖 message，但需要两轮不同 message 类型（ActionSubmitted、CellClicked），无法简单 `await` 单一路径。
- 保持 return + run_worker：当前方案的问题是在 _submit_input 中判断条件脆弱。可修复但语义不如 event 清晰。

**选择**：使用 `asyncio.Event`。`_advance_loop` 中 `await self._pending_human.wait()`，所有人类输入提交后统一由 `_maybe_resume_loop()` 判断是否 `set()`。

### 2. DEMOLISH_TARGET 取消：target_position=None 视为取消信号

引擎在 `WAITING_FOR_DEMOLISH_TARGET` 状态收到 `EngineInput(kind=DEMOLISH_TARGET, target_position=None)` 时，当前会 `raise ValueError`。本设计将其改为取消语义：引擎不消耗拆除卡，回到 `READY_FOR_ACTION` 重新计算动作。

**引擎变更**（最小化）：
- `advance()` 中 `WAITING_FOR_DEMOLISH_TARGET` 分支：若 `engine_input.target_position is None`，设置 `_step_cursor = _StepCursor.READY_FOR_ACTION`，不调用 `_execute_demolish_target`，不进入 END。
- `_validate_input`：DEMOLISH_TARGET 时允许 `target_position is None`（取消）或 `target_position in candidates`（提交）。

**替代方案考虑**：
- TUI 侧保存状态回退：TUI 不修改 InternalGameState 的铁律不可破。
- 新增 `InputKind.CANCEL`：引入新枚举值后所有 handler 需增加分支，过度设计。
- `target_position=-1` 哨兵：丑陋且与 domain 类型语义冲突。

**选择**：`target_position=None` 作为 DEMOLISH_TARGET 的取消信号。None 原本就表示"未设置"，语义自然。

### 3. 候选格高亮：BoardWidget 接收 `highlight_positions` reactive

BoardWidget 当前只接收 `GameSnapshot`，不知道 DEMOLISH_TARGET 候选格。需要额外通道传入高亮集合。

**方案**：为 BoardWidget 添加 reactive 属性 `highlight_positions: frozenset[int]`，watcher 遍历 CellWidget 为候选格添加 CSS class `candidate`，非候选格移除。CellWidget 在 `candidate` class 下使用高亮边框。

数据流：`GameScreen._apply_step_result()` → `board.set_highlight_positions(candidates)` → BoardWidget watcher → CellWidget.set_class("candidate", True/False)。

`GameScreen` 从 `result.required_input.candidates` 提取候选集，非 DEMOLISH_TARGET 阶段传入空集清除高亮。

### 4. 按钮标签序号：ActionBar 内部添加前缀

在 `watch_required_input` 构建 Button 时，label 从 `"购买"` 改为 `"[1] 购买"`。ACTION_CHOICE 和 JAIL_CHOICE 均适用。ROLL_DICE 单按钮不需要序号（Enter/Space 已足够）。

## Risks / Trade-offs

- **[Risk] `target_position=None` 取消语义与其他 InputKind 冲突**：其他 kind（如 JAIL_CHOICE）的 `action=None` 仍为非法。取消仅对 DEMOLISH_TARGET 生效。→ 在 `_validate_input` 中仅对 DEMOLISH_TARGET 放宽 None 检查。
- **[Risk] `asyncio.Event` 引入状态竞争**：若连续快速点击触发多次 `_submit_input`，可能 `set()` 后 `_advance_loop` 推进又立即停在人类输入，第二次点击的 `_submit_input` 发现无 `_current_result.required_input`。→ `_submit_input` 开头检查 `self._pending_human.is_set()` 防御。
- **[Risk] 候选格高亮的清除时机**：AI 回合、非 DEMOLISH_TARGET 阶段、game_over 时均需清除。→ `_apply_step_result` 统一处理：非 DEMOLISH_TARGET 时传空 `frozenset`。
