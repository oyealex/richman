# project-development-environment Specification

## Purpose
TBD - created by archiving change setup-project-dev-environment. Update Purpose after archive.
## Requirements
### Requirement: uv-managed Python project

仓库 SHALL 定义一个由 `uv` 管理的 Python 项目，包含项目元数据、Python 版本约束、运行时依赖、开发依赖，以及由依赖同步生成的锁文件。

#### Scenario: 项目元数据存在

- **WHEN** 开发环境脚手架创建完成
- **THEN** 仓库包含带有项目元数据和 Python 版本要求的 `pyproject.toml`

#### Scenario: 依赖可以同步

- **WHEN** 开发者运行 `uv sync`
- **THEN** `uv` 创建或更新项目虚拟环境和锁文件，且不需要临时手动安装依赖

### Requirement: Source and test layout

仓库 SHALL 使用 `src/richman` 包布局和顶层 `tests` 目录，并与文档中的模块边界保持一致。

#### Scenario: 包模块可以导入

- **WHEN** 开发环境同步完成
- **THEN** 测试可以基于已配置的项目布局导入 `richman` 包

#### Scenario: 模块骨架遵循设计

- **WHEN** 检查脚手架结构
- **THEN** 它包含 domain、board、rules、player、engine、render 契约和应用入口的包位置

### Requirement: Repeatable developer commands

项目 SHALL 通过 `uv run` 提供可重复执行的测试、lint、格式检查和类型检查命令。

#### Scenario: 通过 uv 运行测试

- **WHEN** 开发者运行 `uv run pytest`
- **THEN** pytest 发现并执行测试套件

#### Scenario: 通过 uv 运行 lint 和格式检查

- **WHEN** 开发者运行 `uv run ruff check` 和 `uv run ruff format --check`
- **THEN** Ruff 对已配置的源码和测试文件执行 lint 与格式规则检查

#### Scenario: 通过 uv 运行类型检查

- **WHEN** 开发者运行 `uv run mypy src`
- **THEN** mypy 使用项目配置对源码包执行类型检查

### Requirement: TUI-ready development dependencies

项目 SHALL 包含构建和测试 Textual TUI 所需的依赖，同时不将核心游戏模块耦合到 Textual。

#### Scenario: 运行时 UI 依赖可用

- **WHEN** 开发环境同步完成
- **THEN** Textual 和 Rich 可供 TUI adapter 实现使用

#### Scenario: 支持异步 UI 测试

- **WHEN** 增加 Textual app 测试
- **THEN** pytest 支持 `App.run_test()` 风格测试所需的异步测试执行

