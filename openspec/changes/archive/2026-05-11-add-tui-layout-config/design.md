## Context

TUI 设计文档（`docs/TUI_DESIGN.md` 第三节）定义了配置化坐标布局：棋盘格视觉位置由 `tui_layout` 决定，游戏移动顺序仍由 `board_cells` 的 position 顺序决定。二者通过 `position` 对齐。

当前 `GameConfig`（`src/richman/domain/models.py`）只包含游戏逻辑配置，没有视觉布局信息。BoardWidget 无法仅凭 `board_cells` 知道每个格子应该渲染在终端的哪个位置。

Engine step API 已完成，console driver 已迁移，TUI 目前是最小 smoke shell。下一步是让 BoardWidget 能渲染棋盘，而 `tui_layout` 是 BoardWidget 的前置依赖。

## Goals / Non-Goals

**Goals:**
- 在 domain 层定义 `TuiCellLayout`、`TuiRect`、`TuiLayout` 三个纯数据 dataclass
- `GameConfig` 增加可选 `tui_layout: TuiLayout | None` 字段
- 默认 10 格棋盘提供完整 `tui_layout`
- JSON/YAML 配置文件支持解析 `tui_layout` 段
- domain 公共 API 导出新增类型
- 布局数据不依赖 Textual、Rich 或任何渲染框架

**Non-Goals:**
- 不实现布局校验逻辑（校验属于下一个 change `add-tui-layout-validation`）
- 不实现 BoardWidget 或任何 Textual widget
- 不修改 board 模块（board 负责空间查询，不负责视觉坐标）
- 不修改 engine 模块
- 不让 `tui_layout` 影响游戏移动顺序

## Decisions

### 决策 1：数据类型放在 domain 层

`TuiLayout` 等类型放在 `richman.domain.models`，与 `GameConfig` 同文件。

**理由**：`tui_layout` 是 `GameConfig` 的可选字段，属于游戏配置数据。domain 层是纯数据层，不依赖任何 UI 框架，满足 TUI 设计文档"domain 只承载布局数据，不依赖 Textual"的约束。

**替代方案**：放在 `richman.adapters.textual_tui` 内部。被否决，因为 `GameConfig` 需要引用该类型，而 domain 不能依赖 adapter。

### 决策 2：三个 dataclass 的字段设计

```python
@dataclass(frozen=True, slots=True)
class TuiCellLayout:
    position: int      # 对应 board_cells position
    row: int           # slot 网格中的行坐标（0 基）
    column: int        # slot 网格中的列坐标（0 基）

@dataclass(frozen=True, slots=True)
class TuiRect:
    row: int           # 矩形左上角行坐标
    column: int        # 矩形左上角列坐标
    row_span: int      # 占用行数
    column_span: int   # 占用列数

@dataclass(frozen=True, slots=True)
class TuiLayout:
    rows: int                            # slot 网格总行数
    columns: int                         # slot 网格总列数
    center: TuiRect                      # 中心展示区矩形
    cells: tuple[TuiCellLayout, ...]     # 所有格子的视觉坐标
```

**理由**：与 TUI 设计文档 3.1 节的字段定义完全对齐。`frozen=True` 保持与 domain 其他类型一致的不可变风格。`slots=True` 减少内存开销。

`TuiRect` 使用 `row_span`/`column_span` 而非 `rows`/`columns`，以避免与 `TuiLayout.rows`/`columns` 混淆。

### 决策 3：GameConfig.tui_layout 为可选字段

`tui_layout: TuiLayout | None = None`，默认为 `None`。

**理由**：TUI 布局是视觉层关注点，不是游戏逻辑的必要条件。console 模式和 headless 测试不需要 `tui_layout`。TUI 入口应在 `tui_layout` 为 `None` 时拒绝启动并给出明确错误，而非让 domain 强制要求布局。

### 决策 4：默认布局采用 9×13 网格

默认 10 格棋盘使用 9 行 × 13 列的 slot 网格，中心展示区占 5 行 × 9 列。格子围绕中心形成逆时针环形路径。

**理由**：与 TUI 设计文档示例布局尺寸一致。9×13 网格在标准终端（80×24 或更大）中有足够空间。10 个格子均匀分布在四边，视觉上形成清晰的环形路径。

具体坐标：

| position | 类型 | row | column |
|----------|------|-----|--------|
| 0 | START | 8 | 0 |
| 1 | PROPERTY (南街) | 8 | 2 |
| 2 | CHANCE | 8 | 4 |
| 3 | PROPERTY (东街) | 6 | 12 |
| 4 | BLANK | 4 | 12 |
| 5 | JAIL_SPACE | 0 | 11 |
| 6 | PROPERTY (西街) | 0 | 8 |
| 7 | CHANCE | 0 | 5 |
| 8 | GO_TO_JAIL | 0 | 2 |
| 9 | PROPERTY (北街) | 2 | 0 |

Center: row=2, column=2, row_span=5, column_span=9

**替代方案**：使用更小的网格（如 5×7）。被否决，因为未来可能有更大的地图，9×13 为扩展留出空间。

### 决策 5：配置文件解析采用嵌套结构

JSON/YAML 中 `tui_layout` 作为顶层键，结构直接映射 dataclass 字段：

```yaml
tui_layout:
  rows: 9
  columns: 13
  center:
    row: 2
    column: 2
    row_span: 5
    column_span: 9
  cells:
    - position: 0
      row: 8
      column: 0
    - position: 1
      row: 8
      column: 2
    # ...
```

**理由**：与 TUI 设计文档 3.1 节示例 YAML 保持一致。字段名使用 `row_span`/`column_span` 与 `TuiRect` 对齐。

## Risks / Trade-offs

- **[风险] 默认布局坐标可能不美观**：当前默认布局注重功能正确性（position 不重复、不与 center 重叠），视觉优化可在后续调整坐标值而不改变 schema → **缓解**：坐标值是纯数据，修改不需要代码变更
- **[风险] `tui_layout` 与 `board_cells` 长度不一致**：配置文件可能定义错误数量的 cell 布局 → **缓解**：校验逻辑在下一个 change 中实现（`add-tui-layout-validation`），当前只做数据建模和解析
- **[权衡] `TuiLayout` 放在 domain 而非 adapter**：增加了 domain 的类型数量，但避免了循环依赖（GameConfig → TuiLayout），且符合"domain 承载所有配置数据"的架构原则
