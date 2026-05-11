## 1. Domain 层新增 TUI 布局类型

- [x] 1.1 在 `src/richman/domain/models.py` 新增 `TuiCellLayout` dataclass（frozen, slots），包含 `position: int`、`row: int`、`column: int`
- [x] 1.2 在 `src/richman/domain/models.py` 新增 `TuiRect` dataclass（frozen, slots），包含 `row: int`、`column: int`、`row_span: int`、`column_span: int`
- [x] 1.3 在 `src/richman/domain/models.py` 新增 `TuiLayout` dataclass（frozen, slots），包含 `rows: int`、`columns: int`、`center: TuiRect`、`cells: tuple[TuiCellLayout, ...]`
- [x] 1.4 `GameConfig` 增加可选字段 `tui_layout: TuiLayout | None = None`

## 2. Domain 公共 API 导出

- [x] 2.1 在 `src/richman/domain/__init__.py` 中导入并导出 `TuiCellLayout`、`TuiRect`、`TuiLayout`
- [x] 2.2 更新 `__all__` 列表包含三个新类型

## 3. App 层默认布局和配置解析

- [x] 3.1 在 `src/richman/app.py` 的 `build_default_config()` 中为默认 10 格棋盘构造 `TuiLayout`（9 行 × 13 列网格，center 占 5×9，cells 按逆时针环形排列）
- [x] 3.2 在 `src/richman/app.py` 的 `_parse_game_config()` 中新增 `_parse_tui_layout()` 辅助函数，从配置 dict 解析可选的 `tui_layout` 段
- [x] 3.3 `_parse_tui_layout()` 解析 `rows`、`columns`、`center`（含 `row`、`column`、`row_span`、`column_span`）和 `cells` 列表（每项含 `position`、`row`、`column`）
- [x] 3.4 `tui_layout` 段为可选：不存在时 `GameConfig.tui_layout` 为 `None`

## 4. 测试覆盖

- [x] 4.1 在 `tests/test_domain_models.py` 中新增测试：`TuiCellLayout` 构造与不可变性、`TuiRect` 构造与不可变性、`TuiLayout` 构造与不可变性
- [x] 4.2 测试 `GameConfig` 默认 `tui_layout=None`，以及显式传入 `tui_layout` 后字段正确
- [x] 4.3 在 `tests/test_app.py` 中新增测试：`build_default_config()` 返回的配置包含非空 `tui_layout`，且 cells 的 position 覆盖所有 board_cells 索引
- [x] 4.4 测试 `load_config()` 从 JSON 文件解析 `tui_layout`
- [x] 4.5 测试 `load_config()` 从 YAML 文件解析 `tui_layout`
- [x] 4.6 测试 `load_config()` 在配置不含 `tui_layout` 时返回 `None`

## 5. 质量检查

- [x] 5.1 运行 `uv run ruff check src tests` 确保无 lint 错误
- [x] 5.2 运行 `uv run mypy src tests` 确保类型检查通过
- [x] 5.3 运行 `uv run pytest` 确保全部测试通过
- [x] 5.4 运行 `openspec validate --specs --strict` 确保规格校验通过
