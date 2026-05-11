## Why

当前 `GameConfig` 只描述棋盘格的游戏逻辑属性（类型、地块配方、卡片），不包含 TUI 渲染所需的视觉坐标信息。根据 TUI 设计文档，棋盘采用配置化坐标布局——格子围绕固定中心展示区排列，视觉位置由 `tui_layout` 决定，游戏移动顺序仍由 `board_cells` 的 position 顺序决定。在 BoardWidget 可以实现之前，必须先建立 `tui_layout` 数据模型并集成到配置系统中。

## What Changes

- 在 `richman.domain` 新增三个不可变 dataclass：`TuiCellLayout`（单个格子的视觉坐标）、`TuiRect`（矩形区域）、`TuiLayout`（完整棋盘视觉布局）
- `GameConfig` 增加可选字段 `tui_layout: TuiLayout | None`
- `build_default_config()` 为默认 10 格棋盘提供 `tui_layout`
- `load_config()` / `_parse_game_config()` 支持从 JSON/YAML 解析 `tui_layout`
- domain 公共 API 导出新增类型
- 相关测试覆盖新增类型的不可变性、默认配置含布局、配置文件解析布局

## Capabilities

### New Capabilities

- `tui-layout-config`: TUI 棋盘视觉布局的配置数据模型，包含 `TuiCellLayout`、`TuiRect`、`TuiLayout` 三个纯数据类型，以及布局数据从 JSON/YAML 配置文件的解析

### Modified Capabilities

- `game-domain-model`: 新增 TUI 布局模型要求，`GameConfig` 增加可选的 `tui_layout` 字段
- `app-assembly`: 默认配置和配置文件加载必须支持 `tui_layout`

## Impact

- `src/richman/domain/models.py` — 新增 `TuiCellLayout`、`TuiRect`、`TuiLayout`；`GameConfig` 增加 `tui_layout` 字段
- `src/richman/domain/__init__.py` — 导出新增类型
- `src/richman/app.py` — `build_default_config()` 补默认布局；`_parse_game_config()` 解析 `tui_layout`
- `tests/test_domain_models.py` — 覆盖新增类型
- `tests/test_app.py` — 覆盖默认配置含布局、配置文件解析布局
