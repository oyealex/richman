## 1. 实现 CellWidget

- [x] 1.1 创建 `widgets/cell.py`，定义 `CellWidget(Static)` 和内部 `CellClicked(Message)` 消息类
- [x] 1.2 实现 CellWidget 构造函数：接收 `position: int`、`cell_info: PublicCellInfo | None`、`owner_name: str | None`、`players_on_cell: tuple[str, ...]`、`is_current_player_cell: bool`
- [x] 1.3 定义 `DEFAULT_CSS` 类变量：width=12、height=5、border、高亮色/普通色
- [x] 1.4 实现 `render()` 方法：3 行内容（position+类型、名称、等级+归属/棋子），cell_info 为 None 时渲染空占位格
- [x] 1.5 实现 `on_click()` 发出 `CellClicked(position)` 消息
- [x] 1.6 实现 `update_data(cell_info, owner_name, players_on_cell, is_current_player_cell)` 方法，更新内部数据并调用 `self.refresh()`

## 2. 实现 CenterPanel

- [x] 2.1 创建 `widgets/center_panel.py`，定义 `CenterPanel(Static)`
- [x] 2.2 定义 `DEFAULT_CSS` 类变量
- [x] 2.3 实现构造函数：接收 `snapshot: GameSnapshot`
- [x] 2.4 实现 `render()` 方法：显示回合、阶段、当前玩家名、骰子（None 时显示"-"）、最近 3-5 条事件
- [x] 2.5 实现 `update_snapshot(snapshot)` 方法，更新内部数据并调用 `self.refresh()`

## 3. 实现 BoardWidget

- [x] 3.1 创建 `widgets/board.py`，定义 `BoardWidget(Widget)`
- [x] 3.2 实现构造函数：接收 `snapshot: GameSnapshot`、`geometry: TuiLayoutGeometry`、`terminal_size: tuple[int, int] | None = None`
- [x] 3.3 定义 `DEFAULT_CSS` 类变量：容器尺寸 = min_terminal_rows/cols
- [x] 3.4 实现 `_build_cell_widgets()`：对每个 position，从 `GameSnapshot.public_players` 解析 `owner_name`（通过 `public_board.cells[position].owner_player_index` 查找）、`players_on_cell`（过滤 position 匹配的玩家名）、`is_current_player_cell`
- [x] 3.5 实现 `compose()`：尺寸不足时 yield 错误 Static（含 `min_terminal_rows/cols` 和 `terminal_size`）；正常时按 `position_rects` 绝对定位 yield CellWidget 列表 + CenterPanel
- [x] 3.6 实现 `on_cell_widget_cell_clicked()` handler，暂存最新点击的 position 到实例属性
- [x] 3.7 实现 `update_snapshot(snapshot)` 方法：遍历子 CellWidget 调用 `update_data(...)`，更新 CenterPanel，不重新 compose

## 4. 接入现有 app.py 并修复默认快照

- [x] 4.1 修改 `app.py`：接收 `GameConfig`，用 `compute_layout_geometry(config)` 计算 geometry
- [x] 4.2 在 `compose()` 中使用 `BoardWidget` 替代 `Static(format_snapshot(...))` 面板，传入 `terminal_size`（从 `self.size` 获取）
- [x] 4.3 修改 `_default_snapshot()` 的 `public_board.cells` 覆盖默认 `build_default_config()` 的全部 10 个 position，避免 snapshot 只有 1 格而 layout 有 10 格

## 5. 编写测试

- [x] 5.1 测试 `CellWidget` render 内容包含 position、类型标识、名称、归属（owner_name 非 None 和 None 两种场景）
- [x] 5.2 测试 `CellWidget.on_click()` 发出 `CellClicked(position)` 消息
- [x] 5.3 测试 `CellWidget.update_data()` 后 render 更新
- [x] 5.4 测试 `CenterPanel` render 包含阶段、玩家名、骰子（含 None 场景）、事件
- [x] 5.5 测试 `BoardWidget.compose()` 在尺寸充足时包含 CellWidget 和 CenterPanel
- [x] 5.6 测试 `BoardWidget.compose()` 在尺寸不足时显示错误提示且无 CellWidget
- [x] 5.7 测试 `BoardWidget.update_snapshot()` 后子 widget 内容更新
- [x] 5.8 测试现有 TUI smoke test（`tests/test_textual_tui.py`）仍通过

## 6. 质量检查

- [x] 6.1 运行 `uv run ruff check src tests`
- [x] 6.2 运行 `uv run mypy src tests`
- [x] 6.3 运行 `uv run pytest`
- [x] 6.4 运行 `openspec validate --specs --strict`
