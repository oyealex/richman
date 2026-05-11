## 1. Domain 数据结构

- [x] 1.1 新增 step/input 相关枚举和数据类，覆盖 ROLL_DICE、ACTION_CHOICE、DEMOLISH_TARGET、JAIL_CHOICE。
- [x] 1.2 新增 `StepResult` 或等价 frame 数据结构，包含 snapshot、增量 events、phase、required_input 和 game_over。
- [x] 1.3 为结构化输入增加基本校验字段：kind、player_index、action、target_position。
- [x] 1.4 更新 domain 包导出，确保新类型可从 `richman.domain` 导入。

## 2. Engine Step API

- [x] 2.1 修改 `GameEngine.create`，移除 renderer 参数并初始化 step 游标。
- [x] 2.2 实现 `GameEngine.advance(input=None)` 主入口，返回 `StepResult`。
- [x] 2.3 将回合开始、监狱倒计时、等待掷骰、骰子结果、移动、落点、动作、回合结束拆成可恢复 step。
- [x] 2.4 在所有人类输入节点返回 `RequiredInput`，不调用 renderer 或阻塞输入方法。
- [x] 2.5 实现结构化输入校验，拒绝错误 kind、错误 player、非法 action 和非法拆除目标。
- [x] 2.6 暴露本 step 新增事件，同时保留 snapshot 完整事件日志。
- [x] 2.7 在终局时返回 game-over StepResult，记录 GAME_OVER，但不调用 render 方法。

## 3. AI 与玩家决策边界

- [x] 3.1 为 AI 当前玩家的 ROLL_DICE 输入生成非阻塞确认输入。
- [x] 3.2 使用 AIPlayer 策略从 RequiredInput.options 中选择合法动作。
- [x] 3.3 使用 AIPlayer 策略从 RequiredInput.candidates 中选择合法拆除目标。
- [x] 3.4 确保 step-driven TUI/adapter 不通过 HumanPlayer 阻塞输入路径获取人类输入。
- [x] 3.5 保留或调整 HumanPlayer 兼容路径，使其不导入 engine、render adapter 或 UI 框架。

## 4. 兼容运行与 Console Driver

- [x] 4.1 将 `GameEngine.start(max_turns=None)` 改为基于 `advance()` 的兼容循环。
- [x] 4.2 实现 console step driver：渲染 StepResult、收集 RequiredInput、提交 EngineInput。
- [x] 4.3 更新 app 层 engine 装配，创建 engine 时不传 renderer。
- [x] 4.4 更新 `run_game`，通过 console step driver 保留 `richman play` 现有语义。
- [x] 4.5 确保 `richman play --players --max-turns --seed --config` 参数行为保持兼容。

## 5. Render/Adapter 边界

- [x] 5.1 调整 render 相关使用点，使 engine 不导入 `richman.render`。
- [x] 5.2 保留 render 格式化和 prompt 原语供 console driver 使用。
- [x] 5.3 确保 adapter 只消费 GameSnapshot/StepResult，不读取或修改 InternalGameState。
- [x] 5.4 确保终局展示由 adapter/driver 根据 StepResult 或 GAME_OVER 事件完成。

## 6. 测试与回归

- [x] 6.1 新增 step API 测试：初次 advance 开始回合并返回 TURN_START。
- [x] 6.2 新增 ROLL_DICE required input 和有效输入推进测试。
- [x] 6.3 新增 ACTION_CHOICE required input、非法动作拒绝和空动作跳过测试。
- [x] 6.4 新增 DEMOLISH_TARGET required input、候选目标校验和执行测试。
- [x] 6.5 新增 JAIL_CHOICE required input、有无免狱卡分支测试。
- [x] 6.6 新增 AI-only 对局自动推进和 game_over StepResult 测试。
- [x] 6.7 更新 app/CLI 测试，验证 `richman play` 仍可 bounded run。
- [x] 6.8 运行 `uv run pytest`、`uv run ruff`、`uv run mypy` 并修复回归。
