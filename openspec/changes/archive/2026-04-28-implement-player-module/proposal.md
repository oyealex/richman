## Why

当前项目已完成 `domain`、`board` 和 `rules` 模块，但还缺少负责玩家输入与 AI 决策的 `player` 模块。按既有模块设计，`player` 需要在 `engine` 实现前先提供稳定的决策接口，确保后续回合流程可以通过统一边界获取人类玩家和 AI 玩家选择。

## What Changes

- 新增 `richman.player` 模块，定义无状态的玩家决策抽象和公共导出入口。
- 实现 `HumanPlayer`，通过受限 `engine_context` 调用渲染输入原语完成掷骰等待、动作选择和拆除目标选择。
- 实现基础 `AIPlayer`，只基于 `PlayerView`、可选动作列表和候选目标进行确定性决策。
- 保持 player 模块只依赖 `richman.domain` 和标准库，不依赖 board、rules、engine、render 或 adapter。
- 增加单元测试覆盖公共 API、依赖边界、动作校验、HumanPlayer 输入委托、AIPlayer 信息边界和拆除目标选择。

## Capabilities

### New Capabilities

- `player-decision-model`: 定义玩家决策模块的抽象接口、人类玩家输入委托、基础 AI 决策策略，以及 player 模块的信息边界和依赖边界。

### Modified Capabilities

无。

## Impact

- 受影响代码：`src/richman/player/`、`tests/`。
- 受影响 API：新增 `richman.player` 公共 API，供后续 `engine` 在掷骰、入狱判决、回合动作和拆除目标选择时调用。
- 依赖影响：不新增第三方运行时依赖；HumanPlayer 通过 `engine_context` 间接使用 render 输入原语，但 player 模块源码不导入 render。
- 后续影响：为 `engine` 模块实现五阶段主循环和玩家交互点提供决策边界。
