## 1. 新增校验模块骨架

- [x] 1.1 创建 `src/richman/adapters/textual_tui/layout.py`，定义 `TuiLayoutValidationResult` dataclass（frozen, slots），包含 `errors: tuple[str, ...]` 和 `warnings: tuple[str, ...]`（warnings 字段预留给未来）
- [x] 1.2 定义 `validate_tui_layout(config: GameConfig) -> TuiLayoutValidationResult` 函数签名

## 2. 实现必须拒绝的校验规则

- [x] 2.1 `tui_layout` 为 `None` 时返回 error
- [x] 2.2 `rows <= 0` 或 `columns <= 0` 时返回 error
- [x] 2.3 `center.row < 0` 或 `center.column < 0` 时返回 error
- [x] 2.4 `center.row_span <= 0` 或 `center.column_span <= 0` 时返回 error
- [x] 2.5 center 矩形越界（`row + row_span > rows` 或 `column + column_span > columns`）时返回 error
- [x] 2.6 缺失 `board_cells` 中的 position 时返回 error
- [x] 2.7 `cells` 包含 `board_cells` 中不存在的 position 时返回 error
- [x] 2.8 position 重复时返回 error
- [x] 2.9 cell row 或 column 越界（负数或 >= rows/columns）时返回 error
- [x] 2.10 两个不同 position 的 cell 具有相同 `(row, column)` 时返回 error
- [x] 2.11 cell 坐标落入 center 矩形时返回 error

## 3. 编写测试

- [x] 3.1 创建 `tests/test_textual_tui_layout.py`
- [x] 3.2 测试合法默认布局通过校验（errors 为空）
- [x] 3.3 测试 `tui_layout=None` 被拒绝
- [x] 3.4 测试 `rows <= 0` 和 `columns <= 0` 被拒绝
- [x] 3.5 测试 `center.row < 0` 和 `center.column < 0` 被拒绝
- [x] 3.6 测试 center row_span/column_span <= 0 被拒绝
- [x] 3.7 测试 center 矩形越界被拒绝
- [x] 3.8 测试缺失 position 被拒绝
- [x] 3.9 测试多余 position 被拒绝
- [x] 3.10 测试重复 position 被拒绝
- [x] 3.11 测试 cell 坐标越界被拒绝
- [x] 3.12 测试重复坐标被拒绝
- [x] 3.13 测试 cell 与 center 重叠被拒绝
- [x] 3.14 测试校验函数不修改输入 config
- [x] 3.15 测试多个 error 同时被收集（而非在第一个错误处终止）

## 4. 质量检查

- [x] 4.1 运行 `uv run ruff check src tests`
- [x] 4.2 运行 `uv run mypy src tests`
- [x] 4.3 运行 `uv run pytest`
- [x] 4.4 运行 `openspec validate --specs --strict`
