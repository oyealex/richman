## Context

`richman.engine` 是唯一持有完整可变状态树（`InternalGameState`）的模块，运行五阶段回合主循环。它依赖 domain（类型）、board（空间计算）、rules（规则计算）、player（决策）、render（渲染）五个模块，仅被 app 模块消费。

当前所有依赖模块已实现并通过验证（93 tests, ruff + mypy 全部通过）。MODULE_DESIGN.md 已详细定义了 engine 的接口、状态树结构、视图生成规则和完整的回合流程。

## Goals / Non-Goals

**Goals:**
- 实现 `GameEngine` 类，持有并修改 `InternalGameState`
- 实现五阶段回合循环：EFFECT_UPDATE → DICE_ROLL → LANDING → ACTION → END
- 实现全部落点处理逻辑（六种格子类型、机会卡、移动卡连锁、入狱）
- 实现破产回收流程（债务支付、地块回收、玩家出局）
- 实现动作计算与执行（BUY/UPGRADE/USE_DEMOLISH/SKIP）
- 实现 PlayerView 和 GameSnapshot 的裁剪生成
- 提供受限 InputContext，只暴露 prompt_choice，不暴露内部状态

**Non-Goals:**
- 不实现存档/读档（序列化）
- 不实现网络对战
- 不实现交易阶段或自定义阶段
- 不修改其他模块的公共 API

## Decisions

### 1. 工厂方法 create + 可选 seed

`GameEngine.create(config, board, players, renderer, seed=None)` 作为静态工厂，校验 JAIL_SPACE 存在性、初始化随机数生成器和 `InternalGameState`。

**Alternatives considered**: 构造函数直接初始化。选择工厂方法是因为需要校验（JAIL_SPACE 位置查找），且 seed 参数提供测试确定性。

### 2. 回合流程用返回值传播"提前结束"

`_process_landing()` 和各子方法返回 `bool`（True = 回合应结束）。入狱、破产等情况通过返回值链向上传播，调用方检查后跳过后续阶段。

**Alternatives considered**: 异常传播或状态标志。返回值更明确、类型安全，不引入异常的控制流语义。

### 3. 移动卡连锁通过递归实现

`_execute_move_intent()` 在移动后递归调用 `_process_landing()`，自然处理多级连锁。每次只处理阶段③落点效果，阶段④只在最外层 landing 返回后执行一次。

**Rationale**: 递归直接表达"连锁"语义，代码量少。棋盘有限大小和步数范围保证不会无限递归。

### 4. 债务支付统一入口 `_pay_debt`

租金、机会卡扣款、银行付款统一使用 `_pay_debt(amount, creditor_index, event_types)`，内部处理"现金足够→直接付"和"现金不足→回收地块→付清或破产"两条分支。

**Alternatives considered**: 每种债务场景单独实现。统一入口避免重复代码和分叉行为。

### 5. 视图按需增量生成

`_build_snapshot()` 和 `_build_player_view()` 每次调用时从 `InternalGameState` + `Board` 重新构建视图，不缓存。Board 的不可变性保证公共信息一致性。

**Rationale**: 避免缓存失效问题。视图构建轻量（纯数据拷贝），性能不影响回合制游戏。

### 6. 受限 InputContext

`_EngineInputContext` 仅包装 `Renderer.prompt_choice()`，engine 将该实例传给 Player.decide()。Player 模块无法通过此上下文访问 InternalGameState 或 engine 的任何 mutation API。

**Rationale**: 符合 MODULE_DESIGN 的约束，防止 player 越权。

## Risks / Trade-offs

- **[Risk] 移动卡连环触发机会卡→移动卡，理论上可无限循环** → 实际上移动卡步数有限、棋盘有限，概率极低且最终会终止。暂不加循环检测。
- **[Risk] 空卡组** → CHANCE 格落在无卡组的情况未明确处理，但配置校验应在 app 层保证一致性。当前 engine 在无卡时直接跳过。
- **[Trade-off] 事件日志无限增长** → 一局完整游戏的事件数量有限（~数百条），不构成内存问题。如需限制可加最大条数截断。
