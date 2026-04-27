## 1. 模块结构与公共 API

- [x] 1.1 在 `src/richman/rules/` 中建立 rules 实现文件，并保持模块只导入 `richman.domain` 和标准库。
- [x] 1.2 从 `richman.rules` 包入口导出 `calculate_rent`、`can_upgrade`、`resolve_card_intent`、`calculate_bankruptcy`、`can_afford`。
- [x] 1.3 增加 rules 公共 API 导入测试和源码依赖边界测试，确认不依赖 board、player、engine、render 或 adapter。

## 2. 基础规则计算

- [x] 2.1 实现 `calculate_rent(template, level)`，按 `template.rents[level]` 返回租金。
- [x] 2.2 在 `calculate_rent` 中拒绝负等级和超出租金表范围的等级。
- [x] 2.3 实现 `can_upgrade(template, property_state)`，当等级低于最高有效等级时返回 `True`，满级时返回 `False`。
- [x] 2.4 在 `can_upgrade` 中拒绝负等级和超过最高有效等级的地块状态。
- [x] 2.5 实现 `can_afford(cash, amount)`，判断非负现金是否覆盖非负金额，并拒绝负输入。

## 3. 卡牌意图解析

- [x] 3.1 实现 `MONEY_GAIN` 到 `GrantMoneyIntent` 的解析，并校验 `amount` 存在且合法。
- [x] 3.2 实现 `MONEY_LOSS` 到 `DeductMoneyIntent` 的解析，并校验 `amount` 存在且合法。
- [x] 3.3 实现 `MOVE` 到 `MoveIntent` 的解析，并校验 `direction`、`min_steps`、`max_steps` 存在且步数范围合法。
- [x] 3.4 实现 `GO_TO_JAIL` 到 `GoToJailIntent` 的解析。
- [x] 3.5 实现 `JAIL_PASS` 和 `DEMOLISH` 到 `ObtainCardIntent` 的解析。
- [x] 3.6 确认 `resolve_card_intent` 不执行随机步数、移动、扣款、入狱、手牌变更或事件记录。

## 4. 破产回收计划

- [x] 4.1 实现 `calculate_bankruptcy(properties, shortfall)`，按 `acquired_at` 从早到晚选择回收地块。
- [x] 4.2 计算每块被回收地块的退款为 `purchase_price + upgrade_invested`。
- [x] 4.3 在退款覆盖资金缺口后停止继续选择地块，并返回 `remaining_shortfall=0`。
- [x] 4.4 当所有地块仍无法覆盖缺口时，返回剩余缺口。
- [x] 4.5 处理 `shortfall=0` 的空回收方案，并拒绝负数资金缺口。
- [x] 4.6 对相同 `acquired_at` 的地块保持传入列表中的相对顺序。

## 5. 单元测试

- [x] 5.1 新增 `tests/test_rules.py`，覆盖 rules 公共 API 导出、依赖边界和纯函数无状态修改。
- [x] 5.2 覆盖租金计算的所有等级、最低等级、最高等级和非法等级。
- [x] 5.3 覆盖升级可行性的可升级、满级、非法等级和不读取现金约束。
- [x] 5.4 覆盖所有卡牌类型的 intent 映射，以及缺少参数、负金额、非法移动步数范围等错误输入。
- [x] 5.5 覆盖支付能力判断的足够、不足、零金额和负输入。
- [x] 5.6 覆盖破产回收的获取时间排序、相同时间稳定顺序、刚好覆盖、超额覆盖、不足覆盖、零缺口和负缺口。

## 6. 验证与交接

- [x] 6.1 运行 `uv run pytest` 确认测试通过。
- [x] 6.2 运行 `uv run ruff check` 和 `uv run ruff format --check` 确认风格检查通过。
- [x] 6.3 运行 `uv run mypy src` 确认类型检查通过。
- [x] 6.4 实现完成后更新 `docs/DEVELOPMENT_PROGRESS.md`，记录 rules 模块状态和下一步建议。
