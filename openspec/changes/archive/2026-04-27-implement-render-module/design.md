## Context

项目当前已完成 `domain`、`board`、`rules` 和 `player`，下一步需要补齐 `render`，为后续 `engine` 提供展示与人类输入边界。`docs/MODULE_DESIGN.md` 明确 render 的定位是“纯展示 + 输入”，只依赖 `domain`，接收 `GameSnapshot`，不能主动访问或修改 `InternalGameState`。

当前 `src/richman/render/ports.py` 仍使用 `GameSnapshotView`、`DecisionRequest`、`PlayerDecision` 等占位类型，Textual TUI smoke test 也基于这些占位类型构造。由于 `domain` 已经实现 `GameSnapshot`、`GameEvent`、`PlayerState`、`PropertyState`、公开棋盘和公开玩家视图，本变更应将 render 边界收敛到真实领域模型，同时保留 Textual adapter 的隔离性。

## Goals / Non-Goals

**Goals:**

- 提供 `Renderer` 协议或等价边界，覆盖 `render_frame`、`render_event_log`、`prompt_choice`、`prompt_number` 和 `render_game_over`。
- 让 `richman.render` 公共 API 直接消费 `domain.GameSnapshot` 和 `GameEvent`，不再要求 engine 适配占位视图。
- 提供一个标准库实现，用于当前终端展示、测试和后续 HumanPlayer 输入上下文集成。
- 在 render 层对事件日志做 viewer 级隐私遮蔽，避免展示其他玩家现金、手牌数量、地块购买价和累计升级投入。
- 更新 Textual TUI adapter，使 Textual/Rich 专属类型只留在 `richman.adapters.textual_tui` 内部，并继续支持 headless smoke test。
- 增加测试覆盖公共 API、依赖边界、快照展示、事件遮蔽、输入校验和 Textual adapter 构造。

**Non-Goals:**

- 不实现 engine 五阶段主循环、状态修改、事件生成或 `snapshot_for`。
- 不修改 `domain.GameSnapshot`、`GameEvent` 或玩家/地块状态模型。
- 不实现完整交互式 Textual 游戏循环；Textual adapter 只需要能消费快照并在测试中构造展示。
- 不引入新的 UI 框架、网络传输层或异步 request/response controller。
- 不改变 player 决策策略；HumanPlayer 仍只通过受限输入上下文获取选择。

## Decisions

### 1. render 核心直接使用 domain 视图模型

`render_frame(snapshot)` 接收 `domain.GameSnapshot`，`render_event_log(events, viewer_index)` 接收 `GameEvent` 序列。render 模块不再定义平行的 `GameSnapshotView` 来复制回合、阶段、棋盘、玩家或私有信息。

理由：`GameSnapshot` 已经是 engine 面向 render 生成的只读展示快照，继续使用占位视图会造成额外映射层，并增加后续 engine 集成成本。

替代方案：保留 `GameSnapshotView` 作为 render 自己的视图模型，由 engine 或 adapter 映射。该方案适合复杂 UI 布局，但当前模块设计要求 render 直接接收 `GameSnapshot`，因此不采用。

### 2. `Renderer` 协议加标准库默认实现

render 模块提供 `Renderer` 协议，并提供标准库实现（例如 `ConsoleRenderer` 或等价实现）。包级 `render_frame`、`render_event_log`、`prompt_choice`、`prompt_number`、`render_game_over` 可以委托默认 renderer，方便 engine 早期集成和单元测试。

理由：协议让 Textual 或未来 Web adapter 可以替换实现；标准库默认实现避免 render 模块只剩抽象，后续 engine 可以先以同步终端方式跑通。

替代方案：只提供协议，不提供默认实现。该方案会让 engine/app 在初期必须先完成 adapter 装配，延迟集成反馈，因此不采用。

### 3. 事件日志采用保守遮蔽策略

render 不应假定 `GameEvent.data` 中所有字段都能直接展示。实现时应通过小型格式化/遮蔽辅助函数处理事件数据：公开字段可以展示；现金余额、手牌数量、购买价、累计升级投入、回收金额等私密字段仅在事件明确属于当前 viewer 时展示，否则以“已隐藏”或不展示替代。

理由：engine 可以完整记录事件以便调试和回放，但 render 是用户可见边界，必须按 viewer 保护信息可见性。

替代方案：要求 engine 在生成 `GameSnapshot.event_log` 前完成全部遮蔽。该方案能简化 render，但会把展示策略推回 engine，并削弱 render 作为展示边界的职责；后续 engine 仍可预处理事件，但 render 必须保留最后一道遮蔽。

### 4. 输入原语负责合法性校验

`prompt_choice(question, options)` 在进入交互前拒绝空选项，并保证返回值来自 `options`；`prompt_number(question, min_value, max_value)` 拒绝非法范围，并保证返回边界内整数。具体实现可以接受 1-based 序号或精确文本，但返回值必须是原始合法选项或合法整数。

理由：HumanPlayer 和 engine context 可以信任 render 输入结果合法，避免在动作执行阶段重复处理 UI 输入错误。

替代方案：让 render 返回任意字符串，由 player 或 engine 再校验。该方案会扩大调用方防御逻辑，并让 UI 错误更晚暴露，因此不采用。

### 5. Textual adapter 只做适配和展示

Textual TUI adapter 可以把 `GameSnapshot` 转成 Panel、Static、Widget 等 Textual/Rich 对象，但这些类型不能出现在 `richman.render` 的 engine-facing API 中。adapter 构造应允许传入快照，也允许在无快照时构造一个最小示例快照或空展示，以便 headless smoke test 不启动真实终端会话。

理由：这延续现有 `render-adapter-architecture` 规格：Textual 是首个实现，但不能污染 domain、render、player 或 engine 边界。

替代方案：把 Textual app 直接做成 `Renderer` 的唯一实现。该方案会让 engine 早期集成依赖 Textual 事件循环，也不利于单元测试，因此不采用。

## Risks / Trade-offs

- `GameEvent.data` 是开放映射，字段语义可能不统一 → 采用保守遮蔽和集中格式化辅助函数，未知字段默认不展示或只展示安全字符串。
- 标准库默认 renderer 的界面不会像 Textual 一样丰富 → 该实现只承担可运行边界和测试目标，复杂布局留给 Textual adapter。
- 包级默认函数可能隐藏 renderer 注入点 → 同时导出 `Renderer` 协议和具体实现，engine 后续可以通过依赖注入使用 adapter 实例。
- Textual adapter 从占位类型迁移到 `GameSnapshot` 会影响现有 smoke test → 同步更新测试 fixture，确保 headless 构造仍通过。
- render 负责最后一道事件遮蔽可能与 engine 未来预遮蔽重复 → 允许重复遮蔽，隐私安全优先于少量展示逻辑重复。
