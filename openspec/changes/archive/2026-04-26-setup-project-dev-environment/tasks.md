## 1. 项目元数据与依赖

- [x] 1.1 创建 `pyproject.toml`，包含项目元数据、`requires-python >=3.13`、包配置和命令/工具配置。
- [x] 1.2 增加 Textual、Rich 以及可选 CLI 入口支持所需的运行时依赖。
- [x] 1.3 增加 pytest、pytest-asyncio、Ruff 和 mypy 开发依赖。
- [x] 1.4 增加 `.python-version`，并更新 `.gitignore` 以覆盖 Python、uv、virtualenv、缓存和测试产物。
- [x] 1.5 使用 `uv` 运行依赖同步，并生成 `uv.lock`。

## 2. 包骨架

- [x] 2.1 创建 `src/richman`，包含包初始化和应用元数据。
- [x] 2.2 创建 `domain`、`board`、`rules`、`player`、`engine` 和 `render` 模块包。
- [x] 2.3 创建 `src/richman/render/ports.py`，包含最小的、框架无关的 snapshot、decision request 和 player decision 占位契约。
- [x] 2.4 创建 `src/richman/cli.py` 和/或 `src/richman/__main__.py` 作为初始可执行入口。

## 3. Textual Render Adapter

- [x] 3.1 创建 `src/richman/adapters/textual_tui`，包含最小 Textual app shell。
- [x] 3.2 将 Textual、Rich renderable、CSS、widget 和快捷键绑定保留在 Textual adapter 包内部。
- [x] 3.3 将初始 app shell 连接到占位 render-port 数据，且不导入 engine 内部实现。
- [x] 3.4 确保 Textual app 可以在 headless 测试中构造，且不会启动阻塞式终端会话。

## 4. 测试与质量配置

- [x] 4.1 增加 smoke tests，证明 `richman` 包和计划中的模块包都可以导入。
- [x] 4.2 为可执行入口增加 smoke test。
- [x] 4.3 使用 pytest-asyncio 增加异步 Textual app 构造测试。
- [x] 4.4 在 `pyproject.toml` 中配置 pytest、pytest-asyncio、Ruff 和 mypy。
- [x] 4.5 运行 `uv run pytest`。
- [x] 4.6 运行 `uv run ruff check`。
- [x] 4.7 运行 `uv run ruff format --check`。
- [x] 4.8 运行 `uv run mypy src`。
