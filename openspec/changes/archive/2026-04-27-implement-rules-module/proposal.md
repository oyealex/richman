## Why

`domain` 和 `board` 已经提供共享领域类型与棋盘空间计算，但后续 `engine` 仍缺少一个可复用、可独立测试的规则计算层。现在需要实现 `rules` 模块，把租金、升级可行性、卡牌意图解析、破产回收和支付判断这些纯规则稳定下来，作为引擎执行回合流程前的基础能力。

## What Changes

- 新增 `richman.rules` 模块，提供不持有状态、不执行 I/O、不修改游戏状态的纯函数规则 API。
- 提供租金计算能力，根据 `PropertyTemplate.rents` 和地块等级返回应收租金。
- 提供升级可行性判断，仅判断地块等级是否允许继续升级，现金约束由 engine 结合支付判断处理。
- 提供卡牌意图解析，将 `CardDefinition` 转换为结构化 `CardIntent`，只描述效果，不执行移动、扣款、入狱或手牌变更。
- 提供破产回收方案计算，按地块获取时间从早到晚生成回收清单、退款总额和剩余缺口。
- 提供支付能力判断，供 engine 在生成购买、升级等可选动作时复用。
- 增加 rules 单元测试，覆盖正常规则、边界等级、非法输入、卡牌类型映射和破产回收顺序。

## Capabilities

### New Capabilities

- `rules-engine`: 定义游戏纯规则计算能力，包括租金、升级、卡牌意图、破产回收和支付能力判断。

### Modified Capabilities

无。

## Impact

- 影响代码：`src/richman/rules/`、`src/richman/rules/__init__.py`。
- 影响测试：新增 `tests/test_rules.py`。
- 依赖关系：`rules` 只依赖 `richman.domain` 和标准库，不依赖 `board`、`player`、`engine`、`render` 或 adapter。
- API 影响：新增 `richman.rules` 公共导出；不修改现有 `domain`、`board`、`render` 或 CLI API。
