## Context

当前项目已经完成 `domain` 模块，`GameConfig.board_cells`、`BoardCellDefinition`、`CellType` 和 `PropertyTemplate` 已经可以描述静态棋盘数据。`engine` 尚未实现，但其回合流程会依赖 `board` 提供格子查询、环形移动、起点经过次数和拆除范围候选位置。

`board` 位于架构第二层，职责是棋盘空间计算。它可以持有不可变的棋盘静态数据，但不能持有玩家、地块归属、租金、事件日志或任何运行时状态。

## Goals / Non-Goals

**Goals:**

- 提供 `richman.board` 公共 API，供后续 `engine` 使用。
- 从 `GameConfig` 创建不可变 `Board`，并在创建时校验棋盘静态配置。
- 支持格子类型查询、地块模板查询和棋盘总格数查询。
- 支持有符号步数的环形移动，并准确计算本次移动进入 START 的次数。
- 支持以中心格为基准的环形范围查询，结果稳定、去重，可直接作为拆除卡候选位置基础。
- 用单元测试覆盖移动、起点计数、反向移动、查询和范围去重。

**Non-Goals:**

- 不处理玩家位置更新、起点奖金发放、地块购买、升级、拆除或入狱状态。
- 不实现租金、卡牌、破产回收等规则逻辑。
- 不定义新的棋盘配置模型；继续复用 `domain.GameConfig` 和 `BoardCellDefinition`。
- 不引入渲染、输入、随机数或外部依赖。

## Decisions

### Decision: `Board` 是不可变静态空间对象

实现使用冻结数据结构保存 `tuple[BoardCellDefinition, ...]` 和预计算的 START 位置。创建后不允许修改棋盘格、地块模板或 START 索引。

原因是棋盘布局属于静态配置，运行时的地块归属和等级已经由 `InternalGameState.properties_by_position` 负责。把这两类数据分开，可以避免 `board` 和 `engine` 双写状态。

备选方案是让 `Board` 保存 `PropertyState` 或玩家占位信息，但这会破坏设计文档中“engine 是唯一完整状态持有者”的边界，因此不采用。

### Decision: 使用 `GameConfig` 作为创建入口

`create(config: GameConfig) -> Board` 从 `config.board_cells` 创建棋盘，不新增 `BoardConfig`。这样可以直接复用当前 `domain` 已完成的配置模型，减少多套配置对象之间的转换。

备选方案是定义独立 `BoardConfig`，但当前需求没有棋盘专属的额外字段，新增模型只会增加同步成本。

### Decision: 显式查询校验位置，移动和范围执行环形计算

`get_cell_type` 和 `get_property_template` 要求输入位置已经是有效棋盘位置；越界位置抛出 `ValueError`。`move` 的起点位置和 `get_range` 的中心位置同样先校验，随后由函数内部根据步数或半径执行环形取模。

这样可以在直接查询时尽早暴露 engine 或测试中的错误，同时保留移动和范围查询对环形棋盘的核心能力。

备选方案是所有查询都自动取模，但这会让 `get_cell_type(board, 999)` 这类调用悄悄通过，后续定位状态错误更困难。

### Decision: 起点经过次数按路径进入 START 计算

`move` 返回 `MoveResult(new_position, start_crossings)`。无论正向还是反向移动，只要路径中的某一步进入 START，就计入一次；移动开始时已经在 START 不计入；步数为 0 时不计入；正好停在 START 也计入。

这是后续 engine 发放起点奖金的唯一依据，LANDING 阶段不再重复处理 START 奖金。

### Decision: 范围查询返回稳定顺序并去重

`get_range(board, center, radius)` 返回中心格、顺时针 1..radius、逆时针 1..radius 的位置，并在环形重叠时保留首次出现的位置。半径为 0 时只返回中心格；半径覆盖超过半个棋盘时也不重复返回位置。

稳定顺序便于测试、渲染候选项和 AI 决策；去重保证拆除目标不会重复出现。

## Risks / Trade-offs

- [Risk] 配置校验过松会把非法棋盘留到 engine 阶段才暴露。→ Mitigation: 创建 `Board` 时校验非空棋盘、恰好一个 START、PROPERTY 格必须携带地块模板、非 PROPERTY 格不得携带地块模板。
- [Risk] 起点计数和 LANDING 的 START 处理重复会导致奖金翻倍。→ Mitigation: spec 明确 `start_crossings` 是奖金依据，board 只返回计数，engine 后续只消费该计数。
- [Risk] 反向移动经过 START 的边界容易出错。→ Mitigation: 单元测试覆盖从 START 出发、从 START 附近后退、跨越多圈和正好停在 START。
- [Risk] 范围查询顺序如果未定义，后续 UI/AI 测试可能不稳定。→ Mitigation: spec 固定顺序为中心、顺时针、逆时针，并要求去重。
