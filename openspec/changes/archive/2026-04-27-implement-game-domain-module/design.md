## Context

`docs/MODULE_DESIGN.md` 将 `domain` 定位为整个终端大富翁项目的地基：它只定义所有模块共享的类型、枚举、数据结构、配置和常量，不包含计算逻辑、状态修改或 I/O。当前仓库已有 `src/richman/domain` 包骨架，其他模块也已预留包位置；`render.ports` 里存在临时的 `GameSnapshotView` 占位类型，后续应由正式 domain 快照模型承接 engine-facing 数据结构。

本变更需要先落地 domain 模块，使 board、rules、player、engine、render 可以在后续变更中基于同一组领域对象协作。实现必须遵守现有 Python 项目约束：Python 3.13、`src/richman` 包布局、mypy strict-ish 配置、Ruff 格式和 lint 规则。

## Goals / Non-Goals

**Goals:**

- 在 `richman.domain` 中提供 `docs/MODULE_DESIGN.md` 描述的共享领域模型。
- 保持 domain 只依赖 Python 标准库，不导入 board、rules、player、engine、render 或 adapter 模块。
- 使用明确、可类型检查的数据结构表达棋盘模板、卡片定义、玩家状态、动作、阶段、事件、回收方案、内部状态、对外快照和游戏配置。
- 为后续模块提供稳定的导出 API，并通过测试锁定关键结构约束。

**Non-Goals:**

- 不实现棋盘移动、租金计算、卡牌解析、破产计算、回合推进、渲染或玩家决策逻辑。
- 不在本变更中替换 Textual adapter 的展示实现，也不要求 render 立即消费完整 `GameSnapshot`。
- 不引入运行时第三方依赖或配置文件加载机制。
- 不在 domain 层强制执行所有游戏规则校验；规则合法性由 board/rules/engine 在后续模块中处理。

## Decisions

### 使用标准库 dataclass、Enum 和类型别名实现模型

采用 `@dataclass(slots=True)` 表达结构化数据，模板类和配置类使用 `frozen=True`，运行时状态类保持可变以匹配 `InternalGameState` 由 engine 唯一写入的设计。枚举使用 Python 标准库 `Enum`，不引入 Pydantic、attrs 或 msgspec。

替代方案是使用 Pydantic 或 attrs 获得更强校验与转换能力，但这会给零依赖 domain 层增加额外运行时依赖，也会把配置解析和校验问题提前放进领域模型。当前阶段更需要轻量、稳定、易测试的类型基础。

### 将带载荷的卡牌意图建模为冻结 dataclass 联合

`CardIntent` 在模块设计中表示 rules 解析卡牌后返回的效果意图，其中 `GrantMoney(amount)`、`Move(direction, min_steps, max_steps)` 等都需要携带参数。Python `Enum` 不适合承载这些不同形状的载荷，因此实现上使用 `GrantMoneyIntent`、`DeductMoneyIntent`、`MoveIntent`、`GoToJailIntent`、`ObtainCardIntent` 等冻结 dataclass，并用 `CardIntent` 类型别名汇总。

替代方案是定义一个通用 `CardIntent` dataclass 加 `kind` 字段和若干可选字段。该方案字段更松散，mypy 难以帮助调用方收窄类型，也更容易构造出无效组合。

### 区分模板、运行时状态和视图数据

`PropertyTemplate`、`CardDefinition`、`GameConfig` 表示不可变配方或配置；`PropertyState`、`PlayerState`、`InternalGameState` 表示 engine 持有的运行时状态；`PlayerView`、`GameSnapshot` 和公开信息对象表示裁剪后的读模型。`players[].holdings` 只保存 `PropertyRef`，不复制等级、归属、购买价或升级投入等可变地块字段。

替代方案是让 `PlayerState` 直接包含完整 `PropertyState` 副本。这样读取方便，但会制造多个可变真源，后续购买、升级、拆除和破产回收都更容易出现不一致。

### 事件采用通用事件类型加结构化 payload

domain 定义 `GameEventType` 枚举和 `GameEvent` 数据结构，`GameEvent.data` 使用 `Mapping[str, object]` 承载不同事件的字段。事件类型列表来自 `docs/MODULE_DESIGN.md`，具体事件产生和隐私遮蔽由 engine/render 后续负责。

替代方案是为每种事件定义独立 dataclass。它的类型精度更高，但事件数量较多，当前 domain 先落地基础模型时会引入大量样板；通用事件结构足以支撑日志、测试和后续迭代。

### 对外 API 集中从 `richman.domain` 导出

实现可以拆分到子文件以保持可读性，但 `richman.domain` 必须重新导出公共类型，便于后续模块使用 `from richman.domain import PlayerState, Action`。这降低跨模块导入路径的耦合，也让 domain API 更清晰。

替代方案是要求调用方导入 `richman.domain.state`、`richman.domain.cards` 等内部路径。该方式文件边界清楚，但会把内部组织泄露给所有模块，后续重组成本更高。

## Risks / Trade-offs

- [Risk] domain 模型过早固定，后续 engine 实现时发现字段不足或命名不顺手。→ Mitigation：优先覆盖模块设计中明确列出的字段，保持结构简单；后续通过 OpenSpec 变更演进 API。
- [Risk] `GameEvent.data: Mapping[str, object]` 类型较宽，无法在静态类型层验证每类事件 payload。→ Mitigation：先用 `GameEventType` 锁定事件名，事件 payload 的强约束留给 engine 事件工厂或后续专门变更。
- [Risk] dataclass 可变状态对象可能被非 engine 模块误改。→ Mitigation：domain 只提供类型；后续通过模块依赖、视图裁剪和测试确保 board/rules/player/render 不接收 `InternalGameState`。
- [Risk] 当前 render 占位 `GameSnapshotView` 与新 `GameSnapshot` 并存一段时间。→ Mitigation：本变更保持兼容，后续 render/engine 集成变更再替换 adapter-facing 类型。

## Migration Plan

1. 在 `src/richman/domain` 中新增或重组领域模型实现，并从 `richman.domain` 统一导出。
2. 增加 domain 单元测试，覆盖枚举、常量、不可变配方、运行时状态引用和快照/视图结构。
3. 保持现有 CLI、Textual smoke test 和 render 占位契约可用。
4. 运行 `uv run pytest`、`uv run ruff check`、`uv run ruff format --check` 和 `uv run mypy src` 验证变更。

回滚策略：若后续发现 domain API 不适合实现，可在尚未被其他新模块广泛依赖前通过一次 OpenSpec 修改调整模型；本变更不涉及数据迁移或持久化格式。

## Open Questions

- `GameEvent.data` 是否需要在 engine 落地后升级为逐事件 dataclass。
- `GameSnapshot` 与现有 `render.ports.GameSnapshotView` 的替换节奏由后续 render/engine 集成变更决定。
