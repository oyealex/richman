# TUI Board Widget

## Purpose

提供 Textual BoardWidget 体系——按 `TuiLayoutGeometry` 的终端字符坐标渲染棋盘格、中心信息区，发出 CellClicked 点击消息，尺寸不足时展示错误状态。所有 widget 代码限制在 `richman.adapters.textual_tui.widgets` 包内。
## Requirements
### Requirement: BoardWidget renders board grid from snapshot and geometry

系统 SHALL 提供 `BoardWidget` Textual widget，接收 `GameSnapshot`、`TuiLayoutGeometry` 和可选的 `terminal_size: tuple[int, int] | None`，按 `position_rects` 绝对定位渲染所有棋盘格和中心信息区。尺寸充足性由 `terminal_size` 直接与 `min_terminal_rows/cols` 比较判断，`terminal_size=None` 时回退到 `geometry.is_terminal_sufficient`。

#### Scenario: BoardWidget renders all cells from geometry

- **WHEN** 向 BoardWidget 传入 `GameSnapshot` 和合法的 `TuiLayoutGeometry`，终端尺寸充足
- **THEN** BoardWidget 的子 widget 中 MUST 包含与 `geometry.position_rects` 中每个 position 对应的 `CellWidget`
- **AND** 每个 CellWidget MUST 使用绝对定位，`offset` 等于 `(left, top)`

#### Scenario: BoardWidget renders center panel

- **WHEN** BoardWidget 正常渲染棋盘
- **THEN** 子 widget 中 MUST 包含一个 `CenterPanel`，位于 `geometry.center_rect` 对应位置

#### Scenario: BoardWidget shows error state when terminal insufficient

- **WHEN** `terminal_size` 非 None 且 `rows < min_terminal_rows` 或 `cols < min_terminal_cols`
- **THEN** BoardWidget MUST 渲染错误提示文字，包含 `geometry.min_terminal_rows/cols`（需要尺寸）和 `terminal_size`（当前尺寸）
- **AND** BoardWidget MUST NOT 渲染任何 CellWidget
- **AND** BoardWidget 容器 MUST 设置 `width: 100%`、`height: auto` 确保错误文案可见

### Requirement: CellWidget displays cell content per TUI design spec

系统 SHALL 提供 `CellWidget`（继承 Textual `Static`），渲染单个棋盘格的内容：position 编号、cell 类型标识、名称、归属/等级、当前站立玩家棋子。

#### Scenario: CellWidget shows position and type

- **WHEN** 渲染一个 START 类型、position=0 的 CellWidget
- **THEN** 内容 MUST 包含 "0"（position 编号）
- **AND** 内容 MUST 包含表示 START 的视觉标识

#### Scenario: CellWidget shows property name

- **WHEN** 渲染一个 property cell，`PublicCellInfo.property_name` 为 "海滨别墅"
- **THEN** 内容 MUST 包含 "海滨别墅"

#### Scenario: CellWidget shows owner name

- **WHEN** 渲染一个 property cell，传入 `owner_name="AI-1"`
- **THEN** 内容 MUST 包含 "AI-1"

#### Scenario: CellWidget shows unowned property

- **WHEN** 渲染一个 property cell，传入 `owner_name=None`
- **THEN** 内容 MUST 显示 "无主" 或等效空置标识

#### Scenario: CellWidget shows level dots

- **WHEN** 渲染一个 property cell，`PublicCellInfo.level` 为 2
- **THEN** 内容 MUST 包含表示等级 2 的视觉标识

#### Scenario: CellWidget shows player tokens on cell

- **WHEN** 渲染一个 cell，传入 `players_on_cell` 包含玩家名
- **THEN** 内容 MUST 包含该玩家名称或缩略标识

#### Scenario: CellWidget highlights current player cell

- **WHEN** `is_current_player_cell=True`
- **THEN** CellWidget MUST 添加 CSS class `current`，使用高亮边框样式

### Requirement: CellWidget emits CellClicked message on click

系统 SHALL 在用户点击 `CellWidget` 时发出 `CellWidget.CellClicked(position)` 冒泡消息。

#### Scenario: Click emits CellClicked with correct position

- **WHEN** 用户点击 position=3 的 CellWidget
- **THEN** CellWidget MUST 发出 `CellWidget.CellClicked` 消息
- **AND** 消息的 `position` 属性 MUST 为 3

#### Scenario: CellClicked message is a Textual Message

- **WHEN** 检查 `CellWidget.CellClicked` 类
- **THEN** 它 MUST 继承 `textual.message.Message`

### Requirement: CenterPanel displays current game state

系统 SHALL 提供 `CenterPanel` widget（继承 Textual `Static`），展示当前回合/阶段、当前玩家名称、骰子点数、最近事件。

#### Scenario: CenterPanel shows current phase

- **WHEN** 渲染 CenterPanel，`GameSnapshot.phase` 为 `DICE_ROLL`
- **THEN** 内容 MUST 包含 "DICE_ROLL" 或对应中文阶段名

#### Scenario: CenterPanel shows current player name

- **WHEN** 渲染 CenterPanel，`GameSnapshot.current_player_index` 对应玩家 "Alice"
- **THEN** 内容 MUST 包含 "Alice"

#### Scenario: CenterPanel shows dice value

- **WHEN** `GameSnapshot.dice_value` 为 7
- **THEN** 内容 MUST 包含 "7"

#### Scenario: CenterPanel shows dash when dice is None

- **WHEN** `GameSnapshot.dice_value` 为 None
- **THEN** 内容 MUST 显示 "-" 或等效空值表示

#### Scenario: CenterPanel shows recent events

- **WHEN** `GameSnapshot.event_log` 包含 10 条事件
- **THEN** CenterPanel MUST 展示最近 3 到 5 条事件

### Requirement: Board widgets are isolated in textual_tui adapter

系统 SHALL 确保 CellWidget、CenterPanel、BoardWidget 的源码位于 `richman.adapters.textual_tui.widgets` 包内，不污染 domain、engine 或 render 模块。

#### Scenario: Widget imports stay within adapter boundary

- **WHEN** 检查 `widgets/board.py`、`widgets/cell.py`、`widgets/center_panel.py` 的导入
- **THEN** 它们 MUST NOT 导入 `richman.engine`、`richman.board`、`richman.rules`、`richman.player`
- **AND** Textual 导入 MUST 限制在 `richman.adapters.textual_tui` 包内

### Requirement: BoardWidget updates render when snapshot changes

系统 SHALL 支持 BoardWidget 在接收新 `GameSnapshot` 后更新所有 CellWidget 和 CenterPanel 的显示内容。

#### Scenario: Snapshot update refreshes cell content

- **WHEN** BoardWidget 接收新的 `GameSnapshot`（如玩家移动后）
- **THEN** 所有受影响的 CellWidget MUST 更新显示内容反映新状态

#### Scenario: Snapshot update refreshes center panel

- **WHEN** BoardWidget 接收新的 `GameSnapshot`（如阶段变更）
- **THEN** CenterPanel MUST 更新显示当前阶段、骰子、事件

### Requirement: BoardWidget accepts highlight positions for candidate cells

系统 SHALL 为 BoardWidget 提供 `highlight_positions: Reactive[frozenset[int]]` reactive 属性，接收需要高亮的 position 集合。watcher 为对应 CellWidget 添加或移除 CSS class `candidate`。

#### Scenario: Setting highlight_positions adds candidate class

- **WHEN** `board.highlight_positions = frozenset({3, 5})`
- **THEN** position 3 和 5 的 CellWidget MUST 添加 CSS class `candidate`
- **AND** 其他 CellWidget MUST NOT 有 `candidate` class

#### Scenario: Updating highlight_positions replaces previous highlights

- **WHEN** `board.highlight_positions` 从 `frozenset({3, 5})` 变为 `frozenset({7})`
- **THEN** position 7 的 CellWidget MUST 有 `candidate` class
- **AND** position 3 和 5 的 CellWidget MUST NOT 有 `candidate` class

#### Scenario: Empty highlight_positions clears all highlights

- **WHEN** `board.highlight_positions = frozenset()`
- **THEN** 所有 CellWidget 的 `candidate` CSS class MUST 被移除

### Requirement: CellWidget renders candidate highlight style

系统 SHALL 为 CellWidget 定义 `candidate` CSS class，以高亮边框样式区分候选格。

#### Scenario: Candidate cell has distinctive border

- **WHEN** CellWidget 拥有 CSS class `candidate`
- **THEN** 该 CellWidget MUST 使用区别于 `current` 的高亮边框样式
- **AND** `candidate` 和 `current` class 可同时存在（玩家站在候选格上时）

