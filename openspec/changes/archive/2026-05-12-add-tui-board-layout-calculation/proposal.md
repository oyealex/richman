## Why

`tui_layout` 配置模型和校验层已就位，但缺少从配置生成可渲染几何信息的计算层。BoardWidget 需要知道每个 position 对应的 slot 矩形、中心区位置、所需最小终端尺寸，以及当前尺寸是否足够。这一步是纯几何计算，不依赖 Textual widget，先稳定它再写 BoardWidget 可以避免渲染与布局逻辑耦合。

## What Changes

- 在 `src/richman/adapters/textual_tui/layout.py` 扩展纯布局计算函数。
- 定义固定 cell 尺寸与间距常量。
- 新增 `TuiLayoutGeometry` dataclass，承载 position→slot 映射、center panel 矩形、最小尺寸、尺寸不足判断结果。
- 新增 `compute_layout_geometry(config, terminal_size)` 函数，输入合法 `GameConfig` 和终端尺寸，输出几何计算结果。
- 非法布局（`validate_tui_layout` 返回 errors）拒绝进入计算。
- 新增对应测试覆盖默认布局、中心区尺寸、position 映射、尺寸不足场景。

## Capabilities

### New Capabilities

- `tui-board-layout-calculation`: 根据 `TuiLayout` 计算棋盘几何信息——固定 cell 尺寸下的 position→slot 映射、center panel 矩形、最小终端尺寸、尺寸不足判断。

### Modified Capabilities

<!-- 本次不修改现有 capability 的 requirement -->

## Impact

- **新增文件**: 无（在现有 `src/richman/adapters/textual_tui/layout.py` 扩展）
- **修改文件**: `src/richman/adapters/textual_tui/layout.py`、`tests/test_textual_tui_layout.py`
- **依赖**: `richman.domain`（GameConfig, TuiLayout, TuiRect, TuiCellLayout）、`validate_tui_layout`
- **不依赖**: Textual、Rich、engine、任何 widget
