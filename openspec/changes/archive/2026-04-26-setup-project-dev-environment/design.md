## 背景

仓库当前只有规则文档和模块设计文档。还没有 Python 项目元数据、源码包、测试框架、依赖锁文件或可执行入口。

既有架构已经划分了 `domain`、`board`、`rules`、`player`、`render`、`engine` 和 `app`。新的开发环境应保留这些边界，同时将 Textual 作为首个渲染实现。render 层是一个端口，而不是应用核心：未来 Web 渲染器必须能够消费同样的游戏快照，并提交同样的用户决策。

## 目标 / 非目标

**目标：**

- 建立由 `uv` 管理的 Python 项目。
- 使用 `src/richman` 包布局，并让模块目录与 `docs/MODULE_DESIGN.md` 对齐。
- 配置可重复执行的应用运行、测试、lint、format 和类型检查命令。
- 将 Textual/Rich 作为首个 UI 栈，同时保持渲染实现可替换。
- 围绕 step-based 契约设计 engine 集成，使其可由 TUI 事件循环或未来 Web 请求/事件层驱动。
- 在领域实现开始前，提供足够的占位模块和测试来验证环境可用。

**非目标：**

- 不实现游戏规则、棋盘行为、玩家 AI 或完整 engine 主循环。
- 不构建完整 Textual UI。
- 不构建 Web 渲染器。
- 不引入持久化、网络通信、socket 多人游戏或发布打包能力。

## 决策

### 使用 `uv` 和 `pyproject.toml`

使用 `uv` 作为项目和依赖管理工具。依赖同步完成后，仓库应包含 `pyproject.toml`、`.python-version` 和 `uv.lock`。

考虑过的替代方案：

- `pip` + `requirements.txt`：更简单，但在锁文件和项目元数据工作流上较弱。
- Poetry：能力完整，但对一个小型 Python 应用来说偏重。
- Hatch：适合打包工作流，但本项目当前更需要快速本地开发和测试迭代。

### 以 Python 3.13 为基线并兼容 3.14

将 `requires-python` 设置为支持现代 Python 3.13+ 语法和类型能力。除非实施环境已经统一使用 3.14，否则本地 `.python-version` 固定为稳定的 3.13 解释器。

考虑过的替代方案：

- Python 3.11/3.12：可用范围更广，但与当前现代开发基线不够一致。
- 仅支持 Python 3.14：可行，但 3.13 基线能降低依赖兼容性风险，同时仍允许使用 3.14。

### 保持 `render` 为端口，并将 Textual 放入 adapter 包

创建独立于 Textual 实现的 render-facing 契约模块。建议结构如下：

```text
src/richman/
  domain/
  board/
  rules/
  player/
  engine/
  render/
    __init__.py
    ports.py
  adapters/
    textual_tui/
      __init__.py
      app.py
      widgets/
  cli.py
```

`render` 契约应描述 render adapter 如何接收 `GameSnapshot` 数据并提交决策。Textual 专属的 widget、CSS、快捷键绑定和 screen 组合应保留在 `adapters/textual_tui` 内部。

考虑过的替代方案：

- 将 Textual 直接放入 `render`：初期简单，但后续难以干净地增加 Web renderer。
- 先保留纯 CLI `render`：依赖更少，但与“一开始就构建 TUI”的决策冲突。

### engine 集成采用 step-based 方式而不是阻塞式方式

未来 engine 应暴露面向 step 的交互边界，而不是一个直接调用终端 prompt 的阻塞式 `start()` 循环。render adapter 应能通过购买、升级、使用卡牌、跳过或选择拆除目标等决策来驱动 engine。

预期形态如下：

```text
Render Adapter
  receives GameSnapshot / DecisionRequest
  emits PlayerDecision
        |
        v
GameController
  calls Engine.step(decision)
  handles AI auto-decisions
  publishes next snapshot/request
        |
        v
Engine
  owns InternalGameState mutations
```

具体类名可在实施时细化，但边界方向必须保持不变：render 读取快照并提交决策；engine 拥有状态变更权。

考虑过的替代方案：

- 让 `HumanPlayer` 继续负责阻塞式 prompt：适合简单 CLI，但不适合 Textual 和 Web。
- 让 Textual 直接修改 `InternalGameState`：原型更快，但违反文档中“单一状态所有者”的规则。

### 从一开始支持 Textual app 测试

加入 pytest 和 `pytest-asyncio`，让 Textual app 测试可以在 headless 模式下使用 `App.run_test()` 和 pilot 交互。

考虑过的替代方案：

- 仅手动测试 TUI：一旦用户操作会影响游戏状态，这种方式就不够可靠。
- 立即引入 snapshot testing：后续有价值，但对初始环境偏重。

## 风险 / 取舍

- Textual 引入 async/event-loop 约束 -> 尽量保持 engine 逻辑同步且纯粹；将 async 行为隔离在 adapter/controller 层。
- Adapter 抽象可能过早过度设计 -> 只定义首个 TUI 所需的最小 snapshot/request/decision 契约。
- 未来 Web 需求可能与 TUI 不同 -> 在边界上使用普通领域数据结构，避免 engine-facing 契约出现 Textual/Rich 类型。
- Python 版本漂移可能阻碍部分机器搭建环境 -> 使用 3.13 作为基线，并允许可用环境使用 3.14。
- UI 测试可能变慢或变脆弱 -> 优先覆盖 domain、board、rules 和 controller 测试；Textual pilot 测试只覆盖关键交互。

## 迁移计划

1. 增加项目元数据和依赖配置。
2. 创建包骨架和占位入口。
3. 增加质量命令配置。
4. 增加包导入、CLI 入口和 Textual app 构造的最小 smoke tests。
5. 运行 `uv sync`、`uv run pytest`、`uv run ruff check`、`uv run ruff format --check` 和 `uv run mypy src`。

在游戏实现开始前回滚很简单：删除脚手架文件和锁文件，然后用修订后的选择重新运行 OpenSpec 任务。

## 待确认问题

- 本仓库本地 `.python-version` 应固定为 `3.13` 还是 `3.14`？
- 是否立即引入 Typer 支持 `richman play`，还是首个可执行入口只使用 `python -m richman`？
- 初始 Textual adapter 只需要构造 smoke test，还是也需要使用 `App.run_test()` 做最小渲染测试？
