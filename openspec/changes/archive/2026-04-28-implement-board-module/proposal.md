## Why

`domain` 模块已经提供棋盘格、地块配方和游戏配置等共享模型，但后续 `engine` 仍缺少可复用的棋盘空间计算能力。现在需要实现 `board` 模块，先把环形移动、起点经过计数、范围查询和格子查询稳定下来，作为 `rules`、`engine` 和拆除卡逻辑的基础。

## What Changes

- 新增 `richman.board` 模块，提供不可变棋盘对象和面向位置编号的纯查询/计算接口。
- 支持从 `GameConfig.board_cells` 创建棋盘，并校验棋盘格定义满足运行所需的不变量。
- 提供格子类型查询、地块模板查询、棋盘总格数查询。
- 提供环形移动计算，返回新位置和本次移动进入 START 格的次数。
- 提供以当前位置为中心的环形范围查询，用于后续拆除卡候选目标计算。
- 增加 board 单元测试，覆盖正向/反向移动、跨越起点、正好停在起点、范围去重和查询边界。

## Capabilities

### New Capabilities

- `board-spatial-model`: 定义棋盘不可变空间模型、格子查询、环形移动和范围查询能力。

### Modified Capabilities

无。

## Impact

- 影响代码：`src/richman/board/`、`src/richman/board/__init__.py`。
- 影响测试：新增或更新 `tests/test_board.py`。
- 依赖关系：`board` 只依赖 `richman.domain`，不依赖 `rules`、`player`、`engine`、`render` 或 adapter。
- API 影响：新增 `richman.board` 公共导出；不修改现有 `domain`、`render` 或 CLI API。
