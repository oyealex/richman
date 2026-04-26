# 终端大富翁 — 模块架构设计

---

## 设计原则

- **高内聚**：每个模块只做一件事，内部紧密关联
- **低耦合**：模块间通过明确的接口交互，不直接访问对方的内部状态
- **单向依赖**：依赖关系是单向无环的（DAG），可按依赖顺序逐层开发和测试
- **易于扩展**：新增内容（新地块、新卡片、新机制）只需修改对应模块，不波及全链路
- **事件日志**：engine 每次状态变更记录事件，用于渲染展示和调试，但不作为模块间通信机制

---

## 依赖关系图

```
                    ┌──────────┐
                    │  domain  │  零依赖，纯类型定义
                    └────┬─────┘
           ┌─────────┬───┼───┬─────────┐
           ▼         ▼   │   ▼         ▼
       ┌──────┐  ┌──────┐│┌──────┐  ┌──────┐
       │board │  │rules │││player│  │render│  平级模块，主要依赖 domain
       └──┬───┘  └──┬───┘│└──┬───┘  └──┬───┘
          │         │    │   │         │
          └────┬────┴────┴───┴────┬────┘
               ▼                  │
           ┌───────┐◄─────────────┘
           │engine │  状态树持有者，唯一写状态的模块
           └───┬───┘
               ▼
           ┌───────┐
           │  app  │  入口，装配所有模块
           └───────┘
```

### 调用方向

- engine 调 render 展示状态（推 `GameSnapshot` 快照）
- engine 获取决策输入时只调用 player；如果是 HumanPlayer，再由 HumanPlayer 通过 render 获取终端输入
- render 永远不主动调 engine
- render 只依赖 domain，可插拔替换

---

## 开发顺序

```
domain → board, rules, render, player (并行) → engine → app
  ①                        ②                          ③       ④
```

按此顺序，每个模块开发完即可独立测试，不需要后续模块存在。

---

## 模块详解

---

### ① domain — 领域模型

**定位**：整个项目的地基。所有模块都用到的类型、枚举、数据结构、常量，定义在这里。**零逻辑，零依赖**。

**内容**：

#### 棋盘相关

| 类型 | 说明 |
|---|---|
| `CellType` 枚举 | START / PROPERTY / CHANCE / GO_TO_JAIL / JAIL_SPACE / BLANK |
| `PropertyTemplate` | 不可变地块配方：名称、地价、四级租金 `[空地,1级,2级,3级]`、升级费 |

#### 卡片相关

| 类型 | 说明 |
|---|---|
| `CardType` 枚举 | MONEY_GAIN / MONEY_LOSS / MOVE / GO_TO_JAIL / JAIL_PASS / DEMOLISH |
| `MoveDirection` 枚举 | FORWARD / BACKWARD / RANDOM |
| `CardDefinition` | 不可变卡片配方：类型、描述、参数。金钱卡包含 `amount`；移动卡包含 `direction`、`min_steps`、`max_steps`；保留卡不包含运行时状态 |
| `CardIntent` 枚举 | rules 解析卡牌后返回的效果意图：<br>立即效果：`GrantMoney(amount)` / `DeductMoney(amount)` / `Move(direction, min_steps, max_steps)` / `GoToJail()`<br>获得保留卡：`ObtainCard(CardType)` — 用于 JAIL_PASS 和 DEMOLISH |

#### 玩家相关

| 类型 | 说明 |
|---|---|
| `PropertyState` | InternalGameState 中唯一保存的运行时地块状态：格子编号、owner_player_index、当前等级（0~3）、获取时间戳、购买价 `purchase_price`、累计升级投入 `upgrade_invested` |
| `PropertyRef` | 玩家持有地块引用：通常为 `position` 或 `property_id`，指向 `InternalGameState.properties_by_position` 中的 `PropertyState`，不复制等级、归属、成本等可变字段 |
| `HandCards` | 手牌计数器：`jail_pass: int`、`demolish: int` |
| `PlayerState` | 完整玩家状态：name、cash、position、holdings: list[PropertyRef]、hand、jail_rounds_left、bankrupt |
| `PlayerView` | 给特定玩家决策用的裁剪视图——仅包含该玩家可见的信息（自己的 cash/hand/持有地投入可见，他人的隐藏），不包含 render 布局信息 |

#### 动作相关

| 类型 | 说明 |
|---|---|
| `Action` 枚举 | BUY / UPGRADE / USE_DEMOLISH / USE_JAIL_PASS / ACCEPT_JAIL / SKIP |

#### 游戏流控

| 类型 | 说明 |
|---|---|
| `Phase` 枚举 | EFFECT_UPDATE / DICE_ROLL / LANDING / ACTION / END |
| `GameEvent` | 事件类型 + 数据（见事件类型清单） |
| `ReclaimPlan` | 破产回收方案：`reclaimed: [(position, refund)]`、`total_refund: int`、`remaining_shortfall: int` |

#### 顶层状态树

| 类型 | 说明 |
|---|---|
| `InternalGameState` | engine 持有的唯一完整可变状态树，结构见下文 |
| `GameSnapshot` | 用于 render 的状态快照，包含公开棋盘/玩家信息、viewer 私有信息、viewer 持有地投入和事件日志；render 展示时必须按 viewer 隐藏私有数据 |
| `GameConfig` | 配置结构：board_cells[]、cards[]、start_cash、start_bonus、jail_rounds、demolish_range、dice_sides |

#### 常量

`START_BONUS`、`JAIL_ROUNDS`、`DICE_SIDES`、`DEMOLISH_RANGE`

**不含什么**：任何计算逻辑、状态修改、I/O。

---

### ② board — 棋盘

**定位**：棋盘的空间模型。操作的是位置编号，不碰状态树。**依赖 domain**。

**对外接口**：

```python
Board           create(config: BoardConfig) -> Board
CellType        get_cell_type(board, position: int) -> CellType
PropertyTemplate get_property_template(board, position: int) -> PropertyTemplate | None
MoveResult      move(board, position: int, steps: int) -> MoveResult
list[int]       get_range(board, center: int, radius: int) -> list[int]
int             total_cells(board) -> int
```

**关键行为**：
- `move`：给定位置和有符号步数，在环形棋盘上计算新位置。正数顺时针前进，负数逆时针后退，返回 `MoveResult(new_position, start_crossings)`
- `start_crossings`：本次移动过程中进入 START 格的次数；正好停在 START 也计入一次，移动开始时已经位于 START 不计入。engine 只根据这个计数发放起点奖金，LANDING 阶段不再额外发钱
- `get_range`：以 center 为中心，沿顺时针和逆时针各延伸 radius 格，去重后返回位置列表。环形边界自动取模处理，不可重复选中同一格
- `GO_TO_JAIL` 表示"入狱格"，踩中会触发入狱判决；`JAIL_SPACE` 表示"监狱格"，被关押玩家移动到这里，普通玩家走到这里无事发生
- 棋盘创建后不可变，所有查询函数为纯函数

**扩展点**：换棋盘形状只需换此模块。

---

### ③ rules — 规则引擎

**定位**：所有游戏逻辑以纯函数形式存在。不持有状态，不调用其他模块。**依赖 domain**。

**对外接口**：

```python
int             calculate_rent(template: PropertyTemplate, level: int) -> int
bool            can_upgrade(template: PropertyTemplate, property_state: PropertyState) -> bool
CardIntent      resolve_card_intent(card: CardDefinition) -> CardIntent
ReclaimPlan     calculate_bankruptcy(properties: list[PropertyState], shortfall: int) -> ReclaimPlan
bool            can_afford(cash: int, amount: int) -> bool
```

**关键行为**：
- `calculate_rent`：根据地块模板和当前等级，返回应收租金
- `can_upgrade`：仅判断地块等级是否允许升级（当前等级 < 3）。现金是否足够由 engine 在计算动作列表时结合 `can_afford` 处理
- `resolve_card_intent`：输入卡片配方，返回 `CardIntent`。纯声明——不执行任何效果。立即效果类返回对应的 Intent，可保留类返回 `ObtainCard(CardType)`。`MoveIntent` 的方向和步数范围来自 `CardDefinition`，具体步数由 engine 在落实时随机决定
- `calculate_bankruptcy`：输入玩家持有的 `PropertyState` 列表和当前资金缺口 `shortfall`，返回回收方案。按获取时间从早到晚逐个回收，每块退还 `purchase_price + upgrade_invested`，直到覆盖缺口或全部卖光
- **抽卡机制**：从配置中定义的所有卡片中，每次独立均匀随机抽取一张（有放回）。每张卡片被抽到的概率均等。engine 负责随机抽取，然后调 `resolve_card_intent` 解析
- 所有函数为纯函数，输入 → 输出，无副作用

**扩展点**：新卡牌效果只需在 `resolve_card_intent` 中加分支；新租金规则只改 `calculate_rent`。

---

### ④ player — 决策器

**定位**：玩家决策模块。根据当前局面决定采取哪个动作。**不持有任何状态，不修改任何状态**。**依赖 domain**。

**对外接口**：

```python
class Player(ABC):
    name: str
    def wait_for_dice(self) -> None            # 等待掷骰触发
    def decide(self, view: PlayerView, actions: list[Action], engine_context) -> Action
    def choose_demolish_target(self, view: PlayerView, candidates: list[int], engine_context) -> int

class HumanPlayer(Player):
    # wait_for_dice: 调 render.prompt_choice 等待用户按键
    # decide: 通过 engine_context 调 render.prompt_choice 获取用户输入
    # choose_demolish_target: 通过 engine_context 调 render.prompt_choice 获取目标位置

class AIPlayer(Player):
    # wait_for_dice: 直接 return（AI 不需要等待）
    # decide: 根据策略（保守/激进/均衡）自行计算最优动作
    # choose_demolish_target: 根据策略自行选择目标位置
```

**关键设计**：
- `PlayerView` 是裁剪后的视图——只包含该玩家能看到的信息。HumanPlayer 可以展示自己的全部数据；AIPlayer 严格遵守信息可见性
- `PlayerView` 与 `GameSnapshot` 分工不同：`PlayerView` 面向 player 决策，字段尽量少；`GameSnapshot` 面向 render 展示，包含布局、事件和当前 viewer 的私有展示数据
- `actions` 是 engine 根据当前局面算好的可选动作列表，player 只负责从中选一个
- `decide` 返回 `Action`，`choose_demolish_target` 返回目标位置，均由 engine 执行。player 模块不执行任何状态变更
- engine 获取输入时只调用 player。HumanPlayer 通过 `engine_context` 使用 render 的输入原语；AIPlayer 直接基于 `PlayerView` 自行决策
- `engine_context` 只能暴露 render 的输入原语和必要的展示辅助，不能暴露 `InternalGameState`、engine mutation API、随机数源或其他玩家私密字段
- player 模块不依赖 board/rules/engine——只依赖 domain。决策所需的所有上下文通过 `PlayerView`、`actions`、候选目标和 `engine_context` 传入

**扩展点**：新 AI 策略（LLM 驱动的 NPC、强化学习玩家）只需新增 `Player` 子类。

---

### ⑤ engine — 游戏引擎

**定位**：唯一持有完整可变状态树的模块。跑五阶段游戏主循环，调 board/rules 计算结果，直接改状态树，调 player 获取决策，调 render 展示快照，维护事件日志。**依赖 domain、board、rules、player、render**。

**对外接口**：

```python
GameEngine         create(config: GameConfig, board: Board, players: list[Player], renderer) -> GameEngine
InternalGameState  get_state() -> InternalGameState
GameSnapshot       snapshot_for(viewer_index: int) -> GameSnapshot
InternalGameState  start() -> InternalGameState   # 主循环，返回最终完整状态
```

**内部持有的完整状态树**：

```
InternalGameState
├── turn: int                          # 当前回合数
├── current_player_index: int          # 行动顺序中的位置
├── phase: Phase                       # 当前处于五个阶段中的哪个
├── dice_value: int | None             # 阶段②后填入，阶段⑤清空
├── players: [PlayerState]             # 所有玩家状态；holdings 只保存 PropertyRef
├── properties_by_position: dict[int, PropertyState]
│                                      # 地块运行时状态的唯一真源，玩家 holdings 指向这里
├── event_log: [GameEvent]             # 最近 N 条完整事件
└── available_actions: [Action] | None # 阶段④时有值，否则为空
```

**对外裁剪快照**：

```
GameSnapshot
├── turn: int
├── current_player_index: int
├── viewer_index: int                  # 此快照的目标观众（玩家索引）
├── phase: Phase
├── dice_value: int | None
├── public_board: PublicBoardInfo      # 格子类型、地块归属、地块等级等公开棋盘信息
├── public_players: [PublicPlayerInfo] # 名称、位置、入狱状态、破产状态
├── viewer_private: PlayerState        # viewer_index 对应玩家的完整状态
├── viewer_private_properties: [PropertyState]
│                                      # viewer 持有地的完整投入信息，仅对 viewer 可见
├── event_log: [GameEvent]             # 完整事件的展示视图；render 必须隐藏私有字段
└── available_actions: [Action] | None
```

> 状态规则：所有可变状态只在 `InternalGameState` 中维护。地块等级、归属、获取时间和投入成本只保存在 `properties_by_position`；`players[].holdings` 只保存引用/索引，不复制地块状态。`GameSnapshot` 是 engine 按 viewer 临时生成的只读展示快照，`PlayerView` 是按玩家生成的决策视图。render 与 player 永远拿不到其他玩家的现金、手牌数量和具体投入成本。

> 事件规则：`InternalGameState.event_log` 保存完整事件，方便调试和回放；生成 `GameSnapshot` 或 render 展示时必须按 viewer 隐藏私有数据。公开事件可以展示卡牌内容、卡牌效果是否触发、破产消息、卡牌使用者/目标/结果；不得展示其他玩家现金余额、手牌数量、具体地块投入成本等私有字段。

#### 视图生成规则

- `PlayerView`：engine 给当前决策玩家生成，只包含决策必要数据。自己的 cash、hand、持有地完整投入可见；其他玩家只包含公开信息。
- `GameSnapshot`：engine 给 render 生成，包含完整画面所需的公开棋盘/玩家信息、当前 viewer 的私有展示信息、事件日志。
- AIPlayer 和 HumanPlayer 都只接收 `PlayerView`，不能接收 `InternalGameState`。HumanPlayer 如需展示完整画面，由 engine/render 使用 `GameSnapshot` 完成。
- `GameSnapshot.event_log` 可以承载完整事件对象，但 render 输出到屏幕前必须按 viewer 做隐私遮蔽。

#### 回合流程（五阶段）

```
process_turn(player):

  ① EFFECT_UPDATE
     记录事件 TURN_START
     遍历玩家的效果队列（按获得先后顺序）：
       - 当前仅监狱倒计时：如果 jail_rounds_left > 0，减 1
         记录事件 JAIL_TICKED
         如果归零 → 记录 JAIL_RELEASED
       - 未来可扩展：冰冻、双倍租金等效果在此阶段更新和触发
     如果 jail_rounds_left > 0:
       直接跳到⑤（在监狱中，跳过②③④）

  ② DICE_ROLL
     记录事件 WAIT_DICE
     → 调 player.wait_for_dice()
       （HumanPlayer: 等用户按键；AIPlayer: 直接返回）
     → 随机生成骰子值
     → 调 board.move(position, dice_value) 计算移动
     → 记录事件 DICE_ROLLED, PLAYER_MOVED
     → 根据 MoveResult.start_crossings 发放起点奖金
       （每进入 START 一次发一次；正好停在 START 已计入；开局位于 START 不计入）
     → 记录 START_BONUS_GRANTED(crossings, total_bonus)

  ③ LANDING
     根据落点格子类型处理：

     ├─ START:
     │    记录事件 LANDED_ON(START)
     │    （不在此处发奖金，奖金已由移动结果的 start_crossings 统一处理）
     │
     ├─ PROPERTY(无主):
     │    记录事件 LANDED_ON(PROPERTY, position), PROPERTY_AVAILABLE
     │    → 进入④
     │
     ├─ PROPERTY(他人):
     │    查地主 jail_rounds_left
     │    ├─ 地主在监狱中:
     │    │    记录事件 RENT_SKIPPED_OWNER_IN_JAIL
     │    │    → 进入④
     │    └─ 地主自由:
     │         调 rules.calculate_rent → 记录 RENT_DUE
     │         调内部 pay() 扣款
     │         如果现金不足 → shortfall = rent - cash
     │           根据 players[].holdings 引用取出对应 PropertyState 列表
     │           调 rules.calculate_bankruptcy(properties, shortfall) → 逐个回收地块
     │           每回收一块记录 PROPERTY_RECLAIMED
     │           如果回收后能覆盖缺口：
     │             完成全额租金支付 → 记录 RENT_PAID → 进入④
     │           如果全部回收仍不足：
     │             不支付部分租金，地主收不到缺少资金，也收不到破产玩家剩余资金
     │             记录 RENT_UNPAID_BANKRUPTCY, PLAYER_BANKRUPT
     │             地块全部变回空地（无主、0级），现金清零，手牌作废，标记 bankrupt=true
     │             现金清零只是状态清理，不代表剩余资金转给银行或地主
     │             → 跳到⑤
     │         如果现金足够：
     │           完成全额租金支付 → 记录 RENT_PAID → 进入④
     │
     ├─ PROPERTY(自己):
     │    记录事件 LANDED_ON(自己地块)
     │    如果等级 < 3 → 记录 PROPERTY_UPGRADABLE
     │    → 进入④
     │
     ├─ CHANCE:
     │    抽卡 → 记录 CARD_DRAWN
     │    调 rules.resolve_card_intent
     │    根据 CardIntent 执行：
     │    - GrantMoneyIntent → 现金增加，记录 MONEY_GAINED
     │    - DeductMoneyIntent → 向银行强制付款，记录 MONEY_LOST；若现金不足，按破产回收流程处理，仍不足则记录 PLAYER_BANKRUPT 并跳到⑤
     │    - MoveIntent → 根据 CardDefinition.direction/min_steps/max_steps 随机方向和点数 → board.move → 按 start_crossings 发起点奖金 → 递归③
     │      连锁落点只处理阶段③效果；中间落点不会购买、升级或使用拆除卡。所有连锁结束后，只基于最终落点进入一次阶段④
     │    - GoToJailIntent → 触发"入狱判决"交互（见下方「交互点详述」- 入狱判决）；若接受入狱，当前回合立即跳到⑤，不返回机会卡流程，也不进入阶段④
     │    - ObtainCard → 手牌+1，记录事件
     │    → 进入④
     │
     ├─ GO_TO_JAIL:
     │    触发"入狱判决"交互（见下方「交互点详述」- 入狱判决）
     │    - 如果玩家选择 USE_JAIL_PASS → 记录 JAIL_PASS_USED → 进入④
     │    - 如果玩家选择 ACCEPT_JAIL → 记录 PLAYER_SENT_TO_JAIL，送入 JAIL_SPACE → 跳到⑤
     │    - 如果玩家没有免狱卡 → 自动 ACCEPT_JAIL → 记录 PLAYER_SENT_TO_JAIL，送入 JAIL_SPACE → 跳到⑤
     │
     ├─ JAIL_SPACE:
     │    记录事件 LANDED_ON(JAIL_SPACE)
     │    普通玩家走到监狱格无事发生 → 进入④
     │
     └─ BLANK:
          记录事件 LANDED_ON(BLANK) → 进入④

  ④ ACTION
     计算 available_actions（详见「交互点详述」- 交互点 C）：

     - 停在空地且现金足够买地 → 可加入 BUY
     - 停在自己的地块、等级 < 3 且现金足够升级 → 可加入 UPGRADE
     - 在任意非监狱关押状态的格子、手中有拆除卡且范围内存在 level > 0 的地块 → 可加入 USE_DEMOLISH
     - 只要存在至少一个可选动作 → 加入 SKIP
     - 以上都不满足 → []

     if available_actions 为空:
       → 跳到⑤

     记录事件 WAIT_ACTION(available_actions)
     → 调 player.decide(view, actions) 获取决策
     记录事件 ACTION_CHOSEN(player_name, action)

     执行动作：
     - BUY → 扣钱，add_property（写入 purchase_price、upgrade_invested=0）→ 记录 PROPERTY_BOUGHT
     - UPGRADE → 扣升级费，level+1，upgrade_invested+=升级费 → 记录 PROPERTY_UPGRADED
     - USE_DEMOLISH:
         ① 调 board.get_range 获取候选位置列表
         ② 过滤出 level > 0 的地块作为候选
         ③ 调 player.choose_demolish_target(view, candidates) 获取目标位置
            （HumanPlayer: 通过 render 展示候选列表并获取输入；AIPlayer: 自行选定目标）
         ④ 消耗一张拆除卡，目标地块降一级 → 记录 PROPERTY_DEMOLISHED
     - SKIP → 无事发生

  ⑤ END
     - dice_value = None, phase = EFFECT_UPDATE
     - 记录事件 TURN_END
     - 检查胜利条件（存活人数 == 1）→ 记录 GAME_OVER
     - 推进到下一个未破产玩家
```

#### 交互点详述

以下列出游戏中所有需要玩家做出选择的地方。每个交互点都明确定义了**触发场景、可选动作列表、每个动作的含义**，不会出现模糊的 yes/no。

---

##### 交互点 A：掷骰等待（阶段②）

| 项目 | 内容 |
|---|---|
| 触发场景 | 玩家回合进入阶段②，且玩家不在监狱中 |
| 可选动作 | `[ROLL_DICE]`（单一选项，HumanPlayer 按 Enter 触发，AIPlayer 自动跳过） |
| 机制 | engine 调用 `player.wait_for_dice()` |

---

##### 交互点 B：入狱判决（阶段③）

| 项目 | 内容 |
|---|---|
| 触发场景 | 踩中 GO_TO_JAIL 格，或抽到 GO_TO_JAIL 卡（GoToJailIntent），或移动卡连锁落到 GO_TO_JAIL 格 |
| 判定 | engine 先检查玩家手中有没有免狱卡 |
| 有免狱卡时 | 可选动作：`[USE_JAIL_PASS, ACCEPT_JAIL]` |
| | · `USE_JAIL_PASS`：消耗一张免狱卡，不入狱，继续阶段④ |
| | · `ACCEPT_JAIL`：保留免狱卡，进入监狱（关押 3 轮），当前回合立即结束，不再返回原落点流程或进入阶段④ |
| 无免狱卡时 | 自动执行 `ACCEPT_JAIL`，不询问玩家 |
| 机制 | engine 构造临时动作列表，调用 `player.decide()` |

---

##### 交互点 C：回合动作选择（阶段④）

| 项目 | 内容 |
|---|---|
| 触发场景 | 玩家进入阶段④ |
| 可选动作 | engine 根据当前局面计算，可能包含： |
| | · `BUY`：仅当停在无主地块且现金足够支付地价时出现 |
| | · `UPGRADE`：仅当停在自己的地块、等级 < 3 且现金足够支付升级费时出现 |
| | · `USE_DEMOLISH`：仅当手中有拆除卡，且当前位置前后范围内存在 level > 0 的地块时出现；可在任意格子使用，包括他人地块、空白格、JAIL_SPACE |
| | · `SKIP`：只要存在至少一个可选动作就出现；如果没有可选动作则 `[]` → 直接跳过 |
| 动作含义 | · `BUY`：支付地价，获得地块所有权，不会因买不起而触发破产 |
| | · `UPGRADE`：支付升级费，地块等级 +1（仅限一次），不会因升不起而触发破产 |
| | · `USE_DEMOLISH`：进入交互点 D（目标选择），成功使用后消耗一张拆除卡 |
| | · `SKIP`：无事发生，回合结束 |
| 机制 | engine 构造动作列表，调用 `player.decide()` |

---

##### 交互点 D：拆除目标选择（阶段④子步骤）

| 项目 | 内容 |
|---|---|
| 触发场景 | 玩家在交互点 C 中选择了 `USE_DEMOLISH` |
| 可选动作 | engine 调用 `board.get_range(current_position, demolish_range)` 获取候选位置列表，过滤出有等级（level > 0）的地块 |
| | · 候选列表中的每个地块位置为一个独立目标选项：`[position=3, position=7, ...]` |
| | · 正常情况下候选列表不会为空，因为交互点 C 已过滤；若状态变化导致为空，则不消耗拆除卡并返回交互点 C |
| 每个选项的展示 | "拆除 {地块名}（{主人名} 的 {N} 级地，降为 {N-1} 级）" |
| 机制 | engine 将候选列表传给 `player.choose_demolish_target()`；HumanPlayer 通过 render 展示候选列表并获取输入；AIPlayer 自行计算最优目标 |

---

**关键行为**：
- **唯一的状态写入口**：所有状态变更（现金加减、地块归属、手牌增减、等级变化）都在 engine 内部的方法中完成
- **地块状态唯一真源**：购买、升级、拆除、破产回收只修改 `InternalGameState.properties_by_position`；`players[].holdings` 只增删引用，不保存可变地块字段
- **调用链**：engine → board（空间计算）→ rules（规则计算）→ player（决策）→ 自身（执行并记录事件）；HumanPlayer 如需输入，再通过 render 的 prompt 原语完成
- **事件日志**：每次状态变更记录事件。render 展示事件日志，调试可回溯

**扩展点**：新阶段（如交易阶段）可在 `process_turn` 中插入；新动作类型在阶段④中追加。

---

### ⑥ render — 终端渲染

**定位**：接收 GameSnapshot 快照画画面，用户操作返回输入。**纯展示 + 输入，不包含游戏逻辑**。**只依赖 domain**。

**对外接口**：

```python
None    render_frame(snapshot: GameSnapshot)    # 画一整帧
None    render_event_log(events: list[GameEvent])
str     prompt_choice(question: str, options: list[str]) -> str
int     prompt_number(question: str, min: int, max: int) -> int
None    render_game_over(winner_name: str)
```

**关键设计**：
- 完全被动：engine 推 `GameSnapshot` → render 画。render 不知道 engine 的内部状态树
- 隐私保护：render 根据 `snapshot.viewer_index` 和 `snapshot.viewer_private` 决定展示哪些私密信息，不会越权。事件日志可以完整记录在 engine 中，但 render 展示事件时必须隐藏其他玩家的现金余额、手牌数量和具体投入成本
- 交互原语通用：`prompt_choice` 签名与具体渲染技术（curses/rich/web）无关
- 无状态：render 每次画完就忘，下次 engine 传来新快照再画

**扩展点**：换渲染方式（curses → rich → web）只需换此模块。

---

### ⑦ app — 应用入口

**定位**：装配所有模块，加载配置，启动游戏。**依赖所有模块**。

**流程**：

```
main():
    1. 加载配置文件（YAML/JSON）
       → 棋盘布局、地块数据、卡片数据、游戏参数
    2. domain:    解析为 GameConfig
    3. board:     create(config.board_cells)
    4. render:    初始化终端渲染器
    5. player:    创建玩家实例（Human 或 AI；HumanPlayer 注入 render 或输入上下文）
    6. rules:     不需要初始化（纯函数模块）
    7. engine:    create(config, board, players, render)
    8. engine.start() → 主循环
       - 每回合：engine 产生事件 → 更新 InternalGameState → 生成 GameSnapshot → render.render_frame()
       - 需要输入：engine 调 player；HumanPlayer 再通过 render.prompt_*() 获取真实玩家输入
    9. render.render_game_over(winner)
```

**扩展点**：多游戏模式、存档读档、网络对战在 app 层实现。

---

## 模块依赖总表

| 模块 | 有状态？ | 依赖 | 被依赖 |
|---|---|---|---|
| domain | 否（纯类型） | 无 | 所有模块 |
| board | 是（棋盘数据，不可变） | domain | engine |
| rules | 否（纯函数） | domain | engine |
| player | 否（纯决策） | domain | engine |
| engine | **是（完整状态树）** | domain, board, rules, player, render | app |
| render | 否（纯展示 + 输入） | domain | engine, app（HumanPlayer 通过 engine_context 间接使用） |
| app | 否（装配） | 全部 | 无 |

---

## 关键设计决策

### 1. 为什么状态树只由 engine 持有？

player 模块原先负责状态 CRUD，但引入 HumanPlayer 和 AIPlayer 后，player 的职责变成了"决策"。把状态管理收回 engine：

- **职责单一**：player 只管"选什么"，不管"怎么改"
- **一致性**：所有状态变更集中在一处，不会出现"player 改了一部分、engine 改了另一部分"的混乱
- **AI 安全**：AIPlayer 只接收由 `InternalGameState` 裁剪出的 `PlayerView`，即使 AI 有 bug 也不会越权看到其他玩家的私密信息

### 2. 为什么不用事件总线？

事件驱动适合多消费者、跨网络、真正异步的场景。本项目是单线程、同步、回合制 TUI 游戏——engine、player、render 的交互都发生在明确的回合阶段内，直接调用的解耦效果和事件总线一样，但代码量更少、调试更直观。

作为折中，engine 内部维护事件日志：每次状态变更记录事件，render 展示，调试可回溯。将来要上回放或联机，这个日志可以直接作为事件源。

### 3. 为什么 render 只依赖 domain？

常见做法是 render 调 engine 的方法获取数据，但这造成双向耦合。

本方案中 engine 生成 `GameSnapshot` 快照（domain 中的纯数据）推给 render，render 只负责画和返回输入原语结果。render 不知道 engine 的内部状态树。换 curses、换 rich、换 web 前端，只换 render 模块。

### 4. 为什么 rules 是纯函数且不依赖 board/player？

`calculate_rent(template, level)` 不关心这块地在棋盘上哪个位置、属于谁——它只做乘法。`calculate_bankruptcy(properties, shortfall)` 不关心这些 `PropertyState` 是从哪个模块取出来的——它只做排序和累加。

纯函数可以完全用单元测试覆盖，不需要模拟任何游戏状态。这是整个项目里测试成本最低、置信度最高的模块。

---

## 核心测试场景

以下场景必须覆盖到单元测试或集成测试中，避免规则边界在实现中分叉：

| 场景 | 期望 |
|---|---|
| 起点多次经过 | `board.move` 返回正确 `start_crossings`，engine 按次数发放奖金 |
| 后退经过起点 | 负步数移动也能正确计算 `start_crossings` |
| 正好停在起点 | 只通过 `start_crossings` 发一次奖金，LANDING 不重复发 |
| 他人地块付租后仍存活 | 支付租金后进入阶段④，若有拆除卡且有目标，可使用拆除卡 |
| 地主坐牢 | 其他玩家踩中该地主地块时免租，并可继续阶段④ |
| 机会卡移动连锁 | 连锁中只处理阶段③效果，连锁结束后只按最终落点进入一次阶段④ |
| 机会卡入狱 | 接受入狱后立即结束当前回合，不进入阶段④ |
| 监狱倒计时 | 入狱玩家前两轮只扣减并结束；归零释放后继续当回合阶段② |
| 买不起/升不起 | `BUY`/`UPGRADE` 不出现在可选动作中，且不会触发破产 |
| 破产不足支付租金 | 玩家出局，地主不收到部分租金或剩余现金，破产玩家现金清零仅作为状态清理 |
| 事件日志隐私 | engine 完整记录事件；render 展示时不泄露非 viewer 的现金、手牌和具体投入 |
| AI 信息边界 | AIPlayer 只能收到裁剪后的 `PlayerView`，不能访问 `InternalGameState` 或其他玩家私密字段 |

---

## 事件类型清单

| 事件 | 触发时机 | 携带数据 |
|---|---|---|
| `TURN_START` | 阶段① | player_name |
| `TURN_END` | 阶段⑤ | player_name |
| `JAIL_TICKED` | 阶段① | player_name, remaining |
| `JAIL_RELEASED` | 阶段①（归零时） | player_name |
| `WAIT_DICE` | 阶段② | player_name |
| `DICE_ROLLED` | 阶段② | value |
| `PLAYER_MOVED` | 阶段②/移动卡 | player_name, from_position, to_position |
| `START_BONUS_GRANTED` | 阶段②/移动卡 | player_name, crossings, total_bonus |
| `LANDED_ON` | 阶段③ | player_name, cell_type, position |
| `PROPERTY_AVAILABLE` | 阶段③ | position, name, price, rents |
| `PROPERTY_UPGRADABLE` | 阶段③ | position, name, current_level, upgrade_cost |
| `RENT_DUE` | 阶段③ | from_player, to_player, amount |
| `RENT_PAID` | 阶段③ | from_player, to_player, amount |
| `RENT_UNPAID_BANKRUPTCY` | 阶段③ | from_player, to_player, amount |
| `RENT_SKIPPED_OWNER_IN_JAIL` | 阶段③ | from_player, owner_name |
| `CARD_DRAWN` | 阶段③ | player_name, card_description |
| `MONEY_GAINED` | 机会卡 | player_name, amount |
| `MONEY_LOST` | 机会卡 | player_name, amount |
| `PLAYER_SENT_TO_JAIL` | GO_TO_JAIL 格/入狱卡 | player_name, jail_position |
| `JAIL_PASS_USED` | 阶段③（免狱） | player_name |
| `PROPERTY_BOUGHT` | 阶段④ | player_name, position, name, price |
| `PROPERTY_UPGRADED` | 阶段④ | player_name, position, from_level, to_level |
| `PROPERTY_DEMOLISHED` | 阶段④ | user_name, owner_name, position, from_level, to_level |
| `PROPERTY_RECLAIMED` | 破产处理 | player_name, position, refund |
| `PLAYER_BANKRUPT` | 破产处理 | player_name |
| `WAIT_ACTION` | 阶段④ | available_actions |
| `ACTION_CHOSEN` | 阶段④ | player_name, action |
| `GAME_OVER` | 阶段⑤ | winner_name |
