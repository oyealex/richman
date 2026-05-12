## 1. 新增布局几何计算骨架

- [x] 1.1 在 `src/richman/adapters/textual_tui/layout.py` 中定义 `CELL_WIDTH`、`CELL_HEIGHT`、`CELL_GAP` 常量
- [x] 1.2 定义 `TuiLayoutGeometry` frozen dataclass，包含 `position_rects: Mapping[int, tuple[int, int, int, int]]`、`center_rect`、`min_terminal_rows`、`min_terminal_cols`、`is_terminal_sufficient` 字段。`position_rects` 实现时用 `MappingProxyType` 包装确保不可变
- [x] 1.3 定义 `compute_layout_geometry(config, terminal_size=None)` 函数签名

## 2. 实现几何计算逻辑

- [x] 2.1 实现校验先行：调用 `validate_tui_layout(config)`，errors 非空时抛出 `ValueError`
- [x] 2.2 实现 cell 终端坐标计算：`position -> (top, left, bottom, right)` 映射，存入 dict 后用 `MappingProxyType` 包装赋值给 `position_rects`
- [x] 2.3 实现 center panel 终端坐标矩形计算
- [x] 2.4 实现 `min_terminal_rows` / `min_terminal_cols` 计算
- [x] 2.5 实现 `is_terminal_sufficient` 判断（terminal_size=None 时为 True）

## 3. 编写测试

- [x] 3.1 导入新常量、`TuiLayoutGeometry`、`compute_layout_geometry`
- [x] 3.2 测试默认布局几何：position_rects 包含所有 position、center_rect 非零、min_terminal 为正整数
- [x] 3.3 测试 cell 坐标常量导出为正整数
- [x] 3.4 测试 position 映射一致性：cell 在 (0,0) 映射到原点，(1,2) 映射到预期坐标
- [x] 3.5 测试任意两个不同 position 的终端字符矩形不重叠
- [x] 3.6 测试 center_rect 与 TuiRect 行/列/跨度一致
- [x] 3.7 测试默认 9×13 布局的 min_terminal_rows=45, min_terminal_cols=168
- [x] 3.8 测试所有 position_rects 不超出 min_terminal 范围
- [x] 3.9 测试 terminal_size 充足时 is_terminal_sufficient=True
- [x] 3.10 测试 terminal_size 不足时 is_terminal_sufficient=False
- [x] 3.11 测试 terminal_size=None 时 is_terminal_sufficient=True
- [x] 3.12 测试非法布局抛出 ValueError

## 4. 质量检查

- [x] 4.1 运行 `uv run ruff check src tests`
- [x] 4.2 运行 `uv run mypy src tests`
- [x] 4.3 运行 `uv run pytest`
- [x] 4.4 运行 `openspec validate --specs --strict`
