## Why

Engine 是整个游戏唯一持有完整可变状态树的模块，负责运行五阶段回合主循环并连接 board、rules、player、render 四个平级模块。前六个模块（domain、board、rules、player、render、项目骨架）已全部实现并通过验证，engine 是实现顺序中的下一个模块，完成后即可进入 app 装配层。

## What Changes

- 新增 `richman.engine` 模块，提供 `GameEngine` 类
- 实现 `create(config, board, players, renderer)` 工厂方法，校验输入并初始化 `InternalGameState`
- 实现 `start()` 主循环，调度五阶段回合（效果更新 → 掷骰移动 → 落点效果 → 玩家动作 → 回合结束）
- 实现 `get_state()` 和 `snapshot_for(viewer_index)` 供调试和渲染使用
- 实现回合内全部游戏机制：移动与起点奖金、落点处理（空地/己方/他人地块、机会卡、入狱格/监狱格、空白格）、租金支付与破产回收、机会卡抽取与效果执行、移动卡连锁、入狱判决、阶段④动作计算与执行（购买/升级/拆除/跳过）
- 实现事件日志记录与视图裁剪（`PlayerView`、`GameSnapshot`）
- 实现受限 `InputContext`，确保 player 模块只能通过 `prompt_choice` 获取输入

## Capabilities

### New Capabilities

- `engine-core`: GameEngine 的状态初始化、主循环、回合推进和游戏结束判定
- `engine-turn-flow`: 五阶段回合流程（EFFECT_UPDATE / DICE_ROLL / LANDING / ACTION / END）
- `engine-landing`: 落点处理逻辑（六种格子类型、租金、入狱、机会卡）
- `engine-bankruptcy`: 债务支付与破产回收流程
- `engine-view-generation`: PlayerView 与 GameSnapshot 的裁剪生成

### Modified Capabilities

无。engine 消费已有模块的公共 API，不修改任何现有规格的行为要求。

## Impact

- 新增 `src/richman/engine/model.py` 和 `src/richman/engine/__init__.py`
- 依赖 `domain`（类型）、`board`（空间计算）、`rules`（规则计算）、`player`（决策接口）、`render`（渲染接口）
- 仅被 `app` 模块依赖
- 新增 `tests/test_engine.py`
