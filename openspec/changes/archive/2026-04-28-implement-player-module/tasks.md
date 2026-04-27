## 1. 模块结构与公共 API

- [x] 1.1 在 `src/richman/player/` 中建立 player 实现文件，并保持模块只导入 `richman.domain` 和标准库。
- [x] 1.2 定义 `Player` 抽象接口，包含 `name`、`wait_for_dice()`、`decide(view, actions, engine_context)` 和 `choose_demolish_target(view, candidates, engine_context)`。
- [x] 1.3 定义受限输入上下文协议或等价边界，用于 HumanPlayer 获取动作和目标选择，但不暴露 engine 状态写入 API。
- [x] 1.4 从 `richman.player` 包入口导出 `Player`、`HumanPlayer`、`AIPlayer` 及必要的公开辅助类型。

## 2. HumanPlayer 实现

- [x] 2.1 实现 `HumanPlayer` 构造与 `name` 属性，允许注入受限输入原语以支持掷骰等待。
- [x] 2.2 实现 `wait_for_dice()`，等待注入的输入原语完成，且不修改任何游戏状态。
- [x] 2.3 实现 `decide(view, actions, engine_context)`，将合法 `Action` 列表转换为用户选项并返回用户选择对应的 `Action`。
- [x] 2.4 在 `decide` 中拒绝空动作列表，并确保返回值只能来自传入的 `actions`。
- [x] 2.5 实现 `choose_demolish_target(view, candidates, engine_context)`，将候选位置转换为用户选项并返回用户选择的位置。
- [x] 2.6 在 `choose_demolish_target` 中拒绝空候选列表，并确保返回值只能来自传入的 `candidates`。

## 3. AIPlayer 实现

- [x] 3.1 实现 `AIPlayer` 构造与 `name` 属性，并保持 `wait_for_dice()` 为无状态直接返回。
- [x] 3.2 实现确定性的动作优先级策略，始终只从传入的 `actions` 中选择动作。
- [x] 3.3 覆盖入狱判决场景：只有 `ACCEPT_JAIL` 时返回 `ACCEPT_JAIL`，提供 `USE_JAIL_PASS` 时可选择使用免狱卡。
- [x] 3.4 实现稳定的拆除目标选择策略，默认从传入候选列表中选择固定位置。
- [x] 3.5 确保 AIPlayer 不调用随机源、不读取 `InternalGameState`、不导入 board/rules/engine/render。

## 4. 单元测试

- [x] 4.1 新增 player 公共 API 导入测试和源码依赖边界测试。
- [x] 4.2 覆盖 `Player` 接口的必需方法与 HumanPlayer、AIPlayer 的接口实现。
- [x] 4.3 覆盖 HumanPlayer 的掷骰等待、动作选择、拆除目标选择和非法空输入错误。
- [x] 4.4 覆盖 AIPlayer 的确定性动作选择、强制入狱、免狱卡选择、空动作错误和稳定目标选择。
- [x] 4.5 覆盖 player 决策不修改 `PlayerView` 中的玩家状态、地块状态、事件日志或可选动作数据。
- [x] 4.6 覆盖 player 信息边界，确认 player 测试替身只接收 `PlayerView` 和显式选项，不需要 `InternalGameState`。

## 5. 验证与交接

- [x] 5.1 运行 `uv run pytest` 确认测试通过。
- [x] 5.2 运行 `uv run ruff check` 和 `uv run ruff format --check` 确认风格检查通过。
- [x] 5.3 运行 `uv run mypy src` 确认类型检查通过。
- [x] 5.4 实现完成后更新 `docs/DEVELOPMENT_PROGRESS.md`，记录 player 模块状态和下一步建议。
