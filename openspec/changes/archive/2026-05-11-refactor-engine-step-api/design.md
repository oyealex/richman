## Context

当前 engine 以同步 `start()` 主循环为中心，内部直接调用 renderer 展示 frame、通过 player/HumanPlayer 阻塞获取掷骰和动作输入，并在终局时调用 renderer 展示胜者。这种模式适合早期 console，但不适合 Textual TUI 的事件循环：TUI 需要主动驱动游戏、在关键展示点暂停、播放短动画，并通过按钮、快捷键和鼠标提交结构化输入。

`docs/TUI_DESIGN.md` 已确定新的架构方向：Engine 不直接调用 Renderer，也不阻塞等待输入；Console、TUI、测试都通过同一套 step API 驱动 Engine。该设计需要同时调整 domain 数据结构、engine 回合状态机、player 决策边界、render adapter 关系和 app/CLI 装配方式。

## Goals / Non-Goals

**Goals:**

- 提供统一 `GameEngine.advance(input=None) -> StepResult`，让所有 adapter 一致驱动游戏。
- Engine 保持唯一状态写入者，但不再依赖 renderer 或终端输入。
- 将五阶段回合流程拆成中等粒度 step：所有输入点停下，关键展示点返回 frame。
- 保留 `GameEngine.start()` 作为兼容 helper，内部基于 step API 实现。
- 保留 `richman play` 现有用户语义，内部迁移为 console step driver。
- 让测试可以直接提交结构化输入并断言 StepResult、snapshot 和事件。

**Non-Goals:**

- 不实现完整 Textual TUI 棋盘、弹窗、toast 或 `tui_layout`。
- 不改变游戏规则本身：购买、升级、租金、破产、入狱、卡牌效果仍保持原语义。
- 不引入外部事件循环框架或异步运行时依赖。
- 不在 adapter 层复制 engine 规则。

## Decisions

### 1. Engine 使用统一 step API，而不是 renderer callback

`GameEngine.advance(input=None)` 是新的主要交互入口。它返回 `StepResult`，包含当前 snapshot、新增事件、当前阶段、可选输入请求和终局信息。

理由：

- TUI 可以在主线程事件循环中驱动 engine，不需要后台线程等待旧同步 loop。
- Console 和测试可复用同一交互协议。
- Engine 依赖方向更清楚：只依赖 domain/board/rules/player 策略，不依赖 render I/O。

备选方案是保留同步 engine，用后台 worker 和输入队列桥接 TUI。该方案侵入少，但会让动画和输入时机受旧 render hook 限制，并引入线程复杂度。

### 2. Step 粒度采用中等粒度

Engine 必须在以下节点返回 StepResult：

- 需要外部输入：等待掷骰、动作选择、拆除目标选择、入狱判决。
- 关键展示点：回合开始、监狱倒计时、骰子结果、玩家移动、落点、抽卡、租金支付、破产、动作执行、回合结束、游戏结束。

普通内部计算不必拆成独立 step。

理由：

- 既满足 TUI 展示和动画需求，又避免状态机被拆得过碎。
- 每个 StepResult 都可测试，且与事件日志天然对应。

### 3. 结构化输入替代阻塞 HumanPlayer 输入

新增 `RequiredInput` 和 `EngineInput` 或等价类型：

- `ROLL_DICE`
- `ACTION_CHOICE`
- `DEMOLISH_TARGET`
- `JAIL_CHOICE`

人类输入由 adapter 根据 `RequiredInput` 收集并提交。AI 仍可使用 `AIPlayer` 策略，但由 engine 或 driver 在收到 AI 当前玩家的输入请求时非阻塞地产生 `EngineInput`。

理由：

- HumanPlayer 的阻塞 `InputContext` 与 TUI 不兼容。
- AI 决策仍属于 player 策略能力，保持可测试和可替换。

### 4. Engine 内部维护推进游标

为支持中断和恢复，engine 需要维护当前 step 所处的内部控制状态。实现方式可以是显式枚举状态，例如：

- `READY_TO_START_TURN`
- `WAITING_FOR_ROLL`
- `SHOWING_DICE_RESULT`
- `SHOWING_MOVE`
- `PROCESSING_LANDING`
- `WAITING_FOR_ACTION`
- `WAITING_FOR_DEMOLISH_TARGET`
- `WAITING_FOR_JAIL_CHOICE`
- `SHOWING_TURN_END`
- `GAME_OVER`

这些内部状态不必全部暴露到 domain，但 StepResult 必须暴露稳定的 `Phase`、snapshot、events 和 required_input。

理由：

- 显式状态比生成器/协程更容易序列化、调试和单元测试。
- 不需要引入 async runtime。

### 5. `start()` 作为兼容 helper

`start(max_turns=None)` 继续返回 `InternalGameState`。它内部循环调用 `advance()`，当遇到人类输入请求时通过一个 console/headless driver 或兼容输入 provider 提交输入。

如果调用方没有提供可满足人类输入的 provider，`start()` 只能用于 AI-only 或测试预置输入场景；现有 `run_game()` 创建的默认 AI 对局应保持可运行。

理由：

- 降低迁移风险。
- 旧测试可以逐步迁移到 step API。

### 6. 事件增量由 StepResult 暴露

StepResult 应包含本次 step 新增事件，而 snapshot 仍包含完整 event_log。Adapter 展示最新事件提示时可直接用增量事件，事件日志 modal 可用 snapshot 的完整日志。

理由：

- 避免 adapter 自己比较 event_log 长度。
- 保持 GameSnapshot 兼容现有 render 格式化逻辑。

## Risks / Trade-offs

- [Risk] 状态机拆分后容易遗漏原同步流程中的清理逻辑。 → Mitigation: 以现有 `_process_turn()` 为行为基准，逐段迁移并为每个阶段补 step 测试。
- [Risk] `start()` 兼容层与 `advance()` 产生两套流程。 → Mitigation: `start()` 只能调用 `advance()`，不得直接调用旧私有阶段方法。
- [Risk] AI 自动输入放在 engine 还是 driver 中可能边界不清。 → Mitigation: 先保留 AI 策略在 player 模块，engine/driver 只调用策略生成合法 EngineInput，不让 adapter 修改状态。
- [Risk] 现有 render `Renderer` 协议仍包含 prompt API，与新边界重叠。 → Mitigation: 本次不要求删除所有旧 API，但 engine 不再依赖它；后续可单独清理 render 兼容 API。
- [Risk] 修改跨 domain/engine/player/render/app 多模块，回归面大。 → Mitigation: 先迁移 console AI-only 路径，确保 `richman play` 和现有规则测试通过，再增加 TUI 使用点。

## Migration Plan

1. 在 domain 中新增 step/input 相关纯数据类型。
2. 重构 `GameEngine.create` 去除 renderer 依赖，初始化 step 游标。
3. 将 `_process_turn()` 的逻辑拆入可恢复的 step 状态机。
4. 实现输入校验：无输入时返回 RequiredInput，有输入时验证 player_index、kind、action/target 合法性。
5. 将 AI 决策接入 required input 处理，支持 AI-only 对局自动推进。
6. 将 `start()` 改为基于 `advance()` 的兼容循环。
7. 将 app/CLI 的 console 运行路径改为 step driver，并保持 `richman play` 行为。
8. 更新现有测试，并新增 StepResult 场景测试。

## Open Questions

- `StepResult` 是否需要显式 `display_kind` 区分同一 `Phase` 下的不同展示点，还是仅依赖事件类型和 phase。
- `start()` 在遇到真实 HumanPlayer 输入请求时是否保留旧阻塞行为，还是明确只支持 AI-only/预置输入。
- `Renderer` 协议中的 `prompt_choice`、`prompt_number` 是否在本次变更中标记为 legacy，还是留到后续 render 清理变更处理。
