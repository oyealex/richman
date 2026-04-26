## 1. Domain API 结构

- [x] 1.1 确定 `src/richman/domain` 的源码组织方式，并保留 `richman.domain` 作为公共导出入口
- [x] 1.2 在 domain 公共 API 中导出后续模块需要直接使用的枚举、常量、数据结构、卡牌意图和类型别名
- [x] 1.3 确认 domain 源码只依赖 Python 标准库，不导入 board、rules、player、engine、render 或 adapters

## 2. 枚举、常量与静态配方

- [x] 2.1 实现 `CellType`、`CardType`、`MoveDirection`、`Action`、`Phase` 和 `GameEventType`
- [x] 2.2 实现 `START_BONUS`、`JAIL_ROUNDS`、`DICE_SIDES`、`DEMOLISH_RANGE` 默认常量
- [x] 2.3 实现不可变 `PropertyTemplate`，包含名称、价格、四级租金和升级费
- [x] 2.4 实现不可变 `CardDefinition`，支持金钱卡、移动卡、入狱卡和可保留卡的定义字段
- [x] 2.5 实现不可变 `GameConfig`，承载棋盘格、卡片和默认游戏参数

## 3. 卡牌意图与运行时状态

- [x] 3.1 实现冻结的卡牌意图结构：`GrantMoneyIntent`、`DeductMoneyIntent`、`MoveIntent`、`GoToJailIntent`、`ObtainCardIntent`
- [x] 3.2 定义 `CardIntent` 类型别名，汇总所有卡牌意图结构
- [x] 3.3 实现 `PropertyState`、`PropertyRef`、`HandCards`、`PlayerState` 和 `ReclaimPlan`
- [x] 3.4 实现 `InternalGameState`，包含回合、当前玩家、阶段、骰子、玩家列表、地块状态索引、事件日志和可选动作

## 4. 视图、快照与事件模型

- [x] 4.1 实现公开棋盘和公开玩家信息结构，用于 `GameSnapshot` 的公开数据部分
- [x] 4.2 实现 `PlayerView`，用于 player 决策输入，并避免包含 render 布局对象或完整 `InternalGameState`
- [x] 4.3 实现 `GameSnapshot`，区分公开信息、viewer 私有状态、viewer 持有地完整状态、事件日志和可选动作
- [x] 4.4 实现 `GameEvent`，使用 `GameEventType` 和结构化数据映射表达事件日志条目

## 5. 测试覆盖

- [x] 5.1 新增 domain 导入和公共 API 导出测试，覆盖 `from richman.domain import PlayerState, Action, GameSnapshot`
- [x] 5.2 新增 domain 依赖边界测试，验证 domain 源码不导入上层模块
- [x] 5.3 新增枚举和常量测试，覆盖设计文档要求的枚举成员和默认常量
- [x] 5.4 新增不可变配方测试，验证 `PropertyTemplate`、`CardDefinition`、`GameConfig` 创建后不可修改
- [x] 5.5 新增运行时状态测试，验证 `PlayerState.holdings` 只保存 `PropertyRef`，可变地块字段保存在 `InternalGameState.properties_by_position`
- [x] 5.6 新增视图和事件模型测试，验证 `GameSnapshot` 的公开/私有字段分离，以及 `GameEventType` 覆盖模块设计中的事件清单

## 6. 质量验证

- [x] 6.1 运行 `uv run pytest`，确认现有测试和新增 domain 测试通过
- [x] 6.2 运行 `uv run ruff check` 和 `uv run ruff format --check`，确认 lint 和格式检查通过
- [x] 6.3 运行 `uv run mypy src`，确认 domain 类型定义满足项目类型检查配置
