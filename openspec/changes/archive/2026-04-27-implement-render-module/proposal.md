## Why

当前项目已完成 `domain`、`board`、`rules` 和 `player` 模块，`render` 仍停留在占位契约，无法按 `GameSnapshot` 展示真实游戏局面，也无法为 `HumanPlayer` 提供稳定输入原语。按 `docs/MODULE_DESIGN.md` 的依赖顺序，需要先补齐 render 模块，才能让后续 engine 和 app 在不耦合具体 UI 框架的前提下推进完整回合流程。

## What Changes

- 将 `richman.render` 从占位视图契约扩展为面向 `domain.GameSnapshot`、`GameEvent` 和人类输入的渲染边界。
- 提供框架无关的 render 协议，覆盖整帧展示、事件日志展示、选项输入、数字输入和终局展示。
- 保持 render 模块只依赖 `richman.domain` 和标准库，不导入 engine、board、rules、player 或具体 adapter。
- 调整首个 Textual TUI adapter，使其消费 render 协议或其兼容实现，并保持 Textual 专属类型隔离在 adapter 包内。
- 增加测试覆盖公共 API、依赖边界、快照展示输入、事件隐私遮蔽、输入校验和 Textual adapter smoke 行为。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `render-adapter-architecture`: 将现有 render adapter 边界从占位契约完善为可实现的 render 模块契约，明确 `GameSnapshot` 展示、事件隐私遮蔽、输入原语和 Textual adapter 隔离要求。

## Impact

- 受影响代码：`src/richman/render/`、`src/richman/adapters/textual_tui/`、`tests/`。
- 受影响 API：更新 `richman.render` 公共 API，供后续 `engine` 推送快照、展示事件、获取人类玩家输入和展示终局。
- 依赖影响：不新增第三方运行时依赖；Textual/Rich 继续仅作为 adapter 实现细节保留在 `richman.adapters.textual_tui` 内。
- 后续影响：为 `engine` 实现五阶段主循环、HumanPlayer 输入委托和 app 装配提供稳定渲染边界。
