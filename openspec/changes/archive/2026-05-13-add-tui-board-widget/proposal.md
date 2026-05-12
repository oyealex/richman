## Why

TUI 校验层和几何计算层已就位，但当前 Textual TUI 仍然只是展示 `format_snapshot()` 文本面板的 smoke shell。真正的棋盘可视化——按配置坐标放置格子、显示中心动态区、响应格子点击——需要 BoardWidget 体系。这是 TUI 从"能跑"到"能看"的关键一步。

## What Changes

- 新增 `widgets/cell.py`：`CellWidget` 单个棋盘格 widget，显示 position、cell 类型、名称、归属/等级、站立的玩家棋子。点击时发出 `CellClicked(position)` message。
- 新增 `widgets/center_panel.py`：`CenterPanel` widget，展示当前回合/阶段、当前玩家名、骰子点数、最近 3-5 条事件。
- 新增 `widgets/board.py`：`BoardWidget` 主容器，接收 `GameSnapshot` + `TuiLayoutGeometry`，按 `position_rects` 使用绝对坐标排放 `CellWidget`，中间放置 `CenterPanel`。
- 终端尺寸不足时 BoardWidget 渲染错误提示而非错位棋盘。
- 更新现有 `app.py` 使用 BoardWidget 替代 `Static(format_snapshot(...))` 面板。

## Capabilities

### New Capabilities

- `tui-board-widget`: Textual BoardWidget 体系——按 `TuiLayoutGeometry` 的终端字符坐标渲染棋盘格、中心信息区，发出点击消息，尺寸不足时展示错误状态。

### Modified Capabilities

<!-- 本次变更不修改现有 capability 的 requirement。BoardWidget 消费 GameSnapshot 和 TuiLayoutGeometry 是 render-adapter-architecture 的已有要求，本次是实现而非规格变更。 -->

## Impact

- **新增文件**: `widgets/board.py`、`widgets/cell.py`、`widgets/center_panel.py`
- **修改文件**: `app.py`（从 smoke shell 改为使用 BoardWidget）、`widgets/__init__.py`（可选，按需导出）
- **依赖**: `richman.domain`（GameSnapshot 等）、`textual`（widget, message, geometry）、`layout.py`（TuiLayoutGeometry）
- **不依赖**: engine、rules、player、滚动/缩放
