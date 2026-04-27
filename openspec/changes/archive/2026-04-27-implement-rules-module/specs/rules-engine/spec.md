## ADDED Requirements

### Requirement: Rules module boundary

系统 SHALL 提供 `richman.rules` 作为游戏纯规则计算模块，并保持该模块只依赖 `richman.domain` 和标准库，不持有玩家状态、棋盘对象、事件日志、随机源或渲染状态。

#### Scenario: Rules package is importable

- **WHEN** 开发者导入 `richman.rules`
- **THEN** 该包成功导入并导出 rules 公共 API

#### Scenario: Rules does not depend on higher modules

- **WHEN** 检查 `src/richman/rules` 的源码导入
- **THEN** rules 模块不导入 `richman.board`、`richman.player`、`richman.engine`、`richman.render` 或 adapter 模块

#### Scenario: Rules functions are side-effect free

- **WHEN** 使用 rules API 计算租金、升级可行性、卡牌意图、破产回收方案或支付能力
- **THEN** rules 不修改 `InternalGameState`、`PlayerState`、`PropertyState`、玩家手牌、事件日志、随机源或渲染状态

### Requirement: Rent calculation

系统 SHALL 提供 `calculate_rent(template: PropertyTemplate, level: int) -> int`，根据地块模板的租金表和当前等级返回应收租金。

#### Scenario: Rent is selected by level

- **WHEN** 使用包含四级租金的 `PropertyTemplate` 调用 `calculate_rent(template, level)`
- **THEN** 系统返回 `template.rents[level]`

#### Scenario: Rent calculation supports all configured levels

- **WHEN** `level` 是 `template.rents` 的有效索引
- **THEN** `calculate_rent` 返回该等级对应租金

#### Scenario: Rent calculation rejects invalid level

- **WHEN** `level` 小于 0 或大于等于 `template.rents` 的长度
- **THEN** `calculate_rent` MUST 拒绝该等级并报告规则输入错误

### Requirement: Upgrade eligibility

系统 SHALL 提供 `can_upgrade(template: PropertyTemplate, property_state: PropertyState) -> bool`，仅根据地块等级规则判断该地块是否还能继续升级。

#### Scenario: Property below maximum level can upgrade

- **WHEN** `property_state.level` 小于 `template.rents` 的最高有效等级
- **THEN** `can_upgrade` 返回 `True`

#### Scenario: Property at maximum level cannot upgrade

- **WHEN** `property_state.level` 等于 `template.rents` 的最高有效等级
- **THEN** `can_upgrade` 返回 `False`

#### Scenario: Upgrade eligibility ignores cash

- **WHEN** 判断地块是否可以升级
- **THEN** `can_upgrade` 不读取玩家现金、不判断玩家是否买得起升级费
- **AND** 现金约束由 engine 结合 `can_afford` 处理

#### Scenario: Upgrade eligibility rejects invalid level

- **WHEN** `property_state.level` 小于 0 或大于 `template.rents` 的最高有效等级
- **THEN** `can_upgrade` MUST 拒绝该等级并报告规则输入错误

### Requirement: Card intent resolution

系统 SHALL 提供 `resolve_card_intent(card: CardDefinition) -> CardIntent`，将卡片配方解析为 domain 中的结构化卡牌意图，且不执行任何卡牌效果。

#### Scenario: Money gain card resolves to grant money intent

- **WHEN** `CardDefinition.card_type` 为 `MONEY_GAIN` 且携带 `amount`
- **THEN** `resolve_card_intent` 返回 `GrantMoneyIntent(amount)`

#### Scenario: Money loss card resolves to deduct money intent

- **WHEN** `CardDefinition.card_type` 为 `MONEY_LOSS` 且携带 `amount`
- **THEN** `resolve_card_intent` 返回 `DeductMoneyIntent(amount)`

#### Scenario: Move card resolves to move intent

- **WHEN** `CardDefinition.card_type` 为 `MOVE` 且携带 `direction`、`min_steps` 和 `max_steps`
- **THEN** `resolve_card_intent` 返回 `MoveIntent(direction, min_steps, max_steps)`
- **AND** 具体移动步数由 engine 在执行意图时决定

#### Scenario: Go to jail card resolves to jail intent

- **WHEN** `CardDefinition.card_type` 为 `GO_TO_JAIL`
- **THEN** `resolve_card_intent` 返回 `GoToJailIntent()`

#### Scenario: Retainable cards resolve to obtain card intent

- **WHEN** `CardDefinition.card_type` 为 `JAIL_PASS` 或 `DEMOLISH`
- **THEN** `resolve_card_intent` 返回携带同一卡牌类型的 `ObtainCardIntent`

#### Scenario: Card intent resolution validates required parameters

- **WHEN** 金钱卡缺少 `amount`，或移动卡缺少 `direction`、`min_steps`、`max_steps`，或移动卡步数范围非法
- **THEN** `resolve_card_intent` MUST 拒绝该卡片定义并报告规则输入错误

### Requirement: Bankruptcy reclaim planning

系统 SHALL 提供 `calculate_bankruptcy(properties: list[PropertyState], shortfall: int) -> ReclaimPlan`，根据资金缺口生成确定性的地块回收方案，而不执行任何状态修改。

#### Scenario: Bankruptcy plan reclaims oldest properties first

- **WHEN** 使用多个 `PropertyState` 和正数 `shortfall` 调用 `calculate_bankruptcy`
- **THEN** 系统按 `acquired_at` 从早到晚选择回收地块
- **AND** 每块地的退款金额为 `purchase_price + upgrade_invested`

#### Scenario: Bankruptcy plan stops after covering shortfall

- **WHEN** 已选择地块的 `total_refund` 大于或等于 `shortfall`
- **THEN** `calculate_bankruptcy` 停止继续选择地块
- **AND** 返回的 `remaining_shortfall` 为 0

#### Scenario: Bankruptcy plan reports remaining shortfall

- **WHEN** 所有传入地块的退款总额仍小于 `shortfall`
- **THEN** 返回的 `remaining_shortfall` 为 `shortfall - total_refund`

#### Scenario: Bankruptcy plan handles zero shortfall

- **WHEN** `shortfall` 为 0
- **THEN** `calculate_bankruptcy` 返回空的 `reclaimed`、`total_refund` 为 0、`remaining_shortfall` 为 0

#### Scenario: Bankruptcy plan preserves stable order for ties

- **WHEN** 多个地块具有相同 `acquired_at`
- **THEN** `calculate_bankruptcy` MUST 按传入列表中的相对顺序处理这些地块

#### Scenario: Bankruptcy plan rejects negative shortfall

- **WHEN** `shortfall` 小于 0
- **THEN** `calculate_bankruptcy` MUST 拒绝该资金缺口并报告规则输入错误

### Requirement: Affordability check

系统 SHALL 提供 `can_afford(cash: int, amount: int) -> bool`，用于判断指定现金是否足以支付非负金额。

#### Scenario: Cash covers amount

- **WHEN** `cash` 大于或等于 `amount`
- **THEN** `can_afford` 返回 `True`

#### Scenario: Cash does not cover amount

- **WHEN** `cash` 小于 `amount`
- **THEN** `can_afford` 返回 `False`

#### Scenario: Affordability accepts zero amount

- **WHEN** `amount` 为 0 且 `cash` 非负
- **THEN** `can_afford` 返回 `True`

#### Scenario: Affordability rejects negative inputs

- **WHEN** `cash` 小于 0 或 `amount` 小于 0
- **THEN** `can_afford` MUST 拒绝该输入并报告规则输入错误

### Requirement: Rules public API export

系统 SHALL 从 `richman.rules` 包入口导出 rules 公共函数，使后续模块不依赖 rules 内部文件组织。

#### Scenario: Common rules APIs can be imported from package root

- **WHEN** 后续模块执行 `from richman.rules import calculate_rent, can_upgrade, resolve_card_intent, calculate_bankruptcy, can_afford`
- **THEN** 导入成功且无需知道 rules 内部源码文件布局
