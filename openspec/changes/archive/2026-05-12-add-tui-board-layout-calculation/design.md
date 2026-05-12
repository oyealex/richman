## Context

`tui_layout` 配置模型（`TuiLayout`、`TuiCellLayout`、`TuiRect`）和 `validate_tui_layout()` 校验层已完成。当前缺少的是将合法布局转换为可渲染几何数据的计算层。BoardWidget 需要知道每个 position 对应的终端字符坐标矩形、中心区位置、以及当前终端尺寸是否足够容纳棋盘。

约束：
- 不做自动缩放，不做滚动。
- 不依赖 Textual、Rich 或任何 widget 框架。
- 计算层只依赖 `richman.domain` 和同文件内的 `validate_tui_layout`。

## Goals / Non-Goals

**Goals:**
- 定义固定 cell 尺寸常量（字符宽度、字符高度、间距）。
- `TuiLayoutGeometry` dataclass：承载 position→row/col 坐标范围映射、center panel 坐标范围、棋盘所需最小终端尺寸、尺寸不足判断。
- `compute_layout_geometry(config, terminal_size)`：输入合法 `GameConfig` 和 `(rows, cols)` 终端尺寸，输出 `TuiLayoutGeometry`。
- 非法布局（`validate_tui_layout` 返回 errors）直接以 `ValueError` 拒绝。
- 测试覆盖默认布局几何、position 映射一致性、尺寸充足/不足判断。

**Non-Goals:**
- 不创建任何 Textual widget（`textual.widget`）。
- 不修改 `GameConfig`、`GameSnapshot` 或 engine。
- 不实现滚动或缩放。
- 不在此 change 中将几何数据接入 BoardWidget。

## Decisions

### Cell 尺寸常量

每个 cell 渲染区域定义为 12 字符宽 × 5 字符高（行数 = 面板边框 2 + 内容 3），与 `docs/TUI_DESIGN.md` 第 126 行的默认格子尺寸一致。水平间距 1 字符，垂直间距 0 字符（cell 在垂直方向紧密排列）。

- `CELL_WIDTH = 12`
- `CELL_HEIGHT = 5`
- `CELL_GAP = 1`

这些值作为模块级常量，未来可通过参数覆盖。

终端字符坐标计算：
```
cell_left(col)   = col * (CELL_WIDTH + CELL_GAP)
cell_top(row)    = row * CELL_HEIGHT
cell_right(col)  = cell_left(col) + CELL_WIDTH
cell_bottom(row) = cell_top(row) + CELL_HEIGHT
```

### TuiLayoutGeometry dataclass

```python
from collections.abc import Mapping

@dataclass(frozen=True, slots=True)
class TuiLayoutGeometry:
    position_rects: Mapping[int, tuple[int, int, int, int]]  # position -> (top, left, bottom, right)
    center_rect: tuple[int, int, int, int]                     # (top, left, bottom, right)
    min_terminal_rows: int
    min_terminal_cols: int
    is_terminal_sufficient: bool
```

`position_rects` 存储每个 position 在终端字符坐标中的矩形，使用 `(row_start, col_start, row_end, col_end)` 半开区间（row_end/col_end 为排他边界），与 `TuiRect` 的 `row_span`/`column_span` 语义一致。类型声明为 `Mapping` 而非 `dict`，实现时用 `MappingProxyType` 包装以确保 dataclass frozen 真正不可变。

### 校验先行

`compute_layout_geometry` 首先调用 `validate_tui_layout(config)`，若返回的 `errors` 非空则抛出 `ValueError` 并列出所有错误。合法布局才能进入计算。

### terminal_size 参数

`terminal_size` 为 `tuple[int, int] | None`，表示 `(rows, cols)`。传入 `None` 时 `is_terminal_sufficient` 为 `True`（不判断充足性，仅做几何计算）。

## Risks / Trade-offs

- **Cell 尺寸硬编码**: 12×5 是合理默认值，但极窄终端（<168 列）可能放不下。→ 使用模块常量，后续可参数化。尺寸不足时 `is_terminal_sufficient=False`，TUI 显示错误页。
- **不做缩放**: 终端太小直接拒绝，用户体验受限。→ 这是 TUI_DESIGN.md 的明确决策，未来再评估缩放。
