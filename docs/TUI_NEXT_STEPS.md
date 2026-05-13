# TUI 后续开发接手说明

最后更新：2026-05-14

## 当前状态

当前 TUI 主线已经完成从 CLI 到游戏主屏幕的基本闭环：

- `richman play` 保留 console 模式行为，并通过 step API 驱动 engine。
- `richman tui` 已新增，能加载默认或自定义配置并启动 `RichmanTuiApp`。
- `RichmanTuiApp` 的游戏模式进入 `TitleScreen -> SetupScreen -> GameScreen`。
- `SetupScreen` 支持总玩家数和人类玩家名设置，确认后创建 players、engine 并进入 `GameScreen`。
- `RichmanTuiApp` 仍保留测试/快速启动路径：传入 engine 和 player controllers 时可直接进入 `GameScreen`。
- 当前 `openspec list --json` 应返回空变更列表。

已完成并归档的相关 OpenSpec change：

| Change | 状态 | 说明 |
|---|---|---|
| `refactor-engine-step-api` | 已归档 | Engine 提供 `advance(input)`、`StepResult`、`RequiredInput`、`EngineInput` |
| `add-tui-layout-config` | 已归档 | `GameConfig` 支持 `tui_layout`，默认配置和配置文件解析支持 TUI 布局 |
| `add-tui-layout-validation` | 已归档 | 新增 `validate_tui_layout(config)`，拒绝缺失、重复、越界、覆盖中心区等非法布局 |
| `add-tui-board-layout-calculation` | 已归档 | 新增 `compute_layout_geometry(config, terminal_size)`，计算棋盘终端字符几何 |
| `add-tui-board-widget` | 已归档 | 新增 `BoardWidget`、`CellWidget`、`CenterPanel`，按配置化布局渲染棋盘 |
| `add-tui-step-driver` | 已归档 | 新增 `GameScreen` 和 `ActionBar`，TUI 可通过 step API 推进游戏并提交输入 |
| `add-tui-app-entry` | 已归档 | 新增 `richman tui`、`run_tui_game()`、`create_tui_players()`，打通 TUI 启动入口 |
| `add-tui-title-setup-screens` | 已归档 | 新增 `TitleScreen`、`SetupScreen`，形成 `TitleScreen -> SetupScreen -> GameScreen` 屏幕流 |

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

### TUI Layout

- `GameConfig.tui_layout: TuiLayout | None = None`
- `build_default_config()` 提供默认 10 格 TUI 布局
- `load_config()` 支持从 JSON/YAML 解析 `tui_layout`
- `validate_tui_layout(config)` 返回结构化 errors/warnings
- `compute_layout_geometry(config, terminal_size=None)` 生成：
  - `position_rects`
  - `center_rect`
  - `min_terminal_rows`
  - `min_terminal_cols`
  - `is_terminal_sufficient`

### TUI Widgets

- `BoardWidget` 接收 `GameSnapshot`、`TuiLayoutGeometry` 和可选 `terminal_size`
- `CellWidget` 渲染单个格子并发出 `CellClicked(position)`
- `CenterPanel` 展示当前回合、阶段、玩家、骰子和最近事件
- 终端尺寸不足时，`BoardWidget` 显示明确错误状态

### TUI Step Driver

- `GameScreen(engine, config, player_controllers)` 持有已装配 engine
- `GameScreen` 在 mount 后通过 `engine.advance()` 自动推进非输入 step
- AI 玩家通过 `player_controllers` 检测并自动提交输入
- 人类玩家通过 `ActionBar` 或棋盘点击提交输入
- `ActionBar` 根据 `RequiredInput` 渲染掷骰、动作、入狱选择或拆除目标提示
- `ActionBar` 支持按钮点击、Enter/Space 和数字键快捷输入

### TUI App Flow

- `create_tui_players(players_count, human_name="玩家")` 创建 1 个 `HumanPlayer(human_name)` + N-1 个 `AIPlayer`
- `run_tui_game(players_count=2, seed=None, config_path=None)` 加载 config 并以游戏模式启动 TUI
- `richman tui --players N --seed S --config PATH` 可启动 TUI
- `TitleScreen` 展示欢迎和开始提示
- `SetupScreen` 设置总玩家数和人类玩家名，确认后创建 engine 并进入 `GameScreen`
- `tui --players` 表示总玩家数；`play --players` 仍表示 AI 玩家数量

## 下一步建议

下一步最适合开发的是 **主游戏页常驻信息条**。

建议新建 OpenSpec change：`add-tui-player-event-bars`。

原因：

- 当前 `GameScreen` 只有 Header、BoardWidget 和 ActionBar，缺少设计文档中的 PlayerStrip、EventLine 和快捷键 Footer。
- CenterPanel 已经能显示部分状态，但主屏幕外层还没有稳定的信息结构，后续 modal/toast 缺少入口。
- EventLine 是 `EventLogModal` 的自然入口；PlayerStrip 是 AI 信息 toast 的自然入口。
- 这个 change 可以在不改 engine、不改规则、不改 BoardWidget 布局模型的前提下提升主游戏页结构。

## 推荐实现范围

### 1. 新增 PlayerStrip

目标：在 `GameScreen` 中展示玩家概览，左侧突出人类玩家，右侧展示 AI 公开状态。

建议新增：

- `src/richman/adapters/textual_tui/widgets/player_strip.py`
- 对应测试放入 `tests/test_textual_tui_game_screen.py` 或新建 `tests/test_textual_tui_game_bars.py`

建议行为：

- 从 `GameSnapshot.public_players` 和 `viewer_private` 派生展示内容。
- 人类玩家可显示现金、位置、手牌数量、破产/入狱状态。
- AI 玩家只显示公开信息：名称、位置、破产/入狱状态。
- 不显示 AI 现金、手牌、投入成本等私密字段。

验收点：

- `PlayerStrip.update_snapshot(snapshot)` 能更新展示。
- AI 私密字段不会出现。
- 当前玩家有视觉标记。

### 2. 新增 EventLine

目标：在 `GameScreen` 中展示最新事件，为后续 EventLogModal 留入口。

建议新增：

- `src/richman/adapters/textual_tui/widgets/event_line.py`

建议行为：

- 展示 `StepResult.events` 或 `snapshot.event_log` 中最新一条可展示事件。
- 没有事件时展示空状态。
- 支持点击或 `E` 快捷键时发出消息，例如 `EventLine.OpenRequested`，本轮可以只发消息不实现 modal。

验收点：

- 新事件到来时 EventLine 文本更新。
- 没有事件时不报错。
- 点击 EventLine 或按 `E` 能触发可测试消息。

### 3. 调整 GameScreen 布局

目标：让主游戏页接近设计文档的结构：Header、Board、PlayerStrip、EventLine、ActionBar。

建议：

- 保留现有 Header。
- BoardWidget 仍占主要空间。
- ActionBar 仍位于底部。
- 新增 PlayerStrip 和 EventLine 后，`board_terminal_size` 计算要扣除新增行高。
- 新增行高建议先固定：
  - Header: 1
  - PlayerStrip: 1
  - EventLine: 1
  - ActionBar: 5

验收点：

- `compute_layout_geometry(config, terminal_size=board_terminal_size)` 使用扣除信息条后的尺寸。
- `_apply_step_result()` 更新 BoardWidget、ActionBar、PlayerStrip、EventLine。
- 不改变 `GameEngine` 和 `StepResult` 语义。

### 4. 测试策略

建议覆盖：

- `GameScreen.compose()` 包含 `PlayerStrip`、`EventLine`、`BoardWidget`、`ActionBar`。
- board 可用尺寸扣除新增信息条高度。
- `_apply_step_result()` 更新 PlayerStrip 和 EventLine。
- EventLine 显示最新事件。
- PlayerStrip 不泄露 AI 私密字段。
- `richman tui` CLI 和 Title/Setup 流保持通过。

## 后续路线

### 1. `add-tui-player-event-bars`

补齐主游戏页常驻信息条：

- PlayerStrip：展示人类玩家私密信息和 AI 公开信息
- EventLine：展示最新一条事件
- Footer/help text：展示快捷键提示或保留 Textual Footer

### 2. `add-tui-modals`

补齐覆盖层交互：

- `CellDetailModal`
- `EventLogModal`
- 可选 `JailChoiceModal`（如果后续决定入狱选择不用 ActionBar）

### 3. `add-tui-target-highlighting`

增强二步选择体验：

- DEMOLISH_TARGET 时高亮候选格
- 非候选格禁用或弱化
- 取消选择后回到动作选择

### 4. `add-tui-polish`

做体验和视觉收尾：

- 更完整的颜色语义
- AI 行动短提示
- 更稳定的焦点管理
- 更清晰的尺寸不足错误页

## 不建议现在做的事情

- 不做地图自动缩放。
- 不做地图滚动。
- 不重写规则逻辑到 TUI。
- 不把 Textual、Rich widget 或终端事件类型放进 domain、board、rules、player、engine。
- 不让 TUI 直接修改 `InternalGameState`。
- 不把 `tui_layout` 与游戏移动顺序混在一起；移动顺序仍由 `board_cells` 的 position 决定。
- 不在 Player/Event bars change 中实现完整 modal、格子详情弹窗或 AI toast。

## 继续开发时建议先看的文件

- `docs/TUI_DESIGN.md`
- `openspec/specs/tui-app-entry/spec.md`
- `openspec/specs/tui-title-screen/spec.md`
- `openspec/specs/tui-setup-screen/spec.md`
- `openspec/specs/tui-game-screen/spec.md`
- `openspec/specs/tui-action-bar/spec.md`
- `openspec/specs/tui-board-widget/spec.md`
- `src/richman/app.py`
- `src/richman/cli.py`
- `src/richman/adapters/textual_tui/app.py`
- `src/richman/adapters/textual_tui/screens/title.py`
- `src/richman/adapters/textual_tui/screens/setup.py`
- `src/richman/adapters/textual_tui/screens/game.py`
- `src/richman/adapters/textual_tui/widgets/action_bar.py`
- `tests/test_textual_tui_app.py`
- `tests/test_textual_tui_game_screen.py`

## 快速状态检查命令

```bash
openspec list --json
openspec validate --specs --strict
uv run ruff check src tests
uv run mypy src tests
uv run pytest
```
