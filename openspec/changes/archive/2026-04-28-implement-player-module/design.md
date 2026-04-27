## Context

项目当前已实现 `domain`、`board` 和 `rules`，下一层需要补齐 `player`，为后续 `engine` 的五阶段回合流程提供统一决策边界。`docs/MODULE_DESIGN.md` 已明确 player 的定位：只负责“选什么”，不负责“怎么改状态”，且只依赖 `domain`。

当前 `domain` 已提供 `Action`、`PlayerView`、`PlayerState`、`PropertyState` 等决策所需类型。`PlayerView` 已经按 viewer 裁剪，不包含 `InternalGameState`，因此 player 模块可以在不接触完整状态树的前提下完成动作选择。

## Goals / Non-Goals

**Goals:**

- 提供 `Player` 抽象接口，覆盖掷骰等待、动作选择和拆除目标选择三个交互点。
- 提供 `HumanPlayer`，通过受限输入上下文委托终端渲染层获取用户选择。
- 提供基础 `AIPlayer`，只基于 `PlayerView`、可选动作和候选目标做确定性决策。
- 保持 player 模块无游戏状态写入能力，不能修改玩家、地块、阶段、事件日志或随机源。
- 保持 player 模块只导入 `richman.domain` 和标准库。

**Non-Goals:**

- 不实现 engine 的五阶段主循环、动作列表计算、状态修改或事件记录。
- 不实现 render 的 UI 布局、终端控件或 Textual adapter。
- 不实现复杂 AI、搜索算法、LLM 玩家或强化学习策略。
- 不新增 `Action` 枚举或修改 `PlayerView` 的数据结构。

## Decisions

### 1. Player 接口只返回决策，不执行决策

`Player.decide(view, actions, engine_context)` 返回 `Action`，`Player.choose_demolish_target(view, candidates, engine_context)` 返回目标位置，实际买地、升级、入狱、拆除和扣卡仍由 engine 执行。

理由：这符合“engine 是唯一状态写入口”的设计，避免 player 与 engine 分别修改状态导致双写不一致。

替代方案：让 HumanPlayer 或 AIPlayer 直接调用 engine API 执行动作。该方案会让 player 依赖 engine，并破坏 AI 的信息边界，因此不采用。

### 2. HumanPlayer 只通过受限上下文获取输入

HumanPlayer 不导入 render，也不持有 `InternalGameState`。它只使用 `engine_context` 或构造时注入的受限输入原语，把 `Action` 或候选位置转换为选项并接收选择结果。

理由：这样可以保留 render 可替换性，并让 HumanPlayer 在单元测试中通过 fake context 验证。

替代方案：在 player 模块直接导入 Textual 或 Rich 输入函数。该方案会把 UI 框架泄漏进 player，不符合模块依赖设计。

### 3. AIPlayer 使用简单、确定性的策略

基础 AI 不调用随机源，不读取 engine，也不依赖 board/rules。默认策略只在传入的 `actions` 中按固定优先级选择合法动作；拆除目标默认选择候选列表中的第一个位置。

理由：当前变更的目标是建立稳定边界，而不是优化 AI。确定性策略便于单元测试，也能保证后续 engine 集成时行为可预测。

替代方案：AIPlayer 自行计算地块价值、租金收益或拆除收益。该方案需要更多 board/rules/engine 上下文，会扩大 player 的依赖和职责，因此留到后续策略扩展。

### 4. 非法输入在 player 边界尽早失败

`decide` 必须只返回 `actions` 中存在的动作；`choose_demolish_target` 必须只返回 `candidates` 中存在的位置。空动作列表或空候选列表属于调用方契约错误，应抛出明确异常。

理由：engine 后续可以信任 player 返回值合法，减少执行阶段的防御性分支；同时测试能明确覆盖交互边界。

替代方案：非法输入时自动返回 `SKIP` 或 `-1`。该方案会隐藏上游状态错误，不利于定位问题，因此不采用。

## Risks / Trade-offs

- 基础 AI 策略较弱 → 通过明确标注为基础确定性策略缓解，后续可新增 `Player` 子类扩展策略。
- HumanPlayer 的输入上下文签名与未来 render 细节可能需要微调 → 通过定义最小 prompt 协议和 fake context 测试缓解，避免绑定具体 UI 框架。
- `wait_for_dice()` 在既有设计中没有 `engine_context` 参数 → 实现时可通过 HumanPlayer 构造注入等待回调，或保持无上下文 no-op，后续 engine 集成时再按实际输入流收敛；该变更不修改核心决策模型。
- player 模块无法自行判断买地、升级或拆除是否可行 → 这是刻意约束，engine 必须先计算合法 `actions` 和候选目标，再交给 player 选择。
