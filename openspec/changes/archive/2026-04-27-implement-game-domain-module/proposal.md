## Why

当前仓库已经建立模块骨架，但 `domain` 仍缺少可供 board、rules、player、engine、render 共同依赖的领域模型契约。先实现 `docs/MODULE_DESIGN.md` 中定义的 domain 模块，可以为后续模块提供稳定、零依赖、零逻辑的类型基础，避免各模块重复定义状态结构或隐式耦合。

## What Changes

- 在 `src/richman/domain` 中实现游戏领域模型，覆盖棋盘、卡片、玩家、动作、阶段、事件、破产回收、顶层状态树、快照、配置和常量。
- 保持 domain 模块无业务计算逻辑、无 I/O、无对 board/rules/player/engine/render 的依赖。
- 为 domain 模型补充单元测试，验证枚举、数据结构默认值、不可变配方和关键状态引用结构符合设计约束。
- 保持现有 render adapter、开发环境和 CLI 行为不变；本变更不引入破坏性 API 变更。

## Capabilities

### New Capabilities

- `game-domain-model`: 定义终端大富翁游戏的共享领域类型、枚举、数据结构、配置和常量，作为 board、rules、player、engine、render 等模块的共同基础。

### Modified Capabilities

无。

## Impact

- 主要影响 `src/richman/domain` 及其导出 API。
- 新增或更新针对 domain 模型的测试文件，预计位于 `tests` 目录。
- 后续 board、rules、player、engine、render 实现将依赖这些领域类型。
- 不新增运行时第三方依赖，不改变现有 CLI、Textual adapter 或 render 契约行为。
