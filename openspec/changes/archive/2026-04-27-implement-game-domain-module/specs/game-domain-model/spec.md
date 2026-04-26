## ADDED Requirements

### Requirement: Domain module boundary

系统 SHALL 提供 `richman.domain` 作为游戏共享领域模型模块，并保持该模块无项目内反向依赖、无 I/O、无业务计算逻辑。

#### Scenario: Domain package is importable

- **WHEN** 开发者导入 `richman.domain`
- **THEN** 该包成功导入并导出游戏领域模型的公共 API

#### Scenario: Domain does not depend on higher modules

- **WHEN** 检查 `src/richman/domain` 的源码导入
- **THEN** domain 模块不导入 `richman.board`、`richman.rules`、`richman.player`、`richman.engine`、`richman.render` 或 adapter 模块

#### Scenario: Domain contains no game rule execution

- **WHEN** 使用 domain 模型构造棋盘、卡片、玩家、状态或快照数据
- **THEN** domain 不执行移动、租金、抽卡、破产、回合推进、渲染或输入处理

### Requirement: Shared enumerations and constants

系统 SHALL 定义游戏模块共享的枚举和默认常量，使后续模块可以使用同一套稳定标识。

#### Scenario: Board enumerations are available

- **WHEN** 后续模块需要识别棋盘格类型
- **THEN** domain 提供 `CellType`，包含 `START`、`PROPERTY`、`CHANCE`、`GO_TO_JAIL`、`JAIL_SPACE`、`BLANK`

#### Scenario: Card enumerations are available

- **WHEN** 后续模块需要定义或解析卡片
- **THEN** domain 提供 `CardType`，包含 `MONEY_GAIN`、`MONEY_LOSS`、`MOVE`、`GO_TO_JAIL`、`JAIL_PASS`、`DEMOLISH`
- **AND** domain 提供 `MoveDirection`，包含 `FORWARD`、`BACKWARD`、`RANDOM`

#### Scenario: Turn and action enumerations are available

- **WHEN** engine、player 或 render 需要表达游戏阶段和玩家动作
- **THEN** domain 提供 `Phase`，包含 `EFFECT_UPDATE`、`DICE_ROLL`、`LANDING`、`ACTION`、`END`
- **AND** domain 提供 `Action`，包含 `BUY`、`UPGRADE`、`USE_DEMOLISH`、`USE_JAIL_PASS`、`ACCEPT_JAIL`、`SKIP`

#### Scenario: Default game constants are available

- **WHEN** 后续模块需要读取默认游戏参数
- **THEN** domain 提供 `START_BONUS`、`JAIL_ROUNDS`、`DICE_SIDES`、`DEMOLISH_RANGE`

### Requirement: Immutable templates and configuration

系统 SHALL 定义不可变的地块配方、卡片配方和游戏配置对象，用于承载静态游戏数据。

#### Scenario: Property template describes static property data

- **WHEN** 构造 `PropertyTemplate`
- **THEN** 它包含地块名称、地价、四级租金和升级费
- **AND** 创建后的模板不可被修改

#### Scenario: Card definition describes static card data

- **WHEN** 构造 `CardDefinition`
- **THEN** 它包含卡片类型、描述和对应参数字段
- **AND** 金钱卡可以携带 `amount`
- **AND** 移动卡可以携带 `direction`、`min_steps`、`max_steps`
- **AND** 保留卡定义不包含玩家手牌等运行时状态
- **AND** 创建后的卡片定义不可被修改

#### Scenario: Game config groups static setup data

- **WHEN** 构造 `GameConfig`
- **THEN** 它包含棋盘格配置、卡片配置、起始现金、起点奖金、监狱轮数、拆除范围和骰子面数
- **AND** 创建后的配置不可被修改

### Requirement: Structured card intents

系统 SHALL 定义 rules 解析卡片后返回的结构化卡牌意图，且这些意图只描述效果，不执行效果。

#### Scenario: Immediate money intents are represented

- **WHEN** rules 需要表达金钱增加或扣除效果
- **THEN** domain 提供可携带金额的 `GrantMoney` 和 `DeductMoney` 意图结构

#### Scenario: Movement and jail intents are represented

- **WHEN** rules 需要表达移动或入狱效果
- **THEN** domain 提供可携带方向和步数范围的 `Move` 意图结构
- **AND** domain 提供不执行状态变更的 `GoToJail` 意图结构

#### Scenario: Obtainable card intents are represented

- **WHEN** rules 需要表达获得免狱卡或拆除卡
- **THEN** domain 提供可携带 `CardType` 的 `ObtainCard` 意图结构

### Requirement: Runtime state model

系统 SHALL 定义 engine 持有和修改的运行时状态结构，并保持地块状态的唯一真源位于 `InternalGameState.properties_by_position`。

#### Scenario: Property state contains runtime property fields

- **WHEN** engine 创建或更新 `PropertyState`
- **THEN** 该状态包含格子编号、拥有者玩家索引、当前等级、获取时间戳、购买价和累计升级投入

#### Scenario: Player holdings are references

- **WHEN** 构造 `PlayerState`
- **THEN** 玩家持有地列表使用 `PropertyRef`
- **AND** `PropertyRef` 指向 `InternalGameState.properties_by_position` 中的地块状态
- **AND** `PlayerState.holdings` 不复制地块等级、归属、购买价或升级投入

#### Scenario: Player state contains complete player runtime fields

- **WHEN** 构造 `PlayerState`
- **THEN** 它包含玩家名称、现金、当前位置、持有地引用、手牌计数、剩余监狱轮数和破产标记

#### Scenario: Internal game state contains the mutable state tree

- **WHEN** engine 构造 `InternalGameState`
- **THEN** 它包含当前回合、当前玩家索引、阶段、骰子值、玩家列表、按位置索引的地块状态、事件日志和可选动作列表

#### Scenario: Reclaim plan describes bankruptcy recovery

- **WHEN** rules 需要返回破产回收方案
- **THEN** domain 提供 `ReclaimPlan`，包含被回收地块及退款、总退款和剩余缺口

### Requirement: View and snapshot models

系统 SHALL 定义面向 player 决策和 render 展示的裁剪视图模型，使后续模块不需要读取完整内部状态树。

#### Scenario: Player view is decision-oriented

- **WHEN** engine 为玩家决策生成 `PlayerView`
- **THEN** 该视图包含决策所需的当前玩家公开和私有信息
- **AND** 该视图不包含 render 布局对象或 `InternalGameState`

#### Scenario: Game snapshot is render-oriented

- **WHEN** engine 为 render 生成 `GameSnapshot`
- **THEN** 该快照包含回合、当前玩家、viewer、阶段、骰子值、公开棋盘、公开玩家、viewer 私有状态、viewer 持有地完整状态、事件日志和可选动作

#### Scenario: Snapshot separates public and private data

- **WHEN** render 消费 `GameSnapshot`
- **THEN** 其他玩家的现金、手牌数量和具体地块投入不出现在公开玩家信息中
- **AND** viewer 自己的完整玩家状态和持有地投入通过 viewer 私有字段提供

### Requirement: Event model

系统 SHALL 定义游戏事件模型，用于 engine 记录状态变更、render 展示日志和调试回放。

#### Scenario: Event type list is available

- **WHEN** engine 需要记录模块设计中的事件
- **THEN** domain 提供覆盖 `TURN_START`、`TURN_END`、`JAIL_TICKED`、`JAIL_RELEASED`、`WAIT_DICE`、`DICE_ROLLED`、`PLAYER_MOVED`、`START_BONUS_GRANTED`、`LANDED_ON`、`PROPERTY_AVAILABLE`、`PROPERTY_UPGRADABLE`、`RENT_DUE`、`RENT_PAID`、`RENT_UNPAID_BANKRUPTCY`、`RENT_SKIPPED_OWNER_IN_JAIL`、`CARD_DRAWN`、`MONEY_GAINED`、`MONEY_LOST`、`PLAYER_SENT_TO_JAIL`、`JAIL_PASS_USED`、`PROPERTY_BOUGHT`、`PROPERTY_UPGRADED`、`PROPERTY_DEMOLISHED`、`PROPERTY_RECLAIMED`、`PLAYER_BANKRUPT`、`WAIT_ACTION`、`ACTION_CHOSEN`、`GAME_OVER` 的事件类型

#### Scenario: Event carries structured data

- **WHEN** engine 创建 `GameEvent`
- **THEN** 事件包含事件类型和结构化数据映射
- **AND** domain 不在事件创建时执行隐私遮蔽或渲染格式化

### Requirement: Public API export

系统 SHALL 从 `richman.domain` 包入口导出 domain 公共模型，使其他模块不依赖 domain 内部文件组织。

#### Scenario: Common models can be imported from package root

- **WHEN** 后续模块执行 `from richman.domain import PlayerState, Action, GameSnapshot`
- **THEN** 导入成功且无需知道 domain 内部源码文件布局
