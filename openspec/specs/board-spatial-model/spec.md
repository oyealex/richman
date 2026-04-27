# board-spatial-model Specification

## Purpose

定义终端大富翁游戏的棋盘空间模型能力，包括不可变棋盘创建、静态格子查询、环形移动和范围查询，作为后续 engine、拆除卡和棋盘展示逻辑的基础。

## Requirements

### Requirement: Board module boundary

系统 SHALL 提供 `richman.board` 作为棋盘空间模型模块，并保持该模块只依赖 `richman.domain`，不持有玩家、租金、事件日志或可变游戏状态。

#### Scenario: Board package is importable

- **WHEN** 开发者导入 `richman.board`
- **THEN** 该包成功导入并导出 board 公共 API

#### Scenario: Board does not depend on higher modules

- **WHEN** 检查 `src/richman/board` 的源码导入
- **THEN** board 模块不导入 `richman.rules`、`richman.player`、`richman.engine`、`richman.render` 或 adapter 模块

#### Scenario: Board contains no runtime state mutation

- **WHEN** 使用 board API 查询格子、计算移动或计算范围
- **THEN** board 不修改 `InternalGameState`、玩家状态、地块运行时状态、事件日志、随机源或渲染状态

### Requirement: Immutable board creation

系统 SHALL 从 `GameConfig.board_cells` 创建不可变棋盘对象，并在创建时校验棋盘静态配置满足空间计算所需不变量。

#### Scenario: Board is created from game config

- **WHEN** 使用包含合法 `board_cells` 的 `GameConfig` 调用 `create`
- **THEN** 系统返回可供查询和移动计算使用的 `Board`
- **AND** 后续修改原始配置引用不得改变已创建 `Board` 的格子序列

#### Scenario: Board requires non-empty cells

- **WHEN** 使用空 `board_cells` 创建棋盘
- **THEN** `create` MUST 拒绝该配置并报告配置错误

#### Scenario: Board requires exactly one start cell

- **WHEN** `board_cells` 中没有 START 格或包含多个 START 格
- **THEN** `create` MUST 拒绝该配置并报告配置错误

#### Scenario: Property cells require property templates

- **WHEN** 某个 PROPERTY 格没有 `PropertyTemplate`
- **THEN** `create` MUST 拒绝该配置并报告配置错误

#### Scenario: Non-property cells reject property templates

- **WHEN** 非 PROPERTY 格携带 `PropertyTemplate`
- **THEN** `create` MUST 拒绝该配置并报告配置错误

### Requirement: Static board queries

系统 SHALL 提供棋盘总格数、格子类型和地块模板查询，使后续模块可以按位置读取静态棋盘信息。

#### Scenario: Total cell count is available

- **WHEN** 调用 `total_cells(board)`
- **THEN** 系统返回棋盘格总数

#### Scenario: Cell type can be queried by valid position

- **WHEN** 调用 `get_cell_type(board, position)` 且 `position` 在棋盘范围内
- **THEN** 系统返回该位置的 `CellType`

#### Scenario: Property template can be queried for property cell

- **WHEN** 调用 `get_property_template(board, position)` 且该位置是 PROPERTY 格
- **THEN** 系统返回该位置的 `PropertyTemplate`

#### Scenario: Property template query returns none for non-property cell

- **WHEN** 调用 `get_property_template(board, position)` 且该位置不是 PROPERTY 格
- **THEN** 系统返回 `None`

#### Scenario: Static queries reject invalid positions

- **WHEN** 调用静态查询函数且 `position` 小于 0 或大于等于棋盘总格数
- **THEN** 查询函数 MUST 拒绝该位置并报告位置错误

### Requirement: Circular movement

系统 SHALL 提供有符号步数的环形移动计算，并返回新位置和本次移动进入 START 格的次数。

#### Scenario: Forward movement wraps around the board

- **WHEN** 从有效位置向前移动正数步，且路径越过棋盘末尾
- **THEN** `move` 返回取模后的新位置

#### Scenario: Backward movement wraps around the board

- **WHEN** 从有效位置向后移动负数步，且路径越过棋盘开头
- **THEN** `move` 返回取模后的新位置

#### Scenario: Zero-step movement stays in place

- **WHEN** 从有效位置移动 0 步
- **THEN** `move` 返回原位置
- **AND** `start_crossings` 为 0

#### Scenario: Start crossing counts each entry into start

- **WHEN** 移动路径一次或多次进入 START 格
- **THEN** `move` 返回的 `start_crossings` 等于路径进入 START 的次数

#### Scenario: Starting on start does not count until re-entered

- **WHEN** 玩家移动开始时已经位于 START 格
- **THEN** 起始位置本身不计入 `start_crossings`
- **AND** 只有移动过程中再次进入 START 时才计数

#### Scenario: Landing exactly on start counts as crossing

- **WHEN** 移动最终位置正好是 START 格
- **THEN** 本次进入 START MUST 计入 `start_crossings`

#### Scenario: Movement rejects invalid start position

- **WHEN** 调用 `move(board, position, steps)` 且 `position` 小于 0 或大于等于棋盘总格数
- **THEN** `move` MUST 拒绝该位置并报告位置错误

### Requirement: Circular range query

系统 SHALL 提供以中心格为基准的环形范围查询，返回中心格以及顺时针、逆时针半径范围内的去重位置列表。

#### Scenario: Range query includes center

- **WHEN** 调用 `get_range(board, center, radius)` 且 `center` 有效、`radius` 大于等于 0
- **THEN** 返回列表 MUST 包含 `center`

#### Scenario: Range query includes clockwise and counterclockwise positions

- **WHEN** 调用 `get_range(board, center, radius)` 且 `radius` 大于 0
- **THEN** 返回列表包含从 `center` 顺时针 1 到 `radius` 步的位置
- **AND** 返回列表包含从 `center` 逆时针 1 到 `radius` 步的位置

#### Scenario: Range query uses stable ordering

- **WHEN** 调用 `get_range(board, center, radius)`
- **THEN** 返回顺序 MUST 为 `center`、顺时针 1 到 `radius`、逆时针 1 到 `radius`
- **AND** 已出现的位置不得再次出现

#### Scenario: Range query deduplicates wrapped positions

- **WHEN** `radius` 足够大导致顺时针和逆时针范围在环形棋盘上重叠
- **THEN** 每个棋盘位置最多返回一次

#### Scenario: Range query rejects invalid center

- **WHEN** 调用 `get_range(board, center, radius)` 且 `center` 小于 0 或大于等于棋盘总格数
- **THEN** `get_range` MUST 拒绝该中心位置并报告位置错误

#### Scenario: Range query rejects negative radius

- **WHEN** 调用 `get_range(board, center, radius)` 且 `radius` 小于 0
- **THEN** `get_range` MUST 拒绝该半径并报告半径错误

### Requirement: Board public API export

系统 SHALL 从 `richman.board` 包入口导出 board 公共类型和函数，使后续模块不依赖 board 内部文件组织。

#### Scenario: Common board APIs can be imported from package root

- **WHEN** 后续模块执行 `from richman.board import Board, MoveResult, create, get_cell_type, get_property_template, get_range, move, total_cells`
- **THEN** 导入成功且无需知道 board 内部源码文件布局
