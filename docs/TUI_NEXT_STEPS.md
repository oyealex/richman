# TUI 后续开发接手说明

最后更新：2026-05-12

## 当前状态

当前 TUI 主线已经完成两块地基：

- Engine step API 已完成并归档，Console/TUI/测试可以通过 `GameEngine.advance(input)` 使用同一套驱动方式。
- `tui_layout` 配置模型已完成并归档，默认配置和 JSON/YAML 配置文件都可以描述棋盘视觉坐标。

已完成并归档的相关 OpenSpec change：

| Change | 状态 | 说明 |
|---|---|---|
| `refactor-engine-step-api` | 已归档 | Engine 不再直接依赖 renderer，改为返回 `StepResult` / `RequiredInput` |
| `add-tui-layout-config` | 已归档 | 新增 `TuiCellLayout`、`TuiRect`、`TuiLayout`，`GameConfig` 支持可选 `tui_layout`，默认配置和配置文件加载支持布局 |

当前 `openspec list --json` 应返回空变更列表。

## 已完成能力

### Engine Step API

- `GameEngine.advance(input=None) -> StepResult`
- `StepResult.snapshot`
- `StepResult.events`
- `StepResult.required_input`
- `StepResult.game_over`
- `EngineInput`
- `RequiredInput`
- `InputKind`

### TUI Layout 配置模型

已在 `richman.domain` 中提供：

```python
@dataclass(frozen=True, slots=True)
class TuiCellLayout:
    position: int
    row: int
    column: int


@dataclass(frozen=True, slots=True)
class TuiRect:
    row: int
    column: int
    row_span: int
    column_span: int


@dataclass(frozen=True, slots=True)
class TuiLayout:
    rows: int
    columns: int
    center: TuiRect
    cells: tuple[TuiCellLayout, ...]
```

已落地：

- `GameConfig.tui_layout: TuiLayout | None = None`
- `build_default_config()` 提供默认 10 格棋盘布局
- `load_config()` 支持从 JSON/YAML 解析 `tui_layout`
- `richman.domain` 包入口导出 `TuiCellLayout`、`TuiRect`、`TuiLayout`
- 相关测试位于 `tests/test_domain_models.py` 和 `tests/test_app.py`

## 下一步建议

下一步最适合开发的是 **TUI layout 校验层**。

建议新建 OpenSpec change：`add-tui-layout-validation`。

原因：

- `tui_layout` schema 已稳定，但当前只是数据承载，没有校验自定义布局是否可用于 TUI。
- BoardWidget 依赖稳定的 `position -> slot` 映射；如果缺失、重复、越界或覆盖中心区域，会导致后续 widget 渲染和点击映射不可靠。
- TUI 设计要求自定义配置缺少布局时拒绝进入游戏，并显示明确配置错误。
- 当前不做缩放、不做滚动；因此需要先能计算固定布局所需尺寸，才能实现尺寸不足错误页。

## 推荐实现顺序

### 1. 实现 TUI layout 校验

目标：在进入 TUI 棋盘渲染前发现配置错误。

建议新增：

- `src/richman/adapters/textual_tui/layout.py`
- `tests/test_textual_tui_layout.py`

不建议放入 `board`：

- `board` 负责游戏路径和空间计算。
- `tui_layout` 是视觉坐标，只服务 TUI adapter。

建议 API：

```python
@dataclass(frozen=True, slots=True)
class TuiLayoutValidationResult:
    warnings: tuple[str, ...] = ()


def validate_tui_layout(config: GameConfig) -> TuiLayoutValidationResult:
    ...
```

必须拒绝：

- `GameConfig.tui_layout is None`
- `rows <= 0` 或 `columns <= 0`
- `center.row_span <= 0` 或 `center.column_span <= 0`
- `center` 矩形越界
- 缺失任意 `board_cells` position
- `tui_layout.cells` 包含不存在的 position
- `position` 重复
- `(row, column)` 坐标重复
- cell 坐标越界
- cell 坐标落入 center 矩形

建议 warning：

- 相邻 position 在视觉上不相邻。这个问题不阻塞运行，但可能让移动路径难理解。

验收点：

- 缺失 position 被拒绝。
- 重复 position 被拒绝。
- 越界坐标被拒绝。
- 格子与中心区重叠被拒绝。
- 缺少 `tui_layout` 时错误信息明确。
- 合法默认布局通过校验。
- 校验不依赖 engine，不修改 `GameConfig` 或 `GameSnapshot`。

建议规格影响：

- 新增 capability：`tui-layout-validation`
- 可修改 `render-adapter-architecture`：声明 Textual TUI 在进入棋盘渲染前必须校验 `GameConfig.tui_layout`

### 2. 实现 BoardWidget 的纯布局计算层

目标：先稳定“合法布局如何变成可渲染几何信息”，再写 Textual widget。

可以继续放在：

- `src/richman/adapters/textual_tui/layout.py`

建议职责：

- 根据 `TuiLayout` 和固定 cell 尺寸计算最小终端尺寸。
- 生成 `position -> slot` 映射。
- 生成 center panel 的 slot 矩形。
- 提供尺寸不足判断。

当前决策：

- 不做自动缩放。
- 未来可能支持滚动，但当前不实现滚动。
- 中间展示区固定保留，不允许棋盘格占用。

验收点：

- 固定 cell 尺寸下能计算需要的最小宽高。
- 当前终端尺寸不足时能给出当前尺寸和需要尺寸。
- layout 计算不依赖 engine，也不修改 snapshot。

### 3. 接入 Textual BoardWidget

目标：用真实 widget 显示棋盘，而不是只显示 `format_snapshot()` 文本。

建议新增：

- `src/richman/adapters/textual_tui/widgets/board.py`
- `src/richman/adapters/textual_tui/widgets/cell.py`
- `src/richman/adapters/textual_tui/widgets/center_panel.py`

BoardWidget 输入：

- `GameSnapshot`
- `TuiLayout`
- 可选高亮 position 集合，例如拆除候选、当前玩家位置、当前落点

BoardWidget 职责：

- 按 `tui_layout.cells` 坐标渲染全部棋盘格。
- 中心区域固定显示动态内容。
- 每个格子通过 position 与 `GameSnapshot.public_board.cells` 对齐。
- 点击 CellWidget 时回传 position。

中心区建议先显示：

- 当前玩家名称。
- 当前阶段。
- 骰子点数。
- 当前玩家位置。
- 最近 3-5 条事件。

验收点：

- 所有格子都按配置坐标出现。
- 中心区不被格子覆盖。
- 点击任意格子能拿到正确 position。
- 不在 TUI 层重新计算购买、升级、租金、破产等规则。

### 4. 实现 TUI step driver 和输入控件

目标：让 TUI 真正驱动一局游戏。

建议新增入口：

- `richman tui`

建议页面顺序：

- `TitleScreen`
- `SetupScreen`
- `GameScreen`

GameScreen 职责：

- 持有 `GameEngine`。
- 调用 `engine.advance(input)` 获取 `StepResult`。
- 根据 `StepResult.snapshot` 更新 BoardWidget、状态栏、事件栏。
- 根据 `StepResult.required_input` 显示动作按钮、快捷键或 modal。
- 对 AI 玩家自动提交合法输入。

输入映射：

- `ROLL_DICE`：按钮或空格键提交掷骰输入。
- `ACTION_CHOICE`：动作栏按钮和 `1`-`4` 快捷键。
- `DEMOLISH_TARGET`：只允许选择 `RequiredInput.candidates` 中的 position。
- `JAIL_CHOICE`：ModalScreen 或动作栏二选一。

验收点：

- TUI 通过 step API 推进，不绕 engine 私有方法。
- TUI 不直接修改 `InternalGameState`。
- 展示点之间可以短暂停留，UI 不阻塞。
- `required_input` 出现时不会继续自动推进。

## 不建议现在做的事情

- 不做地图自动缩放。
- 不做地图滚动。
- 不重写规则逻辑到 TUI。
- 不让 TUI 读取或修改 `InternalGameState`。
- 不把 Textual、Rich widget 或终端事件类型放进 domain、board、rules、player、engine。
- 不把 `tui_layout` 与游戏移动顺序混在一起；移动顺序仍由 `board_cells` 的 position 决定。

## 下一次 OpenSpec 建议范围

建议 change：`add-tui-layout-validation`

建议只覆盖：

- TUI layout 校验纯逻辑。
- 缺失布局、重复 position、缺失 position、越界坐标、中心区重叠等错误。
- 视觉相邻性 warning。
- 对应单元测试。

建议不要在同一个 change 中实现：

- BoardWidget。
- CenterPanel。
- 点击交互。
- `richman tui` 入口。
- TUI step driver。

## 继续开发时建议先看的文件

- `docs/TUI_DESIGN.md`
- `openspec/specs/tui-layout-config/spec.md`
- `openspec/specs/app-assembly/spec.md`
- `openspec/specs/render-adapter-architecture/spec.md`
- `src/richman/domain/models.py`
- `src/richman/app.py`
- `src/richman/adapters/textual_tui/app.py`
- `tests/test_app.py`
- `tests/test_domain_models.py`
- `tests/test_textual_tui.py`

## 快速状态检查命令

```bash
openspec list --json
openspec validate --specs --strict
uv run ruff check src tests
uv run mypy src tests
uv run pytest
```
