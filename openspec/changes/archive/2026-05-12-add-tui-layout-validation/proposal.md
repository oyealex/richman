## Why

`tui_layout` 数据模型已稳定（`add-tui-layout-config`），但当前只是纯数据承载——对自定义布局没有任何校验。未经校验的布局会导致 BoardWidget 渲染错位、position→slot 映射不可靠、格子与中心区重叠、尺寸不足时无明确错误提示。在接入 BoardWidget 渲染层之前，必须先建立校验边界，确保到达 widget 层的布局数据是合法且可渲染的。

## What Changes

- 新增 `src/richman/adapters/textual_tui/layout.py`，实现 `validate_tui_layout(config: GameConfig) -> TuiLayoutValidationResult`
- 新增 `TuiLayoutValidationResult` dataclass，包含 `errors` 和 `warnings`（warnings 字段预留给未来非阻塞提醒）
- 校验逻辑拒绝：缺失 `tui_layout`、非法网格尺寸、center 矩形非法或越界、position 缺失/重复/越界、cell 坐标与 center 重叠
- 新增 `tests/test_textual_tui_layout.py`，覆盖所有校验规则

## Capabilities

### New Capabilities

- `tui-layout-validation`: TUI 棋盘布局的校验逻辑，验证 `tui_layout` 数据合法性并提供结构化错误和警告

### Modified Capabilities

<!-- 本次变更仅包含纯校验逻辑，不涉及 adapter 接入；adapter 调用校验将在 BoardWidget/GameScreen change 中处理 -->

## Impact

- `src/richman/adapters/textual_tui/layout.py` — 新增，校验纯逻辑和返回类型
- `tests/test_textual_tui_layout.py` — 新增，覆盖各校验场景
- 不修改 domain、board、rules、player、engine 模块
- 不依赖 Textual widget、Rich renderable 或终端尺寸检测
