## 1. Render 公共契约

- [x] 1.1 重构 `src/richman/render/ports.py`，移除或替换 `GameSnapshotView`、`DecisionRequest`、`PlayerDecision` 等占位契约。
- [x] 1.2 定义 `Renderer` 协议，覆盖 `render_frame(snapshot)`、`render_event_log(events, viewer_index)`、`prompt_choice(question, options)`、`prompt_number(question, min_value, max_value)` 和 `render_game_over(winner_name)`。
- [x] 1.3 实现标准库默认 renderer，直接消费 `domain.GameSnapshot` 和 `GameEvent`，且不导入 Textual、Rich、engine、board、rules、player 或 adapters。
- [x] 1.4 在 `src/richman/render/__init__.py` 导出 `Renderer`、默认 renderer 类型、包级委托函数和必要的公开辅助类型。

## 2. 快照展示与终局展示

- [x] 2.1 实现 `render_frame(snapshot)`，展示回合、阶段、骰子、公开棋盘、公开玩家、viewer 私有状态和可用动作。
- [x] 2.2 确保 `render_frame` 只读取 `GameSnapshot`，不要求 `InternalGameState`，也不修改传入的玩家、地块、事件或动作数据。
- [x] 2.3 支持 `available_actions` 为 `None` 或空集合的展示场景，且不伪造任何可用动作。
- [x] 2.4 实现 `render_game_over(winner_name)`，只展示胜者和终局状态，不重新计算胜利条件。

## 3. 事件日志隐私遮蔽

- [x] 3.1 实现事件格式化或遮蔽辅助函数，集中处理 `GameEvent.event_type` 和 `GameEvent.data` 的展示文本。
- [x] 3.2 对非当前 viewer 的现金、手牌数量、购买价、累计升级投入、回收金额等私密字段进行隐藏或省略。
- [x] 3.3 保留公开事件信息展示，包括事件类型、玩家名称、位置、地块名称、等级、卡牌描述、动作名称、破产结果和终局结果。
- [x] 3.4 实现 `render_event_log(events, viewer_index)`，复用遮蔽逻辑并保持无状态、无 mutation。

## 4. 输入原语

- [x] 4.1 实现 `prompt_choice(question, options)`，拒绝空选项，并保证返回值来自传入的 `options`。
- [x] 4.2 支持用户通过 1-based 序号或精确文本选择 `prompt_choice` 选项。
- [x] 4.3 实现 `prompt_number(question, min_value, max_value)`，拒绝 `min_value > max_value` 的非法范围。
- [x] 4.4 确保 `prompt_number` 只返回闭区间 `[min_value, max_value]` 内的整数。

## 5. Textual TUI adapter 迁移

- [x] 5.1 更新 `src/richman/adapters/textual_tui/app.py`，让 Textual app 消费 `GameSnapshot` 或由 render 契约派生的展示数据。
- [x] 5.2 移除 Textual adapter 对旧占位类型的依赖，保持 Textual/Rich 类型只出现在 `richman.adapters.textual_tui` 内。
- [x] 5.3 保留无快照时的最小可构造行为，确保 headless smoke test 不启动阻塞式终端会话。
- [x] 5.4 更新 `src/richman/adapters/textual_tui/__init__.py` 的公开导出，保持 app 导入路径稳定。

## 6. 测试覆盖

- [x] 6.1 新增 render 公共 API 导入测试，覆盖 `Renderer`、包级函数和默认 renderer 导出。
- [x] 6.2 新增 render 依赖边界测试，确认 `src/richman/render` 不导入 engine、board、rules、player、adapters、Textual 或 Rich UI 类型。
- [x] 6.3 新增 `GameSnapshot` 展示测试，覆盖公开棋盘、公开玩家、viewer 私有信息、可用动作和空动作展示。
- [x] 6.4 新增无 mutation 测试，确认渲染快照和事件日志不会修改传入的 domain 对象。
- [x] 6.5 新增事件隐私遮蔽测试，覆盖当前 viewer 私有信息可见、其他玩家私密字段隐藏、公开字段保留。
- [x] 6.6 新增输入原语测试，覆盖空选项错误、合法选择、非法数字范围错误和数字边界校验。
- [x] 6.7 更新 Textual TUI smoke test，使用新的 render/domain 契约构造 app 并通过 headless `run_test()`。

## 7. 验证与交接

- [x] 7.1 运行 `uv run pytest`，确认所有测试通过。
- [x] 7.2 运行 `uv run ruff check` 和 `uv run ruff format --check`，确认风格检查通过。
- [x] 7.3 运行 `uv run mypy src`，确认类型检查通过。
- [x] 7.4 更新 `docs/DEVELOPMENT_PROGRESS.md`，记录 render 模块已实现和下一步 engine/app 建议。
