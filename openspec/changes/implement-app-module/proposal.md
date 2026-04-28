## Why

当前核心模块 domain、board、rules、player、render、engine 已实现，但应用入口仍只是一个 Textual 静态展示壳，无法把配置、棋盘、玩家、渲染器和引擎装配成一局可运行游戏。现在需要实现 app 装配层，完成 `docs/MODULE_DESIGN.md` 中定义的最后一层，让 `richman play` 能启动真实游戏流程。

## What Changes

- 新增 `richman.app` 模块，负责加载默认游戏配置、创建棋盘、创建玩家、初始化 renderer，并启动 `GameEngine`
- 提供默认游戏配置构造能力，包含可运行的棋盘布局、地块模板、机会卡组和游戏参数
- 提供玩家装配能力，支持按数量创建 AI 玩家，并保留后续接入 HumanPlayer 的边界
- 修改 CLI 的 `play` 命令，使其走 app 装配层启动 engine，而不是只启动静态 Textual shell
- 保留 Textual adapter 的 headless smoke 能力，不把完整游戏逻辑放入 adapter

## Capabilities

### New Capabilities

- `app-assembly`: 应用入口装配配置、board、players、renderer 和 engine，并启动一局游戏

### Modified Capabilities

无。app 消费已有模块公共 API，不修改现有模块的行为要求。

## Impact

- 新增 `src/richman/app.py`
- 更新 `src/richman/cli.py`，让 `richman play` 调用 app 装配入口
- 可能更新 `docs/DEVELOPMENT_PROGRESS.md` 记录 app 模块进度
- 新增或更新 `tests/test_app.py`、`tests/test_cli.py`
- 依赖现有 `domain`、`board`、`player`、`render`、`engine` 公共 API，不新增第三方依赖
