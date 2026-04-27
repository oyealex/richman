# 终端大富翁 — 开发进度记录

最后更新：2026-04-28

---

## 当前状态

当前处于**项目骨架、domain 模块、board 模块和 rules 模块已实现，准备继续实现 render/player 等后续模块**的阶段。

已有文档：

| 文档 | 状态 | 用途 |
|---|---|---|
| `docs/GAME_RULES.md` | 已更新 | 面向玩家/产品的游戏规则说明 |
| `docs/MODULE_DESIGN.md` | 已更新 | 面向开发的模块架构、接口契约和测试边界 |
| `docs/DEVELOPMENT_PROGRESS.md` | 当前文件 | 后续开发交接入口 |

当前已完成并归档的 OpenSpec 变更：

| 变更 | 状态 | 说明 |
|---|---|---|
| `setup-project-dev-environment` | 已归档 | 建立 Python 项目、测试/lint/typecheck 命令、模块包骨架和 Textual TUI smoke test |
| `implement-game-domain-module` | 已归档 | 实现 `richman.domain` 共享领域模型，并同步主规格 `game-domain-model` |
| `implement-board-module` | 已归档 | 实现 `richman.board` 不可变棋盘、静态查询、环形移动、范围查询，并同步主规格 `board-spatial-model` |
| `implement-rules-module` | 已归档 | 实现 `richman.rules` 纯规则函数，并同步主规格 `rules-engine` |

当前活动 OpenSpec 变更：

| 变更 | 状态 | 说明 |
|---|---|---|
| 无 | - | 当前没有待处理的 active change |

最近一次验证结果：

- `uv run pytest`：67 passed
- `uv run ruff check`：passed
- `uv run ruff format --check`：passed
- `uv run mypy src`：passed，17 source files

---

## 已完成的设计确认

### 游戏规则

- 游戏是 2-4 人回合制终端大富翁。
- 每位玩家起始现金 `$2000`，开局位于起点但不触发奖金。
- 回合固定分为五阶段：效果更新、掷骰移动、落点效果、玩家动作、回合结束。
- 胜利条件：只剩一名未破产玩家。
- 棋盘格类型为六种：起点、地块、机会卡、入狱格、监狱格、空白格。
- 普通玩家走到监狱格无事发生；入狱格才触发入狱判决。
- 起点奖金通过移动结算统一处理：进入 START 的次数决定发放次数，正好停在 START 计一次，开局站在 START 不计。
- 移动卡可前进或后退，可触发连锁落点效果。
- 移动卡连锁过程中只处理阶段③落点效果；购买、升级、使用拆除卡等阶段④动作只在最终落点执行一次。
- 入狱后当前回合立即结束，不进入阶段④。
- 地主在监狱中时，其地块不收租。
- 买地、升级是可选动作；现金不足时对应动作不出现，不触发破产。
- 拆除卡在阶段④使用，成功使用后消耗一张。
- 破产回收按地块获取时间从早到晚执行，回收价为购买价加累计升级投入。
- 若卖光资产仍不足支付租金，玩家出局；地主不收到缺少部分，也不收到破产玩家剩余现金。破产玩家现金清零只是状态清理。

### 信息可见性

- 公开信息：棋盘格类型、玩家位置、地块归属与等级、监狱状态、当前回合、骰子点数、机会卡内容、卡牌使用结果、破产消息。
- 私密信息：现金、手牌数量、每块地具体投入成本。
- engine 可以完整记录事件日志，但 render 展示事件时必须按 viewer 隐藏私有字段。
- AIPlayer 与 HumanPlayer 都只能接收裁剪后的 `PlayerView`，不能访问 `InternalGameState`。

---

## 当前架构决策

### 模块划分

开发顺序：

```text
domain -> board, rules, render, player -> engine -> app
```

模块职责：

| 模块 | 职责 |
|---|---|
| `domain` | 纯类型、枚举、数据结构、常量；零逻辑、零依赖 |
| `board` | 棋盘空间计算：格子查询、环形移动、范围查询 |
| `rules` | 纯规则函数：租金、卡牌意图、破产回收、资金判断 |
| `player` | 玩家决策；不持有状态、不修改状态 |
| `render` | 终端展示和输入原语；不包含游戏逻辑 |
| `engine` | 唯一完整状态持有者和状态写入口；执行回合流程 |
| `app` | 装配配置、模块、玩家并启动游戏 |

### 状态真源

- `InternalGameState` 是唯一完整可变状态树。
- 地块运行时状态只保存在 `InternalGameState.properties_by_position`。
- `players[].holdings` 只保存 `PropertyRef`，不复制地块等级、归属、成本等可变字段。
- 购买、升级、拆除、破产回收只修改 `properties_by_position`；玩家 holdings 只增删引用。

### 视图边界

- `PlayerView`：给特定 player 决策用，只包含该玩家可见的信息。
- `GameSnapshot`：给 render 展示用，包含公开棋盘/玩家信息、当前 viewer 私有信息、事件日志展示视图。
- `engine_context` 只能暴露 render 输入原语和必要展示辅助，不能暴露 `InternalGameState`、engine mutation API、随机源或其他玩家私密字段。

### 关键类型

- `CellType`: START / PROPERTY / CHANCE / GO_TO_JAIL / JAIL_SPACE / BLANK
- `CardType`: MONEY_GAIN / MONEY_LOSS / MOVE / GO_TO_JAIL / JAIL_PASS / DEMOLISH
- `MoveDirection`: FORWARD / BACKWARD / RANDOM
- `Action`: BUY / UPGRADE / USE_DEMOLISH / USE_JAIL_PASS / ACCEPT_JAIL / SKIP
- `Phase`: EFFECT_UPDATE / DICE_ROLL / LANDING / ACTION / END
- `PropertyState`: 地块运行时状态真源
- `PropertyRef`: 玩家持有地块引用
- `InternalGameState`: engine 内部完整状态
- `GameSnapshot`: render 展示快照
- `PlayerView`: player 决策视图

---

## 已实现

### 项目与测试骨架

- 已建立 `src/richman` 包布局和 `tests` 测试目录。
- 已配置 `pyproject.toml`、`uv.lock`、Ruff、mypy、pytest 和 Textual/Rich 运行依赖。
- 已提供 `richman` CLI 入口和基础包导入 smoke test。
- 已提供 Textual TUI adapter 的最小 smoke test，当前仍使用 `render.ports.GameSnapshotView` 占位视图。

### domain 模块

- 已实现 `src/richman/domain/models.py` 和 `richman.domain` 公共导出入口。
- 已实现共享枚举：`CellType`、`CardType`、`MoveDirection`、`Action`、`Phase`、`GameEventType`。
- 已实现默认常量：`START_BONUS`、`JAIL_ROUNDS`、`DICE_SIDES`、`DEMOLISH_RANGE`。
- 已实现不可变静态配方：`PropertyTemplate`、`CardDefinition`、`BoardCellDefinition`、`GameConfig`。
- 已实现卡牌意图：`GrantMoneyIntent`、`DeductMoneyIntent`、`MoveIntent`、`GoToJailIntent`、`ObtainCardIntent` 和 `CardIntent`。
- 已实现运行时状态：`PropertyState`、`PropertyRef`、`HandCards`、`PlayerState`、`ReclaimPlan`、`InternalGameState`。
- 已实现视图与事件模型：`PublicCellInfo`、`PublicBoardInfo`、`PublicPlayerInfo`、`PlayerView`、`GameSnapshot`、`GameEvent`。
- 已新增 `tests/test_domain_models.py`，覆盖公共 API、依赖边界、不可变模型、状态引用、快照私有/公开分离和事件清单。
- 已同步主 OpenSpec 规格：`openspec/specs/game-domain-model/spec.md`。

### board 模块

- 已实现 `src/richman/board/model.py` 和 `richman.board` 公共导出入口。
- 已实现不可变 `Board`，保存静态棋盘格序列和 START 位置。
- 已实现不可变 `MoveResult`，返回 `new_position` 和 `start_crossings`。
- 已实现 `create(config)`，从 `GameConfig.board_cells` 创建棋盘并校验非空、恰好一个 START、PROPERTY 模板约束。
- 已实现 `total_cells`、`get_cell_type`、`get_property_template` 静态查询。
- 已实现 `move`，支持正向/反向/多圈环形移动和 START 进入次数统计。
- 已实现 `get_range`，按中心、顺时针、逆时针顺序返回去重范围位置。
- 已新增 `tests/test_board.py`，覆盖公共 API、依赖边界、创建校验、静态查询、移动计数和范围查询。
- 已同步主 OpenSpec 规格：`openspec/specs/board-spatial-model/spec.md`。

### rules 模块

- 已实现 `src/richman/rules/model.py` 和 `richman.rules` 公共导出入口。
- 已实现 `calculate_rent(template, level)`，按地块模板租金表和等级返回租金，并拒绝非法等级。
- 已实现 `can_upgrade(template, property_state)`，仅判断等级是否低于最高等级，不处理现金约束。
- 已实现 `resolve_card_intent(card)`，将金钱、移动、入狱、免狱卡和拆除卡解析为 domain 中的结构化 intent，不执行效果。
- 已实现 `calculate_bankruptcy(properties, shortfall)`，按 `acquired_at` 从早到晚生成回收计划，退款为购买价加累计升级投入。
- 已实现 `can_afford(cash, amount)`，判断非负现金是否覆盖非负金额，并拒绝负输入。
- 已新增 `tests/test_rules.py`，覆盖公共 API、依赖边界、纯函数无副作用、租金、升级、卡牌解析、支付判断和破产回收。
- 已同步主 OpenSpec 规格：`openspec/specs/rules-engine/spec.md`。

## 尚未实现

建议优先实现顺序：

1. `render`：将当前占位视图逐步对齐 `domain.GameSnapshot`，保留 adapter 边界。
2. `player`：实现 HumanPlayer 和基础 AIPlayer。
3. `engine`：实现五阶段主循环、状态修改、事件日志、视图裁剪。
4. `app`：加载配置、创建玩家、启动游戏。

---

## 必须优先覆盖的测试场景

从 `MODULE_DESIGN.md` 同步而来，后续实现必须覆盖：

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

## 后续开发注意事项

- 不要让 `player` 或 `render` 直接修改状态。
- 不要在 `PlayerView` 或 `GameSnapshot` 中泄露其他玩家现金、手牌数量、具体投入成本。
- 不要在玩家 `holdings` 中复制地块等级、归属或成本，避免双写不一致。
- 不要在 LANDING 的 START 分支再次发奖金；奖金只由 `MoveResult.start_crossings` 驱动。
- 不要让移动卡连锁中的中间落点执行阶段④动作。
- 不要在破产租金不足时给地主发放部分款项或破产玩家剩余现金。
- `rules` 应保持纯函数，随机、状态修改和事件记录都留给 engine。
- `engine_context` 只允许作为受限输入/展示上下文，不应成为访问 engine 内部的后门。

---

## 下一步建议

下一次继续开发时，可以进入 `render` 或 `player` 模块；二者都只依赖 `domain`，可在 `engine` 前独立实现和测试。
