# engine-turn-flow (delta)

## ADDED Requirements

### Requirement: DEMOLISH_TARGET accepts None as cancellation

系统 SHALL 在 `WAITING_FOR_DEMOLISH_TARGET` 状态收到 `target_position=None` 时将输入视为取消拆除操作，退回动作选择阶段，不消耗拆除卡。

#### Scenario: Engine returns to READY_FOR_ACTION on cancel

- **WHEN** 引擎处于 WAITING_FOR_DEMOLISH_TARGET 且收到 `EngineInput(kind=DEMOLISH_TARGET, target_position=None)`
- **THEN** 引擎 MUST 将 step_cursor 设为 READY_FOR_ACTION
- **AND** MUST NOT 调用 `_execute_demolish_target`
- **AND** MUST NOT 进入 END 阶段
- **AND** MUST NOT 消耗玩家的拆除卡

#### Scenario: Engine validation allows None for DEMOLISH_TARGET

- **WHEN** `_validate_input` 检查 DEMOLISH_TARGET 输入
- **AND** `engine_input.target_position` 为 None
- **THEN** 验证 MUST 通过（视为取消）
- **AND** MUST NOT 检查 `target_position in required.candidates`
