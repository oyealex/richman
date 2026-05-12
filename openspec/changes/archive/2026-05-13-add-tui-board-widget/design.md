## Context

`tui_layout` 校验和几何计算层已完成。`layout.py` 提供 `TuiLayoutGeometry`（position_rects、center_rect、尺寸充足性判断）。当前 `app.py` 仍用 `Static(format_snapshot(...))` 展示纯文本面板，没有真正的棋盘可视化。

本次需要构建 BoardWidget 体系来消费这些几何数据并渲染可交互棋盘。约束：

- 终端字符坐标体系已定义：cell 12×5、center_rect 由 TuiLayout 配置。
- 不在此 change 中做完整游戏驱动、滚动、缩放。
- 必须遵循 render-adapter-architecture：Textual widget 代码限制在 `adapters/textual_tui/` 内部。

## Goals / Non-Goals

**Goals:**
- BoardWidget 按 `TuiLayoutGeometry.position_rects` 绝对定位渲染所有 CellWidget。
- CenterPanel 按 `TuiLayoutGeometry.center_rect` 绝对定位渲染动态信息区。
- CellWidget 显示 position 编号、cell 类型、名称、归属/等级、当前站立的玩家棋子。
- 点击 CellWidget 发出 `CellWidget.CellClicked(position)` 冒泡消息。
- 终端尺寸不足时 BoardWidget 展示错误提示，不渲染错位棋盘。
- 更新现有 `app.py` 使用 BoardWidget 替代 `Static(format_snapshot(...))` 面板。

**Non-Goals:**
- 不做完整游戏驱动（`richman tui` 入口、Title/Setup/GameScreen、engine 自动推进）。
- 不创建动作按钮和输入 modal。
- 不做滚动和缩放。
- 不修改 engine、domain、rules、player。

## Decisions

### 绝对定位策略

使用 Textual 的 `styles.position = "absolute"` + `styles.offset = (col, row)` 将每个 widget 放在父容器中的终端字符坐标位置。

```python
widget.styles.position = "absolute"
widget.styles.offset = (left, top)  # (col, row) — 对应 position_rects 的 (left, top)
```

- **为什么不用 CSS Grid**：Grid 适合规则对齐场景，但 TUI 布局的 center rect 与 cell slot 是交错关系，绝对定位直接映射 `position_rects` 值，零转换。
- **为什么不用 Dock**：Dock 无法表达位置跳跃（如环形棋盘中 cell 可能分布在不同行/列）。

### Widget 尺寸

CellWidget 和 CenterPanel 的 `styles.width` / `styles.height` 直接使用 `TuiRect` 的语义宽度和高度（字符数）：

- CellWidget: `width = CELL_WIDTH`（12 列）, `height = CELL_HEIGHT`（5 行）
- CenterPanel: `width = center_rect[3] - center_rect[1]`, `height = center_rect[2] - center_rect[0]`

### CellWidget 内容格式（遵循 TUI_DESIGN.md 3.2 节）

每格 5 行（含边框）、3 行内容：

```
行1: [00]🏠     ← position 编号 + 类型 emoji
行2: 海滨别墅     ← 名称（过长截断为前4字+"…"）
行3: ●●●  AI-1  ← 等级圆点 + 地主名 / "无主" / 棋子表示
```

- 边框使用 Textual 的 `border` 样式，不手绘边框字符。
- 当前玩家所在格使用高亮边框色（如 green），其他用默认边框。

**CellWidget 数据流**:
- `position: int` — 直接定位，用于显示和消息。
- `cell_info: PublicCellInfo` — 提供 cell_type、property_name、level、owner_player_index。
- `owner_name: str \| None` — 由 BoardWidget 在构造 CellWidget 前从 `GameSnapshot.public_players` 查找 `owner_player_index` 解析得到。这样地主即使不在该格也能显示。
- `players_on_cell: tuple[str, ...]` — BoardWidget 从 `GameSnapshot.public_players` 过滤出位于该 position 的玩家名称并传入。CellWidget 仅负责展示，不查询外部状态。

### CellWidget 基类选择

使用 `Static` 作为基类，因为内容是纯文本渲染（`render()` → Rich renderable）。`on_click` 事件由 Textual 原生支持，无需自定义事件循环。

### 消息传递

```python
class CellWidget(Static):
    class CellClicked(Message):
        def __init__(self, position: int) -> None:
            self.position = position
            super().__init__()

    def on_click(self) -> None:
        self.post_message(self.CellClicked(self.position))
```

BoardWidget 或外层 app 通过 `on_cell_widget_cell_clicked` 处理消息。

### 尺寸不足处理

BoardWidget 构造函数接收 `terminal_size: tuple[int, int] | None`（当前终端 `(rows, cols)`），在 compose 时判断：

- `geometry.is_terminal_sufficient` 为 `True`：正常渲染 CellWidget 列表 + CenterPanel
- `geometry.is_terminal_sufficient` 为 `False` 且 `terminal_size` 非 None：渲染错误提示 Static，显示 `min_terminal_rows/cols`（来自 geometry）和当前 `terminal_size`
- `terminal_size` 为 None：不判断尺寸（仅用于无需判断的场景，如测试）

### CenterPanel 内容

中心区使用 Rich Panel，展示：
- 当前回合 / 当前阶段
- 当前玩家名称
- 骰子点数（若无则显示"-"）
- 最近 3-5 条事件（截取 event_log 尾端，按需格式化）

### 玩家棋子显示

在各 cell 的第三行内容中，通过 `GameSnapshot.public_players` 找出所有位于该 position 的玩家，拼接显示名称。若数量超过 2 人则缩略为「名1+名2…」。

### 快照更新机制

BoardWidget 提供 `update_snapshot(snapshot: GameSnapshot)` 方法，由外层 app 在 `advance()` 后调用：

- 遍历所有子 CellWidget，通过 `cell_info` 字段更新 render 内容。
- 更新 CenterPanel 的显示数据。
- 不重新 compose，避免销毁和重建 widget 树。

CellWidget 和 CenterPanel 各自提供 `update_data(...)` 方法来接收新数据并调用 `self.refresh()`。

### 默认快照对齐

BoardWidget 构造时不验证 snapshot 与 layout 的 position 一致性（`validate_tui_layout` 已在几何计算阶段保证映射完整）。如果 snapshot 的 `public_board.cells` 缺少某些 position（如旧的 `_default_snapshot()` 只有 1 格），CellWidget 使用 `cell_info=None` 渲染空白占位格。App 层负责传入与配置一致的 snapshot。

### CSS 组织

每个 widget 使用 Textual 的 `DEFAULT_CSS` 类变量定义自身样式，不放入 `__init__.py` 或 `app.py`：

```python
class CellWidget(Static):
    DEFAULT_CSS = """
    CellWidget {
        width: 12;
        height: 5;
        border: solid $border;
    }
    """
```

### 文件结构

```
widgets/
  __init__.py      # 可选导出
  cell.py          # CellWidget + CellClicked message + DEFAULT_CSS
  center_panel.py  # CenterPanel widget + DEFAULT_CSS
  board.py         # BoardWidget 主容器 + DEFAULT_CSS
```

## Risks / Trade-offs

- **绝对定位与 Textual 的响应式布局不兼容**: 窗口 resize 时不会自动重排。→ 当前不做缩放，尺寸不足时直接显示错误页。后续 resize 处理交给外层 app。
- **Cell 内容行数固定为 3 行内容 + 2 行边框**：property 名过长需截断。→ 使用前4字+"…"方案，与 TUI_DESIGN.md 一致。
- **Textual async 生命周期**: `compose()` 是同步方法，接收参数需通过 init 传入 Widget 实例而非在 compose 中计算。→ BoardWidget 在 `__init__` 中接收 `snapshot` 和 `geometry`。
