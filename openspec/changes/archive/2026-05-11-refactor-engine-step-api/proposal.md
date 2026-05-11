## Why

当前 `GameEngine.start()` 以同步主循环运行，并通过 renderer/player 边界阻塞等待输入；这与 `docs/TUI_DESIGN.md` 中要求的 TUI 主动驱动、阶段展示、动画停顿和按钮/鼠标输入模型不匹配。

需要将 engine 重构为统一可步进的交互核心，使 console、Textual TUI 和测试都通过同一套 `advance(input)` 流程推进游戏，保持渲染方式架构一致。

## What Changes

- **BREAKING**：`GameEngine.create(...)` 不再要求传入 renderer；engine 不再直接调用 `render_frame()`、`prompt_choice()` 或 `render_game_over()`。
- 新增 engine step API：`advance(input=None)` 返回包含 snapshot、阶段、增量事件、输入请求和终局状态的 `StepResult`。
- 新增结构化输入/请求模型，用于表达等待掷骰、动作选择、拆除目标选择和入狱判决。
- 将原同步回合流程拆成中等粒度展示点：用户输入点必须停下，骰子结果、移动、落点、抽卡、租金、破产和回合结束等关键展示点也应返回 frame。
- 保留 `start()` 作为兼容 helper，但其内部基于 step API 实现，不再维护独立规则流程。
- Console/play 入口改为 adapter/driver：渲染 `StepResult`，收集输入，再提交给 engine。
- AI 决策通过非阻塞策略在 step 流程中生成输入；人类玩家输入由 adapter 提交，不再通过 `HumanPlayer` 的阻塞输入上下文驱动 TUI。
- `GameSnapshot` 仍作为主要展示快照来源，并由 `StepResult` 携带给各类 adapter。

## Capabilities

### New Capabilities

无。该变更重构既有 engine 和 adapter 边界，不引入独立的新业务能力。

### Modified Capabilities

- `engine-core`：engine 生命周期、工厂、公开 API 和 `start()` 兼容行为改为基于 step API。
- `engine-turn-flow`：五阶段回合流程从同步执行改为可步进展示点和结构化输入驱动。
- `engine-view-generation`：snapshot/view 生成需要支持 StepResult frame 和增量事件。
- `render-adapter-architecture`：render/adapter 从被 engine 调用改为驱动 engine，console/Textual/test 使用统一交互边界。
- `player-decision-model`：AI 决策保留为策略能力；人类输入改由 adapter 结构化提交，TUI 不使用阻塞 `InputContext`。
- `app-assembly`：app/CLI 装配需要支持无 renderer 的 engine 创建和 console step driver，同时保留 `richman play` 语义。

## Impact

- 影响 `src/richman/domain`：新增 StepResult、RequiredInput、EngineInput 或等价纯数据类型。
- 影响 `src/richman/engine`：重构主循环、输入处理、事件展示点和终局处理。
- 影响 `src/richman/player`：调整人类/AI 决策边界，避免 TUI 依赖阻塞输入上下文。
- 影响 `src/richman/render` 和 console adapter：从 engine-callback 风格迁移到 step driver。
- 影响 `src/richman/app.py`、`src/richman/cli.py`：engine 装配和 `richman play` 运行方式需要更新。
- 影响测试：现有 engine/app/render/player 测试需要迁移或补充 step API 场景。
