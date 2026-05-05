## Context

`richman.app` 是模块架构中的最后一层，负责把已实现的 domain、board、player、render 和 engine 装配成可运行应用。当前 `richman play` 只启动 Textual 静态壳，不能加载游戏配置、创建玩家或启动 `GameEngine`；`docs/MODULE_DESIGN.md` 已将 app 定义为依赖所有模块但不持有游戏状态的应用入口。

现有核心模块已经通过验证，app 层应尽量薄：它只负责配置解析/默认配置、对象装配和启动流程，不复制 engine 规则，不直接修改 `InternalGameState`。

## Goals / Non-Goals

**Goals:**

- 新增 `richman.app` 应用装配模块
- 提供可测试的默认 `GameConfig` 构造函数
- 提供可测试的玩家构造函数，支持 AI 玩家数量配置
- 提供 `create_engine(...)` 装配函数，将 config、board、players、renderer、seed 串接到 `GameEngine.create`
- 提供 `run_game(...)` 高层入口，启动 engine 并返回最终 `InternalGameState`
- 更新 `richman play` 命令，使其使用 app 装配入口启动真实 engine 流程
- 保持 Textual adapter 作为独立 adapter，不把游戏装配逻辑塞进 adapter

**Non-Goals:**

- 不实现存档/读档
- 不实现外部 YAML/JSON 配置文件解析
- 不实现网络对战或多人远程输入
- 不实现完整交互式 Textual 游戏循环
- 不修改 engine、board、rules、player、render 的公共契约

## Decisions

### 1. 默认配置先使用代码构造

`build_default_config()` 直接返回 `GameConfig`，在代码中声明默认棋盘、地块和机会卡。这样可以不引入额外文件格式和解析错误面，先满足“可运行默认游戏”的目标。

**Alternatives considered**: 立即引入 YAML/JSON 配置文件。当前项目没有配置文件规范，也没有解析依赖；直接引入会扩大 app 模块范围。后续可在 app 层增加 `load_config(path)`，仍然输出同一个 `GameConfig`。

### 2. CLI 默认运行 AI 对局

`richman play` 默认创建 2 名 AI 玩家并使用 `ConsoleRenderer`。这使 CLI 可以在非交互测试中通过 `--max-turns` 限制运行，并避免当前 HumanPlayer 输入流在 Typer 测试中阻塞。

**Alternatives considered**: 默认创建 HumanPlayer。HumanPlayer 需要真实终端输入，当前 Textual adapter 尚未实现完整输入桥接，作为默认会降低可测试性。

### 3. 高层入口返回最终状态

`run_game(...)` 返回 `InternalGameState`，便于 CLI 测试和后续集成测试验证装配结果。app 层不保留状态，状态真源仍由 engine 持有。

**Alternatives considered**: `run_game()` 无返回值。无返回值更像传统 CLI，但会迫使测试绕过高层入口检查结果。

### 4. Textual adapter 暂不承载真实游戏循环

Textual adapter 继续作为展示 adapter/smoke shell 存在；本次只让 `play` 走 app + ConsoleRenderer + engine。这样 app 模块能先完成架构闭环，避免把同步 engine 循环强塞进尚未具备输入桥接的 Textual app。

**Alternatives considered**: 在 Textual app 中直接创建 engine 并运行。当前 engine 是同步循环，Textual 是事件驱动 UI，两者桥接需要额外设计，不应混入 app 最小装配变更。

## Risks / Trade-offs

- **[Risk] 默认 AI 对局可能在完整游戏结束前运行较久** → CLI 提供 `--max-turns`，测试和演示可限制回合数；真实运行可不传限制。
- **[Risk] 默认配置写在代码里不便于玩家修改** → 后续在 app 层新增配置文件加载，不影响当前 `GameConfig` 输出契约。
- **[Trade-off] `play` 先使用 ConsoleRenderer 而不是 Textual** → 换来完整 engine 流程可运行和可测试；Textual 完整交互可作为后续 adapter 变更。
