## 1. PlayerStrip 实现

- [x] 1.1 创建 `widgets/player_strip.py`，定义 PlayerStrip 类（继承 Widget）
- [x] 1.2 实现 `__init__(self, snapshot, player_controllers)`，区分人类/AI 玩家
- [x] 1.3 实现 `render()` 返回 Rich Text，人类玩家展示现金/手牌/位置/状态，AI 仅展示名称/位置/状态
- [x] 1.4 实现 `update_snapshot(snapshot)` 刷新渲染
- [x] 1.5 定义 DEFAULT_CSS：height: 1; layout: horizontal

## 2. EventLine 实现

- [x] 2.1 创建 `widgets/event_line.py`，定义 EventLine 类（继承 Widget）
- [x] 2.2 定义 `EventLine.OpenRequested` 消息类（继承 Message）
- [x] 2.3 实现 `render()` 展示 `event_log[-1]` 格式化文本，空时显示 "--"
- [x] 2.4 实现 `on_click` 发出 OpenRequested 消息
- [x] 2.5 实现 `update_snapshot(snapshot)` 刷新渲染
- [x] 2.6 定义 DEFAULT_CSS：height: 1

## 3. Widget 导出

- [x] 3.1 在 `widgets/__init__.py` 中导出 PlayerStrip 和 EventLine

## 4. GameScreen 布局调整

- [x] 4.1 新增 `_PLAYER_STRIP_HEIGHT = 1` 和 `_EVENT_LINE_HEIGHT = 1` 常量
- [x] 4.2 修改 `compose()`：在 BoardWidget 之后插入 PlayerStrip 和 EventLine
- [x] 4.3 修改 `board_rows` 计算：扣减 PlayerStrip 和 EventLine 高度
- [x] 4.4 修改 `_apply_step_result()`：同步更新 PlayerStrip 和 EventLine
- [x] 4.5 在 `compose()` 中传 `player_controllers` 给 PlayerStrip
- [x] 4.6 在 GameScreen 级绑定 E 键，按下时发出 `EventLine.OpenRequested` 消息

## 5. 测试

- [x] 5.1 创建 `tests/test_textual_tui_player_strip.py`：测试 PlayerStrip 组件存在、人类信息完整、AI 隐私不泄露、快照更新
- [x] 5.2 创建 `tests/test_textual_tui_event_line.py`：测试 EventLine 组件存在、事件渲染、空状态、OpenRequested 消息
- [x] 5.3 扩展 `tests/test_textual_tui_game_screen.py`：测试 compose 包含 PlayerStrip 和 EventLine、棋盘尺寸扣减正确
- [x] 5.4 运行 `uv run pytest` 全量测试确保无回归
- [x] 5.5 运行 `uv run ruff check src tests` 和 `uv run mypy src tests` 确保 lint/类型检查通过
