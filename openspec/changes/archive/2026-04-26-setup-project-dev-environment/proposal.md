## 为什么

项目当前已经完成游戏规则和模块设计文档，但还没有可执行的开发环境。现在建立开发环境，可以为后续实现文档中定义的 `domain`、`board`、`rules`、`engine`、`player` 和 `render` 模块提供稳定基础，并让测试与质量检查可重复执行。

渲染层需要从一开始就支持一等的 TUI 体验，同时保持可替换，使未来的 Web 渲染器能够复用同一套 engine 契约。

## 变更内容

- 创建由 `uv` 管理的 Python 项目脚手架，源码位于 `src/richman`，测试位于 `tests`。
- 在 `pyproject.toml` 中定义项目元数据、Python 版本约束、运行时依赖、开发依赖和可重复执行的质量命令。
- 增加与 `docs/MODULE_DESIGN.md` 对齐的初始模块和包结构。
- 引入 render adapter 边界，使 UI 实现只消费快照并提交用户决策，不直接修改游戏状态。
- 将 Textual 作为首个渲染实现目标，同时保留未来 Web 渲染器复用同一 engine-facing 契约的能力。
- 增加基础测试、lint、format 和类型检查配置，支撑纯 `domain`、`board`、`rules` 与状态机式 `engine` 模块开发。

## Capabilities

### New Capabilities

- `project-development-environment`: 覆盖 Python 项目脚手架、依赖管理、包布局、开发命令和质量门禁。
- `render-adapter-architecture`: 覆盖渲染器抽象、Textual TUI 作为首个 adapter、未来 Web adapter 兼容性，以及 engine/render 交互边界。

### Modified Capabilities

- 无。

## 影响

- 受影响文件和目录：`pyproject.toml`、`.python-version`、`.gitignore`、`src/richman/**`、`tests/**`，以及可选的开发文档。
- 运行时依赖：首个 TUI render adapter 使用 Textual/Rich；如需要 CLI 入口，可引入 Typer。
- 开发依赖：pytest、pytest-asyncio、Ruff 和 mypy。
- 架构影响：engine 实现应暴露基于 step 的交互点供 render adapter 驱动，而不是依赖阻塞式终端输入。
