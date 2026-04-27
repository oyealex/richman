## Context

当前项目已经完成 `domain` 模块和 `board` 模块。`domain` 提供 `PropertyTemplate`、`PropertyState`、`CardDefinition`、`CardIntent`、`ReclaimPlan` 等共享类型；`board` 提供空间查询、环形移动和拆除范围查询。后续 `engine` 会持有并修改完整状态树，但它需要一个独立的 `rules` 层来完成纯规则计算。

`rules` 位于架构第二层，职责是游戏规则计算。它不持有状态，不调用 `board`、`player`、`engine`、`render` 或 adapter，不执行随机抽卡、随机步数、玩家决策、事件记录、状态修改或 I/O。

## Goals / Non-Goals

**Goals:**

- 提供 `richman.rules` 公共 API，供后续 `engine` 在回合流程中复用。
- 实现租金计算、升级可行性判断、卡牌意图解析、破产回收方案计算和支付能力判断。
- 保持所有 rules API 为纯函数：输入相同则输出相同，不修改传入对象，不读写外部状态。
- 对规则边界做显式处理，非法等级、非法金额、缺少必要参数的卡牌定义应尽早报错。
- 用单元测试覆盖正常路径、边界值、错误输入和模块依赖边界。

**Non-Goals:**

- 不实现抽卡随机性；engine 从配置卡堆中随机抽取卡片。
- 不实现移动随机步数；engine 根据 `MoveIntent` 的方向和步数范围决定具体移动。
- 不执行卡牌效果；rules 只返回 `CardIntent`。
- 不修改玩家现金、手牌、地块等级、地块归属、事件日志或破产状态。
- 不判断购买和升级动作是否应该出现；engine 负责结合位置、归属、现金和 rules 结果生成动作列表。
- 不引入外部依赖、配置加载、渲染或输入逻辑。

## Decisions

### Decision: rules API 全部设计为纯函数

`calculate_rent`、`can_upgrade`、`resolve_card_intent`、`calculate_bankruptcy` 和 `can_afford` 都只根据入参返回结果，不写入 `InternalGameState`、`PlayerState` 或 `PropertyState`。

原因是设计文档明确要求 engine 是唯一状态写入口。rules 只提供可测试的计算单元，可以被 engine、测试或未来 AI 评估逻辑重复调用，而不会产生隐藏副作用。

备选方案是让 rules 直接扣款、升级或修改手牌，但这会让状态变更分散到 engine 之外，破坏事件记录和隐私裁剪的一致性，因此不采用。

### Decision: 卡牌解析返回 domain 中的结构化 intent

`resolve_card_intent(card: CardDefinition) -> CardIntent` 将卡片配方映射为 `GrantMoneyIntent`、`DeductMoneyIntent`、`MoveIntent`、`GoToJailIntent` 或 `ObtainCardIntent`。金钱卡和移动卡必须携带对应参数；免狱卡和拆除卡统一返回 `ObtainCardIntent`。

原因是卡牌解析和卡牌执行要分离：rules 知道卡牌描述的效果类型，engine 才知道当前玩家、棋盘位置、随机源、事件日志和入狱交互。

备选方案是返回字符串或字典，但 domain 已经定义了结构化 intent 类型，直接使用这些类型可以让后续 engine 和测试获得更稳定的类型契约。

### Decision: 升级判断只处理等级上限，不处理现金

`can_upgrade(template, property_state)` 只根据地块当前等级和模板租金等级数量判断是否还能升级。现金是否足够支付 `template.upgrade_cost` 由 engine 通过 `can_afford` 组合判断。

原因是升级动作可用性由多个条件组成：玩家是否停在自己的地块、是否未入狱、是否有现金、地块是否未满级。rules 只负责其中可独立判断的等级规则，避免拿到不必要的玩家状态。

备选方案是把现金也传入 `can_upgrade`，但这会让函数职责和 `can_afford` 重叠，因此不采用。

### Decision: 破产回收只生成计划，不执行回收

`calculate_bankruptcy(properties, shortfall)` 按 `PropertyState.acquired_at` 从早到晚排序，逐个计算退款 `purchase_price + upgrade_invested`，直到覆盖缺口或地块耗尽，并返回 `ReclaimPlan`。如果获取时间相同，保持传入列表中的相对顺序。

原因是回收动作涉及删除玩家持有引用、清空地块归属、记录 `PROPERTY_RECLAIMED`、判断最终破产和清理手牌，这些都属于 engine 的状态写入和事件职责。rules 只提供确定性的回收计划。

备选方案是让 rules 返回新的玩家状态和地块状态副本，但当前架构没有不可变状态树，复制会增加复杂度，也容易让 engine 与 rules 对状态来源产生分歧。

### Decision: 非法规则输入显式拒绝

租金等级必须落在 `PropertyTemplate.rents` 的有效索引内；升级等级不能为负，且满级地块不可升级；金额和资金缺口不能为负；卡牌定义缺少对应字段或移动步数范围非法时应抛出 `ValueError`。

原因是 domain 数据类本身只承载数据，不做完整业务校验。rules 是这些数据进入 engine 执行前的规则边界，应尽早暴露配置或调用错误。

备选方案是对非法输入返回默认值，例如租金返回 0 或卡牌返回空意图，但这会掩盖配置错误，让 engine 在更远的位置出现难以定位的问题。

## Risks / Trade-offs

- [Risk] rules 对非法输入过于宽松会把坏配置留到 engine 阶段才暴露。→ Mitigation: 在租金、升级、卡牌解析、支付和破产计算入口添加边界校验，并用单元测试覆盖。
- [Risk] rules 过度参与动作生成会与 engine 职责重叠。→ Mitigation: spec 明确 rules 不读取玩家位置、地块归属和事件日志，只返回局部规则计算结果。
- [Risk] 破产回收排序不稳定会导致测试、事件顺序和玩家体验不一致。→ Mitigation: 固定按 `acquired_at` 升序排序，时间相同保持输入顺序。
- [Risk] 卡牌 intent 与执行语义混淆会导致 rules 引入随机数或状态修改。→ Mitigation: `resolve_card_intent` 只返回 domain intent，随机抽卡、随机步数和效果执行全部留给 engine。
