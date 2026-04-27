## 1. 模块结构与公共 API

- [x] 1.1 在 `src/richman/board/` 中建立 board 实现文件，并保持模块只导入 `richman.domain` 和标准库。
- [x] 1.2 定义不可变 `Board` 类型，保存棋盘格序列和预计算 START 位置。
- [x] 1.3 定义不可变 `MoveResult` 类型，包含 `new_position` 和 `start_crossings`。
- [x] 1.4 从 `richman.board` 包入口导出 `Board`、`MoveResult`、`create`、`get_cell_type`、`get_property_template`、`get_range`、`move`、`total_cells`。

## 2. 棋盘创建与静态查询

- [x] 2.1 实现 `create(config: GameConfig) -> Board`，从 `config.board_cells` 创建棋盘快照。
- [x] 2.2 在创建时校验棋盘非空、恰好一个 START、PROPERTY 格必须有 `PropertyTemplate`、非 PROPERTY 格不得有 `PropertyTemplate`。
- [x] 2.3 实现位置校验辅助，直接查询、移动起点和范围中心遇到越界位置时报告错误。
- [x] 2.4 实现 `total_cells(board)`、`get_cell_type(board, position)` 和 `get_property_template(board, position)`。

## 3. 环形空间计算

- [x] 3.1 实现 `move(board, position, steps)` 的正向移动和棋盘末尾取模。
- [x] 3.2 实现 `move(board, position, steps)` 的反向移动和棋盘开头取模。
- [x] 3.3 实现 `start_crossings` 计数，覆盖起始 START 不计、路径进入 START 计数、正好停在 START 计数和多圈移动。
- [x] 3.4 实现 `get_range(board, center, radius)`，按中心、顺时针、逆时针的稳定顺序返回去重位置。
- [x] 3.5 在 `get_range` 中拒绝负半径。

## 4. 单元测试

- [x] 4.1 新增 board 公共 API 导入测试和依赖边界测试。
- [x] 4.2 覆盖合法棋盘创建、非法 START 数量、空棋盘、PROPERTY 模板缺失、非 PROPERTY 携带模板等创建校验。
- [x] 4.3 覆盖格子类型查询、地块模板查询、非地块模板返回 `None` 和越界查询错误。
- [x] 4.4 覆盖正向移动、反向移动、0 步移动、跨越起点、从 START 出发、多圈移动和正好停在 START。
- [x] 4.5 覆盖范围查询包含中心、环形两侧扩展、稳定顺序、去重和负半径错误。

## 5. 验证与交接

- [x] 5.1 运行 `uv run pytest` 确认测试通过。
- [x] 5.2 运行 `uv run ruff check` 和 `uv run ruff format --check` 确认风格检查通过。
- [x] 5.3 运行 `uv run mypy src` 确认类型检查通过。
- [x] 5.4 实现完成后更新 `docs/DEVELOPMENT_PROGRESS.md`，记录 board 模块状态和下一步建议。
